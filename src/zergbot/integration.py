"""All per-unit SC2 translation and dispatch live at this boundary."""

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2

from .agents import Action, CommandArbiter, Observation

ROACH_TYPES = {UnitTypeId.ROACH, UnitTypeId.ROACHBURROWED}


class SC2UnitGateway:
    def __init__(self, bot: BotAI) -> None:
        self.bot = bot
        self.units = {}

    async def observe(self) -> list[Observation]:
        roaches = list(self.bot.units.of_type(ROACH_TYPES))
        self.units = {unit.tag: unit for unit in roaches}
        if not roaches:
            return []
        # Exactly one batched query; never infer one roach's abilities from another.
        abilities = await self.bot.get_available_abilities(roaches)
        researched = UpgradeId.BURROW in self.bot.state.upgrades
        return [
            Observation(
                unit.tag,
                unit.health / unit.health_max if unit.health_max > 0 else 0.0,
                unit.is_burrowed,
                AbilityId.BURROWDOWN_ROACH in available,
                AbilityId.BURROWUP_ROACH in available,
                researched,
            )
            for unit, available in zip(roaches, abilities, strict=True)
        ]

    def dispatch(self, arbiter: CommandArbiter, target: Point2, retreat: Point2) -> None:
        for tag, intent in arbiter.commands.items():
            unit = self.units.get(tag)
            if unit is None:
                continue
            # Current BurnySC2 unit calls enqueue orders directly; do not call bot.do again.
            if intent.action is Action.BURROW:
                unit(AbilityId.BURROWDOWN_ROACH)
            elif intent.action is Action.EMERGE:
                unit(AbilityId.BURROWUP_ROACH)
            elif intent.action is Action.ATTACK and not unit.is_burrowed:
                unit.attack(target)
            elif intent.action is Action.RETREAT and not unit.is_burrowed:
                unit.move(retreat)
            # WAIT sends no order and deliberately suppresses lower priority commands.
