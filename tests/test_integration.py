import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from sc2.ids.ability_id import AbilityId as A
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2

from zergbot.agents import Action, CommandArbiter, Intent
from zergbot.bot import ZergBot
from zergbot.integration import ROACH_TYPES, SC2UnitGateway


def unit(tag, burrowed=False, health_max=100):
    result = Mock()
    result.orders = []
    result.tag = tag
    result.health = 40
    result.health_max = health_max
    result.is_burrowed = burrowed
    return result


def test_batched_query_maps_abilities_per_unit_and_checks_research():
    units = [unit(1), unit(2, True), unit(3, health_max=0)]
    bot = SimpleNamespace(
        units=Mock(),
        state=SimpleNamespace(upgrades=set()),
        get_available_abilities=AsyncMock(
            return_value=[[A.BURROWDOWN_ROACH], [A.BURROWUP_ROACH], []]
        ),
    )
    bot.units.of_type.return_value = units
    gateway = SC2UnitGateway(bot)
    observations = asyncio.run(gateway.observe())
    bot.get_available_abilities.assert_awaited_once_with(units)
    bot.units.of_type.assert_called_once_with({U.ROACH, U.ROACHBURROWED})
    assert observations[0].can_burrow and not observations[0].can_emerge
    assert observations[1].can_emerge and not observations[1].can_burrow
    assert observations[1].burrowed
    assert observations[2].health == 0
    assert not observations[0].burrow_researched
    bot.state.upgrades.add(UpgradeId.BURROW)
    assert asyncio.run(gateway.observe())[0].burrow_researched


def test_no_units_skips_network_and_removes_stale_lookup():
    bot = SimpleNamespace(units=Mock(), get_available_abilities=AsyncMock())
    bot.units.of_type.return_value = []
    gateway = SC2UnitGateway(bot)
    gateway.units = {99: unit(99)}
    assert asyncio.run(gateway.observe()) == []
    assert gateway.units == {}
    bot.get_available_abilities.assert_not_awaited()


def test_dispatch_exactly_one_winning_command_and_wait_is_noop():
    gateway = SC2UnitGateway(Mock())
    gateway.units = {i: unit(i, burrowed=i in (2, 3, 6)) for i in range(1, 7)}
    arbiter = CommandArbiter()
    for tag, action in enumerate(
        [Action.BURROW, Action.EMERGE, Action.WAIT, Action.ATTACK, Action.RETREAT, Action.ATTACK], 1
    ):
        arbiter.submit(Intent(tag, action, 100))
        arbiter.submit(Intent(tag, Action.ATTACK, 10))
    arbiter.submit(Intent(999, Action.ATTACK, 10))  # stale tag is harmless
    target, retreat = Point2((10, 10)), Point2((0, 0))
    gateway.dispatch(arbiter, target, retreat)
    gateway.units[1].assert_called_once_with(A.BURROWDOWN_ROACH)
    gateway.units[2].assert_called_once_with(A.BURROWUP_ROACH)
    assert gateway.units[3].mock_calls == []
    gateway.units[4].attack.assert_called_once_with(target)
    gateway.units[5].move.assert_called_once_with(retreat)
    assert gateway.units[6].mock_calls == []


def test_bot_instances_have_independent_agent_state():
    first, second = ZergBot(), ZergBot()
    assert first.registry is not second.registry
    assert first.gateway.bot is first
    assert ROACH_TYPES == {U.ROACH, U.ROACHBURROWED}


def test_real_sc2_unit_enqueues_one_protocol_command():
    # Exercise actual BurnySC2 Unit.__call__, not just a Mock standing in for Unit.
    from s2clientprotocol.raw_pb2 import Unit as RawUnit
    from sc2.unit import Unit

    bot = SimpleNamespace(
        state=SimpleNamespace(game_loop=0),
        unit_command_uses_self_do=False,
        game_data=SimpleNamespace(
            abilities={A.BURROWDOWN_ROACH.value: SimpleNamespace(_proto=SimpleNamespace(target=1))}
        ),
        do=Mock(return_value=True),
    )
    roach = Unit(RawUnit(tag=7, unit_type=U.ROACH.value, health=40, health_max=145), bot)
    gateway = SC2UnitGateway(bot)
    gateway.units = {7: roach}
    arbiter = CommandArbiter()
    arbiter.submit(Intent(7, Action.BURROW, 100))
    arbiter.submit(Intent(7, Action.ATTACK, 10))
    gateway.dispatch(arbiter, Point2((10, 10)), Point2((0, 0)))
    bot.do.assert_called_once()
    command = bot.do.call_args.args[0]
    assert command.ability is A.BURROWDOWN_ROACH
    assert command.unit.tag == 7
    assert command.target is None


