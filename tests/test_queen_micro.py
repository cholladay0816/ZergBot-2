from types import SimpleNamespace

from sc2.position import Point2

from zergbot.queen_micro import defend_motion, grenade_escape


def charge(point=(0, 0), enemy=True):
    return SimpleNamespace(id="KD8CHARGE", is_enemy=enemy, radius=2, positions={Point2(point)})


def test_grenade_uses_visible_enemy_effect_and_pathable_escape():
    pos = Point2((0, 0))
    assert grenade_escape(pos, 0.5, [charge(enemy=False)], lambda p: True) is None
    assert grenade_escape(pos, 0.5, [charge((10, 0))], lambda p: True) is None
    assert grenade_escape(pos, 0.5, [charge()], lambda p: False) is None
    escape = grenade_escape(pos, 0.5, [charge()], lambda p: p.x > 0)
    assert escape == Point2((4, 0))


def test_own_cooldown_kites_only_within_base_envelope():
    pos, base, enemy = Point2((4, 0)), Point2((0, 0)), Point2((8, 0))
    assert defend_motion(pos, base, enemy, 0, 5, 1, lambda p: True) is None
    assert defend_motion(pos, base, enemy, 10, 5, 1, lambda p: True) == Point2((2.5, 0))
    assert defend_motion(pos, base, enemy, 10, 5, 1, lambda p: False) is None


def test_chase_leash_returns_to_base_and_never_requires_enemy_cooldown():
    assert defend_motion(
        Point2((14, 0)), Point2((0, 0)), Point2((20, 0)), 0, 5, 1, lambda p: True
    ) == Point2((0, 0))


def test_worker_interception_does_not_back_away_from_side_mineral_line():
    position, base, enemy = Point2((4, 0)), Point2((0, 0)), Point2((8, 0))
    protected = Point2((4, 6))
    motion = defend_motion(position, base, enemy, 10, 5, 1, lambda p: True, protected)
    assert motion is not None and motion.y > 0
    # A ready in-range shot is never replaced by a cooldown reposition command.
    assert defend_motion(position, base, enemy, 0, 5, 1, lambda p: True, protected) is None


def test_scripted_reaper_chooses_pathable_alternative_instead_of_leaving_attack_order():
    from zergbot.scenarios import escape_point

    point = escape_point(Point2((0, 0)), Point2((3, 0)), lambda p: p.y >= 0 and p.x >= 0)
    assert point is not None and point.y > 0
    assert escape_point(Point2((0, 0)), Point2((3, 0)), lambda p: False) is None
