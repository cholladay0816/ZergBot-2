from zergbot.worker_safety import worker_action


def test_low_health_evacuates_before_defending():
    assert worker_action(0.3, 2, True, 0) == "evacuate"
    assert worker_action(0.8, 2, True, 0) == "defend"
    assert worker_action(0.8, 2, False, 0) == "mine"


def test_defense_is_local_and_time_bounded():
    assert worker_action(0.8, 6, True, 0) == "mine"
    assert worker_action(0.8, 2, True, 224) == "mine"
    assert worker_action(0.3, 2, True, 224) == "mine"


def test_release_reports_handled_workers_to_prevent_second_gather():
    from types import SimpleNamespace

    from zergbot.scenarios import Defender

    class EmptyThreats:
        def filter(self, predicate):
            return self

        def closer_than(self, distance, position):
            return []

    class Minerals:
        def closer_than(self, distance, position):
            return self

        def closest_to(self, worker):
            return "mineral"

    orders = []
    worker = SimpleNamespace(tag=7, gather=orders.append)
    bot = SimpleNamespace(
        enemy_units=EmptyThreats(),
        mineral_field=Minerals(),
        start_location=None,
        workers=[worker],
        worker_defenders={7},
        worker_defense_start=0,
    )
    assert Defender.protect_workers(bot) == {7}
    assert orders == ["mineral"]
    assert bot.worker_defenders == set()
    assert bot.worker_defense_start is None


def test_extended_window_is_explicit_and_still_bounded():
    assert worker_action(0.8, 2, True, 224, max_frames=672) == "defend"
    assert worker_action(0.3, 2, True, 671, max_frames=672) == "evacuate"
    assert worker_action(0.8, 2, True, 672, max_frames=672) == "mine"
    assert worker_action(0.8, 6, True, 224, max_frames=672) == "mine"
