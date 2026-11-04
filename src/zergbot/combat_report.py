"""Readable correlations from retained combat evidence, never exact damage attribution."""

from collections import Counter, defaultdict


def combat_lines(payload):
    buckets = defaultdict(
        lambda: {
            "damage": 0.0,
            "hits": 0,
            "ambiguous": 0,
            "no_candidate": 0,
            "types": Counter(),
            "ids": [],
        }
    )
    effects, buffs, cloak = Counter(), Counter(), Counter()
    for event in payload["events"]:
        if event["kind"] == "damage":
            bucket = buckets[int(event["game_seconds"] // 60)]
            bucket["damage"] += event["hp_shield_loss"]
            bucket["hits"] += 1
            candidates = event.get("candidate_attackers", [])
            bucket["ambiguous"] += len(candidates) > 1
            bucket["no_candidate"] += not candidates
            bucket["types"].update(c.get("type", "unknown") for c in candidates)
            if len(bucket["ids"]) < 6:
                bucket["ids"].append(event["id"])
        elif event["kind"] == "snapshot":
            # Counts are sampled appearances, not distinct units, casts or effects.
            effects.update(e["effect"] for e in event.get("effects", []))
            for unit in event.get("own", []) + event.get("visible_enemy", []):
                buffs.update(str(b) for b in unit.get("buff_ids", []))
                value = unit.get("cloak_raw")
                if value is not None:
                    cloak[str(value)] += 1
    lines = [
        "",
        "## Combat correlations (retained evidence)",
        "",
        "HP/shield loss includes non-combat sources; fatal-frame loss can be absent. "
        "Even one nearby candidate does not establish an attacker or spell caster. "
        "Detailed candidate distances, terrain differences, cloak and effects remain "
        "in the referenced JSON events.",
        "",
        "| Game minute | Observed HP/shield loss | Events | Multiple candidates | "
        "No visible candidate | Candidate types (appearances) | Evidence IDs |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for minute, b in sorted(buckets.items()):
        lines.append(
            f"| {minute} | {b['damage']:.1f} | {b['hits']} | {b['ambiguous']} | "
            f"{b['no_candidate']} | {dict(b['types'])} | {b['ids']} |"
        )
    unavailable = "unavailable in older artifact"
    decisions = payload.get("decision_change_counts", unavailable)
    destructions = payload.get("destruction_observation_counts", unavailable)
    lines += [
        "",
        f"Visible effect sampled appearances: {dict(effects)}.",
        f"Buff ID sampled appearances: {dict(buffs)}.",
        f"Raw protocol cloak-state sampled appearances: {dict(cloak)}. "
        "These are enum values, not inferred detection outcomes.",
        "",
        f"Lifetime recorded decision changes: {decisions}.",
        f"Lifetime destruction observations: {destructions}. "
        "Unknown scope remains unknown; morphing/consumed units "
        "are not automatically combat losses.",
    ]
    return lines


def action_error_description(event, deaths):
    from s2clientprotocol.error_pb2 import ActionResult
    from sc2.ids.ability_id import AbilityId

    try:
        ability = AbilityId(event["ability_id"]).name
    except ValueError:
        ability = "unknown"
    try:
        result = ActionResult.Name(event["result"])
    except ValueError:
        result = "unknown"
    line = (
        f"- Event {event['id']} at {event['game_seconds']:.2f}s: "
        f"unit {event['tag']}, ability {event['ability_id']} ({ability}), "
        f"SC2 result {event['result']} ({result})."
    )
    evidence = deaths.get((event["frame"], event["tag"]))
    if evidence is not None:
        line += (
            f" Same-tag destruction was observed in the same frame (event {evidence}); "
            "this is a correlation, not proof of rejection cause."
        )
    return line
