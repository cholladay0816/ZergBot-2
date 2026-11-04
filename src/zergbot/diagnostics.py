"""Bounded, observation-scoped evidence; never records chat, environment or credentials."""

import json
import re
import time
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiagnosticConfig:
    enabled: bool = True
    sample_frames: int = 112
    max_events: int = 10000
    max_snapshots: int = 512
    max_detail_units: int = 96
    max_events_per_frame: int = 128
    max_damage_per_frame: int = 16
    checkpoint_seconds: float = 30.0

    def __post_init__(self):
        if (
            min(
                self.sample_frames,
                self.max_events,
                self.max_snapshots,
                self.max_detail_units,
                self.max_events_per_frame,
                self.max_damage_per_frame,
                self.checkpoint_seconds,
            )
            <= 0
        ):
            raise ValueError("Diagnostic limits must be positive")


# Values are built from explicit numeric/enum game fields at the adapter boundary.
# Unknown fields are rejected rather than accidentally logging object reprs or secrets.
EVENT_FIELDS = {
    "expansion": {"reason", "location"},
    "snapshot": {
        "own",
        "visible_enemy",
        "own_counts",
        "visible_enemy_counts",
        "effects",
        "economy",
        "upgrades",
        "pending",
        "detail_omitted",
        "engagements",
    },
    "decision": {
        "tag",
        "action",
        "reason",
        "target",
        "health_fraction",
        "burrowed",
        "can_burrow",
        "can_emerge",
        "researched",
        "recovering",
        "pending_morph",
        "observed_order",
    },
    "command_attempt": {"tag", "action", "reason", "target"},
    "action_error": {"tag", "ability_id", "result"},
    "created": {"tag", "unit_type", "scope"},
    "destroyed": {"tag", "unit_type", "scope"},
    "type_changed": {"tag", "unit_type", "previous_type", "scope"},
    "upgrade": {"upgrade"},
    "damage": {
        "victim",
        "hp_shield_loss",
        "candidate_attackers",
        "effects",
        "attribution",
        "candidate_scan_omitted",
    },
    "end": {"outcome", "termination", "error_type"},
}
META_FIELDS = {
    "map",
    "difficulty",
    "seed",
    "realtime",
    "game_limit_seconds",
    "python",
    "burnysc2",
    "bot_version",
    "game_version",
    "base_build",
    "data_version",
}


def safe_metadata(values):
    result = {}
    for key in META_FIELDS & values.keys():
        value = values[key]
        if value is None or isinstance(value, (bool, int, float)):
            result[key] = value
        else:
            # Names/versions only: not arbitrary paths, exception text, argv or settings.
            result[key] = re.sub(r"[^a-zA-Z0-9_. -]", "_", str(value))[:80]
    return result


