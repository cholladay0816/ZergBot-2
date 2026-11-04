from zergbot.opening import HatchFirstOpening


def test_hatch_reservation_starts_at_worker_goal_and_finishes_on_pending_natural():
    plan = HatchFirstOpening()
    assert not plan.reserve(frame=800, workers=15, bases=1, threatened=False)
    assert plan.reserve(frame=900, workers=16, bases=1, threatened=False)
    assert not plan.reserve(frame=950, workers=15, bases=2, threatened=False)
    assert not plan.reserve(frame=1000, workers=20, bases=1, threatened=False)


def test_visible_pressure_aborts_reservation_without_reentering_it():
    plan = HatchFirstOpening()
    assert plan.reserve(frame=900, workers=16, bases=1, threatened=False)
    assert not plan.reserve(frame=904, workers=16, bases=1, threatened=True)
    assert not plan.reserve(frame=1000, workers=16, bases=1, threatened=False)


def test_failed_placement_cannot_freeze_economy_indefinitely():
    plan = HatchFirstOpening()
    assert plan.reserve(frame=900, workers=16, bases=1, threatened=False)
    assert plan.reserve(frame=1571, workers=16, bases=1, threatened=False)
    assert not plan.reserve(frame=1572, workers=16, bases=1, threatened=False)
    assert not HatchFirstOpening().reserve(frame=2688, workers=16, bases=1, threatened=False)
