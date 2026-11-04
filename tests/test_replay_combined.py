import copy

import pytest

from zergbot.replay_combined import combine_passes


def perspective(player, frames=(0, 112)):
    return {
        "perspective": player,
        "replay_sha256": "a" * 64,
        "base_build": "Base98310",
        "data_version": "same",
        "step_frames": 112,
        "termination": "completed",
        "samples": [
            {
                "frame": f,
                "actual_player_id": player,
                "economy": {"minerals": player * 50},
                "own_counts": {"SCV": 12},
                "own_upgrade_ids": [],
                "units": [
                    {"tag": player, "alliance": 1, "owner": player, "orders": []},
                    {"tag": 99, "alliance": 4, "owner": 3 - player, "orders": None},
                ],
            }
            for f in frames
        ],
    }


def test_combined_view_uses_each_own_perspective_and_keeps_missing_frames_unknown():
    data = combine_passes([perspective(1), perspective(2, (0,))])
    first = data["samples"][0]["players"]
    assert first["1"]["economy"]["minerals"] == 50
    assert first["2"]["economy"]["minerals"] == 100
    assert len(first["2"]["units"]) == 1
    assert first["2"]["units"][0]["tag"] == 2
    assert first["2"]["own_unit_details_omitted"] == 11
    assert data["samples"][1]["players"]["2"] is None


@pytest.mark.parametrize("key", ["replay_sha256", "base_build", "data_version", "step_frames"])
def test_mismatched_replays_cannot_be_joined(key):
    first, second = perspective(1), perspective(2)
    second[key] = "different"
    with pytest.raises(ValueError, match="provenance"):
        combine_passes([first, second])


def test_missing_or_wrong_player_and_duplicate_frames_are_rejected():
    first, second = perspective(1), perspective(2)
    with pytest.raises(ValueError, match="exactly"):
        combine_passes([first])
    wrong = copy.deepcopy(second)
    wrong["samples"][0]["actual_player_id"] = 1
    with pytest.raises(ValueError, match="Actual player"):
        combine_passes([first, wrong])
    second["samples"].append(second["samples"][0])
    with pytest.raises(ValueError, match="Duplicate frame"):
        combine_passes([first, second])
