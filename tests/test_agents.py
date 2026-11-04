import pytest

from zergbot.agents import Action, AgentRegistry, CommandArbiter, Intent, Observation, RoachAgent
from zergbot.config import BotConfig
from zergbot.strategy import ArmyStrategy

C = BotConfig()


def obs(health=0.4, burrowed=False, can_burrow=True, can_emerge=True, researched=True, tag=1):
    return Observation(tag, health, burrowed, can_burrow, can_emerge, researched)


@pytest.mark.parametrize(
    "health,expected", [(0.0, Action.BURROW), (0.4, Action.BURROW), (0.41, None)]
)
def test_burrow_boundary(health, expected):
    result = RoachAgent(1).decide(obs(health), 0, C)
    assert (result.action if result else None) == expected


@pytest.mark.parametrize("research,available", [(False, True), (True, False), (False, False)])
def test_missing_capability_retreats(research, available):
    result = RoachAgent(1).decide(obs(researched=research, can_burrow=available), 0, C)
    assert result.action is Action.RETREAT


def test_recovery_hysteresis_and_observed_morph():
    agent = RoachAgent(1)
    assert agent.decide(obs(), 0, C).action is Action.BURROW
    assert agent.decide(obs(0.6, True), 4, C).action is Action.WAIT
    assert agent.decide(obs(0.79, True), 8, C).action is Action.WAIT
    assert agent.decide(obs(0.8, True), 12, C).action is Action.EMERGE
    assert agent.recovering  # command is not proof the morph succeeded
    assert agent.decide(obs(0.8, False), 16, C) is None
    assert not agent.recovering


def test_missing_emerge_and_retry_cooldown():
    agent = RoachAgent(1)
    assert agent.decide(obs(1, True, can_emerge=False), 0, C).action is Action.WAIT
    assert agent.decide(obs(1, True), 1, C).action is Action.EMERGE
    assert agent.decide(obs(1, True), 2, C).action is Action.WAIT
    assert agent.decide(obs(1, True), 65, C).action is Action.EMERGE


def test_failed_burrow_retries_and_retreat_keeps_recovery_state():
    agent = RoachAgent(1)
    assert agent.decide(obs(), 0, C).action is Action.BURROW
    assert agent.decide(obs(), 4, C).action is Action.WAIT
    assert agent.decide(obs(), 64, C).action is Action.BURROW
    assert agent.decide(obs(0.6, can_burrow=False), 128, C).action is Action.RETREAT
    assert agent.decide(obs(0.8), 132, C) is None


def test_identity_survives_morph_and_dead_agents_are_pruned():
    registry = AgentRegistry()
    registry.sync([obs(), obs(tag=2)])
    agent = registry.agents[1]
    agent.decide(obs(), 0, C)
    registry.sync([obs(0.5, True)])
    assert registry.agents[1] is agent
    assert agent.recovering
    assert 2 not in registry.agents
    registry.sync([])
    assert registry.agents == {}


@pytest.mark.parametrize("action", [Action.WAIT, Action.BURROW, Action.EMERGE, Action.RETREAT])
@pytest.mark.parametrize("micro_first", [True, False])
def test_strategy_cannot_override_micro(action, micro_first):
    arbiter = CommandArbiter()
    micro, army = Intent(1, action, 100), Intent(1, Action.ATTACK, 10)
    for intent in [micro, army] if micro_first else [army, micro]:
        arbiter.submit(intent)
    assert list(arbiter.commands.values()) == [micro]


def test_recovering_roaches_do_not_trigger_attack():
    units = [obs(0.5, True, tag=i) for i in range(20)]
    assert all(i.action is Action.RETREAT for i in ArmyStrategy().orders(units, False, C))
    assert all(i.action is Action.ATTACK for i in ArmyStrategy().orders(units, True, C))


@pytest.mark.parametrize("low,high", [(0.8, 0.4), (0.4, 0.4), (0, 0.8), (0.4, 1.1)])
def test_invalid_thresholds(low, high):
    with pytest.raises(ValueError):
        BotConfig(burrow_health=low, emerge_health=high)


def test_mismatched_tag_is_rejected():
    with pytest.raises(ValueError):
        RoachAgent(3).decide(obs(), 0, C)


@pytest.mark.parametrize("observed_order", [None, Action.BURROW])
def test_pending_burrow_cannot_be_interrupted_by_unavailable_ability(observed_order):
    from dataclasses import replace

    agent = RoachAgent(1)
    assert agent.decide(obs(), 0, C).action is Action.BURROW
    for frame in (4, 8, 16, 32):
        transitional = replace(obs(can_burrow=False), transition=observed_order)
        intent = agent.decide(transitional, frame, C)
        assert intent.action is Action.WAIT
        arbiter = CommandArbiter()
        arbiter.submit(intent)
        arbiter.submit(Intent(1, Action.ATTACK, 10))
        assert arbiter.commands[1].action is Action.WAIT
    assert agent.decide(obs(0.5, True), 36, C).action is Action.WAIT
    assert agent.pending_morph is None


