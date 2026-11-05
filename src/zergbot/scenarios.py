"""Isolated debug-setup micro scenarios, never imported by the competitive bot."""

import argparse
import asyncio
import json
import math
import random
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race
from sc2.ids.ability_id import AbilityId as A
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.main import run_game
from sc2.player import Bot
from sc2.position import Point2

from . import cliff_scenario
from .adept_micro import AdeptHarass
from .agents import Action, AgentRegistry, CommandArbiter, Intent
from .burrow_trial import BurrowTrial
from .config import BotConfig
from .diversion import LingDiversion, defend_workers
from .harass_micro import HellionHarass, validate_harass_event
from .integration import SC2UnitGateway
from .queens import QueenManager
from .scenario_geometry import grenade_score, mineral_ingress, predict_visible_position
from .shade_guard import guard_queen
from .siege_spacing import SiegeSpacing, spacing_sample
from .tank_micro import split_waypoint
from .vision_assist import VisionAssist
from .worker_safety import worker_action


def observed_order(order):
    return dict(
        ability=int(order.ability.id.value),
        target=int(order.target) if isinstance(order.target, int) else None,
    )


def cannon_candidates(pylon, home):
    points = {
        Point2(
            (
                round(pylon.x + math.cos(i * math.pi / 8) * radius),
                round(pylon.y + math.sin(i * math.pi / 8) * radius),
            )
        )
        for radius in (3, 5)
        for i in range(16)
    }
    return sorted(points, key=lambda p: (p.distance_to(home), p.x, p.y))


def approach_point(base, center, approach):
    point = base.towards(center, 16)
    return point + Point2((0, (approach - 1) * 6))


def escape_point(position, threat, pathable, distance=3):
    candidates = [
        position
        + Point2((math.cos(i * math.pi / 8) * distance, math.sin(i * math.pi / 8) * distance))
        for i in range(16)
    ]
    valid = [p for p in candidates if pathable(p) and pathable(position.towards(p, 1))]
    return max(valid, key=lambda p: p.distance_to(threat)) if valid else None


