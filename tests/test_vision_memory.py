from types import SimpleNamespace as NS

from sc2.position import Point2

from zergbot.harass_micro import validate_harass_event
from zergbot.vision_memory import VisionMemory


def unit(tag, point, **kwargs):
    u = NS(tag=tag, position=Point2(point), **kwargs)
    u.distance_to = lambda p: u.position.distance_to(p)
    return u


def objects():
    flyer = unit(1, (-20, 0), health_percentage=1, sight_range=11)
    tank = unit(
        2,
        (5, 0),
        is_visible=True,
        is_flying=False,
        can_attack_ground=True,
        can_attack_air=False,
        ground_range=13,
    )
    army = [unit(3, (0, 0))]
    return flyer, tank, army


def test_only_observed_threats_create_memory_and_hidden_changes_have_no_effect():
    u, tank, army = objects()
    p = VisionMemory()
    tank.is_visible = False
    p.observe([tank], army, 10)
    assert p.seen is None
    assert p.decide([u], [tank], army, 10, lambda x: False, lambda x: True)[0] is None
    tank.is_visible = True
    p.observe([tank], army, 14)
    remembered = p.seen
    tank.is_visible = False
    tank.position = Point2((100, 100))
    p.observe([tank], army, 18)
    assert p.seen == remembered and p.seen.position == Point2((5, 0))


def test_reveal_without_terrain_starts_mission_then_holds_real_vision():
    u, tank, army = objects()
    p = VisionMemory()
    p.observe([tank], army, 10)
    assert (
        p.decide([u], [tank], army, 10, lambda x: False, lambda x: True)[2]
        == "retain_observed_threat_vision"
    )
    assert p.target.distance_to(tank.position) == 9
    assert (
        p.decide([u], [], army, 14, lambda x: False, lambda x: True)[2]
        == "reacquire_observed_position"
    )
    assert (
        p.decide([u], [tank], army, 18, lambda x: True, lambda x: True)[2]
        == "hold_sustained_vision"
    )
    assert (
        p.decide([u], [], army, 22, lambda x: True, lambda x: True)[2] == "observed_location_clear"
    )


def test_stale_memory_timeout_and_absent_army_bound_mission():
    u, tank, army = objects()
    p = VisionMemory()
    p.observe([tank], army, 10)
    assert p.decide([u], [], army, 123, lambda x: False, lambda x: True)[2] == "memory_stale"
    p.observe([tank], army, 124)
    p.decide([u], [tank], army, 124, lambda x: False, lambda x: True)
    p.observe([tank], army, 572)
    assert (
        p.decide([u], [tank], army, 572, lambda x: True, lambda x: True)[2]
        == "memory_timeout_or_army_lost"
    )


def test_visible_aa_safety_and_no_flyer_do_not_launch():
    u, tank, army = objects()
    aa = unit(4, (-12, 0), is_visible=True, can_attack_air=True, air_range=5, radius=0.5)
    p = VisionMemory()
    p.observe([tank], army, 10)
    assert (
        p.decide([], [tank], army, 10, lambda x: False, lambda x: True)[2] == "no_safe_memory_flyer"
    )
    assert (
        p.decide([u], [tank, aa], army, 10, lambda x: False, lambda x: True)[2]
        == "no_safe_memory_flyer"
    )
    p.decide([u], [tank], army, 10, lambda x: False, lambda x: True)
    u.health_percentage = 0.5
    assert (
        p.decide([u], [tank], army, 14, lambda x: False, lambda x: True)[2]
        == "memory_abort_visible_aa_or_damage"
    )


def test_visible_terrain_needs_no_assignment_and_sample_serializes(json_roundtrip):
    u, tank, army = objects()
    p = VisionMemory()
    p.observe([tank], army, 10)
    assert (
        p.decide([u], [tank], army, 10, lambda x: True, lambda x: True)[2]
        == "terrain_already_visible"
    )
    event = dict(
        kind="vision_sample",
        frame=10,
        hydras=[],
        flyers=[],
        visible_enemies=[],
        remembered=dict(
            tag=p.seen.tag,
            position=list(p.seen.position),
            last_seen_frame=p.seen.frame,
            terrain_visible=False,
        ),
    )
    validate_harass_event(
        event["kind"], {k: v for k, v in event.items() if k not in ("kind", "frame")}
    )
    assert json_roundtrip(event)["remembered"]["last_seen_frame"] == 10
