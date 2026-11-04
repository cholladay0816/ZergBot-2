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


def test_unknown_replay_unit_type_remains_unknown():
    from zergbot.replay_analysis import unit_name

    assert unit_name(999999) == "UNKNOWN_TYPE_999999"


def test_score_presence_and_zero_are_distinct_and_strict_json_serializable(json_roundtrip):
    response = sc2api_pb2.ResponseObservation()
    response.observation.player_common.player_id = 1
    empty = replay_snapshot(response, 1)
    assert all(v is None for v in empty["economy_score"].values())
    response.observation.score.score_details.collected_minerals = 1234
    response.observation.score.score_details.collected_vespene = 0
    response.observation.score.score_details.collection_rate_minerals = 900.5
    sample = json_roundtrip(replay_snapshot(response, 1))
    assert sample["economy_score"]["collected_minerals"] == 1234
    assert sample["economy_score"]["collected_vespene"] == 0
    assert sample["economy_score"]["collection_rate_minerals"] == 900.5
    assert sample["economy_score"]["collection_rate_vespene"] is None
    assert sample["actual_player_id"] == 1


def test_single_player_cli_does_not_request_two_player_merge(tmp_path, monkeypatch):
    import sys
    from unittest.mock import AsyncMock, Mock

    from zergbot import replay_analysis, replay_combined

    replay = tmp_path / "test.SC2Replay"
    replay.write_bytes(b"test placeholder; mocked protocol")
    payload = dict(perspective=2, samples=[], termination="completed")
    run = AsyncMock(return_value=payload)
    report = Mock()
    combined = Mock()
    monkeypatch.setattr(replay_analysis, "perspective_pass", run)
    monkeypatch.setattr(replay_analysis, "comparative_report", report)
    monkeypatch.setattr(replay_combined, "write_combined", combined)
    monkeypatch.setattr(sys, "argv", ["replay_analysis", str(replay), "--player", "2"])
    replay_analysis.main()
    run.assert_awaited_once_with(replay, 2, 112, 1000)
    report.assert_called_once_with(tmp_path, [payload])
    combined.assert_not_called()
