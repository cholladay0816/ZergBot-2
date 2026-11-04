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
