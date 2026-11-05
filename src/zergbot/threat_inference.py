"""Bounded observation-time regions, not invented attacker identities."""

from dataclasses import dataclass
from math import dist, isfinite


@dataclass(frozen=True)
class DamageEvidence:
    position: tuple[float, float]
    frame: int
    observation_delay: float = 4 / 22.4
    victim_speed_bound: float = 0
    source_confirmed: bool = False


@dataclass(frozen=True)
class SourceBounds:
    unit_type: str
    weapon_range: float
    radii_margin: float
    splash_radius: float
    projectile_delay: float
    movement_speed: float
    can_hide: bool = True


@dataclass(frozen=True)
class TerrainCell:
    position: tuple[float, float]
    height: float
    visible: bool
    detection_complete: bool = False
    visible_throughout_interval: bool = False
    attacker_absent_throughout_interval: bool = False


@dataclass(frozen=True)
class ThreatRegion:
    cells: tuple[TerrainCell, ...]
    source_type: str | None
    source_confirmed: bool
    radius: float
    exhaustive: bool
    assumptions: tuple[str, ...]


def infer_region(evidence, cells, source=None, search_radius=14):
    """A finite sampled region; source bounds must come from trustworthy evidence.

    Source confirmation is never inferred from damage amount. Without confirmed
    type, the radius is only a scout budget, not proof all attackers lie inside.
    Visibility removes cells only with interval coverage and hidden-unit safety.
    A grid cannot prove one exact location, even when one sampled cell remains.
    """
    values = [evidence.observation_delay, evidence.victim_speed_bound, search_radius]
    if source is not None:
        values += [
            source.weapon_range,
            source.radii_margin,
            source.splash_radius,
            source.projectile_delay,
            source.movement_speed,
        ]
    if any(not isfinite(v) or v < 0 for v in values):
        raise ValueError("Uncertainty bounds must be nonnegative")
    confirmed = evidence.source_confirmed and source is not None
    if confirmed:
        delay = evidence.observation_delay + source.projectile_delay
        radius = (
            source.weapon_range
            + source.radii_margin
            + source.splash_radius
            + (source.movement_speed + evidence.victim_speed_bound) * delay
        )
        assumptions = (
            "provided source/range/splash/movement bounds are valid",
            "sampled cells do not prove an exact location",
        )
    else:
        radius = search_radius
        assumptions = (
            "attacker type unknown; radius is a scouting budget only",
            "unseen high ground is a preference, not proof",
            "visible cells may contain hidden or previously firing attackers",
        )
    kept = []
    for cell in cells:
        if dist(cell.position, evidence.position) > radius:
            continue
        excluded = (
            confirmed
            and cell.visible
            and cell.visible_throughout_interval
            and cell.attacker_absent_throughout_interval
            and (not source.can_hide or cell.detection_complete)
        )
        if not excluded:
            kept.append(cell)
    return ThreatRegion(
        tuple(kept),
        source.unit_type if confirmed else None,
        bool(confirmed),
        radius,
        False,
        assumptions,
    )
