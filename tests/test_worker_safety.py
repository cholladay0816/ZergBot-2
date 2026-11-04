from zergbot.worker_safety import worker_action


def test_low_health_evacuates_before_defending():
    assert worker_action(0.3, 2, True, 0) == "evacuate"
    assert worker_action(0.8, 2, True, 0) == "defend"
    assert worker_action(0.8, 2, False, 0) == "mine"


def test_defense_is_local_and_time_bounded():
    assert worker_action(0.8, 6, True, 0) == "mine"
    assert worker_action(0.8, 2, True, 224) == "mine"
    assert worker_action(0.3, 2, True, 224) == "mine"
