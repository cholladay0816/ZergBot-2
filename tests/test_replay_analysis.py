from s2clientprotocol import raw_pb2, sc2api_pb2

from zergbot.replay_analysis import comparative_report, replay_snapshot


def test_player_perspective_fields_and_fog_snapshot_exclusion(tmp_path):
    response = sc2api_pb2.ResponseObservation()
    response.observation.game_loop = 224
    response.observation.player_common.player_id = 2
    response.observation.player_common.minerals = 400
    for tag, alliance, display in [(1, 1, 1), (2, 4, 1), (3, 4, 2)]:
        response.observation.raw_data.units.add(
            tag=tag,
            alliance=alliance,
            display_type=display,
            unit_type=48,
            owner=2 if alliance == 1 else 1,
            weapon_cooldown=9,
            engaged_target_tag=10,
        )
    sample = replay_snapshot(response, 2)
    assert sample["actual_player_id"] == 2
    assert sample["economy"]["minerals"] == 400
    assert sample["economy"]["vespene"] is None
    assert len(sample["units"]) == 2
    assert sample["units"][0]["weapon_cooldown"] == 9
    assert sample["units"][1]["weapon_cooldown"] is None
    assert sample["units"][1]["orders"] is None
    comparative_report(
        tmp_path, [{"perspective": 2, "samples": [sample], "termination": "completed"}]
    )
    report = (tmp_path / "replay-analysis-report.md").read_text()
    assert "never live bot inputs" in report
    assert "400" in report


def test_replay_unit_details_are_capped_but_counts_are_complete():
    response = sc2api_pb2.ResponseObservation()
    for tag in range(10):
        response.observation.raw_data.units.add(
            tag=tag, alliance=1, display_type=raw_pb2.Visible, unit_type=48
        )
    sample = replay_snapshot(response, 1, cap=2)
    assert len(sample["units"]) == 2
    assert sample["units_omitted"] == 8
    assert sample["own_counts"] == {"MARINE": 10}
