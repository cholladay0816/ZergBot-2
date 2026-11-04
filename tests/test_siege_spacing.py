from collections import Counter
from types import MethodType, SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.position import Point2

from zergbot.agents import Action, AgentRegistry, CommandArbiter, Observation
from zergbot.config import BotConfig
from zergbot.diagnostics import MatchDiagnostics
from zergbot.integration import SC2UnitGateway
from zergbot.scenarios import MeasuredBot
from zergbot.siege_spacing import SiegeSpacing, spacing_sample
from zergbot.telemetry import TelemetryAdapter


class Unit:
    def __init__(self, tag, xy, tank=False):
        self.tag = np.int64(tag)
        self.position = Point2(tuple(np.float32(v) for v in xy))
        self.weapon_cooldown = np.float32(24)
        self.radius = 0.5
        self.health = np.float32(145)
        self.is_burrowed = False
        self.is_visible = True
        self.type_id = U.SIEGETANKSIEGED if tank else U.ROACH
        self.ground_range = 13 if tank else 4
        self.move = Mock()

    def distance_to(self, target):
        return self.position.distance_to(getattr(target, "position", target))


def fixture():
    return SiegeSpacing(), [Unit(1, (0, 0)), Unit(2, (1, 0))], Unit(10, (10, 0), True)


def test_attack_commit_guard_then_cooldown_spacing_and_ready_fire_release():
    policy, units, tank = fixture()
    assert not policy.orders(units, [tank], 0, lambda _: True)
    assert not policy.orders(units, [tank], 4, lambda _: True)
    orders = policy.orders(units, [tank], 8, lambda _: True)
    assert orders and all(o.action is Action.MOVE for o in orders)
    for order in orders:
        unit = next(u for u in units if u.tag == order.tag)
        other = next(u for u in units if u.tag != order.tag)
        point = Point2(order.target)
        assert point.distance_to(other.position) >= unit.distance_to(other) + 0.25
        assert point.distance_to(tank.position) >= unit.distance_to(tank) - 0.25
    assert all(o.action is Action.WAIT for o in policy.orders(units, [tank], 12, lambda _: True))
    for u in units:
        u.weapon_cooldown = 0
    assert not policy.orders(units, [tank], 16, lambda _: True)


@pytest.mark.parametrize("condition", ["hidden", "unsieged", "far", "blocked", "burrowed", "alone"])
def test_unavailable_or_unsafe_spacing_does_not_override_attack(condition):
    policy, units, tank = fixture()
    if condition == "hidden":
        tank.is_visible = False
    if condition == "unsieged":
        tank.type_id = U.SIEGETANK
    if condition == "far":
        tank.position = Point2((100, 100))
    if condition == "burrowed":
        for u in units:
            u.is_burrowed = True
    if condition == "alone":
        units = units[:1]

    def pathable(_):
        return condition != "blocked"

    policy.orders(units, [tank], 0, pathable)
    assert not policy.orders(units, [tank], 8, pathable)


def test_dead_state_is_pruned_and_recovery_veto_wins():
    policy, units, tank = fixture()
    policy.orders(units, [tank], 0, lambda _: True)
    orders = policy.orders(units, [tank], 8, lambda _: True)
    arbiter = CommandArbiter()
    for order in orders:
        arbiter.submit(order)
    registry = AgentRegistry()
    obs = Observation(1, 0.2, False, True, False, True)
    registry.sync([obs])
    arbiter.submit(registry.agents[1].decide(obs, 8, BotConfig()))
    assert arbiter.commands[1].action is Action.BURROW
    policy.orders([], [], 12, lambda _: True)
    assert not policy.previous_cooldown and not policy.commit_until and not policy.moving_until


def test_move_dispatch_and_real_production_and_scenario_json_contract(tmp_path, json_roundtrip):
    policy, units, tank = fixture()
    policy.orders(units, [tank], 0, lambda _: True)
    arbiter = CommandArbiter()
    for intent in policy.orders(units, [tank], 8, lambda _: True):
        arbiter.submit(intent)
    gateway = SC2UnitGateway(Mock())
    gateway.units = {int(u.tag): u for u in units}
    gateway.dispatch(arbiter, Point2((10, 0)), Point2((-10, 0)))
    assert all(u.move.call_count == 1 for u in units)
    units[0].is_burrowed = True
    units[0].move.reset_mock()
    gateway.dispatch(arbiter, Point2((10, 0)), Point2((-10, 0)))
    units[0].move.assert_not_called()
    recorder = MatchDiagnostics(tmp_path, {})
    observations = [Observation(int(u.tag), 1, False) for u in units]
    registry = AgentRegistry()
    registry.sync(observations)
    TelemetryAdapter(recorder).decisions(observations, registry, arbiter, 8)
    assert any(e["action"] == "MOVE" for e in json_roundtrip(list(recorder.events)))
    bot = SimpleNamespace(events=[], counts=Counter(), state=SimpleNamespace(game_loop=8))
    bot.record = MethodType(MeasuredBot.record, bot)
    bot.record("siege_sample", **spacing_sample(units, [tank]))
    assert json_roundtrip(bot.events)[0]["army"][0]["tag"] == 1
    with pytest.raises(ValueError):
        bot.record("siege_sample", password="private")
