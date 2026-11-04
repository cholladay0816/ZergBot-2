"""Experimental visible-shade posture; no prediction of commit/cancel intent."""

from .harass_micro import json_point


def guard_point(queen, protected, shades, threats, pathable):
    if queen.health_percentage < 0.3 or not shades:
        return None
    # Existing combat policy owns immediate threats, including the original Adept.
    if any(t.distance_to(protected) < 9 or t.distance_to(queen) < 7 for t in threats):
        return None
    nearby = [s for s in shades if s.distance_to(protected) < 8]
    if not nearby:
        return None
    shade = min(nearby, key=lambda s: s.distance_to(protected))
    distance = protected.distance_to(shade.position)
    target = protected.towards(shade.position, min(2, distance)) if distance else protected
    return target if pathable(target) else None


def guard_queen(bot, queen, protected, shades, threats):
    target = guard_point(queen, protected, shades, threats, bot.in_pathing_grid)
    if target is None:
        return False
    moved = queen.distance_to(target) > 0.75
    if moved:
        queen.move(target)
    if bot.sample_due("shade_guard", bot.state.game_loop, 8):
        bot.record(
            "adept_guard",
            tag=int(queen.tag),
            target_position=json_point(target),
            moved=bool(moved),
            scope="visible_shade_warning_only",
        )
    return True
