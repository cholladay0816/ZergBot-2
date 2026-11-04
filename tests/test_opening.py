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


def test_readiness_budget_is_bounded_and_observation_closed():
    from zergbot.opening import OpeningBudget

    gate = OpeningBudget()
    assert not gate.reserve("pool", frame=1000, needed=True, eligible=False, latest_frame=2688)
    assert gate.reserve("pool", frame=1100, needed=True, eligible=True, latest_frame=2688)
    assert not gate.reserve("pool", frame=1548, needed=True, eligible=True, latest_frame=2688)
    assert not gate.reserve("pool", frame=1552, needed=True, eligible=True, latest_frame=2688)
    assert gate.reserve("queen", frame=3000, needed=True, eligible=True, latest_frame=5600)
    assert not gate.reserve("queen", frame=3004, needed=False, eligible=True, latest_frame=5600)
    assert not gate.reserve("queen", frame=3100, needed=True, eligible=True, latest_frame=5600)


def test_readiness_budget_cannot_begin_late():
    from zergbot.opening import OpeningBudget

    assert not OpeningBudget().reserve(
        "pool", frame=2688, needed=True, eligible=True, latest_frame=2688
    )
