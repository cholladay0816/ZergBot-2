"""Experimental visible-tank spread phase with a hard engagement deadline."""

from sc2.position import Point2


def split_waypoint(position, tank, home, slot, elapsed_frames, pathable):
    if elapsed_frames >= 90 or position.distance_to(tank) <= 4:
        return None
    direction = home - tank
    if direction.length < 0.01:
        return None
    forward = direction.normalized
    lateral = Point2((-forward.y, forward.x))
    lane, row = slot % 8, slot // 8
    point = tank + forward * (6 + 2.5 * row) + lateral * ((lane - 3.5) * 2.5)
    if not pathable(point) or position.distance_to(point) <= 1:
        return None
    return point
