"""Private debug setup and normal-observation controller wiring for cliff tests."""

import math

from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.position import Point2


def in_bounds(bot, point):
    area = bot.game_info.playable_area
    return (
        area.x + 2 < point.x < area.x + area.width - 2
        and area.y + 2 < point.y < area.y + area.height - 2
    )


def is_plateau(bot, point, radius):
    level = bot.get_terrain_height(point)
    offsets = [
        (0, 0),
        (radius, 0),
        (-radius, 0),
        (0, radius),
        (0, -radius),
        (radius * 0.7, radius * 0.7),
        (-radius * 0.7, -radius * 0.7),
    ]
    return all(
        bot.in_pathing_grid(point + Point2(offset))
        and bot.get_terrain_height(point + Point2(offset)) == level
        for offset in offsets
    )


def choose_cliff(bot, approach):
    area = bot.game_info.playable_area
    found = []
    neutrals = list(bot.mineral_field) + list(bot.vespene_geyser)
    for x in range(int(area.x) + 22, int(area.x + area.width) - 22, 4):
        for y in range(int(area.y) + 22, int(area.y + area.height) - 22, 4):
            low = Point2((x, y))
            if any(
                low.distance_to(start) < 28
                for start in [bot.start_location, *bot.enemy_start_locations]
            ):
                continue
            if not bot.in_pathing_grid(low) or any(n.distance_to(low) < 4 for n in neutrals):
                continue
            level = bot.get_terrain_height(low)
            if not is_plateau(bot, low, 3):
                continue
            for separation in (13.5,):
                for i in range(8):
                    direction = Point2((math.cos(i * math.pi / 4), math.sin(i * math.pi / 4)))
                    high, flyer = low + direction * separation, low - direction * 12
                    if not in_bounds(bot, flyer) or not bot.in_pathing_grid(high):
                        continue
                    if bot.get_terrain_height(high) < level + 16 or not is_plateau(bot, high, 1):
                        continue
                    if any(n.distance_to(high) < 2 for n in neutrals):
                        continue
                    found.append((low, high, flyer))
    found.sort(
        key=lambda p: (
            p[0].distance_to(bot.game_info.map_center),
            p[0].distance_to(p[1]),
            p[0].x,
            p[0].y,
            p[1].x,
            p[1].y,
        )
    )
    distinct = []
    for item in found:
        if all(item[0].distance_to(other[0]) >= 15 for other in distinct):
            distinct.append(item)
        if len(distinct) > approach:
            return distinct[approach]
    raise ValueError("No suitable distinct high-ground scenario geometry")


async def setup(bot):
    import numpy as np

    if hasattr(bot.game_info, "terrain_height"):
        np.savez_compressed(
            bot.output / "map-grids.npz",
            terrain=bot.game_info.terrain_height.data_numpy,
            pathing=bot.game_info.pathing_grid.data_numpy,
        )
    low, high, flyer = choose_cliff(bot, bot.options.approach)
    commands = [
        (U.HYDRALISK, 12, low, 1),
        (U.OVERSEER, 1, flyer, 1),
        (U.SIEGETANKSIEGED, 1, high, 2),
    ]
    if bot.options.vision_aa:
        commands.append((U.MARINE, 2, high, 2))
    await bot.client.debug_create_unit(commands)
    bot.record(
        "vision_setup",
        low=[float(v) for v in low],
        high=[float(v) for v in high],
        flyer=[float(v) for v in flyer],
        low_height=int(bot.get_terrain_height(low)),
        high_height=int(bot.get_terrain_height(high)),
        scope="evaluator_setup_only",
    )


def defender_step(bot):
    hydras = list(bot.units(U.HYDRALISK))
    flyers = list(bot.units(U.OVERSEER))
    enemies = list(bot.enemy_units.visible)
    ground_targets = [e for e in enemies if not e.is_flying and e.can_attack_ground]
    for hydra in hydras:
        if ground_targets:
            hydra.attack(min(ground_targets, key=lambda e: (hydra.distance_to(e), e.tag)))
        elif hydra.tag not in bot.vision_held:
            hydra.hold_position()
        bot.vision_held.add(hydra.tag)
    reason = "baseline_hold"
    if bot.options.controller == "micro":
        flyer, target, reason = bot.vision_assist.decide(
            flyers,
            enemies,
            bot.state.game_loop,
            bot.get_terrain_height,
            lambda p: in_bounds(bot, p),
        )
        if flyer is not None and target is not None:
            flyer.move(target)
    if reason != bot.vision_reason:
        bot.record(
            "vision_decision",
            reason=reason,
            target=[float(v) for v in bot.vision_assist.target]
            if bot.vision_assist.target
            else None,
        )
        bot.vision_reason = reason
    if bot.sample_due("vision", bot.state.game_loop, 4):
        bot.record(
            "vision_sample",
            hydras=[
                dict(
                    tag=int(u.tag),
                    health=float(u.health),
                    position=[float(v) for v in u.position],
                    height=int(bot.get_terrain_height(u.position)),
                    sight_range=float(u.sight_range),
                    ground_range=float(u.ground_range),
                )
                for u in hydras
            ],
            flyers=[
                dict(
                    tag=int(u.tag), health=float(u.health), position=[float(v) for v in u.position]
                )
                for u in flyers
            ],
            visible_enemies=[
                dict(
                    tag=int(e.tag),
                    unit_type=e.type_id.name,
                    health=float(e.health),
                    position=[float(v) for v in e.position],
                )
                for e in enemies
            ],
        )


def attacker_step(bot):
    targets = list(bot.enemy_units(U.HYDRALISK).visible)
    for tank in bot.units(U.SIEGETANKSIEGED):
        if targets:
            tank.attack(
                max(targets, key=lambda u: (sum(v.distance_to(u) < 1.5 for v in targets), -u.tag))
            )
        bot.record(
            "vision_weapon",
            tag=int(tank.tag),
            health=float(tank.health),
            position=[float(v) for v in tank.position],
            height=int(bot.get_terrain_height(tank.position)),
            own_cooldown=float(tank.weapon_cooldown),
            visible_hydras=len(targets),
            sight_range=float(tank.sight_range),
            ground_range=float(tank.ground_range),
        )
    for marine in bot.units(U.MARINE):
        flyers = list(bot.enemy_units(U.OVERSEER).visible)
        if flyers:
            marine.attack(min(flyers, key=lambda u: marine.distance_to(u)))
