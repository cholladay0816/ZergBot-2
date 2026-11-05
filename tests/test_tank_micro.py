from sc2.position import Point2

from zergbot.tank_micro import split_waypoint


def test_spread_lanes_are_distinct_and_engagement_is_bounded():
    position, tank, home = Point2((0, 0)), Point2((15, 0)), Point2((-5, 0))
    points = [split_waypoint(position, tank, home, i, 0, lambda p: True) for i in range(16)]
    assert len(set(points)) == 16
    assert min(a.distance_to(b) for i, a in enumerate(points) for b in points[i + 1 :]) >= 2.49
    assert split_waypoint(position, tank, home, 0, 90, lambda p: True) is None
    assert split_waypoint(Point2((12, 0)), tank, home, 0, 0, lambda p: True) is None
    assert split_waypoint(position, tank, home, 0, 0, lambda p: False) is None


def test_tank_death_and_weapon_events_use_real_json_contract(json_roundtrip):
    import asyncio
    from collections import Counter
    from types import MethodType, SimpleNamespace

    from zergbot.scenarios import MeasuredBot

    bot = SimpleNamespace(
        options=SimpleNamespace(scenario="tank"),
        state=SimpleNamespace(game_loop=40),
        events=[],
        counts=Counter(),
        previous_own_types={1: "SIEGETANKSIEGED"},
    )
    bot.record = MethodType(MeasuredBot.record, bot)
    bot.record(
        "siege_weapon", tag=1, own_cooldown=50.0, health=175.0, position=[1.0, 2.0], own_target=2
    )
    asyncio.run(MeasuredBot.on_unit_destroyed(bot, 1))
    assert json_roundtrip(bot.events)[-1]["unit_type"] == "SIEGETANKSIEGED"
