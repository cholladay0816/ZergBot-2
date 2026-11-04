from dataclasses import replace

from zergbot.config import BotConfig
from zergbot.scouting import ScoutManager, SiteEvidence, assess_muta

C = BotConfig()


def verdict(site, **changes):
    args = dict(
        frame=224,
        config=C,
        ready_bases=3,
        workers=66,
        minerals=900,
        gas=900,
        army=12,
        threatened=False,
        local_aa=0,
        mobile_counter=False,
    )
    args.update(changes)
    return assess_muta(site, **args)


def observed():
    site = SiteEvidence((10, 10))
    site.observe(0, True, 10, C.scout_fresh_frames)
    site.observe(112, True, 10, C.scout_fresh_frames)
    return site


def test_unknown_and_partial_vision_never_mean_no_defenses():
    assert verdict(None) == "unknown_no_mineral_line"
    site = SiteEvidence((10, 10))
    assert verdict(site) == "unknown_stale_or_unseen"
    site.observe(0, True, 10, 448)
    assert verdict(site) == "unknown_incomplete_coverage"
    site = observed()
    site.observe(224, False, 0, 448)
    assert verdict(site) == "unknown_incomplete_coverage"
    assert site.workers == 10  # retained history is not presented as currently visible
    assert verdict(site, frame=1000) == "unknown_stale_or_unseen"


def test_candidate_requires_fresh_repeated_coverage_workers_and_reserves():
    site = observed()
    assert verdict(site).startswith("candidate_for_controlled_test")
    for change in ({"minerals": 100}, {"gas": 100}, {"workers": 25}, {"ready_bases": 1}):
        assert verdict(site, **change) == "blocked_economy_reserve"
    for change in ({"threatened": True}, {"army": 0}):
        assert verdict(site, **change) == "blocked_home_defense"
    assert verdict(site, local_aa=1) == "blocked_known_anti_air"
    assert verdict(site, mobile_counter=True) == "blocked_known_anti_air"
    assert verdict(replace(site, workers=2)) == "blocked_low_worker_value"


def test_stale_scouting_requires_two_new_observations_and_only_confirmed_loss_clears():
    site = observed()
    site.observe(1000, True, 10, 448)
    assert site.confirmations == 1
    site.observe(1004, True, 10, 448)
    assert site.confirmations == 1
    scout = ScoutManager(C)
    scout.scout_tag = 10
    scout.defenses = {20: (0, (0, 0), True)}
    scout.destroyed(20)
    assert not scout.defenses and scout.losses == 0
    scout.destroyed(10)
    scout.destroyed(10)
    assert scout.losses == 1


def test_advisory_event_serializes_without_leaking_hidden_information(tmp_path):
    from zergbot.diagnostics import MatchDiagnostics

    recorder = MatchDiagnostics(tmp_path, {"opponent_race": "Protoss"})
    recorder.record(
        "muta_assessment",
        0,
        verdict="unknown_no_mineral_line",
        advisory_only=True,
        target=None,
        age_frames=None,
        coverage=False,
        confirmations=0,
        visible_workers=None,
        remembered_local_aa=0,
        remembered_mobile_counter=False,
        scope="live_observation_memory_not_omniscience",
    )
    assert recorder.payload()["metadata"]["opponent_race"] == "Protoss"
    assert recorder.events[0]["visible_workers"] is None
