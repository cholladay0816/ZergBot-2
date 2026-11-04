from sc2.bot_ai import BotAI

from .agents import AgentRegistry, CommandArbiter
from .config import BotConfig
from .economy import Economy
from .integration import SC2UnitGateway
from .strategy import ArmyStrategy


class ZergBot(BotAI):
    def __init__(self, config: BotConfig | None = None) -> None:
        super().__init__()
        self.config = config or BotConfig()
        self.registry = AgentRegistry()
        self.gateway = SC2UnitGateway(self)
        self.strategy = ArmyStrategy()
        self.economy = Economy(self.config)

    async def on_start(self) -> None:
        self.client.game_step = self.config.game_step

    async def on_step(self, iteration: int) -> None:
        observations = await self.gateway.observe()
        self.registry.sync(observations)
        arbiter = CommandArbiter()
        retreat = (
            self.townhalls.ready.first.position if self.townhalls.ready else self.start_location
        )
        threats = self.enemy_units.filter(lambda u: not u.is_flying).closer_than(25, retreat)
        target = (
            threats.closest_to(retreat).position
            if threats
            else self.enemy_structures.closest_to(retreat).position
            if self.enemy_structures
            else self.enemy_start_locations[0]
        )
        for intent in self.strategy.orders(observations, bool(threats), self.config):
            arbiter.submit(intent)
        for obs in observations:
            intent = self.registry.agents[obs.tag].decide(obs, self.state.game_loop, self.config)
            if intent is not None:
                arbiter.submit(intent)
        self.gateway.dispatch(arbiter, target, retreat)
        await self.economy.step(self, iteration)
