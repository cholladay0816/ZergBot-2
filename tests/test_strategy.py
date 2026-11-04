from zergbot.agents import Action, CommandArbiter, Intent, Observation
from zergbot.config import BotConfig
from zergbot.strategy import ArmyStrategy

C = BotConfig()


def roster(count=15):
    return [Observation(i, 1.0, False) for i in range(count)]


def test_worker_squad_does_not_redirect_main_army():
    strategy = ArmyStrategy()
    orders = strategy.orders(
        roster(), False, C, worker_target=(0, 0), positions={i: (i, 0) for i in range(15)}
    )
    defenders = [o for o in orders if o.reason == "worker_defense"]
    assert {o.tag for o in defenders} == {0, 1}
    assert all(o.target == (0, 0) for o in defenders)
    assert all(
        o.action is Action.ATTACK and o.target is None for o in orders if o.tag not in {0, 1}
    )


def test_squad_is_stable_and_prunes_dead_recovering_and_distant_units():
    s = ArmyStrategy()
    positions = {i: (i, 0) for i in range(15)}
    s.orders(roster(), False, C, worker_target=(0, 0), positions=positions)
    positions[0], positions[1], positions[2] = (10, 0), (11, 0), (0, 0)
    s.orders(roster(), False, C, worker_target=(0, 0), positions=positions)
    assert s.defenders == {0, 1}
    units = [Observation(1, 0.3, True)] + roster()[2:]
    s.orders(units, False, C, worker_target=(0, 0), positions=positions)
    assert s.defenders == {2, 3}
    positions[2] = (100, 0)
    s.orders(units, False, C, worker_target=(0, 0), positions=positions)
    assert s.defenders == {3, 4}
    s.orders(units, False, C)
    assert not s.defenders


def test_full_attack_and_survival_override_worker_assignment():
    s = ArmyStrategy()
    orders = s.orders(
        roster(3), True, C, worker_target=(0, 0), positions={i: (i, 0) for i in range(3)}
    )
    assert all(o.reason == "defend" for o in orders)
    assert not s.defenders
    orders = s.orders(
        roster(3), False, C, worker_target=(0, 0), positions={i: (i, 0) for i in range(3)}
    )
    arbiter = CommandArbiter()
    for order in orders:
        arbiter.submit(order)
    arbiter.submit(Intent(0, Action.WAIT, 100, "morph_in_flight"))
    assert arbiter.commands[0].action is Action.WAIT
    assert arbiter.commands[2].action is Action.RETREAT


def test_no_nearby_healthy_defender_does_not_recall_distant_army():
    s = ArmyStrategy()
    orders = s.orders(
        roster(), False, C, worker_target=(0, 0), positions={i: (100 + i, 0) for i in range(15)}
    )
    assert not s.defenders
    assert all(o.reason == "army_objective" for o in orders)


def test_attack_posture_has_distinct_launch_and_regroup_thresholds():
    s = ArmyStrategy()
    assert all(o.action is Action.RETREAT for o in s.orders(roster(11), False, C))
    assert all(o.action is Action.ATTACK for o in s.orders(roster(12), False, C))
    assert all(o.action is Action.ATTACK for o in s.orders(roster(11), False, C))
    assert all(o.action is Action.ATTACK for o in s.orders(roster(7), False, C))
    assert all(o.action is Action.RETREAT for o in s.orders(roster(6), False, C))
    assert all(o.action is Action.RETREAT for o in s.orders(roster(11), False, C))
    assert all(o.action is Action.ATTACK for o in s.orders(roster(12), False, C))
    s.orders([], False, C)
    assert not s.attacking


def test_defense_bypasses_regroup_without_granting_small_army_offensive_posture():
    s = ArmyStrategy()
    assert all(o.action is Action.ATTACK for o in s.orders(roster(3), True, C))
    assert not s.attacking
    assert all(o.action is Action.RETREAT for o in s.orders(roster(3), False, C))


def test_wounded_and_burrowed_units_do_not_hold_attack_posture():
    s = ArmyStrategy()
    s.orders(roster(), False, C)
    units = roster(6) + [Observation(90, 0.5, False), Observation(91, 1, True)]
    s.orders(units, False, C)
    assert not s.attacking


def test_invalid_regroup_threshold_rejected():
    import pytest

    with pytest.raises(ValueError, match="Regroup"):
        BotConfig(regroup_roaches=12)
