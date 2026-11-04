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
    assert agent.decide(obs(1, True), 9, C).action is Action.EMERGE


def test_failed_burrow_retries_and_retreat_keeps_recovery_state():
    agent = RoachAgent(1)
    assert agent.decide(obs(), 0, C).action is Action.BURROW
    assert agent.decide(obs(), 4, C).action is Action.WAIT
    assert agent.decide(obs(), 8, C).action is Action.BURROW
    assert agent.decide(obs(0.6, can_burrow=False), 12, C).action is Action.RETREAT
    assert agent.decide(obs(0.8), 16, C) is None


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
