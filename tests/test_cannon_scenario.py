from sc2.position import Point2

from zergbot.scenarios import cannon_candidates


def test_cannon_search_is_bounded_around_real_power_source_and_ordered_toward_threat():
    pylon, home = Point2((20, 20)), Point2((0, 0))
    points = cannon_candidates(pylon, home)
    assert 16 <= len(points) <= 32
    assert len(points) == len(set(points))
    assert all(2 <= p.distance_to(pylon) <= 6 for p in points)
    assert all(p.x == round(p.x) and p.y == round(p.y) for p in points)
    assert [p.distance_to(home) for p in points] == sorted(p.distance_to(home) for p in points)
