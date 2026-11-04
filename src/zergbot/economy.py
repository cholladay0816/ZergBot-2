"""Conservative roach economy; one spending decision per step prevents overspend."""

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.upgrade_id import UpgradeId

from .config import BotConfig
from .macro import MacroHatchGate, MacroState, extractor_target, queen_target, worker_target


def needs_overlord(supply_left, supply_cap, pending_overlords, ready_bases, config):
    """Reserve lead time for faster larva throughput without duplicating pending supply."""
    if supply_cap + 8 * pending_overlords >= 200:
        return False
    buffer = min(
        config.supply_buffer_max,
        max(config.supply_buffer_min, 4 + config.supply_buffer_per_base * ready_bases),
    )
    projected_left = supply_left + 8 * pending_overlords
    return projected_left < buffer


class Economy:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.next_expansion_frame = 0
        self.macro_gate = MacroHatchGate()
        self.next_macro_frame = 0

    async def step(self, bot: BotAI, iteration: int, abilities_by_tag=None) -> None:
        if iteration % 8 == 0 and not (
            self.config.adaptive_economy and bot.vespene > max(400, bot.minerals * 1.5)
        ):
            await bot.distribute_workers()
        if not bot.townhalls.ready:
            return
        # Resource bases are map expansion sites, not arbitrary production hatcheries.
        resource_bases = [
            base
            for base in bot.townhalls
            if any(base.distance_to(p) < 8 for p in bot.expansion_locations_list)
        ]
        ready_resources = [base for base in resource_bases if base.is_ready]
        threatened = any(
            bot.enemy_units.filter(lambda u: u.can_attack_ground).closer_than(25, b)
            for b in bot.townhalls.ready
        )
        state = MacroState(
            len(resource_bases),
            len(ready_resources),
            bot.townhalls.ready.amount,
            bot.workers.amount,
            sum(b.ideal_harvesters for b in ready_resources)
            + sum(g.ideal_harvesters for g in bot.gas_buildings.ready),
            bot.minerals,
            bot.vespene,
            bot.larva.amount,
            threatened,
        )
        if iteration % 8 == 0 and self.config.adaptive_economy:
            self.rebalance_gas(bot, state)
        home = bot.townhalls.ready.first
        if needs_overlord(
            bot.supply_left,
            bot.supply_cap,
            bot.already_pending(U.OVERLORD),
            bot.townhalls.ready.amount,
            self.config,
        ):
            bot.train(U.OVERLORD)
            return
        if not bot.structures(U.SPAWNINGPOOL) and not bot.already_pending(U.SPAWNINGPOOL):
            if bot.workers.amount >= 16 and bot.can_afford(U.SPAWNINGPOOL):
                await bot.build(
                    U.SPAWNINGPOOL, near=home.position.towards(bot.game_info.map_center, 5)
                )
                return
        if bot.workers.amount >= 16 and bot.gas_buildings.amount < extractor_target(
            state, self.config
        ):
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
        if bot.structures(U.SPAWNINGPOOL).ready and bot.units(U.QUEEN).amount + bot.already_pending(
            U.QUEEN
        ) < queen_target(state, self.config):
            if bot.train(U.QUEEN):
                return
        if bot.structures(U.ROACHWARREN).ready and not bot.already_pending_upgrade(
            UpgradeId.BURROW
        ):
            if bot.research(UpgradeId.BURROW):
                return
        if (
            bot.workers.amount >= 22 * max(1, len(resource_bases))
            and len(resource_bases) < self.config.max_bases
            and not bot.already_pending(U.HATCHERY)
            and bot.can_afford(U.HATCHERY)
        ):
            if await self.try_expand(bot):
                return
        # Workers cannot consume every larva while the army is absent or the base is attacked.
        roaches = bot.units.of_type({U.ROACH, U.ROACHBURROWED}).amount + bot.already_pending(
            U.ROACH
        )

        reserve = self.config.attack_roaches if threatened else self.config.defensive_roaches
        if bot.workers.amount >= 20 and bot.structures(U.ROACHWARREN).ready and roaches < reserve:
            if bot.train(U.ROACH):
                return
        worker_goal = worker_target(state, self.config)
        if bot.workers.amount + bot.already_pending(U.DRONE) < worker_goal:
            if bot.train(U.DRONE):
                return
        if self.macro_gate.ready(
            state,
            self.config,
            bot.state.game_loop,
            bot.townhalls.amount - len(resource_bases),
            bot.already_pending(U.HATCHERY),
        ):
            if await self.try_macro(bot, home):
                return
        if bot.structures(U.ROACHWARREN).ready:
            bot.train(U.ROACH)

    def rebalance_gas(self, bot, state):
        if state.gas <= max(400, state.minerals * 1.5):
            return
        bases = [b for b in bot.townhalls.ready if b.surplus_harvesters < 0]
        if not bases:
            return
        # The caller skips distribute_workers on these frames, so no worker gets two orders.
        moved = set()
        for gas in bot.gas_buildings.ready:
            for worker in bot.workers:
                if len(moved) >= 3:
                    return
                if (
                    worker.tag in moved
                    or not worker.is_gathering
                    or worker.order_target != gas.tag
                    or worker.is_carrying_vespene
                ):
                    continue
                base = min(bases, key=worker.distance_to)
                patches = bot.mineral_field.closer_than(10, base)
                if patches:
                    worker.gather(patches.closest_to(worker))
                    moved.add(worker.tag)

    async def try_macro(self, bot, home):
        frame = bot.state.game_loop
        if frame < self.next_macro_frame or not bot.can_afford(U.HATCHERY):
            return False
        self.next_macro_frame = frame + self.config.expansion_retry_frames
        near = home.position.towards(bot.game_info.map_center, 11)
        place = await bot.find_placement(
            U.HATCHERY, near, max_distance=6, random_alternative=False, placement_step=2
        )
        if place is None or any(place.distance_to(p) < 8 for p in bot.expansion_locations_list):
            return False
        if bot.enemy_units.closer_than(15, place) or not bot.has_creep(place):
            return False
        submitted = await bot.build(
            U.HATCHERY, near=place, max_distance=0, random_alternative=False, placement_step=1
        )
        self.expansion_event(bot, "macro_submitted" if submitted else "macro_rejected", place)
        return submitted

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
