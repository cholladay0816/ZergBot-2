"""Experimental cooldown-only spacing against currently visible sieged tanks."""

import math

from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.position import Point2

from .agents import Action, Intent


class SiegeSpacing:
    def __init__(self):
        self.previous_cooldown = {}
        self.commit_until = {}
        self.moving_until = {}

    def orders(self, units, enemies, frame, pathable):
        live = {u.tag for u in units}
        for mapping in (self.previous_cooldown, self.commit_until, self.moving_until):
            for tag in set(mapping) - live:
                del mapping[tag]
        tanks = [e for e in enemies if e.is_visible and e.type_id == U.SIEGETANKSIEGED]
        result = []
        for unit in units:
            previous = self.previous_cooldown.get(unit.tag, 0)
            if unit.weapon_cooldown > previous + 1:
                # Conservative attack-animation guard, not a measured damage-point guarantee.
                self.commit_until[unit.tag] = frame + 8
            self.previous_cooldown[unit.tag] = unit.weapon_cooldown
            if unit.is_burrowed or unit.weapon_cooldown <= 0:
                self.moving_until.pop(unit.tag, None)
                continue
            threats = [
                t
                for t in tanks
                if unit.distance_to(t) <= t.ground_range + t.radius + unit.radius + 2
            ]
            if not threats or frame < self.commit_until.get(unit.tag, 0):
                continue
            if frame < self.moving_until.get(unit.tag, 0):
                result.append(Intent(int(unit.tag), Action.WAIT, 40, "siege_spacing_motion"))
                continue
            neighbors = sorted(
                [
                    u
                    for u in units
                    if u.tag != unit.tag and not u.is_burrowed and unit.distance_to(u) < 2.5
                ],
                key=unit.distance_to,
            )[:8]
            if not neighbors:
                continue
            before = min(unit.distance_to(u) for u in neighbors)
            candidates = []
            for i in range(8):
                angle = (i + int(unit.tag) % 8) * math.pi / 4
                point = unit.position + Point2((math.cos(angle) * 1.5, math.sin(angle) * 1.5))
                if not all(pathable(unit.position.towards(point, step)) for step in (0.5, 1, 1.5)):
                    continue
                if any(point.distance_to(t.position) < unit.distance_to(t) - 0.25 for t in threats):
                    continue
                separation = min(point.distance_to(u.position) for u in neighbors)
                if separation < before + 0.25:
                    continue
                score = separation - 0.15 * sum(
                    max(0, point.distance_to(t.position) - unit.distance_to(t)) for t in threats
                )
                candidates.append((score, point))
            if candidates:
                point = max(candidates, key=lambda item: item[0])[1]
                self.moving_until[unit.tag] = frame + 8
                result.append(
                    Intent(
                        int(unit.tag),
                        Action.MOVE,
                        40,
                        "visible_siege_spacing",
                        tuple(float(v) for v in point),
                    )
                )
        return result


def spacing_sample(units, tanks):
    distances = [u.distance_to(v) for i, u in enumerate(units) for v in units[i + 1 :]]
    return dict(
        army=[
            dict(
                tag=int(u.tag),
                position=[float(v) for v in u.position],
                health=float(u.health),
                own_cooldown=float(u.weapon_cooldown),
            )
            for u in units
        ],
        visible_tanks=[
            dict(tag=int(t.tag), position=[float(v) for v in t.position], health=float(t.health))
            for t in tanks
            if t.is_visible
        ],
        minimum_spacing=float(min(distances)) if distances else None,
    )
