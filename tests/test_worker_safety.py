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


def test_expired_defense_releases_once_even_while_threat_remains():
    from types import SimpleNamespace

    from zergbot.scenarios import Defender

    class Threats:
        def filter(self, predicate):
            return self

        def closer_than(self, distance, position):
            return self

        def closest_to(self, worker):
            return object()

    class Minerals:
        def closer_than(self, distance, position):
            return self

        def closest_to(self, worker):
            return "mineral"

    from collections import Counter

    orders = []
    worker = SimpleNamespace(
        tag=7, health_percentage=1, distance_to=lambda _: 2, gather=orders.append
    )
    bot = SimpleNamespace(
        enemy_units=Threats(),
        mineral_field=Minerals(),
        start_location=None,
        workers=[worker],
        worker_defenders={7},
        worker_defense_start=0,
        state=SimpleNamespace(game_loop=1000),
        options=SimpleNamespace(worker_defense_seconds=10, worker_defense_count=6),
        counts=Counter(),
    )
    assert Defender.protect_workers(bot) == {7}
    assert bot.worker_defenders == set()
    assert Defender.protect_workers(bot) == set()
    assert orders == ["mineral"]
    assert bot.counts["worker_mine_commands"] == 1


def test_worker_pull_obeys_selected_participation_cap():
    from collections import Counter
    from types import SimpleNamespace

    from zergbot.scenarios import Defender

    class Threats(list):
        def filter(self, predicate):
            return self

        def closer_than(self, distance, position):
            return self

        def closest_to(self, worker):
            return self[0]

    class Minerals:
        def closer_than(self, distance, position):
            return self

    for count in (1, 6, 12):
        orders = []
        workers = [
            SimpleNamespace(
                tag=i,
                health_percentage=1,
                distance_to=lambda _: 2,
                attack=lambda enemy, tag=i, recorder=orders: recorder.append(tag),
            )
            for i in range(12)
        ]
        bot = SimpleNamespace(
            enemy_units=Threats([SimpleNamespace(health=35)]),
            mineral_field=Minerals(),
            start_location=None,
            workers=workers,
            worker_defenders=set(),
            worker_defense_start=0,
            state=SimpleNamespace(game_loop=1),
            options=SimpleNamespace(worker_defense_seconds=10, worker_defense_count=count),
            counts=Counter(),
        )
        handled = Defender.protect_workers(bot)
        assert len(orders) == len(handled) == count
        assert set(orders) == handled == bot.worker_defenders


def test_scenario_worker_count_rejects_unbounded_pull(monkeypatch):
    import pytest

    from zergbot.scenarios import main

    monkeypatch.setattr(
        "sys.argv", ["scenario", "--scenario", "lings", "--worker-defense-count", "13"]
    )
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
