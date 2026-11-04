import asyncio
import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.upgrade_id import UpgradeId as G
from sc2.position import Point2

from zergbot.adaptive import AdaptiveArmy, AirMemory, pressure_allowed
from zergbot.config import BotConfig
from zergbot.diagnostics import MatchDiagnostics
from zergbot.tech import RoachTech, TechState, next_roach_tech

C = BotConfig(roach_tech=True, adaptive_army=True)
S = TechState(32, 2, 6, False, False, False, False, False, False, False)


@pytest.mark.parametrize(
    "changes", [dict(workers=31), dict(bases=1), dict(roaches=5), dict(threatened=True)]
)
def test_tech_preserves_economy_and_defense(changes):
    assert next_roach_tech(replace(S, **changes), C) is None


def test_sequence_and_pending_readiness_prevent_duplicates():
    assert next_roach_tech(S, C) == U.LAIR
    s = replace(S, lair_started=True)
    assert next_roach_tech(s, C) == U.EVOLUTIONCHAMBER
    s = replace(s, evo_started=True)
    assert next_roach_tech(s, C) is None
    s = replace(s, evo_ready=True)
    assert next_roach_tech(s, C) == G.ZERGMISSILEWEAPONSLEVEL1
    s = replace(s, missile_started=True, lair_ready=True)
    assert next_roach_tech(s, C) == G.GLIALRECONSTITUTION
    assert next_roach_tech(replace(s, speed_started=True), C) is None


class Group(list):
    @property
    def amount(self):
        return len(self)

    @property
    def ready(self):
        return self

    @property
    def idle(self):
        return self


def bot_stub():
    structures = Mock(return_value=Group([object()]))
    structures.of_type.return_value = Group()
    units = Mock(return_value=Group([object()]))
    units.of_type.return_value = Group([object()] * 6)
    return SimpleNamespace(
        structures=structures,
        units=units,
        workers=Group([object()] * 32),
        already_pending=Mock(return_value=0),
        already_pending_upgrade=Mock(return_value=0),
        calculate_cost=Mock(return_value=SimpleNamespace(minerals=150, vespene=100)),
        can_afford=Mock(return_value=True),
        train=Mock(return_value=1),
        research=Mock(return_value=True),
        build=AsyncMock(return_value=True),
        state=SimpleNamespace(game_loop=0),
        telemetry=None,
        vespene=100,
        minerals=150,
        game_info=SimpleNamespace(map_center=Point2((40, 40))),
        time=100,
        supply_left=10,
    )


def test_tech_reserves_minerals_but_not_missing_gas_or_busy_producer():
    bot = bot_stub()
    bot.can_afford.return_value = False
    macro = SimpleNamespace(ready_bases=2, threatened=False)
    tech = RoachTech(C)
    assert asyncio.run(tech.step(bot, None, macro))
    bot.vespene = 99
    assert not asyncio.run(tech.step(bot, None, macro))
    bot.vespene = 100
    bot.structures.return_value = Group()
    assert not asyncio.run(tech.step(bot, None, macro))
    bot.train.assert_not_called()


def test_lair_uses_normal_training_once_without_double_do():
    bot = bot_stub()
    assert asyncio.run(
        RoachTech(C).step(bot, None, SimpleNamespace(ready_bases=2, threatened=False))
    )
    bot.train.assert_called_once_with(U.LAIR)
    bot.research.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        dict(full_local_vision=False),
        dict(workers=0),
        dict(workers=5),
        dict(armed=True),
        dict(healthy_lings=1),
        dict(home_safe=False),
        dict(seconds=300),
    ],
)
def test_ling_pressure_requires_current_local_evidence(changes):
    fields = dict(
        full_local_vision=True, workers=3, armed=False, healthy_lings=2, home_safe=True, seconds=150
    )
    assert pressure_allowed(**fields)
    assert not pressure_allowed(**(fields | changes))


def test_air_memory_expires_and_does_not_invent_unseen_air():
    m = AirMemory()
    unit = SimpleNamespace(
        tag=1,
        is_visible=False,
        is_flying=True,
        can_attack_ground=True,
        can_attack_air=True,
        type_id=U.MUTALISK,
    )
    m.observe([unit], 0)
    assert m.target() == 0
    unit.is_visible = True
    m.observe([unit], 0)
    assert m.target() == 4
    m.observe([], 1344)
    assert m.target() == 4
    m.observe([], 1345)
    assert m.target() == 0
    m.observe([SimpleNamespace(**(vars(unit) | dict(tag=i))) for i in range(30)], 2000)
    assert m.target() == 20


def test_ling_production_quota_and_home_danger_prevent_spam():
    bot = bot_stub()
    a = AdaptiveArmy(C)
    state = SimpleNamespace(threatened=False)
    assert asyncio.run(a.produce(bot, None, state))
    assert a.lings_attempted == 2
    assert not asyncio.run(a.produce(bot, None, state))
    a.pressure_ready = True
    assert not asyncio.run(a.produce(bot, None, SimpleNamespace(threatened=True)))
    for _ in range(3):
        assert asyncio.run(a.produce(bot, None, state))
    assert a.lings_attempted == 8
    assert not asyncio.run(a.produce(bot, None, state))


def test_tech_and_adaptive_events_serialize_with_bounds(tmp_path):
    recorder = MatchDiagnostics(tmp_path, {})
    bot = bot_stub()
    bot.telemetry = SimpleNamespace(recorder=recorder)
    tech = RoachTech(C)
    cost = bot.calculate_cost(U.LAIR)
    for _ in range(100):
        tech.event(bot, U.LAIR, "reserve_minerals", cost)
    AdaptiveArmy(C).event(bot, "anti_air", "recent_visible_air", target_count=4, observed_count=1)
    recorder.finish(termination="test")
    data = json.loads((tmp_path / "match.json").read_text())
    assert sum(e["kind"] == "tech_step" for e in data["events"]) == 1
    assert any(e["kind"] == "adaptive_decision" for e in data["events"])
