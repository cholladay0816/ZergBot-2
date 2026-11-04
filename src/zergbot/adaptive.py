"""Visible-evidence army adaptation and bounded early ling reconnaissance."""

import numpy as np
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.upgrade_id import UpgradeId as G
from sc2.position import Point2

WORKERS = {U.SCV, U.PROBE, U.DRONE}
SPECIAL_AIR = {U.BATTLECRUISER, U.CARRIER, U.VOIDRAY, U.BROODLORD, U.LIBERATOR, U.LIBERATORAG}


def pressure_allowed(*, full_local_vision, workers, armed, healthy_lings, home_safe, seconds):
    # A fully visible LOCAL worker pocket is not evidence that the whole enemy base is safe.
    return (
        full_local_vision
        and 1 <= workers <= 4
        and not armed
        and healthy_lings >= 2
        and home_safe
        and seconds < 300
    )


class AirMemory:
    def __init__(self):
        self.seen = {}
        self.immortals = {}

    def observe(self, enemies, frame):
        for enemy in enemies:
            if (
                enemy.is_visible
                and enemy.is_flying
                and (
                    enemy.can_attack_ground or enemy.can_attack_air or enemy.type_id in SPECIAL_AIR
                )
            ):
                self.seen[enemy.tag] = frame
        self.seen = {tag: time for tag, time in self.seen.items() if frame - time <= 1344}
        for enemy in enemies:
            if enemy.is_visible and enemy.type_id == U.IMMORTAL:
                self.immortals[enemy.tag] = frame
        self.immortals = {tag: time for tag, time in self.immortals.items() if frame - time <= 1344}

    def destroyed(self, tag):
        self.seen.pop(tag, None)
        self.immortals.pop(tag, None)

    def target(self):
        air = min(20, max(4, 2 * len(self.seen))) if self.seen else 0
        ground = min(12, 3 * len(self.immortals)) if len(self.immortals) >= 2 else 0
        return max(air, ground)


