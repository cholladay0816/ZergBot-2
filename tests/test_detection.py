from dataclasses import replace
from types import SimpleNamespace

import pytest

from zergbot.agents import Action, CommandArbiter, Intent, Observation, RoachAgent
from zergbot.config import BotConfig
from zergbot.integration import detection_danger

C = BotConfig(avoid_detected_burrow=True)


def observation(**changes):
    return replace(Observation(1, 0.3, False, True, True, True, detection_danger=True), **changes)


def enemy(**changes):
    fields = dict(
        is_visible=True,
        is_detector=True,
        detect_range=11,
        radius=0.5,
        can_attack_ground=True,
        ground_range=5,
        distance_to=lambda unit: 5,
    )
    return SimpleNamespace(**(fields | changes))


@pytest.mark.parametrize(
    "changes",
    [
        dict(is_visible=False),
        dict(is_detector=False),
        dict(detect_range=0),
        dict(detect_range=2),
        dict(can_attack_ground=False),
        dict(distance_to=lambda unit: 20),
    ],
)
def test_missing_coverage_or_ground_threat_is_not_danger(changes):
    assert not detection_danger(SimpleNamespace(radius=0.5), [enemy(**changes)])


def test_detector_and_attacker_can_be_different_visible_units():
    assert detection_danger(
        SimpleNamespace(radius=0.5), [enemy(can_attack_ground=False), enemy(is_detector=False)]
    )


def test_danger_retreats_then_holds_before_retry_and_wins_arbitration():
    agent = RoachAgent(1)
    intent = agent.decide(observation(), 0, C)
    assert intent.action is Action.RETREAT
    arbiter = CommandArbiter()
    arbiter.submit(Intent(1, Action.ATTACK, 10))
    arbiter.submit(intent)
    assert arbiter.commands[1] == intent
    assert agent.decide(observation(detection_danger=False), 52, C).action is Action.RETREAT
    assert agent.decide(observation(detection_danger=False), 56, C).action is Action.BURROW


def test_detection_cannot_interrupt_morph_and_emergence_is_observed():
    agent = RoachAgent(1)
    assert agent.decide(observation(detection_danger=False), 0, C).action is Action.BURROW
    assert (
        agent.decide(observation(can_burrow=False, transition=Action.BURROW), 4, C).action
        is Action.WAIT
    )
    assert (
        agent.decide(observation(burrowed=True, transition=Action.BURROW), 8, C).action
        is Action.WAIT
    )
    assert agent.decide(observation(burrowed=True), 24, C).action is Action.EMERGE
    assert agent.decide(observation(burrowed=True, can_emerge=False), 28, C).action is Action.WAIT
    assert agent.decide(observation(), 48, C).action is Action.RETREAT


def test_unavailable_emergence_waits_and_disabled_policy_is_unchanged():
    assert (
        RoachAgent(1).decide(observation(burrowed=True, can_emerge=False), 0, C).action
        is Action.WAIT
    )
    assert RoachAgent(1).decide(observation(), 0, BotConfig()).action is Action.BURROW
    assert RoachAgent(1).decide(observation(health=0.9), 0, C) is None


def test_stalled_morph_times_out_without_burrow_retry_under_detection():
    agent = RoachAgent(1)
    agent.decide(observation(detection_danger=False), 0, C)
    assert agent.decide(observation(transition=Action.BURROW), 64, C).action is Action.RETREAT


def test_gateway_uses_shared_query_and_visible_detection_for_each_roach():
    import asyncio
    from unittest.mock import AsyncMock, Mock

    from sc2.ids.ability_id import AbilityId
    from sc2.ids.upgrade_id import UpgradeId

    from zergbot.integration import SC2UnitGateway

    roach = SimpleNamespace(
        tag=1, health=30, health_max=100, is_burrowed=False, orders=[], radius=0.5
    )
    bot = SimpleNamespace(
        config=C,
        units=Mock(),
        enemy_units=[enemy()],
        enemy_structures=[],
        state=SimpleNamespace(upgrades={UpgradeId.BURROW}),
        get_available_abilities=AsyncMock(return_value=[[AbilityId.BURROWDOWN_ROACH]]),
    )
    bot.units.of_type.return_value = [roach]
    observation = asyncio.run(SC2UnitGateway(bot).observe())[0]
    assert observation.detection_danger and observation.can_burrow
    bot.get_available_abilities.assert_awaited_once_with([roach])


def test_detection_decision_serializes_through_bounded_telemetry(tmp_path):
    import json

    from zergbot.agents import AgentRegistry
    from zergbot.diagnostics import MatchDiagnostics
    from zergbot.telemetry import TelemetryAdapter

    recorder = MatchDiagnostics(tmp_path, {})
    registry = AgentRegistry()
    observations = [observation()]
    registry.sync(observations)
    arbiter = CommandArbiter()
    arbiter.submit(registry.agents[1].decide(observations[0], 0, C))
    TelemetryAdapter(recorder).decisions(observations, registry, arbiter, 0)
    recorder.finish(termination="time_limit")
    events = json.loads((tmp_path / "match.json").read_text())["events"]
    decision = next(e for e in events if e["kind"] == "decision")
    assert decision["detection_danger"] is True
    assert decision["reason"] == "observed_detection_danger"
