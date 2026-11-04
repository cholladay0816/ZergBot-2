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
        "--difficulty", choices=["Easy", "Medium", "Hard", "Harder"], default="Hard"
    )
    parser.add_argument("--seed", type=int, default=1)
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
    args = parser.parse_args()
    if not 0 <= args.seed < 2**32:
        parser.error("Seed must be in [0, 2**32)")
    if args.game_time_limit is not None and args.game_time_limit <= 0:
        parser.error("Game time limit must be positive")
    try:
        config = BotConfig(
            random_seed=args.seed,
            worker_defenders=args.worker_defenders,
            regroup_roaches=args.regroup_roaches,
            burrow_escape_frames=args.burrow_escape_frames,
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
                Computer(Race.Terran, Difficulty[args.difficulty]),
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
