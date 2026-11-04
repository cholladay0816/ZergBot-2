from sc2.position import Point2

from zergbot.scenario_geometry import grenade_score, mineral_ingress, predict_visible_position


def test_mineral_ingress_stays_on_worker_side_and_rejects_blocked_setup():
    base, pocket = Point2((0, 0)), Point2((-6, 0))
    points = [mineral_ingress(base, pocket, a, lambda p: True) for a in (0, 1, 2)]
    assert len(set(points)) == 3
    assert all(p.x < pocket.x and 4 <= p.distance_to(pocket) <= 12 for p in points)
    assert mineral_ingress(base, pocket, 1, lambda p: False) is None


def test_visible_motion_prediction_is_bounded_and_handles_missing_history():
    current = Point2((4, 0))
    assert predict_visible_position(current, None, 4) == current
    assert predict_visible_position(current, Point2((0, 0)), 4) == Point2((6, 0))
    assert predict_visible_position(current, current, 4) == current


def test_grenade_opportunity_score_rewards_real_visible_worker_clusters():
    point = Point2((0, 0))
    assert grenade_score(point, [Point2((1, 0))] * 3, []) == (6, 3, 0)
    assert grenade_score(point, [], [Point2((1, 0))]) == (3, 0, 1)
    assert grenade_score(point, [Point2((5, 0))], []) == (0, 0, 0)
