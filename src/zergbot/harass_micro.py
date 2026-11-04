"""Isolated harassment adversaries using own readiness and visible targets only."""

import math

from sc2.position import Point2

HARASS_EVENT_FIELDS = {
    "siege_sample": {"army", "visible_tanks", "minimum_spacing"},
    "hellion_diversion": {
        "tag",
        "reason",
        "position",
        "health",
        "target_tag",
        "worker_distance",
        "stage",
    },
    "hellion_defense": {
        "tag",
        "reason",
        "position",
        "own_cooldown",
        "target_tag",
        "worker_distance",
    },
    "adept_guard": {"tag", "target_position", "moved", "scope"},
    "hellion_route": {"tag", "target", "query_distance", "scope"},
    "hellion_decision": {
        "tag",
        "reason",
        "position",
        "health",
        "own_cooldown",
        "target_tag",
        "target_position",
        "estimated_line_overlap",
        "worker_distance",
    },
    "adept_phase": {
        "stage",
        "tag",
        "shade_tag",
        "mode",
        "position",
        "previous_position",
        "target_position",
        "ability",
        "cast_frame",
        "shade_seen_frame",
        "elapsed_frames",
        "jump_distance",
        "cancel_frame",
        "association",
    },
    "adept_decision": {
        "tag",
        "reason",
        "position",
        "health",
        "shield",
        "own_cooldown",
        "target_tag",
    },
}


def validate_harass_event(kind, fields):
    if kind.startswith(("hellion_", "adept_", "siege_")):
        if kind not in HARASS_EVENT_FIELDS or fields.keys() - HARASS_EVENT_FIELDS[kind]:
            raise ValueError("Unknown harassment diagnostic event or field")


def json_point(point):
    return [float(value) for value in point]


def line_overlap(origin, aim, positions, reach, width=0.75):
    """Approximate alignment score, not the engine's undisclosed splash geometry."""
    dx, dy = aim[0] - origin[0], aim[1] - origin[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return 0
    dx, dy = dx / length, dy / length
    return sum(
        0 <= (p[0] - origin[0]) * dx + (p[1] - origin[1]) * dy <= reach
        and abs((p[0] - origin[0]) * dy - (p[1] - origin[1]) * dx) <= width
        for p in positions
    )


def flank_point(home, center, approach, pathable):
    direction = center - home
    if direction.length < 0.01:
        return None
    direction = direction.normalized
    side = Point2((-direction.y, direction.x))
    preferred = home + side * ((approach - 1) * 10) + direction * 2
    choices = [preferred, home + side * ((approach - 1) * 7) + direction * 3]
    return next((p for p in choices if pathable(p)), None)


class HellionHarass:
    def __init__(self):
        self.previous = {}
        self.routes = {}
        self.last_reason = {}

    async def step(self, bot, hellions, workers, queens, home, approach):
        living = {u.tag for u in hellions}
        for mapping in (self.previous, self.routes, self.last_reason):
            for tag in set(mapping) - living:
                del mapping[tag]
        workers = [u for u in workers if u.is_visible]
        queens = [u for u in queens if u.is_visible]
        for unit in hellions:
            old_position, old_cooldown = self.previous.get(
                unit.tag, (unit.position, unit.weapon_cooldown)
            )
            bot.counts["hellion_moved_with_own_cooldown_samples"] += int(
                unit.weapon_cooldown > 0 and unit.distance_to(old_position) > 0.05
            )
            bot.counts["hellion_weapon_cycle_resets"] += int(
                unit.weapon_cooldown > old_cooldown + 1
            )
            self.previous[unit.tag] = (unit.position, unit.weapon_cooldown)
            if unit.tag not in self.routes:
                route = flank_point(home, bot.game_info.map_center, approach, bot.in_pathing_grid)
                distance = (
                    await bot.client.query_pathing(unit.position, route)
                    if route is not None
                    else None
                )
                self.routes[unit.tag] = route if distance is not None else home
                bot.record(
                    "hellion_route",
                    tag=int(unit.tag),
                    target=json_point(self.routes[unit.tag]),
                    query_distance=float(distance) if distance is not None else None,
                    scope="distance_not_collision_free_route",
                )
            route = self.routes[unit.tag]
            in_range = [w for w in workers if unit.target_in_range(w)]
            bot.counts["hellion_worker_attack_opportunity_samples"] += int(bool(in_range))
            queen = min(queens, key=unit.distance_to) if queens else None
            target = None
            overlap = 0
            if unit.health_percentage < 0.3:
                reason = "retreat_low_health"
                unit.move(home.towards(bot.game_info.map_center, 20))
            elif unit.weapon_cooldown > 0 and queen is not None and unit.distance_to(queen) < 9:
                points = [
                    unit.position
                    + Point2((math.cos(i * math.pi / 4) * 2.5, math.sin(i * math.pi / 4) * 2.5))
                    for i in range(8)
                ]
                valid = [
                    p
                    for p in points
                    if p.distance_to(home) < 17
                    and bot.in_pathing_grid(p)
                    and bot.in_pathing_grid(unit.position.towards(p, 1))
                ]
                if valid:
                    point = max(
                        valid,
                        key=lambda p: p.distance_to(queen.position) - 0.15 * p.distance_to(route),
                    )
                    unit.move(point)
                    reason = "kite_visible_queen"
                else:
                    reason = "hold_no_path_candidate"
            elif in_range:
                target = max(
                    in_range,
                    key=lambda w: (
                        line_overlap(
                            unit.position,
                            w.position,
                            [v.position for v in workers],
                            unit.ground_range + 1,
                        ),
                        -w.health,
                    ),
                )
                overlap = line_overlap(
                    unit.position,
                    target.position,
                    [v.position for v in workers],
                    unit.ground_range + 1,
                )
                unit.attack(target)
                reason = "attack_worker_alignment"
                bot.counts["hellion_worker_attack_commands"] += 1
            elif workers and unit.distance_to(route) < 4:
                target = min(workers, key=unit.distance_to)
                unit.attack(target)
                reason = "approach_visible_workers"
            else:
                unit.move(route)
                reason = "traverse_flank"
            if reason != self.last_reason.get(unit.tag) or bot.sample_due(
                f"hellion-{unit.tag}", bot.state.game_loop, 16
            ):
                bot.record(
                    "hellion_decision",
                    tag=int(unit.tag),
                    reason=reason,
                    position=json_point(unit.position),
                    health=float(unit.health),
                    own_cooldown=float(unit.weapon_cooldown),
                    target_tag=int(target.tag) if target else None,
                    target_position=json_point(target.position) if target else None,
                    estimated_line_overlap=int(overlap),
                    worker_distance=float(min(unit.distance_to(w) for w in workers))
                    if workers
                    else None,
                )
            self.last_reason[unit.tag] = reason