class MatchDiagnostics:
    def __init__(self, directory: Path, metadata: dict, config=None, clock=time.perf_counter):
        self.config = config or DiagnosticConfig()
        self.directory = directory
        self.metadata = safe_metadata(metadata)
        self.bot_config = {}
        self.clock = clock
        self.started = clock()
        self.events = deque(maxlen=self.config.max_events)
        self.snapshots = deque(maxlen=self.config.max_snapshots)
        self.morph_confirmations = Counter()
        self.totals = Counter()
        self.command_counts = Counter()
        self.dropped = 0
        self.sequence = 0
        self.frame = -1
        self.frame_events = 0
        self.last_sample = -self.config.sample_frames
        self.last_checkpoint = self.started
        self.max_frame = 0
        self.outcome = None
        self.termination = "in_progress"
        self.error_type = None
        self.overhead_seconds = 0.0
        self.snapshot_calls = 0
        self.executor = None
        self.pending_write = None
        self.write_errors = 0
        self.finished = False

    def due(self, frame):
        return self.config.enabled and frame - self.last_sample >= self.config.sample_frames

    def record(self, kind, frame, **data):
        if not self.config.enabled:
            return
        if kind not in EVENT_FIELDS or data.keys() - EVENT_FIELDS[kind]:
            raise ValueError("Unknown diagnostic event or field")
        self.max_frame = max(self.max_frame, frame)
        self.totals[kind] += 1
        if kind == "type_changed":
            if data.get("unit_type") == "ROACHBURROWED" and data.get("previous_type") == "ROACH":
                self.morph_confirmations["BURROW"] += 1
            if data.get("unit_type") == "ROACH" and data.get("previous_type") == "ROACHBURROWED":
                self.morph_confirmations["EMERGE"] += 1
        if frame != self.frame:
            self.frame, self.frame_events = frame, 0
        if self.frame_events >= self.config.max_events_per_frame:
            self.dropped += 1
            return
        self.frame_events += 1
        self.sequence += 1
        buffer = self.snapshots if kind == "snapshot" else self.events
        if len(buffer) == buffer.maxlen:
            self.dropped += 1
        buffer.append(
            {
                "id": self.sequence,
                "kind": kind,
                "frame": frame,
                "game_seconds": round(frame / 22.4, 3),
                **data,
            }
        )

    def payload(self):
        wall = max(0.0, self.clock() - self.started)
        return {
            "schema_version": 1,
            "metadata": dict(self.metadata),
            "bot_config": dict(self.bot_config),
            "limits": asdict(self.config),
            "outcome": self.outcome,
            "termination": self.termination,
            "error_type": self.error_type,
            "game_seconds_observed": self.max_frame / 22.4,
            "wall_seconds": wall,
            "observed_game_to_wall_ratio": self.max_frame / 22.4 / wall if wall > 0 else None,
            "totals": dict(self.totals),
            "command_attempt_counts": dict(self.command_counts),
            "morph_confirmations": dict(self.morph_confirmations),
            "dropped_events": self.dropped,
            "snapshot_calls": self.snapshot_calls,
            "instrumentation_seconds": self.overhead_seconds,
            "checkpoint_write_errors": self.write_errors,
            "replay": "match.SC2Replay" if (self.directory / "match.SC2Replay").exists() else None,
            "visibility": "Own state and currently visible enemies only; no full replay analysis.",
            "events": sorted([*self.events, *self.snapshots], key=lambda event: event["id"]),
        }

    def checkpoint(self, force=False):
        if not self.config.enabled:
            return
        now = self.clock()
        if self.pending_write is not None:
            if not self.pending_write.done():
                return  # at most one background write; no unbounded queue
            try:
                self.pending_write.result()
            except OSError:
                self.write_errors += 1
            self.pending_write = None
        if not force and now - self.last_checkpoint < self.config.checkpoint_seconds:
            return
        self.last_checkpoint = now
        if self.executor is None:
            self.executor = ThreadPoolExecutor(
                max_workers=1, thread_name_prefix="match-diagnostics"
            )
        self.pending_write = self.executor.submit(write_artifacts, self.directory, self.payload())

    def finish(self, outcome=None, termination="completed", error_type=None):
        if self.finished:
            return
        self.finished = True
        self.outcome, self.termination = outcome, termination
        self.error_type = re.sub(r"[^a-zA-Z0-9_]", "", error_type or "")[:80] or None
        self.record(
            "end",
            self.max_frame,
            outcome=outcome,
            termination=termination,
            error_type=self.error_type,
        )
        if not self.config.enabled:
            return
        if self.executor is not None:
            self.executor.shutdown(wait=True)
        if self.pending_write is not None:
            try:
                self.pending_write.result()
            except OSError:
                self.write_errors += 1
        write_artifacts(self.directory, self.payload())


def summarize(payload):
    events = payload["events"]
    snapshots = [e for e in events if e["kind"] == "snapshot"]
    findings = []

    def finding(title, evidence, next_step):
        findings.append(
            {"finding": title, "event_ids": evidence[:12], "next_experiment": next_step}
        )

    blocked = [
        e["id"]
        for e in snapshots
        if e["economy"]["supply_left"] < 1 and e["economy"]["supply_cap"] < 200
    ]
    if blocked:
        finding(
            f"Supply-blocked in {len(blocked)} retained samples (not exact duration)",
            blocked,
            "Increase overlord lead time; compare blocked-sample rate with the same seed.",
        )
    floating = [e["id"] for e in snapshots if e["economy"]["minerals"] >= 800]
    if floating:
        finding(
            f"At least 800 minerals in {len(floating)} retained samples",
            floating,
            "Inspect larvae, saturation, pending production and supply before changing spending.",
        )
    errors = [e["id"] for e in events if e["kind"] == "action_error"]
    if errors:
        finding(
            "SC2 reported rejected actions; attempts are not successful casts",
            errors,
            "Group ability/result codes and correlate unit tags with subsequent observations.",
        )
    retreat = [
        e["id"]
        for e in events
        if e["kind"] == "decision" and e["reason"] in {"burrow_unavailable", "burrow_unresearched"}
    ]
    if retreat:
        finding(
            "Roaches retreated because burrowing was unavailable",
            retreat,
            "Compare research timing and individual availability before tuning health thresholds.",
        )
    damage = [e["id"] for e in events if e["kind"] == "damage"]
    if damage:
        finding(
            "Observed own HP/shield losses have candidate causes, not exact attacker attribution",
            damage,
            "Review distances, terrain, cloak and effects beside the replay; retain ambiguity.",
        )
    air = [e["id"] for e in snapshots if any(u["flying"] for u in e["visible_enemy"])]
    if air:
        finding(
            "Visible enemy air units occurred; roaches cannot attack air",
            air,
            "Check enemy types, timing and queen coverage before an anti-air transition.",
        )
    if not findings:
        finding(
            "No heuristic bottleneck detected in retained evidence",
            [],
            "Inspect timeline and replay; absence of sampled evidence is not absence of a problem.",
        )
    return findings


