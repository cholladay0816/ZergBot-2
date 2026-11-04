from sc2.position import Point2

from zergbot.harass_micro import flank_point, line_overlap


def test_alignment_excludes_units_behind_or_outside_reach():
    assert line_overlap((0, 0), (5, 0), [(2, 0), (4, 0.5), (-1, 0), (7, 0), (3, 2)], 6) == 2
    assert line_overlap((0, 0), (0, 0), [(0, 0)], 6) == 0


def test_alignment_rotates_with_aim_without_hidden_target_data():
    assert line_overlap((0, 0), (0, 5), [(0, 2), (0.5, 4), (2, 3)], 6) == 2


def test_flank_is_a_traversal_waypoint_not_a_spawn_advantage():
    home, center = Point2((20, 20)), Point2((40, 20))
    left = flank_point(home, center, 0, lambda _: True)
    right = flank_point(home, center, 2, lambda _: True)
    assert left.x == right.x == 22
    assert left.y == 10 and right.y == 30
    assert flank_point(home, center, 0, lambda _: False) is None


def hellion_fixture(health=1):
    from collections import Counter
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, Mock

    position = Point2((0, 0))
    unit = SimpleNamespace(
        tag=1,
        position=position,
        health=90 * health,
        health_percentage=health,
        weapon_cooldown=0,
        ground_range=5,
        attack=Mock(),
        move=Mock(),
        target_in_range=lambda _: True,
        distance_to=lambda target: position.distance_to(getattr(target, "position", target)),
    )
    bot = SimpleNamespace(
        game_info=SimpleNamespace(map_center=Point2((30, 30))),
        in_pathing_grid=lambda _: True,
        client=SimpleNamespace(query_pathing=AsyncMock(return_value=12)),
        counts=Counter(),
        record=Mock(),
        sample_due=lambda *args: True,
        state=SimpleNamespace(game_loop=4),
    )
    # No enemy orders or cooldown attributes: neither may be required by the policy.
    workers = [
        SimpleNamespace(tag=10 + i, position=Point2((3 + i, 0)), health=hp, is_visible=True)
        for i, hp in enumerate((5, 30))
    ]
    return bot, unit, workers


def test_hellion_prefers_aligned_low_health_worker_with_own_readiness():
    import asyncio

    from zergbot.harass_micro import HellionHarass

    bot, unit, workers = hellion_fixture()
    asyncio.run(HellionHarass().step(bot, [unit], workers, [], Point2((0, 0)), 1))
    unit.attack.assert_called_once_with(workers[0])
    unit.move.assert_not_called()
    assert bot.counts["hellion_worker_attack_opportunity_samples"] == 1


def test_critical_hellion_retreats_without_issuing_an_attack():
    import asyncio

    from zergbot.harass_micro import HellionHarass

    bot, unit, workers = hellion_fixture(0.2)
    asyncio.run(HellionHarass().step(bot, [unit], workers, [], Point2((0, 0)), 1))
    unit.move.assert_called_once()
    unit.attack.assert_not_called()
