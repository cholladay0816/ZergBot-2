"""All per-unit SC2 translation and dispatch live at this boundary."""

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit

from .agents import Action, CommandArbiter, Observation

ROACH_TYPES = {UnitTypeId.ROACH, UnitTypeId.ROACHBURROWED}


def observed_transition(unit: Unit) -> Action | None:
    # Only the active order, not queued future orders, describes a transition.
    orders = unit.orders
    if not orders:
        return None
    ids = {orders[0].ability.id, orders[0].ability.exact_id}
    if ids & {AbilityId.BURROWDOWN, AbilityId.BURROWDOWN_ROACH}:
        return Action.BURROW
    if ids & {AbilityId.BURROWUP, AbilityId.BURROWUP_ROACH}:
        return Action.EMERGE
    return None


def detection_danger(unit, enemies) -> bool:
    """Observed detection coverage plus a plausible nearby ground attack.

    Three units of weapon-range margin are a conservative policy, not proof of
    targeting or damage. Unknown/zero detection ranges do not establish coverage.
    Cloaked unseen observers, fog, scans and spells are not inferred here.
    """
    visible = [enemy for enemy in enemies if enemy.is_visible]
    covered = any(
        enemy.is_detector
        and enemy.detect_range > 0
        and enemy.distance_to(unit) <= enemy.detect_range + unit.radius
        for enemy in visible
    )
    return covered and any(
        enemy.can_attack_ground
        and enemy.distance_to(unit) <= enemy.ground_range + enemy.radius + unit.radius + 3
        for enemy in visible
    )


class SC2UnitGateway:
    def __init__(self, bot: BotAI) -> None:
        self.bot = bot
        self.units = {}
        self.abilities_by_tag = {}

    async def observe(self, extra_units=()) -> list[Observation]:
        roaches = list(self.bot.units.of_type(ROACH_TYPES))
        self.units = {unit.tag: unit for unit in roaches}
        queried = roaches + list(extra_units)
        if not queried:
            self.abilities_by_tag = {}
            return []
        # Exactly one batched query; never infer one roach's abilities from another.
        abilities = await self.bot.get_available_abilities(queried)
        self.abilities_by_tag = {u.tag: set(a) for u, a in zip(queried, abilities, strict=True)}
        researched = UpgradeId.BURROW in self.bot.state.upgrades
        avoid_detection = (
            getattr(getattr(self.bot, "config", None), "avoid_detected_burrow", False) is True
        )
        enemies = (
            list(self.bot.enemy_units) + list(self.bot.enemy_structures) if avoid_detection else []
        )
        return [
            Observation(
                unit.tag,
                unit.health / unit.health_max if unit.health_max > 0 else 0.0,
                unit.is_burrowed,
                AbilityId.BURROWDOWN_ROACH in available,
                AbilityId.BURROWUP_ROACH in available,
                researched,
                observed_transition(unit),
                detection_danger(unit, enemies) if avoid_detection else False,
            )
            for unit, available in zip(roaches, abilities[: len(roaches)], strict=True)
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
                unit.attack(Point2(intent.target) if intent.target is not None else target)
            elif (
                intent.action is Action.MOVE and not unit.is_burrowed and intent.target is not None
            ):
                unit.move(Point2(intent.target))
            elif intent.action is Action.RETREAT and not unit.is_burrowed:
                unit.move(retreat)
            # WAIT sends no order and deliberately suppresses lower priority commands.
