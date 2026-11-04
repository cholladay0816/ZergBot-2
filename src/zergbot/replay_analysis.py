"""Separate bounded post-game replay passes; never imported by competitive decisions."""

import argparse
import asyncio
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from s2clientprotocol import sc2api_pb2 as api
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import get_replay_version
from sc2.sc2process import SC2Process

from .telemetry import field


def unit_name(value):
    try:
        member = UnitTypeId(value)
        return member.name if member.value == value else f"UNKNOWN_TYPE_{value}"
    except ValueError:
        return f"UNKNOWN_TYPE_{value}"


def replay_snapshot(response, perspective, cap=192):
    observation = response.observation
    # Visible display type only, even with fog disabled; absent fields stay unknown.
    units = [u for u in observation.raw_data.units if u.display_type == 1 and u.alliance in (1, 4)]
    selected = sorted(units, key=lambda u: (u.alliance != 1, u.tag))[:cap]
    detail = []
    for unit in selected:
        own = unit.alliance == 1
        detail.append(
            {
                "tag": unit.tag,
                "type": unit_name(unit.unit_type),
                "owner": unit.owner,
                "alliance": unit.alliance,
                "position": [unit.pos.x, unit.pos.y, unit.pos.z],
                "health": field(unit, "health"),
                "shield": field(unit, "shield"),
                "energy": field(unit, "energy"),
                "cloak_raw": field(unit, "cloak"),
                "buff_ids": list(unit.buff_ids)[:16],
                "build_progress": field(unit, "build_progress"),
                "weapon_cooldown": field(unit, "weapon_cooldown") if own else None,
                "engaged_target_tag": field(unit, "engaged_target_tag") if own else None,
                "orders": [
                    {"ability_id": o.ability_id, "target_tag": field(o, "target_unit_tag")}
                    for o in unit.orders[:4]
                ]
                if own
                else None,
            }
        )
    common = observation.player_common
    return {
        "frame": observation.game_loop,
        "game_seconds": observation.game_loop / 22.4,
        "perspective": perspective,
        "actual_player_id": common.player_id,
        "economy": {
            name: field(common, name)
            for name in [
                "minerals",
                "vespene",
                "food_cap",
                "food_used",
                "food_army",
                "food_workers",
                "idle_worker_count",
                "army_count",
            ]
        },
        "economy_score": {
            name: field(observation.score.score_details, name)
            for name in (
                "collected_minerals",
                "collected_vespene",
                "spent_minerals",
                "spent_vespene",
                "collection_rate_minerals",
                "collection_rate_vespene",
            )
        },
        "own_counts": dict(Counter(unit_name(u.unit_type) for u in units if u.alliance == 1)),
        "visible_opponent_counts": dict(
            Counter(unit_name(u.unit_type) for u in units if u.alliance == 4)
        ),
        "own_upgrade_ids": list(observation.raw_data.player.upgrade_ids),
        "units": detail,
        "units_omitted": max(0, len(units) - cap),
        "effects": [
            {
                "effect_id": e.effect_id,
                "owner": e.owner,
                "radius": e.radius,
                "positions": [[p.x, p.y] for p in e.pos[:8]],
                "caster_tag": None,
            }
            for e in observation.raw_data.effects[:32]
        ],
        "observed_death_tags": list(observation.raw_data.event.dead_units)[:192],
        "sampled_actions": [
            {
                "ability_id": a.action_raw.unit_command.ability_id,
                "unit_tags": list(a.action_raw.unit_command.unit_tags)[:64],
            }
            for a in response.actions[:64]
            if a.HasField("action_raw") and a.action_raw.HasField("unit_command")
        ],
    }


