import argparse


def main() -> None:
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
    args = parser.parse_args()
    from sc2 import maps
    from sc2.data import Difficulty, Race
    from sc2.main import run_game
    from sc2.player import Bot, Computer

    from .bot import ZergBot

    run_game(
        maps.get(args.map),
        [Bot(Race.Zerg, ZergBot()), Computer(Race.Terran, Difficulty[args.difficulty])],
        realtime=args.realtime,
    )


if __name__ == "__main__":
    main()
