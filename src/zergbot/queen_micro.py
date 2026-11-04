"""Visible grenade avoidance and own-cooldown positioning; no enemy cooldown access."""

from sc2.position import Point2


def grenade_escape(position, unit_radius, effects, pathable):
    charges = [
        p
        for effect in effects
        if effect.id == "KD8CHARGE" and effect.is_enemy
        for p in effect.positions
        if position.distance_to(p) <= effect.radius + unit_radius + 0.75
    ]
    if not charges:
        return None
    charge = min(charges, key=position.distance_to)
    vector = position - charge
    if vector.length < 0.01:
        vector = Point2((1, 0))
    away = position + vector.normalized * 4
    options = [
        away,
        position + Point2((0, 4)),
        position + Point2((0, -4)),
        position + Point2((4, 0)),
        position + Point2((-4, 0)),
    ]
    valid = [p for p in options if pathable(p)]
    return max(valid, key=lambda p: min(p.distance_to(c) for c in charges)) if valid else None


def defend_motion(
    position, base, enemy_position, cooldown, attack_range, radii, pathable, protected=None
):
    distance = position.distance_to(enemy_position)
    # Keep the queen in a protective base envelope; do not chase a faster Reaper away.
    if position.distance_to(base) > 12 and enemy_position.distance_to(base) > 15:
        return base
    if protected is not None and cooldown > 0:
        # Occupy the approach to the worker pocket between shots, instead of
        # conceding it by blindly backing away from a faster attacker.
        intercept = (
            protected.towards(enemy_position, 3)
            if protected.distance_to(enemy_position) > 0.01
            else protected
        )
        if position.distance_to(intercept) > 1:
            step = position.towards(intercept, min(1.5, position.distance_to(intercept)))
            if step.distance_to(base) <= 12 and pathable(step):
                return step
        return None
    if cooldown > 0 and distance <= attack_range + radii + 1:
        point = (
            position.towards(enemy_position, -1.5)
            if distance > 0.01
            else position + Point2((1.5, 0))
        )
        if point.distance_to(base) <= 12 and pathable(point):
            return point
    return None


def recovery_active(previous, health_fraction, visible_threat):
    return health_fraction < 0.6 if previous else health_fraction < 0.3 and visible_threat


def recovery_motion(position, protected, base, threats, pathable):
    """Use visible threat positions/ranges; never infer enemy weapon readiness."""
    import math

    points = [position, protected, base]
    points += [
        position
        + Point2((math.cos(i * math.pi / 4) * distance, math.sin(i * math.pi / 4) * distance))
        for distance in (3, 6)
        for i in range(8)
    ]
    valid = [
        p
        for p in points
        if pathable(p)
        and (
            position.distance_to(p) < 0.01
            or pathable(position.towards(p, min(1, position.distance_to(p))))
        )
    ]
    if not valid:
        return position  # Hold rather than falling through to an attack command.

    def clearance(point):
        return min((point.distance_to(enemy) - reach for enemy, reach in threats), default=100)

    safe = [p for p in valid if clearance(p) >= 1.5]
    return min(safe, key=lambda p: p.distance_to(protected)) if safe else max(valid, key=clearance)
