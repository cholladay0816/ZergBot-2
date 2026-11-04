"""Compare paired local match artifacts without treating capped ties as wins."""

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean

MATCH_KEYS = (
    "map",
    "difficulty",
    "seed",
    "python_seed",
    "realtime",
    "game_limit_seconds",
    "python",
    "burnysc2",
    "game_version",
    "data_version",
)


def metrics(data):
    snapshots = [e for e in data["events"] if e["kind"] == "snapshot"]
    middle = [e for e in snapshots if 120 <= e["game_seconds"] <= 360]
    result = {
        "outcome": data["outcome"],
        "termination": data["termination"],
        "observed_game_seconds": data["game_seconds_observed"],
        "wall_seconds": data["wall_seconds"],
        "dropped_events": data["dropped_events"],
    }
    for target in (240, 360):
        nearby = [e for e in snapshots if abs(e["game_seconds"] - target) < 0.01]
        result[f"roaches_{target}"] = (
            sum(nearby[0]["own_counts"].get(k, 0) for k in ("ROACH", "ROACHBURROWED"))
            if nearby
            else None
        )
        result[f"minerals_{target}"] = nearby[0]["economy"]["minerals"] if nearby else None
    result["midgame_samples"] = len(middle)
    result["zero_larva_fraction_120_360"] = (
        mean(e["economy"]["larvae"] == 0 for e in middle) if middle else None
    )
    result["supply_block_fraction_120_360"] = (
        mean(e["economy"]["supply_left"] < 1 and e["economy"]["supply_cap"] < 200 for e in middle)
        if middle
        else None
    )
    result["mean_minerals_120_360"] = (
        mean(e["economy"]["minerals"] for e in middle) if middle else None
    )
    result["inject_attempts"] = data.get("command_attempt_counts", {}).get("INJECT", 0)
    result["burrow_observations"] = sum(
        e["kind"] == "type_changed" and e["unit_type"] == "ROACHBURROWED" for e in data["events"]
    )
    result["emerge_observations"] = sum(
        e["kind"] == "type_changed"
        and e["unit_type"] == "ROACH"
        and e["previous_type"] == "ROACHBURROWED"
        for e in data["events"]
    )
    if "morph_confirmations" in data:
        result["burrow_observations"] = data["morph_confirmations"].get("BURROW", 0)
        result["emerge_observations"] = data["morph_confirmations"].get("EMERGE", 0)
    result["action_errors"] = sum(e["kind"] == "action_error" for e in data["events"])
    result["invalid_hatchery_placements"] = sum(
        e["kind"] == "action_error" and e["ability_id"] == 1152 and e["result"] == 44
        for e in data["events"]
    )
    destruction_counts = data.get("destruction_observation_counts")
    result["destruction_count_scope"] = (
        "lifetime_recorded" if destruction_counts is not None else "retained_events"
    )
    for unit_type in ("ROACH", "ROACHBURROWED"):
        result[f"own_{unit_type.lower()}_destructions"] = (
            destruction_counts.get(f"own:{unit_type}", 0)
            if destruction_counts is not None
            else sum(
                e["kind"] == "destroyed"
                and e.get("scope") == "own"
                and e.get("unit_type") == unit_type
                for e in data["events"]
            )
        )
    result["burrow_damage_events_retained"] = sum(
        e["kind"] == "damage" and e.get("victim", {}).get("burrowed", False) for e in data["events"]
    )
    result["instrumentation_seconds"] = data.get("instrumentation_seconds")
    return result


