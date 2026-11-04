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
