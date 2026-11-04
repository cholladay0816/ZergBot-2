"""Stable, visible-only army objectives across ready bases."""

from dataclasses import dataclass
from math import dist


@dataclass(frozen=True)
class Threat:
    tag: int
    position: tuple[float, float]
    worker: bool = False


@dataclass(frozen=True)
class DefenseObjective:
    base_tag: int
    target: tuple[float, float]
    worker_only: bool


class BaseDefense:
    def __init__(self):
        self.base_tag = None
        self.selected_frame = 0

    def select(self, bases, threats, frame, worker_defenders):
        """Keep a threatened base for 112 frames; never retain a vanished threat.

        Combat pressure outranks a small worker incursion immediately. After the
        hold, switch only for at least two additional threats; stable tag ties
        prevent input ordering from causing recall oscillation. Counts are a
        bounded heuristic, not an army-value estimate.
        """
        groups = {}
        for tag, position in bases.items():
            nearby = [t for t in threats if dist(t.position, position) < 25]
            if nearby:
                small = worker_defenders > 0 and len(nearby) <= 2 and all(t.worker for t in nearby)
                groups[tag] = (nearby, small)
        if not groups:
            self.base_tag = None
            return None
        best = min(groups, key=lambda tag: (groups[tag][1], -len(groups[tag][0]), tag))
        current = groups.get(self.base_tag)
        if current is not None:
            immediate = current[1] and not groups[best][1]
            materially_larger = len(groups[best][0]) >= len(current[0]) + 2
            if not immediate and (frame - self.selected_frame < 112 or not materially_larger):
                best = self.base_tag
        if best != self.base_tag:
            self.base_tag = best
            self.selected_frame = frame
        nearby, small = groups[best]
        target = min(nearby, key=lambda t: (dist(t.position, bases[best]), t.tag))
        return DefenseObjective(best, target.position, small)

    @staticmethod
    def retreat(bases, threats, fallback):
        """Do not redirect recovery toward the selected attacked base.

        Prefer a base with no observed threat inside the defense envelope, then
        the base farthest from visible pressure. Fog and path hazards remain
        unknown; this selects an endpoint, not a guaranteed safe route.
        """
        if not bases:
            return fallback

        def score(item):
            tag, position = item
            clearance = min((dist(position, t.position) for t in threats), default=1000)
            return (clearance < 25, -min(clearance, 25), dist(position, fallback), tag)

        return min(bases.items(), key=score)[1]


def defense_sample(objective, retreat, bases):
    return {
        "base_tag": int(objective.base_tag) if objective else None,
        "target": [float(v) for v in objective.target] if objective else None,
        "worker_only": bool(objective and objective.worker_only),
        "retreat": [float(v) for v in retreat],
        "ready_bases": len(bases),
        "scope": "currently_visible_ground_threats",
    }