class MeasuredBot(BotAI):
    def __init__(self, options, output, setup_barrier=None):
        super().__init__()
        self.options, self.output = options, output
        self.setup_barrier = setup_barrier
        self.events = []
        self.counts = Counter()
        self.damage = Counter()
        self.commands = Counter()
        self.previous_positions = {}
        self.last_alive = {}
        self.previous_own_types = {}
        self.termination = "incomplete"
        self.next_samples = {}
        self.worker_defense_start = None
        self.worker_defenders = set()

    async def cleanup_ready(self):
        """Finish initial-worker removal before either side creates scenario actors."""
        if self.setup_barrier is not None:
            await asyncio.wait_for(self.setup_barrier.wait(), timeout=15)
        self.record("cleanup_ready")

    async def setup_ready(self):
        if self.setup_barrier is not None:
            await asyncio.wait_for(self.setup_barrier.wait(), timeout=15)
        self.record("setup_ready")

    def sample_due(self, key, frame, interval):
        if frame < self.next_samples.get(key, 0):
            return False
        self.next_samples[key] = frame + interval
        return True

    def record(self, kind, **fields):
        validate_harass_event(kind, fields)
        if len(self.events) < 3000:
            self.events.append(dict(frame=int(self.state.game_loop), kind=kind, **fields))

    def do(self, action, *args, **kwargs):
        if hasattr(action, "unit"):
            self.commands[action.unit.tag] += 1
            if action.unit.type_id in {U.QUEEN, U.REAPER, U.HELLION, U.ADEPT, U.ADEPTPHASESHIFT}:
                self.record(
                    "own_command",
                    unit_type=action.unit.type_id.name,
                    tag=int(action.unit.tag),
                    ability=action.ability.name,
                    position=list(action.unit.position),
                    own_cooldown=float(action.unit.weapon_cooldown),
                    target_tag=int(action.target.tag) if hasattr(action.target, "tag") else None,
                    target_position=list(action.target)
                    if isinstance(action.target, Point2)
                    else None,
                )
        return super().do(action, *args, **kwargs)

    def begin_frame(self):
        self.commands.clear()
        for error in self.state.action_errors:
            self.record("action_error", ability_id=int(error.ability_id), result=int(error.result))
            self.counts["action_errors"] += 1

    def end_frame(self):
        self.counts["conflicting_unit_frames"] += sum(v > 1 for v in self.commands.values())
        self.last_alive = dict(Counter(u.type_id.name for u in self.units))
        self.previous_own_types = {u.tag: u.type_id.name for u in self.units}

    async def on_unit_destroyed(self, tag):
        if self.options.scenario == "cliff" and tag in self.previous_own_types:
            self.record("vision_destroyed", tag=int(tag), unit_type=self.previous_own_types[tag])
        if self.options.scenario == "tank" and tag in self.previous_own_types:
            self.record("siege_destroyed", tag=int(tag), unit_type=self.previous_own_types[tag])
        if self.options.scenario == "burrow-tank" and tag in self.previous_own_types:
            self.record("burrow_destroyed", tag=int(tag), unit_type=self.previous_own_types[tag])

    async def on_unit_took_damage(self, unit, amount_damage_taken):
        if self.options.scenario == "cliff" and unit.type_id == U.HYDRALISK:
            self.vision_assist.observe_damage(
                unit.position,
                self.state.game_loop,
                self.get_terrain_height,
                self.is_visible,
                lambda point: cliff_scenario.in_bounds(self, point),
            )
            region = self.vision_assist.region
            if region is not None and self.vision_assist.started is None:
                self.record(
                    "vision_inference",
                    source_type=region.source_type,
                    source_confirmed=region.source_confirmed,
                    radius=region.radius,
                    exhaustive=region.exhaustive,
                    candidate_count=len(region.cells),
                    assumptions=list(region.assumptions),
                )
        self.damage[unit.type_id.name] += float(amount_damage_taken)
        self.record(
            "own_damage",
            tag=int(unit.tag),
            unit_type=unit.type_id.name,
            amount=float(amount_damage_taken),
            health=float(unit.health),
        )

    async def on_end(self, result):
        self.termination = str(result)
        self.write()

    def write(self):
        payload = dict(
            player=int(self.player_id),
            scope="own_and_normally_visible_observations",
            termination=self.termination,
            counts=dict(self.counts),
            damage=dict(self.damage),
            last_alive=self.last_alive,
            events=self.events,
        )
        (self.output / f"player-{self.player_id}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )


class Defender(MeasuredBot):
    def __init__(self, options, output, setup_barrier=None):
        super().__init__(options, output, setup_barrier)
        self.config = BotConfig(
            queen_tactical_micro=options.controller == "micro",
            queen_recovery=options.queen_recovery,
        )
        self.manager = QueenManager(self.config)
        self.roach_gateway = SC2UnitGateway(self)
        self.roach_registry = AgentRegistry()
        self.siege_spacing = SiegeSpacing()
        self.telemetry = None
        self.worker_tags = set()
        self.active_charges = set()
        self.split_start = None
        self.split_slots = {}
        self.burrow_trial = BurrowTrial()
        self.vision_assist = VisionAssist()
        self.vision_held = set()
        self.vision_reason = None

    async def on_start(self):
        self.client.game_step = 4
        self.worker_tags = {u.tag for u in self.workers}
        await self.cleanup_ready()
        if self.options.scenario == "cliff":
            await cliff_scenario.setup(self)
            await self.setup_ready()
            return
        base = self.start_location
        queen = base.towards(self.game_info.map_center, 5)
        attack = approach_point(base, self.game_info.map_center, self.options.approach)
        if self.options.scenario == "reaper" and self.options.ingress == "minerals":
            patches = self.mineral_field.closer_than(12, base)
            attack = (
                mineral_ingress(base, patches.center, self.options.approach, self.in_pathing_grid)
                if patches
                else None
            )
            if attack is None:
                raise ValueError("No valid mineral-side Reaper setup point")
        if not self.in_pathing_grid(attack):
            attack = base.towards(self.game_info.map_center, 16)
        commands = [] if self.options.scenario == "tank" else [(U.QUEEN, 1, queen, 1)]
        if self.options.scenario == "burrow-tank":
            commands = [(U.SPAWNINGPOOL, 1, base.towards(self.game_info.map_center, 4), 1)]
            await self.client.debug_all_resources()
        elif self.options.scenario == "roach-tank":
            commands = [
                (U.ROACH, 20, queen, 1),
                (U.OVERLORD, 1, base.towards(self.game_info.map_center, 10), 1),
                (U.SIEGETANKSIEGED, 2, attack, 2),
                (U.MARINE, 8, attack, 2),
                (U.MARAUDER, 4, attack, 2),
            ]
        elif self.options.scenario == "diversion":
            commands = [(U.HELLION, 2, queen, 1), (U.ZERGLING, 12, attack, 2)]
        elif self.options.scenario == "reaper":
            commands.append((U.REAPER, 1, attack, 2))
        elif self.options.scenario == "hellion":
            commands.append((U.HELLION, 2, attack, 2))
        elif self.options.scenario == "adept":
            commands.append((U.ADEPT, 1, attack, 2))
        elif self.options.scenario == "tank":
            commands.extend(
                [
                    (U.ZERGLING, 12, queen, 1),
                    (U.BANELING, 4, queen, 1),
                    (U.OVERLORD, 1, base.towards(self.game_info.map_center, 10), 1),
                    (U.SIEGETANKSIEGED, self.options.tank_count, attack, 2),
                ]
            )
        elif self.options.scenario == "lings":
            commands.append((U.ZERGLING, 6, attack, 2))
        else:
            commands.extend(
                [
                    (U.PROBE, 1, attack, 2),
                    (
                        U.FORGE,
                        1,
                        self.enemy_start_locations[0].towards(self.game_info.map_center, 5),
                        2,
                    ),
                ]
            )
            await self.client.debug_all_resources()
        await self.client.debug_create_unit(commands)
        self.record(
            "debug_setup",
            scenario=self.options.scenario,
            queen_position=list(queen),
            attacker_position=list(attack),
            resource_grant=self.options.scenario == "cannon",
        )
        await self.setup_ready()

    async def on_step(self, iteration):
        self.begin_frame()
        if self.options.scenario == "cliff":
            cliff_scenario.defender_step(self)
            self.end_frame()
            return
        if self.options.scenario == "burrow-tank":
            await self.burrow_trial.step(self)
            self.end_frame()
            return
        if self.options.scenario == "tank":
            self.tank_defense()
        elif self.options.scenario == "roach-tank":
            await self.roach_tank_step()
        if self.options.scenario == "diversion":
            defend_workers(
                self,
                list(self.units(U.HELLION)),
                list(self.enemy_units(U.ZERGLING)),
                self.workers,
                self.start_location,
            )
        queens = list(self.units(U.QUEEN))
        abilities = await self.get_available_abilities(queens) if queens else []
        reserved = set()
        if getattr(self.options, "shade_guard", False) and self.workers:
            shades = list(self.enemy_units(U.ADEPTPHASESHIFT).visible)
            threats = list(self.enemy_units.visible.filter(lambda u: u.can_attack_ground))
            for queen in queens:
                if guard_queen(self, queen, self.workers.center, shades, threats):
                    reserved.add(queen.tag)
        await self.manager.step(
            self,
            {q.tag: set(a) for q, a in zip(queens, abilities, strict=True)},
            reserved_tags=reserved,
        )
        for queen in queens:
            previous = self.previous_positions.get(queen.tag, queen.position)
            self.counts["queen_moved_during_own_cooldown_frames"] += bool(
                queen.weapon_cooldown > 0 and queen.distance_to(previous) > 0.05
            )
            self.previous_positions[queen.tag] = queen.position
        handled = set()
        if self.options.worker_safety:
            handled = self.protect_workers()
        for worker in self.workers.idle:
            if worker.tag in handled:
                continue
            minerals = self.mineral_field.closer_than(12, self.start_location)
            if minerals:
                worker.gather(minerals.closest_to(worker))
        charges = {
            tuple(p)
            for e in self.state.effects
            if e.id == "KD8CHARGE" and e.is_enemy
            for p in e.positions
        }
        fresh = charges - self.active_charges
        self.counts["observed_charge_episodes"] += len(fresh)
        self.counts["charge_visible_frames"] += bool(charges)
        for point in fresh:
            self.record("observed_charge", position=list(point))
        self.active_charges = charges
        self.counts["worker_idle_unit_frames"] += self.workers.idle.amount
        self.counts["worker_gathering_unit_frames"] += sum(u.is_gathering for u in self.workers)
        if iteration % 4 == 0:
            visible = [
                dict(
                    tag=int(u.tag),
                    type=u.type_id.name,
                    position=list(u.position),
                    health=float(u.health),
                )
                for u in self.enemy_units
            ]
            self.record(
                "defender_sample",
                workers=self.workers.amount,
                worker_state=[
                    dict(
                        tag=int(w.tag),
                        position=list(w.position),
                        health=float(w.health),
                        own_cooldown=float(w.weapon_cooldown),
                        gathering=bool(w.is_gathering),
                        returning=bool(w.is_returning),
                        orders=[observed_order(o) for o in w.orders],
                    )
                    for w in self.workers
                ],
                worker_defense_elapsed=(
                    int(self.state.game_loop - self.worker_defense_start)
                    if self.worker_defense_start is not None
                    else None
                ),
                queens=[
                    dict(
                        tag=int(q.tag),
                        position=list(q.position),
                        health=float(q.health),
                        own_cooldown=float(q.weapon_cooldown),
                        nearest_worker_distance=float(
                            min((q.distance_to(w) for w in self.workers), default=0)
                        ),
                    )
                    for q in queens
                ],
                visible_enemy=visible,
                charges=[list(p) for p in charges],
                minerals=int(self.minerals),
            )
        self.counts["workers_lost"] = len(self.worker_tags - {u.tag for u in self.workers})
        self.end_frame()

    def protect_workers(self):
        threats = self.enemy_units.filter(
            lambda u: not u.is_flying and u.can_attack_ground
        ).closer_than(12, self.start_location)
        minerals = self.mineral_field.closer_than(12, self.start_location)
        if not threats or not minerals:
            released = set()
            for worker in self.workers:
                if worker.tag in self.worker_defenders and minerals:
                    worker.gather(minerals.closest_to(worker))
                    released.add(worker.tag)
            self.worker_defenders.clear()
            self.worker_defense_start = None
            return released
        if self.worker_defense_start is None:
            self.worker_defense_start = self.state.game_loop
        selected = {
            w.tag
            for w in sorted(
                self.workers,
                key=lambda w: (-w.health_percentage, w.distance_to(threats.closest_to(w))),
            )[: self.options.worker_defense_count]
        }
        handled = set()
        active = set()
        for worker in self.workers:
            threat = threats.closest_to(worker)
            action = worker_action(
                worker.health_percentage,
                worker.distance_to(threat),
                worker.tag in selected,
                self.state.game_loop - self.worker_defense_start,
                max_frames=int(self.options.worker_defense_seconds * 22.4),
            )
            if action == "evacuate":
                safe = max(minerals, key=lambda m: min(m.distance_to(t) for t in threats))
                worker.gather(safe)
            elif action == "defend":
                local = threats.closer_than(4, worker)
                worker.attack(min(local, key=lambda t: t.health))
            elif worker.tag in self.worker_defenders:
                worker.gather(minerals.closest_to(worker))
            else:
                continue
            handled.add(worker.tag)
            if action != "mine":
                active.add(worker.tag)
            self.counts["worker_" + action + "_commands"] += 1
        # A released worker is handled this frame only. Retaining it would send
        # gather every subsequent frame and can interrupt normal cargo returns.
        self.worker_defenders = active
        return handled

    async def roach_tank_step(self):
        observations = await self.roach_gateway.observe()
        self.roach_registry.sync(observations)
        units = list(self.roach_gateway.units.values())
        enemies = list(self.enemy_units.visible)
        arbiter = CommandArbiter()
        for obs in observations:
            arbiter.submit(Intent(obs.tag, Action.ATTACK, 10, "scenario_army_attack"))
        if self.options.controller == "micro":
            for intent in self.siege_spacing.orders(
                units, enemies, self.state.game_loop, self.in_pathing_grid
            ):
                arbiter.submit(intent)
        for obs in observations:
            intent = self.roach_registry.agents[obs.tag].decide(
                obs, self.state.game_loop, self.config
            )
            if intent is not None:
                arbiter.submit(intent)
        for intent in arbiter.commands.values():
            if intent.reason in {"visible_siege_spacing", "siege_spacing_motion"}:
                self.counts["siege_" + intent.action.name] += 1
        target = approach_point(
            self.start_location, self.game_info.map_center, self.options.approach
        )
        self.roach_gateway.dispatch(arbiter, target, self.start_location)
        if self.sample_due("siege", self.state.game_loop, 16):
            self.record(
                "siege_sample",
                **spacing_sample(
                    units, [e for e in enemies if e.type_id in {U.SIEGETANK, U.SIEGETANKSIEGED}]
                ),
            )

    def tank_defense(self):
        army = list(self.units.of_type({U.ZERGLING, U.BANELING}))
        tanks = self.enemy_units.of_type({U.SIEGETANK, U.SIEGETANKSIEGED})
        if tanks and self.split_start is None:
            self.split_start = self.state.game_loop
            self.split_slots = {u.tag: i for i, u in enumerate(sorted(army, key=lambda u: u.tag))}
        for unit in army:
            if tanks:
                tank = tanks.closest_to(unit)
                waypoint = (
                    split_waypoint(
                        unit.position,
                        tank.position,
                        self.start_location,
                        self.split_slots.get(unit.tag, 0),
                        self.state.game_loop - self.split_start,
                        self.in_pathing_grid,
                    )
                    if self.options.controller == "micro"
                    else None
                )
                if waypoint is not None:
                    unit.move(waypoint)
                else:
                    unit.attack(tank)
            elif self.split_start is None:
                unit.attack(
                    approach_point(
                        self.start_location, self.game_info.map_center, self.options.approach
                    )
                )
        if self.sample_due("tank", self.state.game_loop, 16):
            distances = [a.distance_to(b) for i, a in enumerate(army) for b in army[i + 1 :]]
            self.record(
                "tank_army_sample",
                units=[
                    dict(
                        tag=int(u.tag),
                        type=u.type_id.name,
                        position=list(u.position),
                        health=float(u.health),
                    )
                    for u in army
                ],
                min_pair_distance=float(min(distances)) if distances else None,
                tank_visible=bool(tanks),
                tank_health=[float(t.health) for t in tanks],
                split_elapsed_frames=int(self.state.game_loop - self.split_start)
                if self.split_start is not None
                else None,
            )


class Attacker(MeasuredBot):
    def __init__(self, options, output, setup_barrier=None):
        super().__init__(options, output, setup_barrier)
        self.retreating = False
        self.hellion_controller = HellionHarass()
        self.diversion_controller = LingDiversion()
        self.adept_controller = AdeptHarass(options.adept_mode)
        self.previous_enemy = {}
        self.next_build = 0

    async def on_start(self):
        self.client.game_step = 4
        # Keep town halls to avoid an artificial elimination. Remove only initial workers.
        await self.client.debug_kill_unit(self.workers)
        await self.cleanup_ready()
        await self.setup_ready()

    async def on_step(self, iteration):
        self.begin_frame()
        if self.options.scenario == "cliff":
            cliff_scenario.attacker_step(self)
            self.end_frame()
            return
        workers = [u for u in self.enemy_units if u.type_id in {U.DRONE, U.SCV, U.PROBE}]
        queens = list(self.enemy_units(U.QUEEN))
        home = self.enemy_start_locations[0]
        if self.options.scenario == "diversion":
            await self.diversion_controller.step(
                self,
                list(self.units(U.ZERGLING)),
                workers,
                list(self.enemy_units(U.HELLION)),
                home,
                self.options.ling_split,
                self.options.approach,
            )
        elif self.options.scenario == "reaper":
            for reaper in self.units(U.REAPER):
                await self.reaper_step(reaper, workers, queens, home)
        elif self.options.scenario == "adept":
            await self.adept_controller.step(
                self,
                list(self.units(U.ADEPT)),
                list(self.units(U.ADEPTPHASESHIFT)),
                workers,
                queens,
                home,
            )
        elif self.options.scenario == "hellion":
            await self.hellion_controller.step(
                self, list(self.units(U.HELLION)), workers, queens, home, self.options.approach
            )
        elif self.options.scenario == "lings":
            for ling in self.units(U.ZERGLING):
                targets = [u for u in workers if ling.distance_to(u) < 8] or workers or queens
                if targets:
                    target = min(
                        targets,
                        key=lambda u: (
                            u.health if ling.distance_to(u) < 1.5 else 1000,
                            ling.distance_to(u),
                        ),
                    )
                    ling.attack(target)
                else:
                    ling.attack(home)
        elif self.options.scenario in {"tank", "roach-tank", "burrow-tank"}:
            for tank in self.units.of_type({U.SIEGETANK, U.SIEGETANKSIEGED}):
                targets = list(
                    self.enemy_units.of_type(
                        {U.ROACH, U.ROACHBURROWED}
                        if self.options.scenario in {"roach-tank", "burrow-tank"}
                        else {U.ZERGLING, U.BANELING}
                    ).visible
                )
                if targets:
                    # The scripted tank selects visible clusters, not hidden units.
                    target = max(
                        targets, key=lambda u: sum(v.distance_to(u) < 1.5 for v in targets)
                    )
                    tank.attack(target)
                    self.record(
                        "tank_target",
                        tag=int(target.tag),
                        position=list(target.position),
                        own_cooldown=float(tank.weapon_cooldown),
                    )
            if self.options.scenario == "tank":
                for tank in self.units(U.SIEGETANKSIEGED):
                    self.record(
                        "siege_weapon",
                        tag=int(tank.tag),
                        own_cooldown=float(tank.weapon_cooldown),
                        health=float(tank.health),
                        position=[float(v) for v in tank.position],
                        own_target=int(tank.orders[0].target)
                        if tank.orders and isinstance(tank.orders[0].target, int)
                        else None,
                    )
            if self.options.scenario == "burrow-tank":
                for tank in self.units(U.SIEGETANKSIEGED):
                    self.record(
                        "burrow_tank",
                        tag=int(tank.tag),
                        own_target=int(tank.orders[0].target)
                        if tank.orders and isinstance(tank.orders[0].target, int)
                        else None,
                        own_cooldown=float(tank.weapon_cooldown),
                        position=[float(v) for v in tank.position],
                        visible_roaches=[
                            int(u.tag)
                            for u in self.enemy_units.of_type({U.ROACH, U.ROACHBURROWED}).visible
                        ],
                    )
            if self.options.scenario == "roach-tank":
                targets = list(self.enemy_units.of_type({U.ROACH, U.ROACHBURROWED}).visible)
                for soldier in self.units.of_type({U.MARINE, U.MARAUDER}):
                    if targets:
                        soldier.attack(
                            min(
                                targets,
                                key=lambda u: (
                                    u.health if soldier.target_in_range(u) else 1000,
                                    soldier.distance_to(u),
                                ),
                            )
                        )
        else:
            await self.cannon_step(home)
        self.previous_enemy = {u.tag: (u.position, self.state.game_loop) for u in self.enemy_units}
        self.end_frame()

    async def reaper_step(self, reaper, workers, queens, home):
        previous = self.previous_positions.get(reaper.tag, reaper.position)
        moved = float(reaper.distance_to(previous))
        self.previous_positions[reaper.tag] = reaper.position
        self.counts["moved_during_own_cooldown_frames"] += (
            reaper.weapon_cooldown > 0 and moved > 0.05
        )
        if reaper.health_percentage < 0.55:
            self.retreating = True
        elif reaper.health_percentage > 0.9:
            self.retreating = False
        nearby = [
            u
            for u in workers
            if reaper.distance_to(u) <= reaper.ground_range + reaper.radius + u.radius
        ]
        candidates = nearby or workers or queens
        target = (
            min(
                candidates, key=lambda u: (u.health if u in nearby else 1000, reaper.distance_to(u))
            )
            if candidates
            else None
        )
        queen = min(queens, key=reaper.distance_to) if queens else None
        reason = "approach"
        if self.retreating:
            threat = (queen or target).position if queen or target else home
            point = escape_point(reaper.position, threat, self.in_pathing_grid, 4)
            if point is not None:
                reaper.move(point)
            else:
                reaper.stop()
                self.counts["blocked_retreat_frames"] += 1
            reason = "health_retreat"
        else:
            available = (await self.get_available_abilities([reaper]))[0]
            grenade_target = queen or target
            prediction = None
            coverage = None
            candidates = [grenade_target] if grenade_target is not None else []
            if self.options.grenade_policy == "opportunity":
                candidates = workers + queens
            choices = []
            for candidate in candidates:
                old = self.previous_enemy.get(candidate.tag)
                point = predict_visible_position(
                    candidate.position,
                    old[0] if old else None,
                    self.state.game_loop - old[1] if old else 0,
                )
                if reaper.in_ability_cast_range(A.KD8CHARGE_KD8CHARGE, point):
                    score = grenade_score(
                        point, [w.position for w in workers], [q.position for q in queens]
                    )
                    choices.append((score[0], -reaper.distance_to(point), candidate, point, score))
            if choices:
                _, _, grenade_target, prediction, coverage = max(choices, key=lambda x: x[:2])
            if (
                A.KD8CHARGE_KD8CHARGE in available
                and prediction is not None
                and reaper.in_ability_cast_range(A.KD8CHARGE_KD8CHARGE, prediction)
            ):
                reaper(A.KD8CHARGE_KD8CHARGE, prediction)
                self.counts["grenade_attempts"] += 1
                self.record(
                    "grenade_attempt",
                    target_tag=int(grenade_target.tag),
                    observed_target=list(grenade_target.position),
                    predicted_target=list(prediction),
                    prediction_horizon_seconds=0.5,
                    target_type=grenade_target.type_id.name,
                    estimated_visible_worker_coverage=coverage[1] if coverage else None,
                    estimated_visible_queen_coverage=coverage[2] if coverage else None,
                )
                reason = "grenade"
            elif reaper.weapon_cooldown > 0 and queen is not None and reaper.distance_to(queen) < 9:
                point = escape_point(reaper.position, queen.position, self.in_pathing_grid, 2.5)
                if point is not None:
                    reaper.move(point)
                else:
                    reaper.stop()
                    self.counts["blocked_kite_frames"] += 1
                reason = "cooldown_kite"
            elif target is not None:
                reaper.attack(target)
                reason = "attack_low_worker" if nearby else "approach_target"
            else:
                reaper.move(home)
        self.counts[reason] += 1
        self.record(
            "reaper_decision",
            reason=reason,
            position=list(reaper.position),
            health=float(reaper.health),
            own_cooldown=float(reaper.weapon_cooldown),
            moved_since_observation=moved,
            target_tag=int(target.tag) if target else None,
            target_health=float(target.health) if target else None,
            visible_in_range_worker_health=[float(u.health) for u in nearby],
            queen_distance=float(reaper.distance_to(queen)) if queen else None,
            worker_distance=float(reaper.distance_to(target)) if target else None,
        )

    async def cannon_step(self, home):
        if self.sample_due("construction", self.state.game_loop, 112):
            self.record(
                "construction",
                pylons=[float(u.build_progress) for u in self.structures(U.PYLON)],
                cannons=[float(u.build_progress) for u in self.structures(U.PHOTONCANNON)],
                cannon_state=[
                    dict(
                        tag=int(u.tag),
                        position=list(u.position),
                        ready=bool(u.is_ready),
                        powered=bool(u.is_powered),
                        own_cooldown=float(u.weapon_cooldown),
                        engaged_target=int(u.engaged_target_tag) if u.engaged_target_tag else None,
                    )
                    for u in self.structures(U.PHOTONCANNON)
                ],
            )
        probes = self.units(U.PROBE)
        if not probes or self.state.game_loop < self.next_build:
            return
        probe = probes.first
        if not self.structures(U.PYLON) and not self.already_pending(U.PYLON):
            place = await self.find_placement(
                U.PYLON,
                near=home.towards(self.game_info.map_center, 11),
                max_distance=4,
                random_alternative=False,
            )
            self.next_build = self.state.game_loop + 112
            if place is not None:
                probe.build(U.PYLON, place)
                self.record("pylon_build_attempt", position=list(place))
        elif (
            self.structures(U.PYLON).ready
            and not self.structures(U.PHOTONCANNON)
            and not self.already_pending(U.PHOTONCANNON)
        ):
            pylon = self.structures(U.PYLON).ready.closest_to(home)
            points = cannon_candidates(pylon.position, home)
            legal = await self.can_place(U.PHOTONCANNON, points)
            choices = [p for p, valid in zip(points, legal, strict=True) if valid]
            self.next_build = self.state.game_loop + 112
            self.record(
                "cannon_placement_query",
                pylon_position=list(pylon.position),
                candidates=len(points),
                legal_count=len(choices),
                selected=list(choices[0]) if choices else None,
            )
            if choices:
                probe.build(U.PHOTONCANNON, choices[0])
                self.record("cannon_build_attempt", position=list(choices[0]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", default="AbyssalReefLE")
    parser.add_argument("--game-time-limit", type=int, default=90)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument(
        "--scenario",
        choices=[
            "reaper",
            "lings",
            "cannon",
            "tank",
            "hellion",
            "adept",
            "diversion",
            "roach-tank",
            "burrow-tank",
            "cliff",
        ],
        required=True,
    )
    parser.add_argument("--controller", choices=["baseline", "micro"], default="micro")
    parser.add_argument("--approach", type=int, choices=[0, 1, 2], default=1)
    parser.add_argument("--adept-mode", choices=["commit", "cancel"], default="commit")
    parser.add_argument("--vision-aa", action="store_true")
    parser.add_argument("--tank-count", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--burrow-research", action="store_true")
    parser.add_argument("--burrow-tanks", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--burrow-detection", action="store_true")
    parser.add_argument("--ling-split", action="store_true")
    parser.add_argument("--shade-guard", action="store_true")
    parser.add_argument("--worker-safety", action="store_true")
    parser.add_argument("--worker-defense-count", type=int, choices=range(1, 13), default=6)
    parser.add_argument("--worker-defense-seconds", type=int, default=10)
    parser.add_argument("--queen-recovery", action="store_true")
    parser.add_argument("--ingress", choices=["frontal", "minerals"], default="frontal")
    parser.add_argument(
        "--grenade-policy", choices=["queen-first", "opportunity"], default="queen-first"
    )
    args = parser.parse_args()
    if not 1 <= args.worker_defense_seconds <= 60:
        parser.error("worker defense duration must be 1-60 game seconds")
    output = Path(".local-matches") / (
        "scenario-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + args.scenario
        + "-"
        + args.controller
        + str(args.approach)
    )
    output.mkdir(parents=True)
    random.seed(args.seed)
    np.random.seed(args.seed)
    setup_barrier = asyncio.Barrier(2)
    defender = Defender(args, output, setup_barrier)
    attacker = Attacker(args, output, setup_barrier)
    settings = dict(
        vars(args),
        scope="isolated_debug_setup_normal_fog",
        setup_synchronization="cleanup_then_spawn_two_phase_barrier_15s_timeout",
        python_seed=args.seed,
        game_step=4,
        limitations=(
            "Scripted adversary, not mathematical optimality; no reveal-map/no-cooldown/"
            "invulnerability. Debug-created actors, original town halls retained. Cannon uses "
            "actual Probe construction with Forge and setup resources. No hidden attacker "
            "state enters defender policy."
        ),
    )
    (output / "settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
    try:
        run_game(
            maps.get(args.map),
            [
                Bot(Race.Terran if args.scenario == "diversion" else Race.Zerg, defender),
                Bot(
                    Race.Protoss
                    if args.scenario in {"cannon", "adept"}
                    else Race.Zerg
                    if args.scenario in {"lings", "diversion"}
                    else Race.Terran,
                    attacker,
                ),
            ],
            realtime=False,
            random_seed=args.seed,
            game_time_limit=args.game_time_limit,
            save_replay_as=str(output / "scenario.SC2Replay"),
        )
    finally:
        for bot in (defender, attacker):
            if hasattr(bot, "player_id"):
                bot.write()
    print("Scenario artifacts:", output.resolve())


if __name__ == "__main__":
    main()
