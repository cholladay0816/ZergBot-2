from types import SimpleNamespace

from zergbot.config import BotConfig
from zergbot.queens import QueenManager, queen_priority


def decision(**changes):
    args = dict(
        critical=False,
        direct_threat=False,
        defending=False,
        casting=False,
        inject_due=True,
        can_inject=True,
        role="inject",
        can_creep=True,
    )
    args.update(changes)
    return queen_priority(**args)


def test_inject_reserves_energy_and_commands():
    assert decision() == "inject"
    assert decision(can_inject=False) == "wait"
    assert decision(inject_due=False) == "wait"
    assert decision(casting=True) == "wait"
    assert decision(role="defense_creep") == "creep"


def test_survival_and_real_threats_override_roles():
    assert decision(direct_threat=True, critical=True, casting=True) == "retreat"
    assert decision(direct_threat=True) == "defend"
    assert decision(defending=True, role="defense_creep") == "defend"


def test_assignments_survive_order_changes_and_prune_dead_bases_queens():
    manager = QueenManager(BotConfig())
    bases = [SimpleNamespace(tag=10), SimpleNamespace(tag=20)]
    queens = [SimpleNamespace(tag=i, distance_to=lambda b: b.tag) for i in (1, 2, 3)]
    manager.assign(bases, queens)
    assert manager.injectors == {10: 1, 20: 2}
    manager.assign(list(reversed(bases)), list(reversed(queens)))
    assert manager.injectors == {10: 1, 20: 2}
    manager.assign(bases[1:], queens[2:])
    assert manager.injectors == {20: 3}


def test_real_recorder_accepts_queen_decisions_and_counts_only_attempts(tmp_path):
    from zergbot.diagnostics import MatchDiagnostics

    recorder = MatchDiagnostics(tmp_path, {})
    bot = SimpleNamespace(
        telemetry=SimpleNamespace(recorder=recorder), state=SimpleNamespace(game_loop=0)
    )
    manager = QueenManager(BotConfig())
    queen = SimpleNamespace(tag=1)
    manager.event(bot, queen, "inject", "inject")
    manager.event(bot, queen, "placement_unavailable", "defense_creep")
    assert recorder.command_counts["INJECT"] == 1
    assert sum(recorder.command_counts.values()) == 1
    assert len(recorder.events) == 2


def test_step_injects_once_and_reserves_injector_from_creep(tmp_path):
    import asyncio
    from unittest.mock import AsyncMock, Mock

    from sc2.ids.ability_id import AbilityId as A
    from sc2.position import Point2

    from zergbot.diagnostics import MatchDiagnostics

    class Units(list):
        @property
        def ready(self):
            return self

        def filter(self, pred):
            return Units(u for u in self if pred(u))

        def closer_than(self, distance, unit):
            return Units()

    base = SimpleNamespace(tag=20, position=Point2((10, 10)), has_buff=lambda _: False)
    queen = Mock(
        tag=1,
        orders=[],
        health_percentage=1,
        is_idle=True,
        distance_to=Mock(return_value=2),
        position=Point2((11, 10)),
    )
    recorder = MatchDiagnostics(tmp_path, {})
    bot = SimpleNamespace(
        townhalls=Units([base]),
        units=Mock(return_value=Units([queen])),
        structures=Mock(return_value=Units()),
        enemy_units=Units(),
        state=SimpleNamespace(game_loop=0),
        telemetry=SimpleNamespace(recorder=recorder),
        find_placement=AsyncMock(),
        game_info=SimpleNamespace(map_center=Point2((50, 50))),
    )
    manager = QueenManager(BotConfig())
    asyncio.run(manager.step(bot, {1: {A.EFFECT_INJECTLARVA, A.BUILD_CREEPTUMOR_QUEEN}}))
    queen.assert_called_once_with(A.EFFECT_INJECTLARVA, base)
    queen.attack.assert_not_called()
    queen.move.assert_not_called()
    bot.find_placement.assert_not_awaited()
    queen.reset_mock()
    queen.orders = [object()]
    asyncio.run(manager.step(bot, {1: {A.EFFECT_INJECTLARVA}}))
    queen.assert_not_called()