def compare_pair(baseline, candidate):
    for data in (baseline, candidate):
        if (
            data.get("termination") not in {"completed", "time_limit_or_tie"}
            or data.get("error_type")
            or data.get("outcome") not in {"Victory", "Defeat", "Tie"}
        ):
            raise ValueError("Incomplete or failed matches cannot be performance-compared")
    mismatch = [
        key for key in MATCH_KEYS if baseline["metadata"].get(key) != candidate["metadata"].get(key)
    ]
    if mismatch:
        raise ValueError("Unmatched settings: " + ", ".join(mismatch))
    if baseline.get("bot_config", {}).get("game_step") != candidate.get("bot_config", {}).get(
        "game_step"
    ):
        raise ValueError("Unmatched game step")
    if baseline["limits"]["sample_frames"] != candidate["limits"]["sample_frames"]:
        raise ValueError("Unmatched sample cadence")
    return {
        "seed": baseline["metadata"]["seed"],
        "baseline": metrics(baseline),
        "candidate": metrics(candidate),
    }


def load_matches(paths):
    matches = {}
    for path in paths:
        text = path.read_bytes()
        data = json.loads(text)
        seed = data["metadata"]["seed"]
        if seed in matches:
            raise ValueError("Duplicate seed")
        matches[seed] = (
            data,
            {"path": str(path.resolve()), "sha256": hashlib.sha256(text).hexdigest()},
        )
    return matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, nargs="+", required=True)
    parser.add_argument("--candidate", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline-revision", required=True)
    parser.add_argument("--candidate-revision", required=True)
    args = parser.parse_args()
    baseline, candidate = load_matches(args.baseline), load_matches(args.candidate)
    if baseline.keys() != candidate.keys():
        parser.error("Baseline and candidate must contain the same unique seeds")
    pairs = []
    for seed in sorted(baseline):
        pair = compare_pair(baseline[seed][0], candidate[seed][0])
        pair["evidence"] = {"baseline": baseline[seed][1], "candidate": candidate[seed][1]}
        pairs.append(pair)
    report = {
        "baseline_revision": args.baseline_revision,
        "candidate_revision": args.candidate_revision,
        "pairs": pairs,
        "interpretation": "Exploratory paired runs; capped ties are censored. "
        "Multiple bundled changes do not isolate causes. Sampling/eviction limit metrics.",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "comparison.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# Matched-seed economy experiment",
        "",
        report["interpretation"],
        "",
        f"Baseline: {args.baseline_revision}; candidate: {args.candidate_revision}.",
        "",
        "| Seed | Variant | Outcome | Seconds | Roach 240/360 | Minerals 360 | "
        "Injects | Action errors | Invalid hatchery |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for pair in pairs:
        for variant in ("baseline", "candidate"):
            metric = pair[variant]
            outcome = (
                "Capped tie" if metric["termination"] == "time_limit_or_tie" else metric["outcome"]
            )
            lines.append(
                f"| {pair['seed']} | {variant} | {outcome} | "
                f"{metric['observed_game_seconds']:.2f} | {metric['roaches_240']} / "
                f"{metric['roaches_360']} | {metric['minerals_360']} | "
                f"{metric['inject_attempts']} | {metric['action_errors']} | "
                f"{metric['invalid_hatchery_placements']} |"
            )
    lines += [
        "",
        "## Micro observations",
        "",
        "Destruction observations describe the last known roach type; do not infer an exact "
        "attacker or cause. Retained-event counts may be incomplete. Morph totals can include "
        "several cycles by the same unit.",
        "",
        "| Seed | Variant | Burrows | Emergences | Exposed / buried destruction | Count scope |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for pair in pairs:
        for variant in ("baseline", "candidate"):
            metric = pair[variant]
            lines.append(
                f"| {pair['seed']} | {variant} | {metric['burrow_observations']} | "
                f"{metric['emerge_observations']} | {metric['own_roach_destructions']} / "
                f"{metric['own_roachburrowed_destructions']} | "
                f"{metric['destruction_count_scope']} |"
            )
    lines += [
        "",
        "Detailed metrics, source artifact paths and SHA-256 fingerprints: comparison.json. "
        "A missing timed sample is null, not an inferred zero. Resource metrics and micro "
        "counts are observational; do not claim a stable win rate from this small sample.",
    ]
    (args.output / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
