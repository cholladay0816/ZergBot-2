"""Terrain-guided vision assistance triggered by own unexplained damage.

No setup position, hidden enemy, enemy cooldown or replay input is accepted.
"""

import math

from sc2.position import Point2

from .threat_inference import DamageEvidence, TerrainCell, infer_region


def terrain_candidates(origin, height, in_bounds):
    points = []
    level = height(origin)
    for radius in (4, 7, 10):
        for i in range(16):
            point = origin + Point2(
                (math.cos(i * math.pi / 8) * radius, math.sin(i * math.pi / 8) * radius)
            )
            if in_bounds(point) and height(point) > level + 4:
                points.append(point)
    return points


def air_path_safe(start, end, enemies):
    for enemy in enemies:
        if not enemy.is_visible or not enemy.can_attack_air:
            continue
        reach = enemy.air_range + enemy.radius + 3
        for i in range(9):
            point = start + (end - start) * (i / 8)
            if point.distance_to(enemy.position) < reach:
                return False
    return True


class VisionAssist:
    def __init__(self):
        self.damage_position = None
        self.damage_frame = -10000
        self.flyer_tag = None
        self.origin = None
        self.target = None
        self.started = None
        self.finished = False
        self.region = None

    def observe_damage(self, position, frame, height=None, visible=None, in_bounds=None):
        if self.started is not None or self.finished or frame == self.damage_frame:
            return
        self.damage_position, self.damage_frame = Point2(position), frame
        if height is not None and visible is not None and in_bounds is not None:
            cells = []
            for dx in range(-14, 15, 2):
                for dy in range(-14, 15, 2):
                    point = self.damage_position + Point2((dx, dy))
                    if in_bounds(point):
                        cells.append(TerrainCell(tuple(point), height(point), bool(visible(point))))
            self.region = infer_region(DamageEvidence(tuple(position), frame), cells)

    def decide(self, flyers, visible_enemies, frame, height, in_bounds):
        enemies = [e for e in visible_enemies if e.is_visible]
        combat_visible = any(
            e.can_attack_ground
            and (self.damage_position is None or e.position.distance_to(self.damage_position) <= 18)
            for e in enemies
        )
        flyer = next((u for u in flyers if u.tag == self.flyer_tag), None)
        if self.started is not None:
            if flyer is None:
                self.finished = True
                return None, None, "flyer_lost"
            if flyer.health_percentage < 0.6 or not air_path_safe(
                flyer.position, flyer.position, enemies
            ):
                self.finished = True
                return flyer, self.origin, "abort_visible_aa_or_damage"
            if self.finished:
                return None, None, "finished"
            if combat_visible:
                return flyer, flyer.position, "vision_obtained"
            if frame - self.started >= 224:
                self.finished = True
                return flyer, self.origin, "timeout"
            if not air_path_safe(flyer.position, self.target, enemies):
                self.finished = True
                return flyer, self.origin, "abort_unsafe_route"
            return flyer, self.target, "seek_high_ground_hypothesis"
        if self.finished or combat_visible or self.damage_position is None:
            return None, None, "no_unexplained_damage"
        if frame - self.damage_frame > 112:
            return None, None, "stale_damage"
        eligible = [u for u in flyers if u.health_percentage >= 0.8]
        if not eligible:
            return None, None, "no_healthy_flyer"
        if self.region is not None:
            candidates = [Point2(c.position) for c in self.region.cells]
            cell_by_point = {Point2(c.position): c for c in self.region.cells}
        else:
            candidates = terrain_candidates(self.damage_position, height, in_bounds)
            cell_by_point = {}
        level = height(self.damage_position)

        def preference(point):
            cell = cell_by_point.get(point)
            return (bool(cell and cell.visible), height(point) <= level + 4)

        pairs = [
            (u, p) for u in eligible for p in candidates if air_path_safe(u.position, p, enemies)
        ]
        if not pairs:
            return None, None, "no_safe_terrain_candidate"
        flyer, target = min(
            pairs,
            key=lambda pair: (
                preference(pair[1]),
                pair[0].distance_to(pair[1]) + 0.2 * pair[1].distance_to(self.damage_position),
                pair[0].tag,
                pair[1].x,
                pair[1].y,
            ),
        )
        self.flyer_tag, self.origin = flyer.tag, flyer.position
        self.target, self.started = target, frame
        return flyer, target, "seek_high_ground_hypothesis"
