from collections import Counter
from types import MethodType, SimpleNamespace

import numpy as np
from sc2.position import Point2

from zergbot.scenarios import MeasuredBot
from zergbot.shade_guard import guard_point, guard_queen


class Actor:
    def __init__(self, xy):
        self.position = Point2(xy)
        self.health_percentage = 1
        self.tag = np.int64(1)
        self.commands = []

    def distance_to(self, other):
        return self.position.distance_to(getattr(other, "position", other))

    def move(self, target):
        self.commands.append(target)


def test_visible_warning_yields_to_actual_threat_and_unpathable_destination():
    q, shade, threat = Actor((0, 0)), Actor((12, 0)), Actor((8, 0))
    pocket = Point2((10, 0))
    assert guard_point(q, pocket, [shade], [], lambda _: True) == Point2((12, 0))
    assert guard_point(q, pocket, [], [], lambda _: True) is None
    assert guard_point(q, pocket, [shade], [threat], lambda _: True) is None
    assert guard_point(q, pocket, [shade], [], lambda _: False) is None
    q.health_percentage = 0.2
    assert guard_point(q, pocket, [shade], [], lambda _: True) is None


def test_guard_uses_real_recorder_json_contract_and_holds_without_duplicate_move(json_roundtrip):
    bot = SimpleNamespace(
        events=[],
        counts=Counter(),
        next_samples={},
        state=SimpleNamespace(game_loop=0),
        in_pathing_grid=lambda _: True,
    )
    bot.record = MethodType(MeasuredBot.record, bot)
    bot.sample_due = MethodType(MeasuredBot.sample_due, bot)
    q, shade = Actor((0, 0)), Actor((12, 0))
    pocket = Point2((10, 0))
    assert guard_queen(bot, q, pocket, [shade], [])
    assert len(q.commands) == 1
    q.position = q.commands[0]
    assert guard_queen(bot, q, pocket, [shade], [])
    assert len(q.commands) == 1
    assert json_roundtrip(bot.events)[0]["scope"] == "visible_shade_warning_only"
