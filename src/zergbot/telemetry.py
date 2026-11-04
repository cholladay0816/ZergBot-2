"""Translate only API-provided evidence; enemy unavailable fields remain null."""

import time
from collections import Counter

from sc2.ids.unit_typeid import UnitTypeId as U

from .agents import Action


def field(proto, name):
    return getattr(proto, name) if proto.HasField(name) else None


def describe_unit(bot, unit, own):
    proto = unit._proto
    return {
        "tag": unit.tag,
        "type": unit.type_id.name,
        "scope": "own" if own else "currently_visible_enemy",
        "position": [round(unit.position.x, 3), round(unit.position.y, 3)],
        "terrain_height": bot.get_terrain_height(unit.position),
        "health": field(proto, "health"),
        "shield": field(proto, "shield"),
        "energy": field(proto, "energy"),
        "flying": unit.is_flying,
        "cloak_raw": field(proto, "cloak"),
        "burrowed": field(proto, "is_burrowed"),
        "detector": unit.is_detector,
        "detect_range": field(proto, "detect_range"),
        "buff_ids": list(proto.buff_ids)[:16],
        "ground_range_base": unit.ground_range,
        "air_range_base": unit.air_range,
        "weapon_cooldown": field(proto, "weapon_cooldown") if own else None,
        "engaged_target_tag": field(proto, "engaged_target_tag") if own else None,
        "orders": [
            {
                "ability_id": o.ability_id,
                "target_tag": field(o, "target_unit_tag"),
                "target_position": [o.target_world_space_pos.x, o.target_world_space_pos.y]
                if o.HasField("target_world_space_pos")
                else None,
            }
            for o in proto.orders[:4]
        ]
        if own
        else None,
    }


def describe_effects(bot):
    result = []
    for effect in list(bot.state.effects)[:32]:
        effect_id = effect.id
        result.append(
            {
                "effect": effect_id.name if hasattr(effect_id, "name") else str(effect_id),
                "owner": effect.owner,
                "radius": effect.radius,
                "positions": [[p.x, p.y] for p in list(effect.positions)[:8]],
                "caster_tag": None,
                "scope": "API_visible_effect",
            }
        )
    return result


