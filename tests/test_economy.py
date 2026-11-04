import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2

from zergbot.config import BotConfig
from zergbot.economy import Economy


class Group(list):
    @property
    def ready(self):
        return self

    @property
    def amount(self):
        return len(self)

    @property
    def first(self):
        return self[0]


def economy_bot():
    home = SimpleNamespace(
        position=Point2((10, 10)),
        has_buff=lambda _: True,
        distance_to=lambda p: Point2((10, 10)).distance_to(p),
        is_ready=True,
        ideal_harvesters=16,
        surplus_harvesters=0,
    )
    bot = SimpleNamespace(
        townhalls=Group([home]),
        supply_left=10,
        supply_cap=44,
        workers=SimpleNamespace(amount=20),
        gas_buildings=Group([SimpleNamespace(ideal_harvesters=3)] * 2),
        expansion_locations_list=[Point2((10, 10))],
        minerals=300,
        vespene=100,
        larva=Group([object()]),
        structures=Mock(return_value=Group([home])),
        units=Mock(return_value=Group([home])),
        enemy_units=Mock(),
        enemy_structures=Mock(),
        state=SimpleNamespace(game_loop=0),
        get_next_expansion=AsyncMock(return_value=Point2((30, 30))),
        can_place_single=AsyncMock(return_value=True),
        already_pending=Mock(return_value=0),
        already_pending_upgrade=Mock(return_value=1),
        can_afford=Mock(return_value=True),
        distribute_workers=AsyncMock(),
        train=Mock(return_value=1),
        build=AsyncMock(return_value=True),
        expand_now=AsyncMock(),
        research=Mock(return_value=True),
    )
    bot.units.of_type.return_value = Group([home] * 6)
    bot.enemy_units.filter.return_value.closer_than.return_value = Group()
    bot.enemy_structures.closer_than.return_value = Group()
    return bot


def test_supply_priority_spends_only_once():
    bot = economy_bot()
    bot.supply_left = 2
    asyncio.run(Economy(BotConfig()).step(bot, 0))
    bot.train.assert_called_once_with(U.OVERLORD)
    bot.distribute_workers.assert_awaited_once()
    bot.research.assert_not_called()
    bot.build.assert_not_awaited()


def test_pending_supply_does_not_prevent_worker_production():
    bot = economy_bot()
    bot.supply_left = 2
    bot.already_pending.side_effect = lambda kind: int(kind is U.OVERLORD)
    asyncio.run(Economy(BotConfig()).step(bot, 1))
    bot.train.assert_called_once_with(U.DRONE)


def test_research_precedes_production_and_completed_research_is_not_repeated():
    bot = economy_bot()
    bot.already_pending_upgrade.return_value = 0
    asyncio.run(Economy(BotConfig()).step(bot, 1))
    bot.research.assert_called_once_with(UpgradeId.BURROW)
    bot.train.assert_not_called()
    bot.research.reset_mock()
    bot.already_pending_upgrade.return_value = 1
    asyncio.run(Economy(BotConfig()).step(bot, 2))
    bot.research.assert_not_called()
    bot.train.assert_called_once_with(U.DRONE)


def test_no_ready_base_is_safe():
    bot = economy_bot()
    bot.townhalls = Group()
    asyncio.run(Economy(BotConfig()).step(bot, 1))
    bot.train.assert_not_called()
    bot.research.assert_not_called()


def test_expansion_and_roach_production_respect_base_limit():
    bot = economy_bot()
    bot.workers.amount = 22
    asyncio.run(Economy(BotConfig()).step(bot, 1))
    bot.build.assert_awaited_once_with(
        U.HATCHERY,
        near=Point2((30, 30)),
        max_distance=0,
        random_alternative=False,
        placement_step=1,
    )
    bot.train.assert_not_called()
    bot.build.reset_mock()
    asyncio.run(Economy(BotConfig(max_bases=1)).step(bot, 2))
    bot.build.assert_not_awaited()
    bot.train.assert_called_once_with(U.ROACH)


def test_defensive_roaches_precede_optional_workers():
    bot = economy_bot()
    bot.units.of_type.return_value = Group()
    asyncio.run(Economy(BotConfig()).step(bot, 1))
    bot.train.assert_called_once_with(U.ROACH)


