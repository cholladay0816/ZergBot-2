"""Pure decisions: no SC2 objects, network calls, or speculative morph state."""

from dataclasses import dataclass
from enum import Enum, auto

from .config import BotConfig


class Action(Enum):
    ATTACK = auto()
    RETREAT = auto()
    BURROW = auto()
    EMERGE = auto()
    WAIT = auto()


@dataclass(frozen=True)
class Observation:
    tag: int
    health: float
    burrowed: bool
    can_burrow: bool = False
    can_emerge: bool = False
    burrow_researched: bool = False


@dataclass(frozen=True)
class Intent:
    tag: int
    action: Action
    priority: int


class CommandArbiter:
    """One winner per tag per frame; first submission wins equal priorities.

    WAIT is an intentional veto, preventing strategy orders during recovery.
    """

    def __init__(self) -> None:
        self.commands: dict[int, Intent] = {}

    def submit(self, intent: Intent) -> None:
        previous = self.commands.get(intent.tag)
        if previous is None or intent.priority > previous.priority:
            self.commands[intent.tag] = intent


@dataclass
class RoachAgent:
    tag: int
    recovering: bool = False
    last_attempt_frame: int = -1000000

    def decide(self, obs: Observation, frame: int, config: BotConfig) -> Intent | None:
        if obs.tag != self.tag:
            raise ValueError("Observation tag does not match agent")
        if obs.health <= config.burrow_health or obs.burrowed:
            self.recovering = True
        if not obs.burrowed and obs.health >= config.emerge_health:
            self.recovering = False
        if not self.recovering:
            return None
        ready = frame - self.last_attempt_frame >= config.retry_frames
        if obs.burrowed:
            action = Action.WAIT
            if obs.health >= config.emerge_health and obs.can_emerge and ready:
                action = Action.EMERGE
        elif obs.burrow_researched and obs.can_burrow:
            action = Action.BURROW if ready else Action.WAIT
        else:
            action = Action.RETREAT
        if action in (Action.BURROW, Action.EMERGE):
            self.last_attempt_frame = frame
        return Intent(self.tag, action, 100)


class AgentRegistry:
    """Tags survive roach burrow/unburrow type changes; absent tags are pruned."""

    def __init__(self) -> None:
        self.agents: dict[int, RoachAgent] = {}

    def sync(self, observations: list[Observation]) -> None:
        living = {obs.tag for obs in observations}
        self.agents = {tag: agent for tag, agent in self.agents.items() if tag in living}
        for obs in observations:
            if obs.tag not in self.agents:
                self.agents[obs.tag] = RoachAgent(obs.tag)
