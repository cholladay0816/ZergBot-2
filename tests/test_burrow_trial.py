import asyncio
from collections import Counter
from types import MethodType
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest
from sc2.ids.ability_id import AbilityId as A
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2

from zergbot.agents import Observation
from zergbot.burrow_trial import BurrowTrial, trial_sample
from zergbot.scenarios import MeasuredBot


def bot_fixture(researched=False, requested=True, tanks=1, detection=False):
    bot = NS(
        options=NS(burrow_research=requested, burrow_tanks=tanks, burrow_detection=detection),
        state=NS(upgrades={UpgradeId.BURROW} if researched else set(), game_loop=0),
        townhalls=NS(ready=NS(first=Mock())),
        game_data=NS(
            upgrades={UpgradeId.BURROW.value: NS(research_ability=NS(id=A.RESEARCH_BURROW))}
        ),
        get_available_abilities=AsyncMock(return_value=[[A.RESEARCH_BURROW]]),
        can_afford=Mock(return_value=True),
        client=NS(debug_create_unit=AsyncMock()),
        start_location=Point2((0, 0)),
        game_info=NS(map_center=Point2((100, 0))),
        events=[],
        counts=Counter(),
    )
    bot.record = MethodType(MeasuredBot.record, bot)
    return bot


def test_actual_research_submission_does_not_mean_ready_and_never_spawns_early():
    bot, trial = bot_fixture(), BurrowTrial()
    asyncio.run(trial.step(bot))
    bot.townhalls.ready.first.assert_called_once_with(A.RESEARCH_BURROW)
    bot.client.debug_create_unit.assert_not_awaited()
    asyncio.run(trial.step(bot))
    bot.townhalls.ready.first.assert_called_once()
    bot.state.upgrades.add(UpgradeId.BURROW)
    asyncio.run(trial.step(bot))
    assert trial.spawned


def test_unavailable_research_does_not_fake_readiness():
    bot, trial = bot_fixture(), BurrowTrial()
    bot.get_available_abilities.return_value = [[]]
    asyncio.run(trial.step(bot))
    assert not trial.research_submitted and not trial.spawned


@pytest.mark.parametrize("tanks,detection", [(1, False), (2, False), (3, True)])
def test_setup_ownership_counts_and_real_json_contract(tanks, detection, json_roundtrip):
    bot, trial = bot_fixture(True, True, tanks, detection), BurrowTrial()
    asyncio.run(trial.step(bot))
    commands = bot.client.debug_create_unit.await_args.args[0]
    assert commands[:2] == [
        (U.ROACH, 1, Point2((7, 0)), 1),
        (U.SIEGETANKSIEGED, tanks, Point2((14, 0)), 2),
    ]
    assert any(c[0] == U.RAVEN for c in commands) == detection
    assert json_roundtrip(bot.events)[0]["researched"] is True


def test_observation_sample_and_death_use_real_allowlist_and_json(json_roundtrip):
    bot = bot_fixture()
    unit = NS(
        tag=np.int64(1),
        health=np.float32(7),
        health_max=np.float32(145),
        position=Point2((np.float32(1), np.float32(2))),
        orders=[],
    )
    bot.record(
        "burrow_sample",
        **trial_sample(unit, Observation(1, 7 / 145, False, True, False, True), None),
    )
    bot.options.scenario = "burrow-tank"
    bot.previous_own_types = {1: "ROACH"}
    asyncio.run(MeasuredBot.on_unit_destroyed(bot, 1))
    assert json_roundtrip(bot.events)[-1]["unit_type"] == "ROACH"
    bot.record(
        "burrow_tank",
        tag=10,
        own_cooldown=50.0,
        own_target=1,
        position=[14.0, 0.0],
        visible_roaches=[1],
    )
    assert json_roundtrip(bot.events)[-1]["own_target"] == 1

    with pytest.raises(ValueError):
        bot.record("burrow_sample", password="secret")
