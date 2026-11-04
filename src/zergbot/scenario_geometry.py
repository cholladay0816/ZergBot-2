"""Pure geometry for isolated scenario setup and visible-motion estimates."""

import math

from sc2.position import Point2


def mineral_ingress(base, pocket, approach, pathable):
    direction = pocket - base
    if direction.length < 0.01:
        return None
    direction = direction.normalized
    side = Point2((-direction.y, direction.x))
    desired = pocket + direction * 6 + side * ((approach - 1) * 4)
    points = [desired] + [
        desired + Point2((math.cos(i * math.pi / 4) * radius, math.sin(i * math.pi / 4) * radius))
        for radius in (2, 4, 6)
        for i in range(8)
    ]
    valid = [
        p
        for p in points
        if pathable(p)
        and 4 <= p.distance_to(pocket) <= 12
        and (p.x - base.x) * direction.x + (p.y - base.y) * direction.y > 0
    ]
    return min(valid, key=lambda p: p.distance_to(desired)) if valid else None


def predict_visible_position(position, old_position, elapsed_frames):
    if old_position is None or elapsed_frames <= 0:
        return position
    velocity = (position - old_position) * (22.4 / elapsed_frames)
    return (
        position + velocity.normalized * min(2, velocity.length * 0.5)
        if velocity.length
        else position
    )


def grenade_score(point, workers, queens):
    # Estimated coverage of CURRENT visible positions, not future-hit knowledge.
    worker_count = sum(point.distance_to(p) <= 2 for p in workers)
    queen_count = sum(point.distance_to(p) <= 2 for p in queens)
    return 2 * worker_count + 3 * queen_count, worker_count, queen_count
