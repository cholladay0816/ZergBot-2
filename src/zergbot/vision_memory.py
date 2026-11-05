"""Bounded assistance for a legally observed threat, separate from unknown damage."""

from dataclasses import dataclass

from sc2.position import Point2

from .vision_assist import air_path_safe


@dataclass(frozen=True)
class SeenThreat:
    tag: int
    position: Point2
    frame: int


class VisionMemory:
    def __init__(self):
        self.seen = None
        self.flyer_tag = None
        self.origin = None
        self.target = None
        self.started = None
        self.finished = False

    def observe(self, enemies, army, frame):
        visible = [
            e
            for e in enemies
            if e.is_visible
            and not e.is_flying
            and e.can_attack_ground
            and any(u.distance_to(e.position) <= 18 for u in army)
        ]
        current = next((e for e in visible if self.seen and e.tag == self.seen.tag), None)
        if current is None and (self.seen is None or frame - self.seen.frame > 112):
            current = min(visible, key=lambda e: (-e.ground_range, e.tag), default=None)
        if current is not None:
            self.seen = SeenThreat(int(current.tag), Point2(current.position), frame)

    def decide(self, flyers, enemies, army, frame, terrain_visible, in_bounds):
        enemies = [e for e in enemies if e.is_visible]
        if self.finished:
            return None, None, "memory_finished"
        flyer = next((u for u in flyers if u.tag == self.flyer_tag), None)
        if self.started is not None:
            if flyer is None:
                self.finished = True
                return None, None, "memory_flyer_lost"
            if flyer.health_percentage < 0.6 or not air_path_safe(
                flyer.position, flyer.position, enemies
            ):
                self.finished = True
                return flyer, self.origin, "memory_abort_visible_aa_or_damage"
            if not army or frame - self.started >= 448:
                self.finished = True
                return flyer, self.origin, "memory_timeout_or_army_lost"
            if terrain_visible(self.seen.position):
                if any(e.tag == self.seen.tag for e in enemies):
                    return flyer, flyer.position, "hold_sustained_vision"
                self.finished = True
                return flyer, self.origin, "observed_location_clear"
            if frame - self.seen.frame > 112:
                self.finished = True
                return flyer, self.origin, "memory_stale"
            if not air_path_safe(flyer.position, self.target, enemies):
                self.finished = True
                return flyer, self.origin, "memory_abort_unsafe_route"
            return flyer, self.target, "reacquire_observed_position"
        if self.seen is None or not army:
            return None, None, "no_observed_threat"
        if frame - self.seen.frame > 112:
            return None, None, "memory_stale"
        if terrain_visible(self.seen.position):
            return None, None, "terrain_already_visible"
        candidates = []
        for u in flyers:
            if u.health_percentage < 0.8:
                continue
            distance = max(2, min(9, u.sight_range - 2))
            target = self.seen.position.towards(u.position, distance)
            if in_bounds(target) and air_path_safe(u.position, target, enemies):
                candidates.append((u, target))
        if not candidates:
            return None, None, "no_safe_memory_flyer"
        flyer, target = min(
            candidates, key=lambda pair: (pair[0].distance_to(pair[1]), pair[0].tag)
        )
        self.flyer_tag, self.origin, self.target = flyer.tag, flyer.position, target
        self.started = frame
        return flyer, target, "retain_observed_threat_vision"
