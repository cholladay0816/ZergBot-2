"""Army-level objectives. Unit survival always has higher command priority."""

from .agents import Action, Intent, Observation
from .config import BotConfig


class ArmyStrategy:
    def orders(
        self, units: list[Observation], under_attack: bool, config: BotConfig
    ) -> list[Intent]:
        # Recovering units do not count toward the attack threshold.
        healthy = sum(not u.burrowed and u.health >= config.emerge_health for u in units)
        action = (
            Action.ATTACK if under_attack or healthy >= config.attack_roaches else Action.RETREAT
        )
        return [
            Intent(u.tag, action, 10, "defend" if under_attack else "army_objective") for u in units
        ]