def test_pending_roaches_satisfy_reserve_without_overproduction():
    bot = economy_bot()
    bot.units.of_type.return_value = Group()
    bot.already_pending.side_effect = lambda kind: 6 if kind is U.ROACH else 0
    asyncio.run(Economy(BotConfig()).step(bot, 1))
    bot.train.assert_called_once_with(U.DRONE)


def test_defense_reserve_increases_under_visible_attack():
    bot = economy_bot()
    bot.enemy_units.filter.return_value.closer_than.return_value = Group([object()])
    asyncio.run(Economy(BotConfig()).step(bot, 1))
    bot.train.assert_called_once_with(U.ROACH)


def test_queen_production_uses_townhall_without_consuming_larva():
    bot = economy_bot()
    bot.units.return_value = Group()
    asyncio.run(Economy(BotConfig()).step(bot, 1))
    bot.train.assert_called_once_with(U.QUEEN)


def test_blocked_expansion_throttles_retries_and_does_not_spend():
    bot = economy_bot()
    bot.can_place_single.return_value = False
    economy = Economy(BotConfig())
    assert not asyncio.run(economy.try_expand(bot))
    bot.state.game_loop = 4
    assert not asyncio.run(economy.try_expand(bot))
    bot.get_next_expansion.assert_awaited_once()
    bot.build.assert_not_awaited()
    bot.state.game_loop = 224
    assert not asyncio.run(economy.try_expand(bot))
    assert bot.get_next_expansion.await_count == 2


def test_visible_enemy_blocks_expansion_before_placement_query():
    bot = economy_bot()
    bot.enemy_units.filter.return_value.closer_than.return_value = Group([object()])
    assert not asyncio.run(Economy(BotConfig()).try_expand(bot))
    bot.can_place_single.assert_not_awaited()
    bot.build.assert_not_awaited()


def test_failed_expansion_does_not_starve_production():
    bot = economy_bot()
    bot.workers.amount = 22
    bot.can_place_single.return_value = False
    asyncio.run(Economy(BotConfig()).step(bot, 1))
    bot.train.assert_called_once_with(U.ROACH)
    bot.build.assert_not_awaited()


def test_supply_lead_scales_with_bases_and_accounts_for_pending_overlords():
    from zergbot.economy import needs_overlord

    config = BotConfig()
    assert needs_overlord(6, 30, 0, 1, config)
    assert not needs_overlord(6, 30, 1, 1, config)
    assert needs_overlord(2, 60, 1, 2, config)
    assert not needs_overlord(2, 60, 2, 2, config)
    assert not needs_overlord(16, 80, 0, 3, config)
    assert not needs_overlord(0, 200, 0, 3, config)
    assert not needs_overlord(0, 196, 1, 3, config)


def test_supply_preempts_production_before_old_four_supply_boundary():
    bot = economy_bot()
    bot.supply_left = 6
    asyncio.run(Economy(BotConfig()).step(bot, 1))
    bot.train.assert_called_once_with(U.OVERLORD)


def test_one_gas_capacity_can_expand_without_waiting_for_impossible_worker_target():
    bot = economy_bot()
    bot.workers.amount = 19
    bot.gas_buildings = Group([SimpleNamespace(ideal_harvesters=3)])
    asyncio.run(Economy(BotConfig()).step(bot, 1))
    bot.build.assert_awaited_once()


def test_actual_attack_reserves_army_before_optional_queen_spending():
    bot = economy_bot()
    bot.units.return_value = Group()
    bot.units.of_type.return_value = Group()
    bot.enemy_units.filter.return_value.closer_than.return_value = Group([object()])
    asyncio.run(Economy(BotConfig()).step(bot, 1))
    bot.train.assert_called_once_with(U.ROACH)


def test_macro_timer_observes_supply_preemption_and_resets_stale_scarcity():
    bot = economy_bot()
    config = BotConfig(
        macro_after_bases=1,
        macro_min_workers=10,
        macro_min_minerals=100,
        macro_wait_frames=8,
        max_bases=1,
    )
    economy = Economy(config)
    asyncio.run(economy.step(bot, 1))
    assert economy.macro_gate.limited_since == 0
    bot.state.game_loop = 8
    bot.larva = Group([object()] * 10)
    bot.supply_left = 2
    asyncio.run(economy.step(bot, 2))
    assert economy.macro_gate.limited_since is None
    bot.state.game_loop = 12
    bot.larva = Group([object()])
    asyncio.run(economy.step(bot, 3))
    assert economy.macro_gate.limited_since == 12
    bot.build.assert_not_awaited()
