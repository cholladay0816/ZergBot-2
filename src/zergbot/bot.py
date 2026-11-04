from sc2.bot_ai import BotAI

from .agents import AgentRegistry, CommandArbiter
from .config import BotConfig
from .economy import Economy
from .integration import SC2UnitGateway
from .strategy import ArmyStrategy
from .telemetry import TelemetryAdapter


class ZergBot(BotAI):
    def __init__(self, config: BotConfig | None = None, diagnostics=None) -> None:
        super().__init__()
        self.config = config or BotConfig()
        self.telemetry = TelemetryAdapter(diagnostics) if diagnostics is not None else None
        self.registry = AgentRegistry()
        self.gateway = SC2UnitGateway(self)
        self.strategy = ArmyStrategy()
        self.economy = Economy(self.config)

    async def on_start(self) -> None:
        self.client.game_step = self.config.game_step
        if self.telemetry and self.telemetry.recorder.config.enabled:
            ping = (await self.client.ping()).ping
            self.telemetry.recorder.metadata.update(
                {
                    "game_version": ping.game_version,
                    "base_build": ping.base_build,
                    "data_version": ping.data_version,
                }
            )

    async def on_step(self, iteration: int) -> None:
        if self.telemetry:
            self.telemetry.sample(self)
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
        if self.telemetry:
            self.telemetry.decisions(observations, self.registry, arbiter, self.state.game_loop)
        self.gateway.dispatch(arbiter, target, retreat)
        await self.economy.step(self, iteration)

    async def on_unit_created(self, unit):
        if self.telemetry:
            self.telemetry.recorder.record(
                "created",
                self.state.game_loop,
                tag=unit.tag,
                unit_type=unit.type_id.name,
                scope="own",
            )

    async def on_unit_type_changed(self, unit, previous_type):
        if self.telemetry:
            self.telemetry.recorder.record(
                "type_changed",
                self.state.game_loop,
                tag=unit.tag,
                unit_type=unit.type_id.name,
                previous_type=previous_type.name,
                scope="own",
            )

    async def on_unit_destroyed(self, unit_tag):
        if self.telemetry:
            self.telemetry.destroyed(self.state.game_loop, unit_tag)

    async def on_upgrade_complete(self, upgrade):
        if self.telemetry:
            self.telemetry.recorder.record("upgrade", self.state.game_loop, upgrade=upgrade.name)

    async def on_unit_took_damage(self, unit, amount_damage_taken):
        if self.telemetry:
            self.telemetry.damage(self, unit, amount_damage_taken)
