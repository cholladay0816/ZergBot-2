"""Isolated ling diversion and worker-anchored Hellion opposition."""

import math

from sc2.position import Point2

from .harass_micro import json_point, line_overlap


def route_points(home, center, side):
    direction = (center - home).normalized
    lateral = Point2((-direction.y, direction.x)) * side
    return [home + direction * 12 + lateral * 12, home + lateral * 12]


class LingDiversion:
    def __init__(self):
        self.roles = {}
        self.stage = {}
        self.started = None

    async def step(self, bot, lings, workers, hellions, home, split, approach):
        frame = bot.state.game_loop
        if not lings:
            return
        if self.started is None:
            self.started = frame
            self.roles = {u.tag: i < 4 for i, u in enumerate(sorted(lings, key=lambda u: u.tag))}
        workers = [w for w in workers if w.is_visible]
        hellions = [h for h in hellions if h.is_visible]
        waypoints = route_points(home, bot.game_info.map_center, -1 if approach == 0 else 1)
        for ling in lings:
            decoy = split and self.roles.get(ling.tag, False) and frame - self.started < 628
            target = None
            if decoy and hellions:
                enemy = min(hellions, key=ling.distance_to)
                point = enemy.position.towards(ling.position, 7)
                if bot.in_pathing_grid(point):
                    ling.move(point)
                    reason = "visible_hellion_distraction"
                else:
                    ling.attack(home)
                    reason = "distraction_no_path"
            elif (
                split
                and not decoy
                and self.stage.get(ling.tag, 0) < 2
                and frame - self.started < 628
            ):
                stage = self.stage.get(ling.tag, 0)
                point = waypoints[stage]
                if ling.distance_to(point) < 2:
                    self.stage[ling.tag] = stage + 1
                distance = (
                    await bot.client.query_pathing(ling.position, point)
                    if ling.tag not in self.stage
                    else 1
                )
                if distance is None or not bot.in_pathing_grid(point):
                    self.stage[ling.tag] = 2
                    ling.attack(home)
                    reason = "flank_unreachable_fallback"
                else:
                    self.stage.setdefault(ling.tag, stage)
                    ling.move(point)
                    reason = "traverse_flank"
            elif workers:
                nearby = [w for w in workers if ling.distance_to(w) < 2]
                target = (
                    min(nearby, key=lambda w: w.health)
                    if nearby
                    else min(workers, key=ling.distance_to)
                )
                ling.attack(target)
                reason = "attack_visible_worker"
            else:
                ling.attack(home)
                reason = "scout_known_start"
            if bot.sample_due(f"diversion-{ling.tag}", frame, 16):
                bot.record(
                    "hellion_diversion",
                    tag=int(ling.tag),
                    reason=reason,
                    position=json_point(ling.position),
                    health=float(ling.health),
                    target_tag=int(target.tag) if target else None,
                    worker_distance=float(min(ling.distance_to(w) for w in workers))
                    if workers
                    else None,
                    stage=int(self.stage.get(ling.tag, 0)),
                )


def defend_workers(bot, hellions, lings, workers, home):
    # Only visible attackers near our actual worker line justify pursuit.
    pocket = workers.center if workers else home
    threats = [u for u in lings if u.is_visible and u.distance_to(pocket) < 14]
    for unit in hellions:
        target = None
        if threats:
            in_range = [u for u in threats if unit.target_in_range(u)]
            target = (
                max(
                    in_range,
                    key=lambda u: (
                        line_overlap(
                            unit.position,
                            u.position,
                            [v.position for v in threats],
                            unit.ground_range + 1,
                        ),
                        -u.health,
                    ),
                )
                if in_range
                else min(threats, key=lambda u: u.distance_to(pocket))
            )
            if unit.weapon_cooldown > 0 and unit.distance_to(target) < 7:
                points = [
                    unit.position
                    + Point2((math.cos(i * math.pi / 4) * 2, math.sin(i * math.pi / 4) * 2))
                    for i in range(8)
                ]
                valid = [p for p in points if p.distance_to(pocket) < 10 and bot.in_pathing_grid(p)]
                if valid:
                    unit.move(
                        max(valid, key=lambda p: min(p.distance_to(t.position) for t in threats))
                    )
                    reason = "kite_near_workers"
                else:
                    unit.attack(target)
                    reason = "attack_no_escape"
            else:
                unit.attack(target)
                reason = "protect_workers"
        else:
            unit.move(pocket.towards(bot.game_info.map_center, 4))
            reason = "hold_worker_line"
        if bot.sample_due(f"hellion-defense-{unit.tag}", bot.state.game_loop, 16):
            bot.record(
                "hellion_defense",
                tag=int(unit.tag),
                reason=reason,
                position=json_point(unit.position),
                own_cooldown=float(unit.weapon_cooldown),
                target_tag=int(target.tag) if target else None,
                worker_distance=float(unit.distance_to(pocket)),
            )
