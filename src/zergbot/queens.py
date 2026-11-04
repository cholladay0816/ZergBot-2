"""Persistent inject roles; one action per queen, shared ability-query results."""

from sc2.ids.ability_id import AbilityId as A
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId as U

from .queen_micro import defend_motion, grenade_escape


def queen_priority(
    *, critical, direct_threat, defending, casting, inject_due, can_inject, role, can_creep
):
    if critical and direct_threat:
        return "retreat"
    if direct_threat or defending:
        return "defend"
    if casting:
        return "wait"
    if role == "inject":
        return "inject" if inject_due and can_inject else "wait"
    return "creep" if can_creep else "rally"


def ground_threat(unit):
    # Some special-attack units lack weapon-table entries in the current API.
    # Treat their type as a possible threat; do not infer cooldown or a current target.
    return unit.can_attack_ground or unit.type_id in {U.VOIDRAY, U.CARRIER}


def base_threat(unit):
    # Air-only attackers threaten overlords and can require base defense too.
    return unit.can_attack_air or ground_threat(unit)


class QueenManager:
    def __init__(self, config):
        self.config = config
        self.injectors = {}  # base tag -> queen tag; stable until either disappears
        self.next_creep_frame = 0
        self.last_decisions = {}

    def assign(self, bases, queens):
        live_bases = {b.tag for b in bases}
        live_queens = {q.tag for q in queens}
        self.injectors = {
            b: q for b, q in self.injectors.items() if b in live_bases and q in live_queens
        }
        free = [q for q in queens if q.tag not in self.injectors.values()]
        for base in bases:
            if base.tag not in self.injectors and free:
                queen = min(free, key=lambda q: (q.distance_to(base), q.tag))
                self.injectors[base.tag] = queen.tag
                free.remove(queen)
        self.last_decisions = {k: v for k, v in self.last_decisions.items() if k in live_queens}

    def event(self, bot, queen, action, role, target=None):
        recorder = bot.telemetry.recorder if bot.telemetry else None
        if recorder and recorder.config.enabled:
            if action in {"inject", "defend", "retreat", "creep", "dodge", "kite"}:
                recorder.command_counts[
                    "INJECT" if action == "inject" else "QUEEN_" + action.upper()
                ] += 1
            target_tag = getattr(target, "tag", None)
            target_type = getattr(target, "type_id", None)
            position = getattr(target, "position", target)
            target_position = list(position) if position is not None else None
            decision = (
                action,
                role,
                target_tag,
                tuple(target_position) if target_tag is None and target_position else None,
            )
            if self.last_decisions.get(queen.tag) != decision:
                recorder.record(
                    "queen_decision",
                    bot.state.game_loop,
                    tag=queen.tag,
                    role=role,
                    action=action,
                    scope="own_observed",
                    target_tag=target_tag,
                    target_position=target_position,
                    target_type=target_type.name if isinstance(target_type, U) else None,
                )
                self.last_decisions[queen.tag] = decision

    async def step(self, bot, abilities):
        bases, queens = list(bot.townhalls.ready), list(bot.units(U.QUEEN).ready)
        self.assign(bases, queens)
        if not bases:
            return
        by_tag = {b.tag: b for b in bases}
        roles = {q: by_tag[b] for b, q in self.injectors.items()}
        extras = [q for q in queens if q.tag not in roles]
        frame = bot.state.game_loop
        creep_budget = frame >= self.next_creep_frame
        for queen in queens:
            base = roles.get(queen.tag) or min(bases, key=queen.distance_to)
            role = "inject" if queen.tag in roles else "defense_creep"
            available = abilities.get(queen.tag, set())
            if self.config.queen_tactical_micro:
                escape = grenade_escape(
                    queen.position, queen.radius, bot.state.effects, bot.in_pathing_grid
                )
                if escape is not None:
                    queen.move(escape)
                    self.event(bot, queen, "dodge", role, escape)
                    continue
            armed = (bot.enemy_units | bot.enemy_structures).filter(base_threat)
            threats = armed.closer_than(15, base)
            direct = armed.closer_than(7, queen).filter(
                lambda enemy, queen=queen: (
                    enemy.can_attack_air if queen.is_flying else ground_threat(enemy)
                )
            )
            # Dedicated inject queens respond locally; extras intercept base threats.
            nearby_extras = [
                q for q in extras if q.health_percentage >= 0.3 and q.distance_to(base) < 20
            ]
            defending = bool(threats) and (role != "inject" or not nearby_extras)
            action = queen_priority(
                critical=queen.health_percentage < 0.3,
                direct_threat=bool(direct),
                defending=defending,
                casting=bool(queen.orders),
                inject_due=not base.has_buff(BuffId.QUEENSPAWNLARVATIMER),
                can_inject=A.EFFECT_INJECTLARVA in available,
                role=role,
                can_creep=creep_budget and A.BUILD_CREEPTUMOR_QUEEN in available,
            )
            target = None
            if action == "retreat":
                enemy = direct.closest_to(queen)
                target = queen.position.towards(enemy.position, -5)
                queen.move(target)
            elif action == "defend":
                enemy = (direct or threats).closest_to(queen)
                target = enemy
                motion = None
                if self.config.queen_tactical_micro:
                    attack_range = queen.air_range if enemy.is_flying else queen.ground_range
                    motion = defend_motion(
                        queen.position,
                        base.position,
                        enemy.position,
                        queen.weapon_cooldown,
                        attack_range,
                        queen.radius + enemy.radius,
                        bot.in_pathing_grid,
                    )
                if motion is not None:
                    target, action = motion, "kite"
                    queen.move(motion)
                else:
                    queen.attack(enemy)
            elif action == "inject":
                target = base
                queen(A.EFFECT_INJECTLARVA, base)
            elif action == "creep":
                # At most one placement query/command per interval for the whole group.
                self.next_creep_frame = frame + self.config.creep_interval_frames
                creep_budget = False
                near = queen.position.towards(bot.game_info.map_center, 7)
                place = await bot.find_placement(
                    A.BUILD_CREEPTUMOR_QUEEN,
                    near,
                    max_distance=5,
                    placement_step=2,
                    random_alternative=False,
                )
                if place is not None and queen.distance_to(place) <= 10:
                    target = place
                    queen(A.BUILD_CREEPTUMOR_QUEEN, place)
                else:
                    action = "placement_unavailable"
            elif action == "rally" and queen.is_idle and queen.distance_to(base) > 10:
                queen.move(base.position.towards(bot.game_info.map_center, 5))
            self.event(bot, queen, action, role, target)
        if creep_budget:
            for tumor in bot.structures(U.CREEPTUMORBURROWED).ready:
                if A.BUILD_CREEPTUMOR_TUMOR not in abilities.get(tumor.tag, set()):
                    continue
                self.next_creep_frame = frame + self.config.creep_interval_frames
                near = tumor.position.towards(bot.game_info.map_center, 8)
                place = await bot.find_placement(
                    A.BUILD_CREEPTUMOR_TUMOR,
                    near,
                    max_distance=3,
                    placement_step=2,
                    random_alternative=False,
                )
                if place is not None and tumor.distance_to(place) <= 10:
                    tumor(A.BUILD_CREEPTUMOR_TUMOR, place)
                break
