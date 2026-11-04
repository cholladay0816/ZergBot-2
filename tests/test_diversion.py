import asyncio
from collections import Counter
from types import MethodType, SimpleNamespace
from unittest.mock import AsyncMock

import numpy as np
from sc2.position import Point2

from zergbot.diversion import LingDiversion, defend_workers, route_points
from zergbot.scenarios import MeasuredBot


class Actor:
    def __init__(self, tag, xy):
        self.tag = np.int64(tag)
        self.position = Point2(xy)
        self.health = np.float32(35)
        self.weapon_cooldown = np.float32(0)
        self.ground_range = 5
        self.is_visible = True
        self.commands = []

    def distance_to(self, other):
        return self.position.distance_to(getattr(other, "position", other))

    def target_in_range(self, other):
        return self.distance_to(other) < 5

    def move(self, target):
        self.commands.append(("move", target))

    def attack(self, target):
        self.commands.append(("attack", target))


def bot():
    b = SimpleNamespace(
        events=[],
        counts=Counter(),
        next_samples={},
        state=SimpleNamespace(game_loop=0),
        in_pathing_grid=lambda _: True,
        game_info=SimpleNamespace(map_center=Point2((50, 50))),
        client=SimpleNamespace(query_pathing=AsyncMock(return_value=20)),
    )
    b.record = MethodType(MeasuredBot.record, b)
    b.sample_due = MethodType(MeasuredBot.sample_due, b)
    return b


def test_split_preserves_spawn_and_expires_then_attacks_actual_workers(json_roundtrip):
    b = bot()
    policy = LingDiversion()
    lings = [Actor(i, (16, 16)) for i in range(12)]
    workers = [Actor(100, (0, 0))]
    hellions = [Actor(200, (6, 6))]
    start = [u.position for u in lings]
    asyncio.run(policy.step(b, lings, workers, hellions, Point2((0, 0)), True, 0))
    assert [u.position for u in lings] == start
    assert sum(policy.roles.values()) == 4
    assert all(len(u.commands) == 1 for u in lings)
    assert {e["reason"] for e in json_roundtrip(b.events)} == {
        "visible_hellion_distraction",
        "traverse_flank",
    }
    b.state.game_loop = 632
    asyncio.run(policy.step(b, lings, workers, hellions, Point2((0, 0)), True, 0))
    assert all(u.commands[-1] == ("attack", workers[0]) for u in lings)


def test_hellion_refuses_distant_decoy_and_targets_actual_worker_threat(json_roundtrip):
    b = bot()
    unit = Actor(200, (4, 0))
    home = Point2((0, 0))
    distant = Actor(1, (20, 0))
    nearby = Actor(2, (3, 0))
    defend_workers(b, [unit], [distant], [], home)
    assert unit.commands[-1][0] == "move"
    b.state.game_loop = 16
    defend_workers(b, [unit], [distant, nearby], [], home)
    assert unit.commands[-1] == ("attack", nearby)
    assert json_roundtrip(b.events)[-1]["target_tag"] == 2
    assert route_points(home, Point2((50, 50)), 1) != route_points(home, Point2((50, 50)), -1)


def test_unreachable_flank_falls_back_without_hidden_worker_target(json_roundtrip):
    b = bot()
    b.client.query_pathing = AsyncMock(return_value=None)
    units = [Actor(i, (16, 16)) for i in range(12)]
    asyncio.run(LingDiversion().step(b, units, [], [], Point2((0, 0)), True, 0))
    events = json_roundtrip(b.events)
    assert any(e["reason"] == "flank_unreachable_fallback" for e in events)
    assert all(e["target_tag"] is None for e in events)