class TelemetryAdapter:
    def __init__(self, recorder):
        self.recorder = recorder
        self.last_decisions = {}
        self.own_tags = {}
        self.enemy_tags = {}
        self.damage_frame = -1
        self.damage_count = 0

    def sample(self, bot):
        r = self.recorder
        if not r.config.enabled:
            return
        start = time.perf_counter()
        frame = bot.state.game_loop
        r.max_frame = max(r.max_frame, frame)
        own = list(bot.units) + list(bot.structures)
        visible = [u for u in list(bot.enemy_units) + list(bot.enemy_structures) if u.is_visible]
        # Active roster only: memory does not grow with dead or disappeared units.
        self.own_tags = {u.tag: u.type_id.name for u in own}
        self.enemy_tags = {u.tag: u.type_id.name for u in visible}
        for error in bot.state.action_errors[:32]:
            r.record(
                "action_error",
                frame,
                tag=int(error.unit_tag),
                ability_id=int(error.ability_id),
                result=int(error.result),
            )
        if r.due(frame):
            r.last_sample = frame
            r.snapshot_calls += 1
            cap = r.config.max_detail_units
            roaches = [u for u in own if u.type_id in {U.ROACH, U.ROACHBURROWED}]
            # Positions at sampled times indicate proximity, not exact engagement starts.
            engagements = [
                {
                    "roach": u.tag,
                    "visible_enemy_tags": [v.tag for v in visible if u.distance_to(v) <= 10][:16],
                }
                for u in roaches[:16]
            ]
            r.record(
                "snapshot",
                frame,
                own=[describe_unit(bot, u, True) for u in own[:cap]],
                visible_enemy=[describe_unit(bot, u, False) for u in visible[:cap]],
                own_counts=dict(Counter(u.type_id.name for u in own)),
                visible_enemy_counts=dict(Counter(u.type_id.name for u in visible)),
                effects=describe_effects(bot),
                economy={
                    "minerals": bot.minerals,
                    "vespene": bot.vespene,
                    "supply_used": bot.supply_used,
                    "supply_cap": bot.supply_cap,
                    "supply_left": bot.supply_left,
                    "workers": bot.workers.amount,
                    "idle_workers": bot.workers.idle.amount,
                    "larvae": bot.larva.amount,
                    "bases": bot.townhalls.amount,
                },
                upgrades=sorted(u.name for u in bot.state.upgrades),
                pending={
                    u.name: bot.already_pending(u)
                    for u in [U.DRONE, U.OVERLORD, U.ROACH, U.HATCHERY, U.ROACHWARREN]
                },
                detail_omitted={
                    "own": max(0, len(own) - cap),
                    "visible_enemy": max(0, len(visible) - cap),
                    "effects": max(0, len(bot.state.effects) - 32),
                },
                engagements=engagements,
            )
            r.checkpoint()
        r.overhead_seconds += time.perf_counter() - start

    def decisions(self, observations, registry, arbiter, frame):
        if not self.recorder.config.enabled:
            return
        start = time.perf_counter()
        active = {o.tag for o in observations}
        self.last_decisions = {k: v for k, v in self.last_decisions.items() if k in active}
        for obs in observations:
            intent = arbiter.commands.get(obs.tag)
            if intent is None:
                continue
            agent = registry.agents[obs.tag]
            signature = (
                intent.action,
                intent.reason,
                obs.burrowed,
                obs.can_burrow,
                obs.can_emerge,
                agent.recovering,
                agent.pending_morph,
                obs.transition,
            )
            changed = self.last_decisions.get(obs.tag) != signature
            if changed:
                self.last_decisions[obs.tag] = signature
                self.recorder.record(
                    "decision",
                    frame,
                    tag=obs.tag,
                    action=intent.action.name,
                    reason=intent.reason,
                    target=intent.target,
                    health_fraction=obs.health,
                    burrowed=obs.burrowed,
                    can_burrow=obs.can_burrow,
                    can_emerge=obs.can_emerge,
                    researched=obs.burrow_researched,
                    recovering=agent.recovering,
                    pending_morph=agent.pending_morph.name if agent.pending_morph else None,
                    observed_order=obs.transition.name if obs.transition else None,
                )
            if intent.action is not Action.WAIT:
                self.recorder.command_counts[intent.action.name] += 1
            if intent.action is not Action.WAIT and (
                changed or intent.action in {Action.BURROW, Action.EMERGE}
            ):
                self.recorder.record(
                    "command_attempt",
                    frame,
                    tag=obs.tag,
                    action=intent.action.name,
                    reason=intent.reason,
                    target=intent.target,
                )
        self.recorder.overhead_seconds += time.perf_counter() - start

    def damage(self, bot, unit, amount):
        r = self.recorder
        if not r.config.enabled:
            return
        frame = bot.state.game_loop
        if frame != self.damage_frame:
            self.damage_frame, self.damage_count = frame, 0
        self.damage_count += 1
        if self.damage_count > r.config.max_damage_per_frame:
            r.dropped += 1
            return
        start = time.perf_counter()
        visible = [u for u in list(bot.enemy_units) + list(bot.enemy_structures) if u.is_visible]
        candidates = []
        for enemy in visible[: r.config.max_detail_units]:
            attack_range = enemy.air_range if unit.is_flying else enemy.ground_range
            distance = unit.distance_to(enemy)
            can_attack = enemy.can_attack_air if unit.is_flying else enemy.can_attack_ground
            if can_attack and distance <= attack_range + unit.radius + enemy.radius + 3:
                candidates.append(
                    {
                        "tag": enemy.tag,
                        "type": enemy.type_id.name,
                        "distance_now": distance,
                        "base_range": attack_range,
                        "terrain_delta_now": bot.get_terrain_height(enemy.position)
                        - bot.get_terrain_height(unit.position),
                        "cloak_raw": field(enemy._proto, "cloak"),
                        "confidence": "candidate_only_current_position_3_unit_margin",
                    }
                )
        candidates.sort(key=lambda c: c["distance_now"])
        r.record(
            "damage",
            frame,
            victim=describe_unit(bot, unit, True),
            hp_shield_loss=amount,
            candidate_attackers=candidates[:8],
            effects=describe_effects(bot),
            attribution="unknown; HP/shield delta does not identify caster or cause",
            candidate_scan_omitted=max(0, len(visible) - r.config.max_detail_units),
        )
        r.overhead_seconds += time.perf_counter() - start

    def destroyed(self, frame, tag):
        scope = (
            "own"
            if tag in self.own_tags
            else "enemy_observed_death"
            if tag in self.enemy_tags
            else "unknown"
        )
        unit_type = self.own_tags.pop(tag, None) or self.enemy_tags.pop(tag, None)
        self.recorder.record("destroyed", frame, tag=tag, unit_type=unit_type, scope=scope)
