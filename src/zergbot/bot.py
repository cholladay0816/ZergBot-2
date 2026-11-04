import random
from dataclasses import asdict

import numpy as np
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

from .agents import AgentRegistry, CommandArbiter
from .config import BotConfig
from .economy import Economy
from .integration import SC2UnitGateway
from .search import ExpansionSearch
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
        self.search = ExpansionSearch()
        self.economy = Economy(self.config)

    async def on_start(self) -> None:
        try:
            await self._initialize()
        except Exception as error:
            # BurnySC2 converts on_start exceptions into Result.Defeat. Preserve
            # the diagnostic distinction without recording arbitrary error text.
            if self.telemetry:
                self.telemetry.recorder.error_type = type(error).__name__
                self.telemetry.recorder.termination = "startup_failed"
            raise

    async def _initialize(self) -> None:
        # Reset after startup/port selection so library placement choices are paired.
        random.seed(self.config.random_seed)
        np.random.seed(self.config.random_seed)
        if self.telemetry:
            self.telemetry.recorder.bot_config = asdict(self.config)
            self.telemetry.recorder.metadata["python_seed"] = self.config.random_seed
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
        observations = await self.gateway.observe(self.units(UnitTypeId.QUEEN).ready)
        self.registry.sync(observations)
        arbiter = CommandArbiter()
        retreat = (
            self.townhalls.ready.first.position if self.townhalls.ready else self.start_location
        )
        threats = self.enemy_units.filter(lambda u: not u.is_flying).closer_than(25, retreat)
        small_worker_incursion = (
            self.config.worker_defenders > 0
            and bool(threats)
            and len(threats) <= 2
            and all(
                u.type_id in {UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.DRONE} for u in threats
            )
        )
        worker_target = (
            tuple(threats.closest_to(retreat).position) if small_worker_incursion else None
        )
        target = (
            threats.closest_to(retreat).position
            if threats and not small_worker_incursion
            else self.enemy_structures.closest_to(retreat).position
            if self.enemy_structures
            else self.enemy_start_locations[0]
        )
        for intent in self.strategy.orders(
            observations,
            bool(threats) and not small_worker_incursion,
            self.config,
            worker_target=worker_target,
            positions={tag: tuple(unit.position) for tag, unit in self.gateway.units.items()},
        ):
            arbiter.submit(intent)
        if (
            self.config.search_expansions
            and self.strategy.attacking
            and not threats
            and not self.enemy_structures
        ):
            previous = self.search.target(
                self.enemy_start_locations[0],
                self.expansion_locations_list,
                [tuple(base.position) for base in self.townhalls],
            )
            positions = [
                tuple(self.gateway.units[obs.tag].position)
                for obs in observations
                if not obs.burrowed and obs.health >= self.config.emerge_health
            ]
            waypoint = self.search.observe(
                positions, self.is_visible(Point2(previous)), self.state.game_loop
            )
            target = Point2(waypoint)
            if waypoint != previous and self.telemetry:
                self.telemetry.recorder.record(
                    "search_waypoint",
                    self.state.game_loop,
                    previous=previous,
                    target=waypoint,
                    route_index=self.search.index,
                    reason="visited_visible_map_site",
                    scope="candidate_location_not_known_enemy",
                )
        for obs in observations:
            intent = self.registry.agents[obs.tag].decide(obs, self.state.game_loop, self.config)
            if intent is not None:
                arbiter.submit(intent)
        if self.telemetry:
            self.telemetry.decisions(observations, self.registry, arbiter, self.state.game_loop)
        self.gateway.dispatch(arbiter, target, retreat)
        await self.economy.step(self, iteration, self.gateway.abilities_by_tag)

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
