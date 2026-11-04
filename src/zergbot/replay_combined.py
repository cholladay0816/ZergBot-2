"""Join exact replay frames from each player's own perspective, offline only."""

import json


def combine_passes(passes):
    by_player = {p["perspective"]: p for p in passes}
    if len(by_player) != len(passes) or set(by_player) != {1, 2}:
        raise ValueError("Require exactly player perspectives 1 and 2")
    first, second = by_player[1], by_player[2]
    for key in ("replay_sha256", "base_build", "data_version", "step_frames"):
        if not first.get(key) or first.get(key) != second.get(key):
            raise ValueError(f"Replay provenance mismatch or missing: {key}")
    indexed = {}
    for player, payload in by_player.items():
        indexed[player] = {}
        for sample in payload["samples"]:
            if sample["actual_player_id"] != player:
                raise ValueError("Actual player does not match requested perspective")
            if sample["frame"] in indexed[player]:
                raise ValueError("Duplicate frame in perspective")
            indexed[player][sample["frame"]] = sample
    frames = sorted(indexed[1].keys() | indexed[2].keys())
    samples = []
    for frame in frames:
        players = {}
        for player in (1, 2):
            source = indexed[player].get(frame)
            if source is None:
                players[str(player)] = None  # no interpolation across unseen/missing frames
                continue
            own = [u for u in source["units"] if u["alliance"] == 1 and u["owner"] == player]
            players[str(player)] = {
                "scope": "own_perspective_observation",
                "economy": source["economy"],
                "counts": source["own_counts"],
                "upgrade_ids": source["own_upgrade_ids"],
                "units": own,
                "own_unit_details_omitted": max(0, sum(source["own_counts"].values()) - len(own)),
                "visible_effects": source.get("effects", []),
                "sampled_actions_from_perspective": source.get("sampled_actions", []),
            }
        samples.append({"frame": frame, "game_seconds": frame / 22.4, "players": players})
    return {
        "schema_version": 1,
        "scope": "postgame_combined_own_perspectives_never_live_input",
        "replay_sha256": first["replay_sha256"],
        "base_build": first["base_build"],
        "data_version": first["data_version"],
        "step_frames": first["step_frames"],
        "perspective_terminations": {str(p): d["termination"] for p, d in by_player.items()},
        "limitations": "Own counts/economy from each player at exact sampled frames. "
        "Unit details are capped; missing frames remain null. Not a complete cast log "
        "or exact damage attribution. Effects from different perspectives may overlap.",
        "samples": samples,
    }


def write_combined(directory, passes):
    combined = combine_passes(passes)
    path = directory / "replay-combined.json"
    path.write_text(json.dumps(combined, indent=2, allow_nan=False), encoding="utf-8")
    report = directory / "replay-analysis-report.md"
    if report.exists():
        with report.open("a", encoding="utf-8") as stream:
            stream.write(
                "\nCombined exact-frame own perspectives: [replay-combined.json]"
                "(replay-combined.json). Missing player frames remain null.\n"
            )
    return path
