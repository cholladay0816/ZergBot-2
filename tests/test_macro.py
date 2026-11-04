from dataclasses import replace

from zergbot.config import BotConfig
from zergbot.macro import MacroHatchGate, MacroState, extractor_target, queen_target, worker_target

C = BotConfig()
S = MacroState(3, 3, 4, 55, 66, 700, 300, 2, False)


def test_macro_hatch_does_not_count_as_resource_saturation():
    assert worker_target(S, C) == 66
    assert worker_target(replace(S, worker_capacity=48), C) == 48
    assert queen_target(S, C) == 6
    assert queen_target(replace(S, ready_bases=1, hatcheries=1), C) == 1


def test_gas_expansion_tracks_workers_and_stockpile():
    assert extractor_target(replace(S, workers=25), C) == 3
    assert extractor_target(S, C) == 6
    assert extractor_target(replace(S, gas=2000), C) == 3


def test_macro_requires_persistent_scarcity_and_safe_economy():
    gate = MacroHatchGate()
    assert not gate.ready(S, C, 0, 0, 0)
    assert gate.ready(S, C, 224, 0, 0)
    assert not gate.ready(replace(S, threatened=True), C, 228, 0, 0)
    assert not gate.ready(S, C, 232, 0, 0)
    assert not gate.ready(S, C, 500, 1, 0)
    assert not gate.ready(S, C, 504, 0, 1)
    assert not gate.ready(replace(S, ready_bases=2), C, 508, 0, 0)
    assert not gate.ready(replace(S, larvae=10), C, 512, 0, 0)
    assert not gate.ready(replace(S, minerals=200), C, 516, 0, 0)
