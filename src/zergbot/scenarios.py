"""Isolated debug-setup micro scenarios, never imported by the competitive bot."""

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race
from sc2.ids.ability_id import AbilityId as A
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.main import run_game
from sc2.player import Bot
from sc2.position import Point2

from .config import BotConfig
from .queens import QueenManager


def approach_point(base, center, approach):
    point = base.towards(center, 16)
    return point + Point2((0, (approach - 1) * 6))


class MeasuredBot(BotAI):
    def __init__(self, options, output):
        super().__init__()
        self.options, self.output = options, output
        self.events = []
        self.counts = Counter()
        self.damage = Counter()
        self.commands = Counter()
        self.previous_positions = {}
        self.last_alive = {}
        self.termination = "incomplete"

    def record(self, kind, **fields):
        if len(self.events) < 3000:
            self.events.append(dict(frame=int(self.state.game_loop), kind=kind, **fields))

    def do(self, action, *args, **kwargs):
        if hasattr(action, "unit"):
            self.commands[action.unit.tag] += 1
            if action.unit.type_id in {U.QUEEN, U.REAPER}:
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

    async def on_unit_took_damage(self, unit, amount_damage_taken):
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
    def __init__(self, options, output):
        super().__init__(options, output)
        self.config = BotConfig(queen_tactical_micro=options.controller == "micro")
        self.manager = QueenManager(self.config)
        self.telemetry = None
        self.worker_tags = set()
        self.active_charges = set()

    async def on_start(self):
        self.client.game_step = 4
        self.worker_tags = {u.tag for u in self.workers}
        base = self.start_location
        queen = base.towards(self.game_info.map_center, 5)
        attack = approach_point(base, self.game_info.map_center, self.options.approach)
        if not self.in_pathing_grid(attack):
            attack = base.towards(self.game_info.map_center, 16)
        commands = [(U.QUEEN, 1, queen, 1)]
        if self.options.scenario == "reaper":
            commands.append((U.REAPER, 1, attack, 2))
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

    async def on_step(self, iteration):
        self.begin_frame()
        queens = list(self.units(U.QUEEN))
        abilities = await self.get_available_abilities(queens) if queens else []
        await self.manager.step(
            self, {q.tag: set(a) for q, a in zip(queens, abilities, strict=True)}
        )
        for queen in queens:
            previous = self.previous_positions.get(queen.tag, queen.position)
            self.counts["queen_moved_during_own_cooldown_frames"] += bool(
                queen.weapon_cooldown > 0 and queen.distance_to(previous) > 0.05
            )
            self.previous_positions[queen.tag] = queen.position
        for worker in self.workers.idle:
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


class Attacker(MeasuredBot):
    def __init__(self, options, output):
        super().__init__(options, output)
        self.retreating = False
        self.previous_enemy = {}
        self.next_build = 0

    async def on_start(self):
        self.client.game_step = 4
        # Keep town halls to avoid an artificial elimination. Remove only initial workers.
        await self.client.debug_kill_unit(self.workers)

    async def on_step(self, iteration):
        self.begin_frame()
        workers = [u for u in self.enemy_units if u.type_id in {U.DRONE, U.SCV, U.PROBE}]
        queens = list(self.enemy_units(U.QUEEN))
        home = self.enemy_start_locations[0]
        if self.options.scenario == "reaper":
            for reaper in self.units(U.REAPER):
                await self.reaper_step(reaper, workers, queens, home)
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
        if reaper.health_percentage < 0.35:
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
            point = (
                reaper.position.towards((queen or target).position, -4)
                if queen or target
                else home.towards(self.game_info.map_center, 25)
            )
            if self.in_pathing_grid(point):
                reaper.move(point)
            reason = "health_retreat"
        else:
            available = (await self.get_available_abilities([reaper]))[0]
            grenade_target = queen or target
            prediction = None
            if grenade_target is not None:
                prediction = grenade_target.position
                old = self.previous_enemy.get(grenade_target.tag)
                if old and self.state.game_loop > old[1]:
                    velocity = (grenade_target.position - old[0]) * (
                        22.4 / (self.state.game_loop - old[1])
                    )
                    if velocity.length > 0:
                        prediction += velocity.normalized * min(2, velocity.length * 0.5)
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
                )
                reason = "grenade"
            elif reaper.weapon_cooldown > 0 and queen is not None and reaper.distance_to(queen) < 9:
                point = reaper.position.towards(queen.position, -2.5)
                if self.in_pathing_grid(point):
                    reaper.move(point)
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
            if place is not None:
                probe.build(U.PYLON, place)
                self.next_build = self.state.game_loop + 112
                self.record("pylon_build_attempt", position=list(place))
        elif (
            self.structures(U.PYLON).ready
            and not self.structures(U.PHOTONCANNON)
            and not self.already_pending(U.PHOTONCANNON)
        ):
            place = await self.find_placement(
                U.PHOTONCANNON,
                near=home.towards(self.game_info.map_center, 8),
                max_distance=5,
                random_alternative=False,
            )
            if place is not None:
                probe.build(U.PHOTONCANNON, place)
                self.next_build = self.state.game_loop + 112
                self.record("cannon_build_attempt", position=list(place))
        if self.state.game_loop % 112 == 0:
            self.record(
                "construction",
                pylons=[float(u.build_progress) for u in self.structures(U.PYLON)],
                cannons=[float(u.build_progress) for u in self.structures(U.PHOTONCANNON)],
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", default="AbyssalReefLE")
    parser.add_argument("--game-time-limit", type=int, default=90)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--scenario", choices=["reaper", "lings", "cannon"], required=True)
    parser.add_argument("--controller", choices=["baseline", "micro"], default="micro")
    parser.add_argument("--approach", type=int, choices=[0, 1, 2], default=1)
    args = parser.parse_args()
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
    defender, attacker = Defender(args, output), Attacker(args, output)
    settings = dict(
        vars(args),
        scope="isolated_debug_setup_normal_fog",
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
                Bot(Race.Zerg, defender),
                Bot(
                    Race.Protoss
                    if args.scenario == "cannon"
                    else Race.Zerg
                    if args.scenario == "lings"
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