class AdaptiveArmy:
    def __init__(self, config):
        self.config = config
        self.air = AirMemory()
        self.lings_attempted = 0
        self.pressure_until = None
        self.pressure_spent = False
        self.pressure_ready = False
        self.next_den_frame = 0
        self.retreat_until = {}
        self.last_events = {}

    def event(self, bot, subject, reason, **values):
        telemetry = getattr(bot, "telemetry", None)
        values = {
            key: value.item() if isinstance(value, np.generic) else value
            for key, value in values.items()
        }
        signature = (reason, tuple(sorted(values.items())))
        if telemetry and self.last_events.get(subject) != signature:
            telemetry.recorder.record(
                "adaptive_decision", bot.state.game_loop, subject=subject, reason=reason, **values
            )
            self.last_events[subject] = signature

    def observe(self, bot):
        if self.config.adaptive_army:
            self.air.observe(list(bot.enemy_units), bot.state.game_loop)

    async def produce(self, bot, home, state):
        if not self.config.adaptive_army:
            return False
        # One scout pair; reinforcement is capped at eight lifetime attempted lings.
        quota = 8 if self.pressure_ready and bot.workers.amount >= 20 else 2
        if (
            self.lings_attempted < quota
            and bot.time < 300
            and not state.threatened
            and bot.structures(U.SPAWNINGPOOL).ready
            and bot.units(U.QUEEN)
            and bot.supply_left >= 4
            and (quota == 2 or bot.minerals >= 150)
        ):
            if bot.train(U.ZERGLING):
                self.lings_attempted += 2
                self.event(
                    bot,
                    "ling_production",
                    "bounded_scout_or_confirmed_pressure",
                    attempted=self.lings_attempted,
                )
                return True
        target = self.air.target()
        if not target:
            return False
        self.event(
            bot,
            "anti_air",
            "recent_visible_air_or_immortals",
            target_count=target,
            observed_count=len(self.air.seen) + len(self.air.immortals),
        )
        if not bot.structures.of_type({U.LAIR, U.HIVE}).ready:
            return False
        den = bot.structures(U.HYDRALISKDEN)
        if not den and not bot.already_pending(U.HYDRALISKDEN):
            if bot.state.game_loop >= self.next_den_frame and bot.can_afford(U.HYDRALISKDEN):
                self.next_den_frame = bot.state.game_loop + 224
                return await bot.build(
                    U.HYDRALISKDEN, near=home.position.towards(bot.game_info.map_center, 9)
                )
            cost = bot.calculate_cost(U.HYDRALISKDEN)
            screen = bot.units.of_type({U.ROACH, U.ROACHBURROWED}).amount
            return (
                bot.state.game_loop >= self.next_den_frame
                and bot.vespene >= cost.vespene
                and bot.workers.amount >= 32
                and screen >= self.config.defensive_roaches
            )
        if (
            den.ready
            and bot.units(U.HYDRALISK).amount >= 4
            and not bot.already_pending_upgrade(G.EVOLVEGROOVEDSPINES)
        ):
            if bot.research(G.EVOLVEGROOVEDSPINES):
                return True
        if den.ready and bot.units(U.HYDRALISK).amount + bot.already_pending(U.HYDRALISK) < target:
            if bot.train(U.HYDRALISK):
                self.event(bot, "hydra_production", "submitted", target_count=target)
                return True
            cost = bot.calculate_cost(U.HYDRALISK)
            # Otherwise continuous cheaper roaches can starve the actual counter.
            return bot.vespene >= cost.vespene
        return False

    def control(self, bot, target, retreat):
        if not self.config.adaptive_army:
            return
        lings = list(bot.units(U.ZERGLING))
        self.retreat_until = {
            tag: frame
            for tag, frame in self.retreat_until.items()
            if any(u.tag == tag for u in lings)
        }
        healthy = [u for u in lings if u.health_percentage >= 0.8]
        armed = [
            u
            for u in list(bot.enemy_units) + list(bot.enemy_structures)
            if u.is_visible
            and u.type_id not in WORKERS
            and (u.can_attack_ground or u.type_id in SPECIAL_AIR)
        ]
        home_safe = not any(u.distance_to(b) < 20 for u in armed for b in bot.townhalls.ready)
        workers = [u for u in bot.enemy_units if u.is_visible and u.type_id in WORKERS]
        pocket = (
            min(workers, key=lambda u: min((u.distance_to(v) for v in lings), default=1e6))
            if workers
            else None
        )
        vision = bool(pocket) and all(
            bot.is_visible(pocket.position + Point2(offset))
            for offset in [(0, 0), (5, 0), (-5, 0), (0, 5), (0, -5)]
        )
        local_workers = sum(u.distance_to(pocket) < 7 for u in workers) if pocket else 0
        danger = bool(pocket) and any(u.distance_to(pocket) < 13 for u in armed)
        safe_pressure = pressure_allowed(
            full_local_vision=vision,
            workers=local_workers,
            armed=danger,
            healthy_lings=len(healthy),
            home_safe=home_safe,
            seconds=bot.time,
        )
        if safe_pressure and not self.pressure_spent and self.pressure_until is None:
            self.pressure_until = bot.state.game_loop + 224
        if self.pressure_until is not None and (
            not safe_pressure or bot.state.game_loop >= self.pressure_until
        ):
            self.pressure_spent = True
            self.pressure_until = None
        self.pressure_ready = safe_pressure and self.pressure_until is not None
        self.event(
            bot,
            "ling_pressure",
            "local_window" if self.pressure_ready else "scout_or_disengage",
            full_local_vision=bool(vision),
            visible_workers=int(local_workers),
            armed_nearby=bool(danger),
        )
        approach = bot.enemy_start_locations[0].towards(bot.game_info.map_center, 10)
        for ling in lings:
            danger_near = [u for u in armed if u.distance_to(ling) < 9]
            if danger_near:
                self.retreat_until[ling.tag] = bot.state.game_loop + 112
            if (
                ling.health_percentage < 0.65
                or bot.state.game_loop < self.retreat_until.get(ling.tag, -1)
                or not home_safe
                or self.pressure_spent
            ):
                ling.move(retreat)
            elif self.pressure_ready and pocket is not None:
                ling.attack(pocket)
            elif ling.distance_to(approach) > 3:
                ling.move(approach)
        # Hydras are actual anti-air. Each receives one command; roach arbitration remains separate.
        roaches = bot.units.of_type({U.ROACH, U.ROACHBURROWED})
        for hydra in bot.units(U.HYDRALISK):
            air = [
                u
                for u in bot.enemy_units
                if u.is_visible
                and u.is_flying
                and (u.can_attack_ground or u.can_attack_air or u.type_id in SPECIAL_AIR)
                and (
                    u.distance_to(hydra) < 12
                    or any(u.distance_to(b) < 22 for b in bot.townhalls.ready)
                )
            ]
            if hydra.health_percentage < 0.3:
                hydra.move(retreat)
            elif air:
                hydra.attack(min(air, key=hydra.distance_to))
            elif bot.strategy.attacking:
                hydra.attack(target)
            elif roaches:
                hydra.move(roaches.closest_to(hydra).position)
            else:
                hydra.move(retreat)