async def perspective_pass(replay, perspective, step_frames, max_samples):
    base_build, data_version = get_replay_version(replay)
    payload = {
        "schema_version": 2,
        "scope": "postgame_player_perspective",
        "disable_fog_requested": True,
        "replay_sha256": hashlib.sha256(replay.read_bytes()).hexdigest(),
        "perspective": perspective,
        "base_build": base_build,
        "data_version": data_version,
        "step_frames": step_frames,
        "max_samples": max_samples,
        "termination": "incomplete",
        "samples": [],
    }
    output = replay.parent / f"replay-perspective-{perspective}.json"
    start = time.perf_counter()
    try:
        async with SC2Process(base_build=base_build, data_hash=data_version) as server:
            result = await server._execute(
                start_replay=api.RequestStartReplay(
                    replay_path=str(replay),
                    observed_player_id=perspective,
                    realtime=False,
                    disable_fog=True,
                    options=api.InterfaceOptions(raw=True, score=True, show_cloaked=True),
                )
            )
            if result.start_replay.HasField("error"):
                raise RuntimeError("Replay start rejected")
            for _ in range(max_samples):
                response = await server._execute(observation=api.RequestObservation())
                if response.observation.HasField("observation"):
                    payload["samples"].append(replay_snapshot(response.observation, perspective))
                if response.observation.player_result or response.status == api.ended:
                    payload["termination"] = "completed"
                    break
                await server._execute(step=api.RequestStep(count=step_frames))
            else:
                payload["termination"] = "sample_limit"
            await server.quit()
    except BaseException as error:
        payload["termination"] = "interrupted_or_failed"
        payload["error_type"] = type(error).__name__
        raise
    finally:
        payload["wall_seconds"] = time.perf_counter() - start
        temporary = output.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
        temporary.replace(output)
    return payload


def comparative_report(directory, passes):
    lines = [
        "# Post-game replay analysis",
        "",
        "These are separate player-perspective replay observations, never live bot inputs. "
        "Disabling fog was requested, but the tested SC2 raw API still limited enemy entries "
        "to visibility. Each player's private economy/orders and full own counts are read "
        "in that player's own perspective; paired own observations provide the fuller view. "
        "Missing fields remain unknown. Sampling is not a complete spell/action log, and "
        "this does not establish exact damage causation. Unit z-position is not terrain height.",
        "",
    ]
    for payload in passes:
        lines += [
            f"## Player {payload['perspective']}",
            "",
            "| Game seconds | Player | Minerals | Gas | Workers supply | Army supply |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        previous_bucket = -1
        for sample in payload["samples"]:
            bucket = int(sample["game_seconds"] // 60)
            if bucket == previous_bucket:
                continue
            previous_bucket = bucket
            economy = sample["economy"]
            lines.append(
                f"| {sample['game_seconds']:.1f} | {payload['perspective']} | "
                f"{economy['minerals']} | {economy['vespene']} | {economy['food_workers']} | "
                f"{economy['food_army']} |"
            )
        lines += [
            "",
            f"Player {payload['perspective']}: {payload['termination']}; "
            f"{len(payload['samples'])} samples. "
            f"Source: replay-perspective-{payload['perspective']}.json.",
            "",
        ]
    lines += [
        "Review matched frame numbers against match.json decision/damage events and the replay. "
        "Compare production, supply and resources before attributing a defeat to micro alone."
    ]
    (directory / "replay-analysis-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument(
        "--player", type=int, choices=(1, 2), help="Analyze one requested player perspective"
    )
    parser.add_argument("--step-frames", type=int, default=112)
    parser.add_argument("--max-samples", type=int, default=1000)
    parser.add_argument("--wall-timeout", type=float, default=180)
    args = parser.parse_args()
    if min(args.step_frames, args.max_samples, args.wall_timeout) <= 0:
        parser.error("Limits must be positive")
    replay = args.replay.resolve(strict=True)

    async def run():
        passes = []
        for player in (args.player,) if args.player is not None else (1, 2):
            passes.append(
                await perspective_pass(replay, player, args.step_frames, args.max_samples)
            )
        comparative_report(replay.parent, passes)
        from .replay_combined import write_combined

        write_combined(replay.parent, passes)

    asyncio.run(asyncio.wait_for(run(), timeout=args.wall_timeout))
    print(replay.parent / "replay-analysis-report.md")


if __name__ == "__main__":
    main()
