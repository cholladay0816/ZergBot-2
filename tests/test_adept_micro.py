import asyncio
from collections import Counter
from types import MethodType, SimpleNamespace

import numpy as np
from sc2.ids.ability_id import AbilityId as A
from sc2.position import Point2

from zergbot.adept_micro import AdeptHarass
from zergbot.scenarios import MeasuredBot


class Actor:
    def __init__(self, tag, position):
        self.tag = np.int64(tag)
        self.position = Point2(tuple(np.float32(v) for v in position))
        self.health = np.float32(70)
        self.shield = np.float32(70)
        self.health_percentage = 1
        self.weapon_cooldown = np.float32(0)
        self.commands = []

    def __call__(self, ability, target=None):
        self.commands.append((ability, target))

    def move(self, target):
        self.commands.append(("move", target))

    def attack(self, target):
        self.commands.append(("attack", target))

    def distance_to(self, target):
        return self.position.distance_to(getattr(target, "position", target))

    def target_in_range(self, target):
        return self.distance_to(target) < 4


def setup(ready=True):
    class Minerals:
        center = Point2((5, 0))

        def closer_than(self, *args):
            return self

    bot = SimpleNamespace(
        events=[],
        counts=Counter(),
        next_samples={},
        state=SimpleNamespace(game_loop=0),
        mineral_field=Minerals(),
        game_info=SimpleNamespace(map_center=Point2((30, 30))),
        in_pathing_grid=lambda _: True,
    )
    bot.record = MethodType(MeasuredBot.record, bot)
    bot.sample_due = MethodType(MeasuredBot.sample_due, bot)

    async def abilities(units):
        return [
            [A.ADEPTPHASESHIFT_ADEPTPHASESHIFT, A.CANCEL_ADEPTPHASESHIFT]
            if u.tag == 1 and ready
            else [A.CANCEL_ADEPTSHADEPHASESHIFT]
            if u.tag == 2
            else []
            for u in units
        ]

    bot.get_available_abilities = abilities
    return bot, Actor(1, (-16, 0)), Actor(2, (-14, 0))


def test_commit_is_verified_from_own_relocation_after_real_shade_observation(json_roundtrip):
    async def run():
        bot, adept, shade = setup()
        policy = AdeptHarass("commit")
        await policy.step(bot, [adept], [], [], [], Point2((0, 0)))
        bot.state.game_loop = 4
        await policy.step(bot, [adept], [shade], [], [], Point2((0, 0)))
        bot.state.game_loop = 144
        shade.position = Point2((5, 0))
        await policy.step(bot, [adept], [shade], [], [], Point2((0, 0)))
        bot.state.game_loop = 160
        adept.position = Point2((5, 0))
        await policy.step(bot, [adept], [], [], [], Point2((0, 0)))
        events = json_roundtrip(bot.events)
        stages = [e["stage"] for e in events if e["kind"] == "adept_phase"]
        assert stages == ["cast_attempt", "shade_observed", "transfer_observed"]
        assert bot.counts["adept_transfer_observed"] == 1
        assert all(
            command[0] not in {A.CANCEL_ADEPTPHASESHIFT, A.CANCEL_ADEPTSHADEPHASESHIFT}
            for command in adept.commands
        )

    asyncio.run(run())


def test_cancel_uses_owned_available_ability_and_does_not_invent_transfer(json_roundtrip):
    async def run():
        bot, adept, shade = setup()
        policy = AdeptHarass("cancel")
        await policy.step(bot, [adept], [], [], [], Point2((0, 0)))
        bot.state.game_loop = 4
        await policy.step(bot, [adept], [shade], [], [], Point2((0, 0)))
        bot.state.game_loop = 120
        await policy.step(bot, [adept], [shade], [], [], Point2((0, 0)))
        assert adept.commands[-1][0] is A.CANCEL_ADEPTPHASESHIFT
        bot.state.game_loop = 124
        await policy.step(bot, [adept], [], [], [], Point2((0, 0)))
        stages = [e["stage"] for e in json_roundtrip(bot.events) if e["kind"] == "adept_phase"]
        assert stages == ["cast_attempt", "shade_observed", "cancel_attempt", "cancel_no_transfer"]
        assert not bot.counts["adept_transfer_observed"]

    asyncio.run(run())


def test_missing_cast_availability_and_caster_death_are_not_successes(json_roundtrip):
    async def run():
        bot, adept, shade = setup(ready=False)
        policy = AdeptHarass("commit")
        await policy.step(bot, [adept], [], [], [], Point2((0, 0)))
        assert not policy.attempted
        assert not bot.counts["adept_cast_attempts"]
        bot, adept, shade = setup()
        await policy.step(bot, [adept], [], [], [], Point2((0, 0)))
        bot.state.game_loop = 4
        await policy.step(bot, [], [], [], [], Point2((0, 0)))
        assert [e["stage"] for e in json_roundtrip(bot.events) if e["kind"] == "adept_phase"] == [
            "cast_attempt",
            "caster_lost",
        ]
        assert not bot.counts["adept_transfer_observed"]

    asyncio.run(run())
