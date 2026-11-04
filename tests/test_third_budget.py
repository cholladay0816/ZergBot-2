import asyncio
from types import SimpleNamespace

from zergbot.config import BotConfig
from zergbot.diagnostics import MatchDiagnostics
from zergbot.economy import Economy
from zergbot.opening import ThirdBaseBudget


def test_hold_times_out_and_cannot_immediately_repeat():
    b = ThirdBaseBudget()
    args = dict(needed=True, eligible=True, safe=True)
    assert b.reserve(frame=0, **args)
    assert b.reserve(frame=220, **args)
    assert not b.reserve(frame=224, **args)
    assert b.reason == "timeout"
    assert not b.reserve(frame=228, **args)
    assert b.reserve(frame=896, **args)


def test_pressure_and_lost_defense_release_then_pending_or_third_closes_hold():
    b = ThirdBaseBudget()
    assert b.reserve(frame=0, needed=True, eligible=True, safe=True)
    assert not b.reserve(frame=4, needed=True, eligible=True, safe=False)
    assert b.started is None and b.reason == "unsafe"
    assert not b.reserve(frame=8, needed=True, eligible=True, safe=True)
    assert not b.reserve(frame=1000, needed=False, eligible=True, safe=True)
    assert not b.reserve(frame=1004, needed=True, eligible=False, safe=True)


def test_failed_placement_release_prevents_another_hold():
    b = ThirdBaseBudget()
    assert b.reserve(frame=0, needed=True, eligible=True, safe=True)
    b.release(4, "placement_failed")
    assert not b.reserve(frame=8, needed=True, eligible=True, safe=True)


def test_real_expansion_event_accepts_budget_reason_json(tmp_path, json_roundtrip):
    recorder = MatchDiagnostics(tmp_path, {})
    bot = SimpleNamespace(
        telemetry=SimpleNamespace(recorder=recorder), state=SimpleNamespace(game_loop=100)
    )
    Economy.expansion_event(bot, "third_budget_holding", None)
    assert json_roundtrip(list(recorder.events))[0]["reason"] == "third_budget_holding"


def test_third_budget_preserves_supply_and_tech_priority_and_releases_failed_placement():
    from sc2.ids.unit_typeid import UnitTypeId as U
    from test_economy import Group, economy_bot

    bot = economy_bot()
    base = bot.townhalls.first
    bot.townhalls = Group([base, base])
    bot.workers.amount = 44
    bot.gas_buildings = Group([SimpleNamespace(ideal_harvesters=3)] * 4)
    base.health_percentage = 1
    bot.units.of_type.return_value = Group([base] * 6)
    bot.units.return_value = Group([base] * 6)
    bot.can_afford.return_value = False
    economy = Economy(BotConfig(third_base_reserve=True))
    bot.supply_left = 2
    asyncio.run(economy.step(bot, 1))
    bot.train.assert_called_once_with(U.OVERLORD)
    bot.train.reset_mock()
    bot.supply_left = 20
    asyncio.run(economy.step(bot, 2))
    bot.train.assert_not_called()
    bot.can_afford.return_value = True
    bot.can_place_single.return_value = False
    asyncio.run(economy.step(bot, 3))
    assert economy.third_budget.reason == "placement_failed"
    bot.train.assert_called_once_with(U.ROACH)
