from zergbot.base_defense import BaseDefense, Threat

BASES = {1: (0, 0), 2: (50, 0), 3: (100, 0)}


def test_natural_and_third_pressure_outside_main_envelope():
    d = BaseDefense()
    assert d.select(BASES, [Threat(9, (52, 0))], 0, 0).base_tag == 2
    assert d.select(BASES, [Threat(9, (102, 0))], 1, 0).base_tag == 3


def test_ties_are_deterministic_and_small_count_changes_do_not_oscillate():
    d = BaseDefense()
    threats = [Threat(9, (52, 0)), Threat(8, (2, 0))]
    assert d.select(dict(reversed(list(BASES.items()))), threats, 0, 0).base_tag == 1
    threats.append(Threat(10, (53, 0)))
    assert d.select(BASES, threats, 200, 0).base_tag == 1
    threats.append(Threat(11, (54, 0)))
    assert d.select(BASES, threats, 201, 0).base_tag == 2


def test_hold_is_bounded_and_does_not_hold_dead_or_departed_threat():
    d = BaseDefense()
    first = [Threat(9, (52, 0))]
    d.select(BASES, first, 0, 0)
    more = first + [Threat(i, (2, i)) for i in range(3)]
    assert d.select(BASES, more, 100, 0).base_tag == 2
    assert d.select(BASES, more, 112, 0).base_tag == 1
    assert d.select(BASES, first, 113, 0).base_tag == 2
    assert d.select(BASES, [], 114, 0) is None
    assert d.base_tag is None


def test_real_attack_preempts_small_worker_squad_immediately():
    d = BaseDefense()
    worker = Threat(8, (1, 0), True)
    assert d.select(BASES, [worker], 0, 2).worker_only
    result = d.select(BASES, [worker, Threat(9, (51, 0))], 1, 2)
    assert result.base_tag == 2 and not result.worker_only


def test_disabled_worker_squad_and_three_workers_use_full_defense():
    d = BaseDefense()
    assert not d.select(BASES, [Threat(8, (1, 0), True)], 0, 0).worker_only
    assert not d.select(BASES, [Threat(i, (i, 0), True) for i in range(3)], 1, 2).worker_only


def test_destroyed_base_and_equal_distance_targets():
    d = BaseDefense()
    assert d.select(BASES, [Threat(9, (51, 0))], 0, 0).base_tag == 2
    assert d.select({1: (0, 0)}, [Threat(9, (51, 0))], 1, 0) is None
    result = d.select(BASES, [Threat(9, (-1, 0)), Threat(8, (1, 0))], 2, 0)
    assert result.target == (1, 0)


def test_recovery_endpoint_prefers_unthreatened_base_without_claiming_safe_path():
    assert BaseDefense.retreat(BASES, [Threat(9, (1, 0))], (0, 0)) == (50, 0)
    assert BaseDefense.retreat(BASES, [Threat(9, (51, 0))], (0, 0)) == (0, 0)
    assert BaseDefense.retreat({}, [], (4, 5)) == (4, 5)


def test_defense_event_uses_real_recorder_and_json_contract(tmp_path, json_roundtrip):
    import numpy as np

    from zergbot.base_defense import DefenseObjective, defense_sample
    from zergbot.diagnostics import MatchDiagnostics

    recorder = MatchDiagnostics(tmp_path, {})
    objective = DefenseObjective(np.int64(2), (np.float32(50), np.float32(1)), False)
    recorder.record("defense_objective", 112, **defense_sample(objective, (0, 0), BASES))
    event = json_roundtrip(list(recorder.events))[0]
    assert event["base_tag"] == 2 and event["target"] == [50, 1]
    recorder.record("defense_objective", 224, **defense_sample(None, (0, 0), BASES))
    assert json_roundtrip(list(recorder.events))[-1]["base_tag"] is None


def test_defense_order_cannot_override_recovery_or_morph_wait():
    from zergbot.agents import Action, CommandArbiter, Observation, RoachAgent
    from zergbot.config import BotConfig
    from zergbot.strategy import ArmyStrategy

    config = BotConfig()
    agent = RoachAgent(1)
    for frame, obs, expected in [
        (0, Observation(1, 0.2, False, True, False, True), Action.BURROW),
        (4, Observation(1, 0.2, False, False, False, True), Action.WAIT),
        (8, Observation(1, 0.3, True, False, True, True), Action.WAIT),
    ]:
        arbiter = CommandArbiter()
        for order in ArmyStrategy().orders([obs], True, config):
            arbiter.submit(order)
        arbiter.submit(agent.decide(obs, frame, config))
        assert arbiter.commands[1].action is expected
