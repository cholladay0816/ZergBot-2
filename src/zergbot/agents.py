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
    transition: Action | None = None


@dataclass(frozen=True)
class Intent:
    tag: int
    action: Action
    priority: int
    reason: str = "unspecified"


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
    pending_morph: Action | None = None
    previous_transition: Action | None = None

    def decide(self, obs: Observation, frame: int, config: BotConfig) -> Intent | None:
        if obs.tag != self.tag:
            raise ValueError("Observation tag does not match agent")
        if obs.health <= config.burrow_health or obs.burrowed:
            self.recovering = True
        if not obs.burrowed and obs.health >= config.emerge_health:
            self.recovering = False
        # A sent command is only an attempt. Protect its observation-latency and
        # animation window, even if available abilities temporarily disappear.
        new_order = obs.transition is not None and obs.transition != self.previous_transition
        self.previous_transition = obs.transition
        if self.pending_morph is None and new_order:
            self.pending_morph = obs.transition
            self.last_attempt_frame = frame
        if self.pending_morph is not None:
            completed = (
                (self.pending_morph is Action.BURROW and obs.burrowed)
                or (self.pending_morph is Action.EMERGE and not obs.burrowed)
            ) and obs.transition is not self.pending_morph
            if completed:
                self.pending_morph = None
            elif frame - self.last_attempt_frame < config.morph_timeout_frames:
                return Intent(self.tag, Action.WAIT, 100, "morph_in_flight")
            else:
                # A continuously stale order must not restart this timer. After
                # timeout, retry if available, otherwise retreat exposed / wait hidden.
                self.pending_morph = None
        if not self.recovering:
            return None
        ready = frame - self.last_attempt_frame >= config.retry_frames
        reason = "healing"
        if obs.burrowed:
            action = Action.WAIT
            if obs.health >= config.emerge_health and obs.can_emerge and ready:
                action = Action.EMERGE
                reason = "recovered"
        elif obs.burrow_researched and obs.can_burrow:
            action = Action.BURROW if ready else Action.WAIT
            reason = "low_health" if ready else "retry_interval"
        else:
            action = Action.RETREAT
            reason = "burrow_unavailable" if obs.burrow_researched else "burrow_unresearched"
        if action in (Action.BURROW, Action.EMERGE):
            self.last_attempt_frame = frame
            self.pending_morph = action
        return Intent(self.tag, action, 100, reason)


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
