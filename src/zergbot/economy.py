"""Conservative roach economy; one spending decision per step prevents overspend."""

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.upgrade_id import UpgradeId

from .config import BotConfig


class Economy:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.next_expansion_frame = 0

    async def step(self, bot: BotAI, iteration: int, abilities_by_tag=None) -> None:
        if iteration % 8 == 0:
            await bot.distribute_workers()
        if not bot.townhalls.ready:
            return
        self.inject(bot, abilities_by_tag or {})
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
        if (
            bot.structures(U.SPAWNINGPOOL).ready
            and bot.units(U.QUEEN).amount + bot.already_pending(U.QUEEN)
            < bot.townhalls.ready.amount
        ):
            if bot.train(U.QUEEN):
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
            if await self.try_expand(bot):
                return
        # Workers cannot consume every larva while the army is absent or the base is attacked.
        roaches = bot.units.of_type({U.ROACH, U.ROACHBURROWED}).amount + bot.already_pending(
            U.ROACH
        )
        threatened = any(
            bot.enemy_units.filter(lambda u: not u.is_flying).closer_than(25, base)
            for base in bot.townhalls.ready
        )
        reserve = self.config.attack_roaches if threatened else self.config.defensive_roaches
        if bot.workers.amount >= 20 and bot.structures(U.ROACHWARREN).ready and roaches < reserve:
            if bot.train(U.ROACH):
                return
        worker_goal = min(self.config.workers, 22 * bot.townhalls.amount)
        if bot.workers.amount + bot.already_pending(U.DRONE) < worker_goal:
            if bot.train(U.DRONE):
                return
        if bot.structures(U.ROACHWARREN).ready:
            bot.train(U.ROACH)

    def inject(self, bot, abilities_by_tag):
        # Energy spells do not share the mineral/gas spending decision. Reserve each
        # base once locally because the injection buff appears only next observation.
        available_bases = [
            base for base in bot.townhalls.ready if not base.has_buff(BuffId.QUEENSPAWNLARVATIMER)
        ]
        for queen in bot.units(U.QUEEN).ready:
            if not available_bases:
                break
            if queen.orders or AbilityId.EFFECT_INJECTLARVA not in abilities_by_tag.get(
                queen.tag, set()
            ):
                continue
            base = min(available_bases, key=queen.distance_to)
            queen(AbilityId.EFFECT_INJECTLARVA, base)
            telemetry = getattr(bot, "telemetry", None)
            if telemetry and telemetry.recorder.config.enabled:
                telemetry.recorder.command_counts["INJECT"] += 1
                telemetry.recorder.record(
                    "command_attempt",
                    bot.state.game_loop,
                    tag=queen.tag,
                    action="INJECT",
                    reason="available_unbuffed_base",
                )
            available_bases.remove(base)

    async def try_expand(self, bot):
        frame = bot.state.game_loop
        if frame < self.next_expansion_frame:
            return False
        self.next_expansion_frame = frame + self.config.expansion_retry_frames
        location = await bot.get_next_expansion()
        if location is None:
            self.expansion_event(bot, "no_location", None)
            return False
        # Do not rebuild into visible attackers, or silently offset a blocked base.
        threats = bot.enemy_units.filter(lambda u: not u.is_flying).closer_than(12, location)
        if threats or bot.enemy_structures.closer_than(8, location):
            self.expansion_event(bot, "visible_enemy_nearby", location)
            return False
        if not await bot.can_place_single(U.HATCHERY, location):
            self.expansion_event(bot, "placement_blocked", location)
            return False
        submitted = await bot.build(
            U.HATCHERY, near=location, max_distance=0, random_alternative=False, placement_step=1
        )

        self.expansion_event(bot, "submitted" if submitted else "not_submitted", location)
        return submitted

    @staticmethod
    def expansion_event(bot, reason, location):
        telemetry = getattr(bot, "telemetry", None)
        if telemetry:
            telemetry.recorder.record(
                "expansion",
                bot.state.game_loop,
                reason=reason,
                location=[location.x, location.y] if location is not None else None,
            )
