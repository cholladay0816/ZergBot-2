import json
from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from s2clientprotocol.raw_pb2 import Unit as RawUnit
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.position import Point2

from zergbot.agents import Action, AgentRegistry, CommandArbiter, Intent, Observation
from zergbot.diagnostics import DiagnosticConfig, MatchDiagnostics, summarize
from zergbot.telemetry import TelemetryAdapter, describe_effects, describe_unit


def recorder(tmp_path, **kwargs):
    return MatchDiagnostics(
        tmp_path, {"map": "AbyssalReefLE", "seed": 1}, DiagnosticConfig(**kwargs)
    )


def test_serialization_crash_report_and_no_secret_collection(tmp_path, monkeypatch):
    monkeypatch.setenv("API_TOKEN", "sensitive-environment-value")
    r = MatchDiagnostics(tmp_path, {"map": "AbyssalReefLE", "password": "private-value"})
    r.record("action_error", 224, tag=7, ability_id=1386, result=12)
    with pytest.raises(ValueError):
        r.record("action_error", 224, chat="private-chat")
    r.finish(termination="crashed_or_interrupted", error_type="RuntimeError")
    text = (tmp_path / "match.json").read_text()
    assert all(
        secret not in text
        for secret in ["private-value", "private-chat", "sensitive-environment-value"]
    )
    result = json.loads(text)
    assert result["termination"] == "crashed_or_interrupted"
    assert result["game_seconds_observed"] == 10
    assert result["events"][0]["ability_id"] == 1386
    assert result["findings"][0]["event_ids"] == [1]
    assert "not proven casters" in (tmp_path / "report.md").read_text()


def test_bounded_event_retention_rate_and_totals(tmp_path):
    r = recorder(tmp_path, max_events=3, max_events_per_frame=2)
    for frame in range(3):
        for tag in range(4):
            r.record("created", frame, tag=tag, unit_type="ROACH", scope="own")
    assert len(r.events) == 3
    assert r.totals["created"] == 12
    assert r.dropped == 9
    assert [e["id"] for e in r.events] == [4, 5, 6]


def test_clock_separates_game_wall_and_disabled_telemetry(tmp_path):
    now = [100.0]
    r = MatchDiagnostics(tmp_path, {}, clock=lambda: now[0])
    r.record("created", 224, tag=1, unit_type="ROACH", scope="own")
    now[0] = 102
    assert r.payload()["wall_seconds"] == 2
    assert r.payload()["observed_game_to_wall_ratio"] == 5
    assert r.due(0)
    r.last_sample = 0
    assert not r.due(111)
    assert r.due(112)
    disabled = recorder(tmp_path / "disabled", enabled=False)
    TelemetryAdapter(disabled).sample(Mock())
    disabled.finish()
    assert not disabled.directory.exists()


def test_slow_writer_has_no_unbounded_queue_or_loop_block(tmp_path):
    r = recorder(tmp_path)
    r.pending_write = Future()
    r.executor = Mock()
    for _ in range(100):
        r.checkpoint(force=True)
    r.executor.submit.assert_not_called()
    assert not tmp_path.joinpath("match.json").exists()


def test_checkpoint_and_finish_atomic_artifacts(tmp_path):
    r = recorder(tmp_path)
    r.checkpoint(force=True)
    r.pending_write.result(timeout=5)
    assert json.loads((tmp_path / "match.json").read_text())["termination"] == "in_progress"
    (tmp_path / "match.SC2Replay").write_bytes(b"fixture")
    r.finish("Tie", "time_limit_or_tie")
    result = json.loads((tmp_path / "match.json").read_text())
    assert result["replay"] == "match.SC2Replay"
    assert result["outcome"] == "Tie"
    assert not list(tmp_path.glob("*.tmp"))


def test_summary_evidence_does_not_claim_exact_supply_duration():
    result = summarize(
        {
            "events": [
                {
                    "id": 5,
                    "kind": "snapshot",
                    "economy": {"supply_left": 0, "supply_cap": 44, "minerals": 1000},
                    "visible_enemy": [],
                }
            ]
        }
    )
    assert len(result) == 2
    assert result[0]["event_ids"] == [5]
    assert "not exact duration" in result[0]["finding"]


def fake_unit(tag=7):
    return SimpleNamespace(
        tag=tag,
        type_id=U.ROACH,
        _proto=RawUnit(
            tag=tag, unit_type=U.ROACH.value, health=40, weapon_cooldown=9, engaged_target_tag=99
        ),
        position=Point2((10, 20)),
        is_flying=False,
        is_detector=False,
        ground_range=4,
        air_range=0,
    )


