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
