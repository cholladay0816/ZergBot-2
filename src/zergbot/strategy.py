"""Army objectives with a bounded squad for small worker incursions."""

from math import dist

from .agents import Action, Intent, Observation
from .config import BotConfig


class ArmyStrategy:
    def __init__(self):
        self.defenders: set[int] = set()
        self.attacking = False

    def orders(
        self,
        units: list[Observation],
        under_attack: bool,
        config: BotConfig,
        *,
        worker_target: tuple[float, float] | None = None,
        support_strength: int = 0,
        allow_offense: bool = True,
        positions: dict[int, tuple[float, float]] | None = None,
    ) -> list[Intent]:
        healthy = [u for u in units if not u.burrowed and u.health >= config.emerge_health]
        # Keep eligible nearby defenders stable instead of rotating every frame.
        # Larger or non-worker incursions still request the full army.
        positions = positions or {}
        eligible = {
            u.tag
            for u in healthy
            if worker_target is not None
            and u.tag in positions
            and dist(positions[u.tag], worker_target) <= 35
        }
        if under_attack or worker_target is None or config.worker_defenders == 0:
            self.defenders.clear()
        else:
            self.defenders.intersection_update(eligible)
            available = sorted(
                eligible - self.defenders,
                key=lambda tag: (dist(positions[tag], worker_target), tag),
            )
            self.defenders.update(
                available[: max(0, config.worker_defenders - len(self.defenders))]
            )
        # One wounded/burrowing member must not recall an otherwise viable army.
        strength = len(healthy) + max(0, support_strength)
        if self.attacking:
            self.attacking = strength > config.regroup_roaches
        elif allow_offense and strength >= config.attack_roaches:
            self.attacking = True
        attack = under_attack or self.attacking
        return [
            Intent(u.tag, Action.ATTACK, 10, "worker_defense", worker_target)
            if u.tag in self.defenders
            else Intent(
                u.tag,
                Action.ATTACK if attack else Action.RETREAT,
                10,
                "defend" if under_attack else "army_objective",
            )
            for u in units
        ]