def test_emergence_waits_for_active_order_to_clear_even_after_type_changes():
    from dataclasses import replace

    agent = RoachAgent(1)
    assert agent.decide(obs(0.8, True), 0, C).action is Action.EMERGE
    assert agent.decide(obs(0.8, True, can_emerge=False), 4, C).action is Action.WAIT
    exposed = replace(obs(0.8), transition=Action.EMERGE)
    assert agent.decide(exposed, 16, C).action is Action.WAIT
    assert agent.decide(obs(0.8), 32, C) is None
    assert agent.pending_morph is None


@pytest.mark.parametrize("available,expected", [(True, Action.BURROW), (False, Action.RETREAT)])
def test_rejected_command_has_bounded_wait(available, expected):
    agent = RoachAgent(1)
    agent.decide(obs(), 0, C)
    assert agent.decide(obs(can_burrow=available), 63, C).action is Action.WAIT
    assert agent.decide(obs(can_burrow=available), 64, C).action is expected


def test_stale_observed_order_does_not_restart_timeout():
    from dataclasses import replace

    agent = RoachAgent(1)
    stalled = replace(obs(can_burrow=False), transition=Action.BURROW)
    # Also protects a transition observed before this controller issued anything.
    assert agent.decide(stalled, 0, C).action is Action.WAIT
    assert agent.decide(stalled, 63, C).action is Action.WAIT
    assert agent.decide(stalled, 64, C).action is Action.RETREAT
    assert agent.decide(stalled, 68, C).action is Action.RETREAT


def test_invalid_morph_timeout():
    with pytest.raises(ValueError):
        BotConfig(morph_timeout_frames=0)


def test_damage_while_hidden_requests_emergence_and_then_bounded_escape():
    agent = RoachAgent(1)
    assert agent.decide(obs(0.5, True), 0, C).action is Action.WAIT
    intent = agent.decide(obs(0.45, True), 4, C)
    assert intent.action is Action.EMERGE and intent.reason == "damaged_while_burrowed"
    assert agent.decide(obs(0.45, True), 8, C).reason == "morph_in_flight"
    exposed = agent.decide(obs(0.45), 24, C)
    assert exposed.action is Action.RETREAT
    assert exposed.reason == "escape_after_burrow_damage"
    assert agent.decide(obs(0.45), 100, C).action is Action.RETREAT
    assert agent.decide(obs(0.45), 116, C).action is Action.BURROW


def test_hidden_damage_waits_for_available_emergence_without_guessing_research():
    agent = RoachAgent(1)
    agent.decide(obs(0.5, True), 0, C)
    blocked = agent.decide(obs(0.45, True, can_emerge=False, researched=False), 4, C)
    assert blocked.action is Action.WAIT
    assert blocked.reason == "escape_emerge_unavailable"
    assert agent.decide(obs(0.45, True, researched=False), 8, C).action is Action.EMERGE


def test_healing_hidden_unit_and_damage_on_first_hidden_observation_do_not_trigger_escape():
    agent = RoachAgent(1)
    agent.decide(obs(0.4), 0, C)
    assert agent.decide(obs(0.3, True), 32, C).reason == "healing"
    assert agent.decide(obs(0.35, True), 36, C).reason == "healing"
    assert agent.escape_until_frame == -1


def test_burrow_damage_never_interrupts_legitimate_pending_transition():
    from dataclasses import replace

    agent = RoachAgent(1)
    agent.decide(obs(0.4), 0, C)
    transitional = replace(obs(0.35, True), transition=Action.BURROW)
    assert agent.decide(transitional, 4, C).reason == "morph_in_flight"
    transitional = replace(obs(0.3, True), transition=Action.BURROW)
    assert agent.decide(transitional, 8, C).reason == "morph_in_flight"
    assert agent.decide(obs(0.3, True), 20, C).action is Action.EMERGE


def test_escape_order_still_overrides_strategy_even_after_health_recovers():
    agent = RoachAgent(1)
    agent.decide(obs(0.7, True), 0, C)
    agent.decide(obs(0.6, True), 4, C)
    intent = agent.decide(obs(0.9), 24, C)
    arbiter = CommandArbiter()
    arbiter.submit(Intent(1, Action.ATTACK, 10))
    arbiter.submit(intent)
    assert arbiter.commands[1].action is Action.RETREAT
    assert agent.decide(obs(0.9), 116, C) is None