def test_enemy_unavailable_fields_are_unknown_even_when_default_or_populated():
    bot = SimpleNamespace(get_terrain_height=lambda p: 128)
    unit = fake_unit()
    enemy = describe_unit(bot, unit, False)
    assert enemy["weapon_cooldown"] is None
    assert enemy["engaged_target_tag"] is None
    assert enemy["orders"] is None
    assert enemy["shield"] is None
    assert enemy["cloak_raw"] is None
    assert enemy["health"] == 40
    assert describe_unit(bot, unit, True)["weapon_cooldown"] == 9


def test_effects_do_not_invent_caster():
    effect = SimpleNamespace(id="PSISTORM", owner=2, radius=1.5, positions={Point2((1, 2))})
    data = describe_effects(SimpleNamespace(state=SimpleNamespace(effects=[effect])))[0]
    assert data["caster_tag"] is None
    assert data["owner"] == 2


def test_repeated_orders_counted_without_filling_event_ring(tmp_path):
    r = recorder(tmp_path)
    adapter = TelemetryAdapter(r)
    observations = [Observation(1, 1, False)]
    registry = AgentRegistry()
    registry.sync(observations)
    arbiter = CommandArbiter()
    arbiter.submit(Intent(1, Action.ATTACK, 10, "army_objective"))
    for frame in range(100):
        adapter.decisions(observations, registry, arbiter, frame)
    assert r.command_counts["ATTACK"] == 100
    assert r.totals["decision"] == 1
    assert r.totals["command_attempt"] == 1
    assert len(r.events) == 2
    adapter.decisions([], registry, CommandArbiter(), 101)
    assert adapter.last_decisions == {}


def test_damage_volume_bound_skips_expensive_work(tmp_path):
    r = recorder(tmp_path, max_damage_per_frame=1)
    adapter = TelemetryAdapter(r)
    adapter.damage_frame, adapter.damage_count = 4, 1
    bot = SimpleNamespace(state=SimpleNamespace(game_loop=4))
    adapter.damage(bot, Mock(), 10)  # no access to units/effects is necessary after cap
    assert r.dropped == 1


def test_unknown_death_is_not_claimed_as_enemy_loss(tmp_path):
    r = recorder(tmp_path)
    adapter = TelemetryAdapter(r)
    adapter.destroyed(4, 999)
    assert r.events[-1]["scope"] == "unknown"


@pytest.mark.parametrize("value", [0, -1])
def test_bad_limits_rejected(value):
    with pytest.raises(ValueError):
        DiagnosticConfig(max_events=value)


def test_sample_excludes_fog_snapshots_and_preserves_visible_counts(tmp_path):
    r = recorder(tmp_path)
    adapter = TelemetryAdapter(r)
    visible, hidden = fake_unit(1), fake_unit(2)
    visible.is_visible, hidden.is_visible = True, False
    bot = SimpleNamespace(
        state=SimpleNamespace(game_loop=0, action_errors=[], effects=[], upgrades=set()),
        units=[],
        structures=[],
        enemy_units=[visible, hidden],
        enemy_structures=[],
        minerals=50,
        vespene=0,
        supply_used=12,
        supply_cap=14,
        supply_left=2,
        workers=SimpleNamespace(amount=12, idle=SimpleNamespace(amount=0)),
        larva=SimpleNamespace(amount=3),
        townhalls=SimpleNamespace(amount=1),
        already_pending=lambda _: 0,
        get_terrain_height=lambda _: 128,
    )
    adapter.sample(bot)
    snapshot = r.payload()["events"][0]
    assert [u["tag"] for u in snapshot["visible_enemy"]] == [1]
    assert snapshot["visible_enemy_counts"] == {"ROACH": 1}
    adapter.sample(bot)
    assert r.snapshot_calls == 1


def test_combat_event_flood_cannot_evict_economy_timeline(tmp_path):
    r = recorder(tmp_path, max_events=2, max_snapshots=2)
    r.record("snapshot", 0, economy={"minerals": 50})
    for frame in range(1, 20):
        r.record("created", frame, tag=frame, unit_type="ROACH", scope="own")
    r.record("snapshot", 112, economy={"minerals": 100})
    events = r.payload()["events"]
    assert [e["frame"] for e in events if e["kind"] == "snapshot"] == [0, 112]
    assert len(r.events) == 2
    assert len(r.snapshots) == 2
    r.record("snapshot", 224, economy={"minerals": 150})
    assert [e["frame"] for e in r.snapshots] == [112, 224]


def test_morph_confirmation_totals_survive_event_eviction(tmp_path):
    r = recorder(tmp_path, max_events=1)
    r.record(
        "type_changed", 0, tag=1, unit_type="ROACHBURROWED", previous_type="ROACH", scope="own"
    )
    r.record(
        "type_changed", 4, tag=1, unit_type="ROACH", previous_type="ROACHBURROWED", scope="own"
    )
    r.record("created", 8, tag=2, unit_type="ROACH", scope="own")
    assert r.payload()["morph_confirmations"] == {"BURROW": 1, "EMERGE": 1}