def test_real_sc2_active_orders_translate_exact_and_remapped_abilities():
    from s2clientprotocol.raw_pb2 import Unit as RawUnit
    from s2clientprotocol.raw_pb2 import UnitOrder as RawOrder
    from sc2.unit import Unit

    from zergbot.integration import observed_transition

    for exact, remapped, expected in [
        (A.BURROWDOWN_ROACH, A.BURROWDOWN, Action.BURROW),
        (A.BURROWUP_ROACH, A.BURROWUP, Action.EMERGE),
        (A.BURROWDOWN, A.BURROWDOWN, Action.BURROW),
        (A.BURROWUP, A.BURROWUP, Action.EMERGE),
    ]:
        bot = SimpleNamespace(
            state=SimpleNamespace(game_loop=4),
            game_data=SimpleNamespace(
                abilities={exact.value: SimpleNamespace(id=remapped, exact_id=exact)}
            ),
        )
        unit = Unit(
            RawUnit(tag=7, unit_type=U.ROACH.value, orders=[RawOrder(ability_id=exact.value)]), bot
        )
        assert observed_transition(unit) is expected
    unit = Mock(
        orders=[
            SimpleNamespace(ability=SimpleNamespace(id=A.ATTACK, exact_id=A.ATTACK)),
            SimpleNamespace(ability=SimpleNamespace(id=A.BURROWDOWN, exact_id=A.BURROWDOWN_ROACH)),
        ]
    )
    assert observed_transition(unit) is None  # queued morph is not active yet


def test_queens_share_single_batched_ability_query():
    roach, queen = unit(1), unit(2)
    bot = SimpleNamespace(
        units=Mock(),
        state=SimpleNamespace(upgrades=set()),
        get_available_abilities=AsyncMock(
            return_value=[[A.BURROWDOWN_ROACH], [A.EFFECT_INJECTLARVA]]
        ),
    )
    bot.units.of_type.return_value = [roach]
    gateway = SC2UnitGateway(bot)
    observations = asyncio.run(gateway.observe([queen]))
    bot.get_available_abilities.assert_awaited_once_with([roach, queen])
    assert len(observations) == 1
    assert gateway.abilities_by_tag[2] == {A.EFFECT_INJECTLARVA}


def test_gameplay_seed_is_set_after_startup_and_is_reproducible():
    import random

    import numpy as np

    from zergbot.config import BotConfig

    saved_random, saved_numpy = random.getstate(), np.random.get_state()
    try:
        bot = ZergBot(BotConfig(random_seed=42))
        bot.client = Mock()
        asyncio.run(bot.on_start())
        assert random.random() == random.Random(42).random()
        assert np.random.random() == np.random.RandomState(42).random_sample()
    finally:
        random.setstate(saved_random)
        np.random.set_state(saved_numpy)


def test_per_unit_target_is_dispatched_without_changing_other_units():
    gateway = SC2UnitGateway(Mock())
    gateway.units = {1: unit(1), 2: unit(2)}
    arbiter = CommandArbiter()
    arbiter.submit(Intent(1, Action.ATTACK, 10, "worker_defense", (2, 3)))
    arbiter.submit(Intent(2, Action.ATTACK, 10, "army_objective"))
    gateway.dispatch(arbiter, Point2((10, 10)), Point2((0, 0)))
    gateway.units[1].attack.assert_called_once_with(Point2((2, 3)))
    gateway.units[2].attack.assert_called_once_with(Point2((10, 10)))


def test_startup_failure_survives_library_defeat_conversion_without_error_text(tmp_path):
    import json

    import pytest

    from zergbot.diagnostics import MatchDiagnostics

    recorder = MatchDiagnostics(tmp_path, {})
    bot = ZergBot(diagnostics=recorder)
    bot._initialize = AsyncMock(side_effect=RuntimeError("SECRET_TOKEN_should_not_be_recorded"))
    with pytest.raises(RuntimeError):
        asyncio.run(bot.on_start())
    # Simulate BurnySC2 returning Defeat rather than propagating startup errors.
    recorder.finish("Defeat", "completed")
    payload = json.loads((tmp_path / "match.json").read_text())
    assert payload["termination"] == "startup_failed"
    assert payload["error_type"] == "RuntimeError"
    assert "SECRET_TOKEN" not in json.dumps(payload)


def test_construction_and_production_events_distinguish_completion():
    from zergbot.economy import Economy

    recorder = Mock()
    bot = SimpleNamespace(
        telemetry=SimpleNamespace(recorder=recorder), state=SimpleNamespace(game_loop=123)
    )
    building = SimpleNamespace(tag=7, type_id=U.SPAWNINGPOOL)
    asyncio.run(ZergBot.on_building_construction_started(bot, building))
    asyncio.run(ZergBot.on_building_construction_complete(bot, building))
    Economy.production_event(bot, U.QUEEN, 1)
    assert [call.args[0] for call in recorder.record.call_args_list] == [
        "construction_started",
        "construction_completed",
        "production_submitted",
    ]
    assert (
        recorder.record.call_args_list[-1].kwargs["scope"] == "own_command_attempt_not_completion"
    )
