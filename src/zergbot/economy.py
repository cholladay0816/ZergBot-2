"""Conservative roach economy; one spending decision per step prevents overspend."""

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.upgrade_id import UpgradeId

from .config import BotConfig


class Economy:
    def __init__(self, config: BotConfig) -> None:
        self.config = config

    async def step(self, bot: BotAI, iteration: int) -> None:
        if iteration % 8 == 0:
            await bot.distribute_workers()
        if not bot.townhalls.ready:
            return
        home = bot.townhalls.ready.first
        if bot.supply_left < 4 and bot.supply_cap < 200 and not bot.already_pending(U.OVERLORD):
            bot.train(U.OVERLORD)
            return
        if not bot.structures(U.SPAWNINGPOOL) and not bot.already_pending(U.SPAWNINGPOOL):
            if bot.workers.amount >= 16 and bot.can_afford(U.SPAWNINGPOOL):
                await bot.build(
                    U.SPAWNINGPOOL, near=home.position.towards(bot.game_info.map_center, 5)
                )
                return
        if bot.workers.amount >= 16 and bot.gas_buildings.amount < bot.townhalls.amount * 2:
            for base in bot.townhalls.ready:
                for geyser in bot.vespene_geyser.closer_than(10, base):
                    if bot.gas_buildings.closer_than(1, geyser):
                        continue
                    if bot.can_afford(U.EXTRACTOR) and not bot.already_pending(U.EXTRACTOR):
                        await bot.build(U.EXTRACTOR, geyser)
                        return
        if (
            bot.structures(U.SPAWNINGPOOL).ready
            and not bot.structures(U.ROACHWARREN)
            and not bot.already_pending(U.ROACHWARREN)
            and bot.can_afford(U.ROACHWARREN)
        ):
            await bot.build(U.ROACHWARREN, near=home.position.towards(bot.game_info.map_center, 7))
            return
        if bot.structures(U.ROACHWARREN).ready and not bot.already_pending_upgrade(
            UpgradeId.BURROW
        ):
            if bot.research(UpgradeId.BURROW):
                return
        if (
            bot.workers.amount >= 22 * bot.townhalls.amount
            and bot.townhalls.amount < self.config.max_bases
            and not bot.already_pending(U.HATCHERY)
            and bot.can_afford(U.HATCHERY)
        ):
            await bot.expand_now()
            return
        worker_goal = min(self.config.workers, 22 * bot.townhalls.amount)
        if bot.workers.amount + bot.already_pending(U.DRONE) < worker_goal:
            if bot.train(U.DRONE):
                return
        if bot.structures(U.ROACHWARREN).ready:
            bot.train(U.ROACH)
