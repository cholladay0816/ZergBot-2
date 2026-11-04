from copy import deepcopy

import pytest

from zergbot.compare import compare_pair, metrics


def match():
    return {
        "metadata": {"seed": 1, "map": "AbyssalReefLE"},
        "outcome": "Tie",
        "termination": "time_limit_or_tie",
        "game_seconds_observed": 240,
        "wall_seconds": 30,
        "dropped_events": 0,
        "limits": {"sample_frames": 112},
        "events": [
            {
                "kind": "snapshot",
                "game_seconds": 240,
                "own_counts": {"ROACH": 2, "ROACHBURROWED": 1},
                "economy": {"minerals": 800, "larvae": 0, "supply_left": 0, "supply_cap": 30},
            }
        ],
    }


def test_missing_timed_sample_is_unknown_and_capped_tie_is_not_win():
    result = metrics(match())
    assert result["roaches_240"] == 3
    assert result["roaches_360"] is None
    assert result["termination"] == "time_limit_or_tie"
    assert result["outcome"] == "Tie"
    assert result["zero_larva_fraction_120_360"] == 1


def test_reject_unmatched_settings_and_cadence():
    baseline = match()
    candidate = deepcopy(baseline)
    candidate["metadata"]["seed"] = 2
    with pytest.raises(ValueError, match="seed"):
        compare_pair(baseline, candidate)
    candidate = deepcopy(baseline)
    candidate["limits"]["sample_frames"] = 224
    with pytest.raises(ValueError, match="cadence"):
        compare_pair(baseline, candidate)


def test_compare_pairs_same_seed_and_preserves_metrics():
    baseline, candidate = match(), match()
    candidate["events"][0]["own_counts"]["ROACH"] = 8
    pair = compare_pair(baseline, candidate)
    assert pair["baseline"]["roaches_240"] == 3
    assert pair["candidate"]["roaches_240"] == 9
