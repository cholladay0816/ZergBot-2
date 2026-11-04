from zergbot.combat_report import combat_lines
from zergbot.diagnostics import DiagnosticConfig, MatchDiagnostics


def test_report_preserves_ambiguous_and_missing_damage_causes():
    payload = {
        "events": [
            {
                "id": 1,
                "kind": "damage",
                "game_seconds": 62,
                "hp_shield_loss": 20,
                "candidate_attackers": [{"type": "MARINE"}, {"type": "SIEGETANK"}],
            },
            {
                "id": 2,
                "kind": "damage",
                "game_seconds": 64,
                "hp_shield_loss": 4,
                "candidate_attackers": [],
            },
            {
                "id": 3,
                "kind": "snapshot",
                "effects": [{"effect": "RAVAGERCORROSIVEBILECP"}],
                "own": [{"buff_ids": [17], "cloak_raw": None}],
                "visible_enemy": [],
            },
        ]
    }
    report = "\n".join(combat_lines(payload))
    assert "| 1 | 24.0 | 2 | 1 | 1 |" in report
    assert "does not establish an attacker" in report
    assert "unavailable in older artifact" in report
    assert "RAVAGERCORROSIVEBILECP" in report


def test_lifetime_decisions_and_destructions_survive_eviction_with_bounded_keys(tmp_path):
    r = MatchDiagnostics(tmp_path, {}, DiagnosticConfig(max_events=1))
    r.record("destroyed", 0, tag=1, unit_type="ROACH", scope="own")
    for n in range(300):
        r.record("decision", n, tag=1, action="ATTACK", reason=str(n))
    payload = r.payload()
    assert payload["destruction_observation_counts"] == {"own:ROACH": 1}
    assert sum(payload["decision_change_counts"].values()) == 300
    assert len(payload["decision_change_counts"]) <= 128
    assert len(payload["events"]) == 1


def test_action_errors_decode_with_death_correlation_without_claiming_cause():
    from zergbot.combat_report import action_error_description

    event = {"id": 3, "game_seconds": 5, "frame": 112, "tag": 7, "ability_id": 1386, "result": 2}
    text = action_error_description(event, {(112, 7): 2})
    assert "BURROWDOWN_ROACH" in text and "NotSupported" in text
    assert "event 2" in text and "not proof" in text
    assert "destruction" not in action_error_description(event, {(112, 8): 2})
    event.update(ability_id=999999, result=999999)
    assert action_error_description(event, {}).count("unknown") == 2
