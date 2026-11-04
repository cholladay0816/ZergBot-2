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
    home = SimpleNamespace(position=Point2((10, 10)))
    return SimpleNamespace(
        townhalls=Group([home]),
        supply_left=10,
        supply_cap=44,
        workers=SimpleNamespace(amount=20),
        gas_buildings=SimpleNamespace(amount=2),
        structures=Mock(return_value=Group([home])),
        already_pending=Mock(return_value=0),
        already_pending_upgrade=Mock(return_value=1),
        can_afford=Mock(return_value=True),
        distribute_workers=AsyncMock(),
        train=Mock(return_value=1),
        build=AsyncMock(),
        expand_now=AsyncMock(),
        research=Mock(return_value=True),
    )


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
    bot.expand_now.assert_awaited_once()
    bot.train.assert_not_called()
    bot.expand_now.reset_mock()
    asyncio.run(Economy(BotConfig(max_bases=1)).step(bot, 2))
    bot.expand_now.assert_not_awaited()
    bot.train.assert_called_once_with(U.ROACH)
