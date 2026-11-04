import argparse
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4


def main() -> None:
    from .config import BotConfig

    defaults = BotConfig()
    parser = argparse.ArgumentParser(
        description="Autonomous roach bot (requires local SC2 and map)"
    )
    parser.add_argument(
        "--map", default="AbyssalReefLE", help="Installed .SC2Map name without extension"
    )
    parser.add_argument("--realtime", action="store_true")
    parser.add_argument(
        "--queen-tactical-micro",
        action=argparse.BooleanOptionalAction,
        default=defaults.queen_tactical_micro,
    )
    parser.add_argument(
        "--adaptive-army", action=argparse.BooleanOptionalAction, default=defaults.adaptive_army
    )
    parser.add_argument(
        "--roach-tech", action=argparse.BooleanOptionalAction, default=defaults.roach_tech
    )
    parser.add_argument(
        "--difficulty", choices=["Easy", "Medium", "Hard", "Harder"], default="Hard"
    )
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--opponent", choices=["Terran", "Protoss", "Zerg"], default="Terran")
    for field in (
        "workers",
        "tech_min_workers",
        "extra_queens",
        "extra_queens_after_bases",
        "macro_hatches",
        "macro_after_bases",
        "macro_min_workers",
        "macro_min_minerals",
        "macro_larva_limit",
        "macro_wait_frames",
        "creep_interval_frames",
        "scout_fresh_frames",
        "scout_defense_memory_frames",
        "muta_min_workers",
        "muta_min_minerals",
        "muta_min_gas",
    ):
        parser.add_argument(
            "--" + field.replace("_", "-"), type=int, default=getattr(defaults, field)
        )
    parser.add_argument(
        "--scouting", action=argparse.BooleanOptionalAction, default=defaults.scouting
    )
    parser.add_argument(
        "--adaptive-economy",
        action=argparse.BooleanOptionalAction,
        default=defaults.adaptive_economy,
    )
    parser.add_argument(
        "--search-expansions",
        action=argparse.BooleanOptionalAction,
        default=defaults.search_expansions,
        help="Search visible-cleared map sites when known enemy structures are gone",
    )
    parser.add_argument(
        "--worker-defenders",
        type=int,
        default=defaults.worker_defenders,
        help="Experimental worker-defense squad; 0 disables",
    )
    parser.add_argument(
        "--regroup-roaches",
        type=int,
        default=defaults.regroup_roaches,
        help="Healthy-roach regroup threshold; 11 restores the old 12-unit trigger",
    )
    parser.add_argument(
        "--avoid-detected-burrow",
        action="store_true",
        help="Experimental visible detector/threat recovery avoidance",
    )
    parser.add_argument(
        "--burrow-escape-frames",
        type=int,
        default=defaults.burrow_escape_frames,
        help="Experimental escape after damage while hidden; 0 disables",
    )
    parser.add_argument(
        "--game-time-limit", type=int, default=None, help="Game seconds; bounded test"
    )
    parser.add_argument("--diagnostics-dir", type=Path, default=Path(".local-matches"))
    parser.add_argument("--no-diagnostics", action="store_true")
    parser.add_argument("--sample-frames", type=int, default=112)
    parser.add_argument("--max-events", type=int, default=10000)
    parser.add_argument(
        "--opening-supply", action=argparse.BooleanOptionalAction, default=defaults.opening_supply
    )
    parser.add_argument(
        "--queen-recovery", action=argparse.BooleanOptionalAction, default=defaults.queen_recovery
    )
    args = parser.parse_args()
    if not 0 <= args.seed < 2**32:
        parser.error("Seed must be in [0, 2**32)")
    if args.game_time_limit is not None and args.game_time_limit <= 0:
        parser.error("Game time limit must be positive")
    try:
        config = BotConfig(
            random_seed=args.seed,
            workers=args.workers,
            extra_queens=args.extra_queens,
            extra_queens_after_bases=args.extra_queens_after_bases,
            macro_hatches=args.macro_hatches,
            macro_after_bases=args.macro_after_bases,
            macro_min_workers=args.macro_min_workers,
            macro_min_minerals=args.macro_min_minerals,
            macro_larva_limit=args.macro_larva_limit,
            macro_wait_frames=args.macro_wait_frames,
            creep_interval_frames=args.creep_interval_frames,
            scout_fresh_frames=args.scout_fresh_frames,
            scout_defense_memory_frames=args.scout_defense_memory_frames,
            muta_min_workers=args.muta_min_workers,
            muta_min_minerals=args.muta_min_minerals,
            muta_min_gas=args.muta_min_gas,
            scouting=args.scouting,
            adaptive_economy=args.adaptive_economy,
            search_expansions=args.search_expansions,
            worker_defenders=args.worker_defenders,
            regroup_roaches=args.regroup_roaches,
            burrow_escape_frames=args.burrow_escape_frames,
            roach_tech=args.roach_tech,
            opening_supply=args.opening_supply,
            adaptive_army=args.adaptive_army,
            queen_tactical_micro=args.queen_tactical_micro,
            queen_recovery=args.queen_recovery,
            tech_min_workers=args.tech_min_workers,
            avoid_detected_burrow=args.avoid_detected_burrow,
        )
    except ValueError as error:
        parser.error(str(error))
    from sc2 import maps
    from sc2.data import Difficulty, Race
    from sc2.main import run_game
    from sc2.player import Bot, Computer

    from .bot import ZergBot
    from .diagnostics import DiagnosticConfig, MatchDiagnostics

    directory = args.diagnostics_dir / (
        datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    )
    recorder = MatchDiagnostics(
        directory,
        {
            "map": Path(args.map).stem,
            "difficulty": args.difficulty,
            "opponent_race": args.opponent,
            "seed": args.seed,
            "realtime": args.realtime,
            "game_limit_seconds": args.game_time_limit,
            "python": platform.python_version(),
            "burnysc2": version("burnysc2"),
            "bot_version": version("zergbot2"),
        },
        DiagnosticConfig(
            enabled=not args.no_diagnostics,
            sample_frames=args.sample_frames,
            max_events=args.max_events,
        ),
    )
    result = None
    termination, error_type = "incomplete", None
    try:
        if not args.no_diagnostics:
            directory.mkdir(parents=True, exist_ok=False)
            recorder.checkpoint(force=True)
            print(f"Diagnostics: {directory.resolve()}")
        result = run_game(
            maps.get(args.map),
            [
                Bot(
                    Race.Zerg,
                    ZergBot(config=config, diagnostics=recorder),
                ),
                Computer(Race[args.opponent], Difficulty[args.difficulty]),
            ],
            realtime=args.realtime,
            random_seed=args.seed,
            game_time_limit=args.game_time_limit,
            save_replay_as=str(directory / "match.SC2Replay") if not args.no_diagnostics else None,
        )
        termination = (
            "time_limit_or_tie"
            if result is not None and result.name == "Tie" and args.game_time_limit
            else "completed"
            if result is not None
            else "incomplete"
        )
    except BaseException as error:
        termination, error_type = "crashed_or_interrupted", type(error).__name__
        raise
    finally:
        recorder.finish(result.name if result is not None else None, termination, error_type)
    if recorder.error_type:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
