"""Isolated real-research burrow timing trial; never used by the match policy."""

from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.ids.upgrade_id import UpgradeId

from .agents import CommandArbiter


def trial_sample(unit, observation, intent):
    return dict(
        tag=int(unit.tag),
        health=float(unit.health),
        health_max=float(unit.health_max),
        position=[float(v) for v in unit.position],
        burrowed=bool(observation.burrowed),
        researched=bool(observation.burrow_researched),
        available=bool(observation.can_burrow),
        transition=observation.transition.name if observation.transition else None,
        action=intent.action.name if intent else None,
        reason=intent.reason if intent else None,
        own_orders=[order.ability.id.name for order in unit.orders],
    )


class BurrowTrial:
    def __init__(self):
        self.research_submitted = False
        self.spawned = False
        self.seen = set()

    async def step(self, bot):
        ready = UpgradeId.BURROW in bot.state.upgrades
        if bot.options.burrow_research and not ready:
            if not self.research_submitted:
                hatch = bot.townhalls.ready.first
                ability = bot.game_data.upgrades[UpgradeId.BURROW.value].research_ability.id
                abilities = (await bot.get_available_abilities([hatch]))[0]
                if ability in abilities and bot.can_afford(UpgradeId.BURROW):
                    hatch(ability)
                    self.research_submitted = True
                    bot.record("burrow_setup", phase="research_submitted", researched=False)
            return
        if not self.spawned:
            base, center = bot.start_location, bot.game_info.map_center
            roach = base.towards(center, 7)
            tank = base.towards(center, 14)
            commands = [
                (U.ROACH, 1, roach, 1),
                (U.SIEGETANKSIEGED, bot.options.burrow_tanks, tank, 2),
            ]
            if bot.options.burrow_detection:
                commands.append((U.RAVEN, 1, roach, 2))
            await bot.client.debug_create_unit(commands)
            self.spawned = True
            bot.record("burrow_setup", phase="actors_spawned", researched=bool(ready))
            return
        observations = await bot.roach_gateway.observe()
        bot.roach_registry.sync(observations)
        arbiter = CommandArbiter()
        for observation in observations:
            unit = bot.roach_gateway.units[observation.tag]
            intent = bot.roach_registry.agents[observation.tag].decide(
                observation, bot.state.game_loop, bot.config
            )
            if intent is not None:
                arbiter.submit(intent)
            elif unit.tag not in self.seen:
                unit.hold_position()
            self.seen.add(unit.tag)
            bot.record("burrow_sample", **trial_sample(unit, observation, intent))
        bot.roach_gateway.dispatch(arbiter, bot.start_location, bot.start_location)