def write_artifacts(directory, payload):
    directory.mkdir(parents=True, exist_ok=True)
    findings = summarize(payload)
    payload = {**payload, "findings": findings}
    lines = [
        "# Match diagnostics",
        "",
        f"Outcome: {payload['outcome'] or 'unknown'}; termination: {payload['termination']}.",
        f"Observed game time: {payload['game_seconds_observed']:.2f}s; "
        f"wall time (including startup): {payload['wall_seconds']:.2f}s.",
        f"Retained events: {len(payload['events'])}; dropped/evicted: {payload['dropped_events']}.",
        f"Replay: {payload['replay'] or 'not available'}.",
        "",
        "Own state is known; enemy detail is limited to current visibility. Enemy orders, "
        "weapon cooldowns and engaged targets are unknown. No full replay/observer pass was run.",
        "Damage events are observed HP/shield deltas, including possible self/environment damage; "
        "fatal-frame damage can be absent. Candidate attackers and effects are correlations, "
        "not proven casters or causes. Base weapon ranges exclude upgrades. Terrain-height "
        "differences are observations, not a universal damage bonus.",
        "",
        "Sampling and ring-buffer eviction limit completeness. Event IDs reference match.json. "
        "Counts and findings use retained evidence; event totals include rate-limited events.",
        "",
    ]
    for item in findings:
        lines += [
            f"- {item['finding']}. Evidence: {item['event_ids']}.",
            f"  Next experiment: {item['next_experiment']}",
        ]
    lines += [
        "",
        "## Economy timeline (retained samples)",
        "",
        "| Game seconds | Minerals | Gas | Workers | Supply | Larvae | Roaches |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    last_bucket = -1
    for event in payload["events"]:
        if event["kind"] != "snapshot":
            continue
        bucket = int(event["game_seconds"] // 60)
        if bucket == last_bucket:
            continue
        last_bucket = bucket
        economy = event["economy"]
        count = event.get("own_counts", {})
        roaches = count.get("ROACH", 0) + count.get("ROACHBURROWED", 0)
        lines.append(
            f"| {event['game_seconds']:.1f} | {economy['minerals']} | "
            f"{economy.get('vespene')} | {economy.get('workers')} | "
            f"{economy.get('supply_used')}/{economy['supply_cap']} | "
            f"{economy.get('larvae')} | {roaches} |"
        )
    morphs = Counter(
        e["unit_type"]
        for e in payload["events"]
        if e["kind"] == "type_changed" and e["unit_type"] in {"ROACH", "ROACHBURROWED"}
    )
    losses = Counter(
        e.get("unit_type") or "unknown"
        for e in payload["events"]
        if e["kind"] == "destroyed" and e["scope"] == "own"
    )
    lines += [
        "",
        "## Command and observation evidence",
        "",
        f"Attempt counts (not confirmations): {payload.get('command_attempt_counts', {})}.",
        f"Observed roach type transitions in retained events: {dict(morphs)}.",
        f"Own destruction-event types: {dict(losses)}. These may include worker "
        "consumption for construction, not just combat kills.",
    ]
    for event in payload["events"]:
        if event["kind"] == "action_error":
            lines.append(
                f"- Event {event['id']} at {event['game_seconds']:.2f}s: "
                f"unit {event['tag']}, ability {event['ability_id']}, "
                f"SC2 result code {event['result']}."
            )
    if (directory / "replay-analysis-report.md").exists():
        lines += [
            "",
            "Separate post-game evidence: [replay analysis](replay-analysis-report.md). "
            "This was not available to the live bot.",
        ]
    for name, content in [
        ("match.json", json.dumps(payload, indent=2, allow_nan=False)),
        ("report.md", "\n".join(lines) + "\n"),
    ]:
        temporary = directory / (name + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(directory / name)
