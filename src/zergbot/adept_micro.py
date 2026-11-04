"""Single-owned-caster shade experiments; attacker state is evaluator-only."""

from sc2.ids.ability_id import AbilityId as A

from .harass_micro import json_point


class AdeptHarass:
    def __init__(self, mode):
        self.mode = mode
        self.attempted = False
        self.active = None
        self.previous_position = None

    def event(self, bot, stage, **fields):
        bot.record("adept_phase", stage=stage, mode=self.mode, **fields)

    async def step(self, bot, adepts, shades, workers, queens, home):
        frame = int(bot.state.game_loop)
        if not adepts:
            if self.active:
                self.event(bot, "caster_lost", cast_frame=self.active["cast_frame"])
                self.active = None
            return
        adept = adepts[0]  # This harness deliberately has exactly one owned caster.
        workers = [u for u in workers if u.is_visible]
        queens = [u for u in queens if u.is_visible]
        queried = [adept] + list(shades)
        abilities = await bot.get_available_abilities(queried)
        available = {u.tag: set(a) for u, a in zip(queried, abilities, strict=True)}
        pocket = bot.mineral_field.closer_than(12, home)
        destination = (
            min(workers, key=adept.distance_to).position
            if workers
            else pocket.center
            if pocket
            else home
        )
        used = set()
        if self.active and not shades and self.active.get("shade_seen_frame") is not None:
            jump = (
                adept.distance_to(self.previous_position)
                if self.previous_position is not None
                else 0
            )
            last_shade = self.active["shade_position"]
            transferred = jump > 3 and adept.distance_to(last_shade) < 3
            stage = (
                "transfer_observed"
                if transferred
                else "cancel_no_transfer"
                if self.active.get("cancel_frame") is not None
                else "shade_disappeared_unconfirmed"
            )
            self.event(
                bot,
                stage,
                tag=int(adept.tag),
                position=json_point(adept.position),
                previous_position=json_point(self.previous_position),
                target_position=json_point(last_shade),
                cast_frame=self.active["cast_frame"],
                shade_seen_frame=self.active["shade_seen_frame"],
                elapsed_frames=frame - self.active["shade_seen_frame"],
                jump_distance=float(jump),
                cancel_frame=self.active.get("cancel_frame"),
            )
            bot.counts["adept_" + stage] += 1
            self.active = None
        if self.active and shades:
            shade = shades[0]
            if self.active.get("shade_seen_frame") is None:
                self.active["shade_seen_frame"] = frame
                self.event(
                    bot,
                    "shade_observed",
                    tag=int(shade.tag),
                    shade_tag=int(shade.tag),
                    position=json_point(shade.position),
                    cast_frame=self.active["cast_frame"],
                    association="single_owned_caster",
                )
                bot.counts["adept_shades_observed"] += 1
            self.active["shade_position"] = shade.position
            age = frame - self.active["shade_seen_frame"]
            if self.mode == "cancel" and age >= 112 and self.active.get("cancel_frame") is None:
                owner, ability = (
                    (adept, A.CANCEL_ADEPTPHASESHIFT)
                    if A.CANCEL_ADEPTPHASESHIFT in available[adept.tag]
                    else (shade, A.CANCEL_ADEPTSHADEPHASESHIFT)
                )
                if ability in available[owner.tag]:
                    owner(ability)
                    used.add(owner.tag)
                    self.active["cancel_frame"] = frame
                    self.event(
                        bot,
                        "cancel_attempt",
                        tag=int(owner.tag),
                        shade_tag=int(shade.tag),
                        ability=ability.name,
                        elapsed_frames=age,
                        cast_frame=self.active["cast_frame"],
                    )
                    bot.counts["adept_cancel_attempts"] += 1
            if self.active.get("cancel_frame") is None:
                shade.move(destination)
            # Once a cancel is submitted, no competing shade movement is issued.
        if (
            self.active
            and not shades
            and self.active.get("shade_seen_frame") is None
            and frame - self.active["cast_frame"] > 64
        ):
            self.event(
                bot, "cast_unconfirmed", tag=int(adept.tag), cast_frame=self.active["cast_frame"]
            )
            self.active = None
        if not self.attempted and A.ADEPTPHASESHIFT_ADEPTPHASESHIFT in available[adept.tag]:
            adept(A.ADEPTPHASESHIFT_ADEPTPHASESHIFT, destination)
            used.add(adept.tag)
            self.attempted = True
            self.active = {"cast_frame": frame}
            self.event(
                bot,
                "cast_attempt",
                tag=int(adept.tag),
                target_position=json_point(destination),
                ability=A.ADEPTPHASESHIFT_ADEPTPHASESHIFT.name,
                cast_frame=frame,
            )
            bot.counts["adept_cast_attempts"] += 1
        reason = "ability_command" if adept.tag in used else "approach"
        target = None
        if adept.tag not in used:
            queen = min(queens, key=adept.distance_to) if queens else None
            nearby = [w for w in workers if adept.target_in_range(w)]
            if adept.health_percentage < 0.3:
                adept.move(home.towards(bot.game_info.map_center, 20))
                reason = "retreat_low_health"
            elif self.active:
                adept.move(home.towards(bot.game_info.map_center, 13))
                reason = "hold_original_during_shade"
            elif adept.weapon_cooldown > 0 and queen is not None and adept.distance_to(queen) < 7:
                point = (
                    adept.position.towards(queen.position, -2)
                    if adept.distance_to(queen) > 0.01
                    else home
                )
                if bot.in_pathing_grid(point):
                    adept.move(point)
                    reason = "kite_visible_queen"
            elif nearby:
                target = min(nearby, key=lambda w: w.health + w.shield)
                adept.attack(target)
                reason = "attack_low_worker"
            elif workers:
                target = min(workers, key=adept.distance_to)
                adept.attack(target)
            else:
                adept.move(destination)
        if bot.sample_due("adept", frame, 16) or reason == "ability_command":
            bot.record(
                "adept_decision",
                tag=int(adept.tag),
                reason=reason,
                position=json_point(adept.position),
                health=float(adept.health),
                shield=float(adept.shield),
                own_cooldown=float(adept.weapon_cooldown),
                target_tag=int(target.tag) if target else None,
            )
        self.previous_position = adept.position
