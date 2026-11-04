"""A bounded two-base roach tech sequence using installed costs and prerequisites."""

from dataclasses import dataclass

from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.upgrade_id import UpgradeId as G


@dataclass(frozen=True)
class TechState:
    workers: int
    bases: int
    roaches: int
    threatened: bool
    lair_started: bool
    lair_ready: bool
    evo_started: bool
    evo_ready: bool
    missile_started: bool
    speed_started: bool


def next_roach_tech(state, config):
    reserve = config.attack_roaches if state.threatened else config.defensive_roaches
    if state.workers < config.tech_min_workers or state.bases < 2 or state.roaches < reserve:
        return None
    if not state.lair_started:
        return U.LAIR
    if not state.evo_started:
        return U.EVOLUTIONCHAMBER
    if state.evo_ready and not state.missile_started:
        return G.ZERGMISSILEWEAPONSLEVEL1
    if state.lair_ready and not state.speed_started:
        return G.GLIALRECONSTITUTION
    return None


class RoachTech:
    def __init__(self, config):
        self.config = config
        self.next_build_frame = 0
        self.last_event = None
        self.last_event_frame = -1000000

    async def step(self, bot, home, macro):
        if not (self.config.roach_tech or self.config.adaptive_army):
            return False
        lairs = bot.structures.of_type({U.LAIR, U.HIVE})
        evos = bot.structures(U.EVOLUTIONCHAMBER)
        roaches = bot.units.of_type({U.ROACH, U.ROACHBURROWED}).amount + bot.already_pending(
            U.ROACH
        )
        state = TechState(
            bot.workers.amount,
            macro.ready_bases,
            roaches,
            macro.threatened,
            bool(lairs) or bool(bot.already_pending(U.LAIR)),
            bool(lairs.ready),
            bool(evos) or bool(bot.already_pending(U.EVOLUTIONCHAMBER)),
            bool(evos.ready),
            bool(bot.already_pending_upgrade(G.ZERGMISSILEWEAPONSLEVEL1)),
            bool(bot.already_pending_upgrade(G.GLIALRECONSTITUTION)),
        )
        goal = next_roach_tech(state, self.config)
        if goal is None:
            return False
        # Do not reserve resources for a busy or missing producer. Emergency supply
        # and army production already ran before this manager in Economy.step.
        if goal == U.LAIR:
            producers = bot.structures(U.HATCHERY).ready.idle
            if not bot.structures(U.SPAWNINGPOOL).ready:
                return False
        elif goal == G.ZERGMISSILEWEAPONSLEVEL1:
            producers = evos.ready.idle
        elif goal == G.GLIALRECONSTITUTION:
            producers = bot.structures(U.ROACHWARREN).ready.idle
        else:
            producers = bot.workers
            if bot.state.game_loop < self.next_build_frame:
                return False
        if not producers:
            return False
        cost = bot.calculate_cost(goal)
        if not bot.can_afford(goal):
            # Gas starvation does not freeze workers/army indefinitely. When gas
            # is ready, reserve the mineral cost so continuous larva spending cannot
            # prevent this bounded sequence from ever starting.
            if bot.vespene >= cost.vespene:
                self.event(bot, goal, "reserve_minerals", cost)
                return True
            return False
        if goal == U.EVOLUTIONCHAMBER:
            self.next_build_frame = bot.state.game_loop + self.config.expansion_retry_frames
            submitted = await bot.build(
                goal, near=home.position.towards(bot.game_info.map_center, 8)
            )
        elif goal == U.LAIR:
            submitted = bool(bot.train(goal))
        else:
            submitted = bot.research(goal)
        self.event(bot, goal, "submitted" if submitted else "rejected", cost)
        return bool(submitted)

    def event(self, bot, goal, reason, cost):
        telemetry = getattr(bot, "telemetry", None)
        if not telemetry:
            return
        key = (goal.name, reason)
        if key == self.last_event and bot.state.game_loop - self.last_event_frame < 112:
            return
        self.last_event, self.last_event_frame = key, bot.state.game_loop
        telemetry.recorder.record(
            "tech_step",
            bot.state.game_loop,
            goal=goal.name,
            reason=reason,
            mineral_cost=cost.minerals,
            gas_cost=cost.vespene,
            minerals=bot.minerals,
            gas=bot.vespene,
        )
