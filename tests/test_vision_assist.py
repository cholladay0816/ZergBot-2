import asyncio
from collections import Counter
from types import MethodType
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

import numpy as np
from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.position import Point2

from zergbot import cliff_scenario
from zergbot.scenarios import MeasuredBot
from zergbot.vision_assist import VisionAssist


def flyer():
    u = NS(tag=1, position=Point2((-10, 0)), health_percentage=1.0, health=200.0, move=Mock())
    u.distance_to = lambda p: u.position.distance_to(p)
    return u


def height(p):
    return 32 if p.x > 2 else 0


def prepare():
    policy = VisionAssist()
    policy.observe_damage((0, 0), 10, height, lambda p: p.x < 2, lambda p: True)
    return policy


def test_damage_required_and_invisible_enemy_cannot_change_decision():
    u = flyer()
    assert VisionAssist().decide([u], [], 10, height, lambda p: True)[0] is None
    hidden = NS(
        is_visible=False,
        can_attack_air=True,
        can_attack_ground=True,
        position=Point2((3, 0)),
        air_range=100,
        radius=1,
    )
    a, b = prepare(), prepare()
    assert (
        a.decide([u], [], 10, height, lambda p: True)[1:]
        == b.decide([u], [hidden], 10, height, lambda p: True)[1:]
    )
    assert a.target.x > 2 and a.region.source_type is None


def test_no_flyer_stale_damage_and_bounded_timeout():
    p = prepare()
    assert p.decide([], [], 10, height, lambda p: True)[2] == "no_healthy_flyer"
    assert p.decide([flyer()], [], 200, height, lambda p: True)[2] == "stale_damage"
    u, p = flyer(), prepare()
    p.decide([u], [], 10, height, lambda p: True)
    assert p.decide([u], [], 234, height, lambda p: True)[2] == "timeout"
    assert p.decide([u], [], 238, height, lambda p: True)[0] is None


def test_visible_aa_and_low_health_abort_and_visible_ground_threat_holds_vision():
    u, p = flyer(), prepare()
    p.decide([u], [], 10, height, lambda p: True)
    tank = NS(
        is_visible=True, can_attack_air=False, can_attack_ground=True, position=Point2((4, 0))
    )
    assert p.decide([u], [tank], 14, height, lambda p: True)[2] == "vision_obtained"
    aa = NS(
        is_visible=True,
        can_attack_air=True,
        can_attack_ground=True,
        position=Point2((-9, 0)),
        air_range=5,
        radius=0.5,
    )
    assert p.decide([u], [aa], 18, height, lambda p: True)[2] == "abort_visible_aa_or_damage"


def test_real_setup_inference_sample_weapon_and_death_json_contract(monkeypatch, json_roundtrip):
    bot = NS(
        options=NS(scenario="cliff", approach=0, vision_aa=False, controller="micro"),
        state=NS(game_loop=10),
        events=[],
        counts=Counter(),
        damage=Counter(),
        client=NS(debug_create_unit=AsyncMock()),
        enemy_units=[],
        get_terrain_height=height,
        is_visible=lambda p: p.x < 2,
        game_info=NS(playable_area=NS(x=-100, y=-100, width=200, height=200)),
        vision_assist=VisionAssist(),
        vision_held=set(),
        vision_reason=None,
        sample_due=lambda *args: True,
        previous_own_types={5: "SIEGETANKSIEGED"},
    )
    bot.record = MethodType(MeasuredBot.record, bot)
    monkeypatch.setattr(
        cliff_scenario,
        "choose_cliff",
        lambda *args: (Point2((0, 0)), Point2((5, 0)), Point2((-18, 0))),
    )
    asyncio.run(cliff_scenario.setup(bot))
    hydra = NS(
        tag=np.int64(2),
        type_id=U.HYDRALISK,
        health=np.float32(80),
        sight_range=9,
        ground_range=5,
        position=Point2((0, 0)),
        hold_position=Mock(),
    )
    asyncio.run(MeasuredBot.on_unit_took_damage(bot, hydra, 10))
    u = flyer()
    bot.units = lambda kind: [hydra] if kind == U.HYDRALISK else [u] if kind == U.OVERSEER else []
    bot.enemy_units = NS(visible=[])
    cliff_scenario.defender_step(bot)
    bot.record(
        "vision_weapon",
        tag=5,
        health=175.0,
        own_cooldown=0.0,
        visible_hydras=12,
        position=[3.0, 4.0],
        height=207,
        sight_range=11.0,
        ground_range=13.0,
    )
    asyncio.run(MeasuredBot.on_unit_destroyed(bot, 5))
    events = json_roundtrip(bot.events)
    assert {e["kind"] for e in events} >= {
        "vision_setup",
        "vision_inference",
        "vision_damage_observation",
        "vision_decision",
        "vision_sample",
        "vision_weapon",
        "vision_destroyed",
    }
    inferred = next(e for e in events if e["kind"] == "vision_inference")
    assert inferred["source_type"] is None and not inferred["source_confirmed"]
    assert not inferred["exhaustive"]


def test_cliff_setup_rejects_slopes_and_blocked_plateaus():
    bot = NS(get_terrain_height=lambda p: int(p.x * 8), in_pathing_grid=lambda p: True)
    assert not cliff_scenario.is_plateau(bot, Point2((10, 10)), 1)
    bot.get_terrain_height = lambda p: 191
    assert cliff_scenario.is_plateau(bot, Point2((10, 10)), 3)
    bot.in_pathing_grid = lambda p: p.x < 11
    assert not cliff_scenario.is_plateau(bot, Point2((10, 10)), 3)


def test_obtained_vision_does_not_extend_bounded_flyer_assignment():
    u, p = flyer(), prepare()
    p.decide([u], [], 10, height, lambda p: True)
    enemy = NS(
        is_visible=True, can_attack_air=False, can_attack_ground=True, position=Point2((4, 0))
    )
    assert p.decide([u], [enemy], 14, height, lambda p: True)[2] == "vision_obtained"
    assert p.decide([u], [enemy], 234, height, lambda p: True)[2] == "timeout"


def test_visible_hit_does_not_become_unexplained_when_enemy_leaves_vision():
    p = prepare()
    p.observe_damage(
        (0, 0), 14, height, lambda p: False, lambda p: True, visible_ground_threat=True
    )
    assert p.region is None
    assert p.decide([flyer()], [], 18, height, lambda p: True)[2] == "no_unexplained_damage"
    # A genuinely new unexplained damage observation may still start a mission.
    p.observe_damage((0, 0), 22, height, lambda p: False, lambda p: True)
    assert p.decide([flyer()], [], 22, height, lambda p: True)[2] == "seek_high_ground_hypothesis"


def test_ranged_formation_preserves_outer_range_and_unit_counts():
    low, high = Point2((0, 0)), Point2((13.5, 0))
    points = cliff_scenario.ranged_formation(low, high)
    assert len(points) == len(set(points)) == 12
    assert min(p.distance_to(high) for p in points) >= 13.5
    assert min(a.distance_to(b) for a in points for b in points if a != b) >= 1.29
