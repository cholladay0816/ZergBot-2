"""Persistent inject roles; one action per queen, shared ability-query results."""

from sc2.ids.ability_id import AbilityId as A
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId as U


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

    def event(self, bot, queen, action, role):
        recorder = bot.telemetry.recorder if bot.telemetry else None
        if recorder and recorder.config.enabled:
            if action in {"inject", "defend", "retreat", "creep"}:
                recorder.command_counts[
                    "INJECT" if action == "inject" else "QUEEN_" + action.upper()
                ] += 1
            decision = (action, role)
            if self.last_decisions.get(queen.tag) != decision:
                recorder.record(
                    "queen_decision",
                    bot.state.game_loop,
                    tag=queen.tag,
                    role=role,
                    action=action,
                    scope="own_observed",
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
            threats = bot.enemy_units.filter(
                lambda e, base=base: e.can_attack_ground and e.distance_to(base) < 15
            )
            direct = threats.closer_than(7, queen)
            # Dedicated inject queens respond locally; extras intercept base threats.
            defending = bool(threats) and (role != "inject" or not extras)
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
            if action == "retreat":
                enemy = direct.closest_to(queen)
                queen.move(queen.position.towards(enemy.position, -5))
            elif action == "defend":
                enemy = threats.closest_to(queen)
                queen.attack(enemy)
            elif action == "inject":
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
                    queen(A.BUILD_CREEPTUMOR_QUEEN, place)
                else:
                    action = "placement_unavailable"
            elif action == "rally" and queen.is_idle and queen.distance_to(base) > 10:
                queen.move(base.position.towards(bot.game_info.map_center, 5))
            self.event(bot, queen, action, role)
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
