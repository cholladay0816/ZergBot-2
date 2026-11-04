"""Bounded live observation memory and advisory-only mutalisk feasibility."""

from dataclasses import dataclass
from math import dist

from sc2.ids.unit_typeid import UnitTypeId as U
from sc2.position import Point2

WORKERS = {U.SCV, U.PROBE, U.DRONE}
TOWNHALLS = {
    U.COMMANDCENTER,
    U.ORBITALCOMMAND,
    U.PLANETARYFORTRESS,
    U.NEXUS,
    U.HATCHERY,
    U.LAIR,
    U.HIVE,
}
# API weapon tables omit some special attacks. Treat these as risks, not harmless.
SPECIAL_AA = {U.BUNKER, U.WIDOWMINE, U.WIDOWMINEBURROWED, U.CARRIER, U.BATTLECRUISER, U.VOIDRAY}
MOBILE_COUNTERS = {
    U.PHOENIX,
    U.THOR,
    U.THORAP,
    U.ARCHON,
    U.CARRIER,
    U.BATTLECRUISER,
    U.CORRUPTOR,
    U.WIDOWMINE,
    U.WIDOWMINEBURROWED,
}


@dataclass
class SiteEvidence:
    position: tuple[float, float]
    last_full_frame: int = -1
    confirmation_frame: int = -1
    confirmations: int = 0
    workers: int = 0
    covered_now: bool = False

    def observe(self, frame, covered, workers, freshness):
        self.covered_now = covered
        if not covered:
            return
        if self.last_full_frame < 0 or frame - self.last_full_frame > freshness:
            self.confirmations = 0
            self.confirmation_frame = -1
        self.last_full_frame = frame
        self.workers = workers
        if self.confirmation_frame < 0 or frame - self.confirmation_frame >= 112:
            self.confirmations = min(2, self.confirmations + 1)
            self.confirmation_frame = frame


def assess_muta(
    site,
    *,
    frame,
    config,
    ready_bases,
    workers,
    minerals,
    gas,
    army,
    threatened,
    local_aa,
    mobile_counter,
):
    # A positive answer is a hypothesis for a future controlled transition, not an order.
    if site is None:
        return "unknown_no_mineral_line"
    if site.last_full_frame < 0 or frame - site.last_full_frame > config.scout_fresh_frames:
        return "unknown_stale_or_unseen"
    if not site.covered_now or site.confirmations < 2:
        return "unknown_incomplete_coverage"
    if local_aa or mobile_counter:
        return "blocked_known_anti_air"
    if site.workers < 6:
        return "blocked_low_worker_value"
    if threatened or army < config.defensive_roaches:
        return "blocked_home_defense"
    if (
        ready_bases < 2
        or workers < config.muta_min_workers
        or minerals < config.muta_min_minerals
        or gas < config.muta_min_gas
    ):
        return "blocked_economy_reserve"
    return "candidate_for_controlled_test_not_spend_authorization"


class ScoutManager:
    def __init__(self, config):
        self.config = config
        self.sites = {}  # at most 8 observed enemy townhall sites
        self.defenses = {}  # tag -> (frame, position, special mobile counter)
        self.scout_tag = None
        self.losses = 0
        self.retreat_until = 0
        self.last_report = None
        self.next_report = 0

    def destroyed(self, tag):
        self.defenses.pop(tag, None)
        if tag == self.scout_tag:
            self.scout_tag = None
            self.losses += 1

    def step(self, bot):
        if not self.config.scouting or bot.state.game_loop % 32:
            return
        frame = bot.state.game_loop
        enemies = [u for u in list(bot.enemy_units) + list(bot.enemy_structures) if u.is_visible]
        for unit in enemies:
            if unit.can_attack_air or unit.type_id in SPECIAL_AA:
                self.defenses[unit.tag] = (
                    frame,
                    tuple(unit.position),
                    unit.type_id in MOBILE_COUNTERS,
                )
            if unit.type_id in TOWNHALLS and unit.tag not in self.sites and len(self.sites) < 8:
                patches = bot.mineral_field.closer_than(10, unit)
                if patches:
                    self.sites[unit.tag] = SiteEvidence(tuple(patches.center))
        self.defenses = {
            tag: data
            for tag, data in self.defenses.items()
            if frame - data[0] <= self.config.scout_defense_memory_frames
        }
        if len(self.defenses) > 128:
            newest = sorted(self.defenses, key=lambda tag: self.defenses[tag][0], reverse=True)[
                :128
            ]
            self.defenses = {tag: self.defenses[tag] for tag in newest}
        for site in self.sites.values():
            x, y = site.position
            covered = all(
                bot.is_visible(Point2((x + dx, y + dy)))
                for dx, dy in [
                    (0, 0),
                    (-7, 0),
                    (7, 0),
                    (0, -7),
                    (0, 7),
                    (-5, -5),
                    (-5, 5),
                    (5, -5),
                    (5, 5),
                ]
            )
            workers = sum(
                u.type_id in WORKERS and u.distance_to(Point2(site.position)) < 12 for u in enemies
            )
            site.observe(frame, covered, workers, self.config.scout_fresh_frames)
        site = max(self.sites.values(), key=lambda s: (s.last_full_frame, s.workers), default=None)
        local = (
            sum(dist(data[1], site.position) < 20 for data in self.defenses.values()) if site else 0
        )
        mobile = any(data[2] for data in self.defenses.values())
        ready = [
            b
            for b in bot.townhalls.ready
            if any(b.distance_to(p) < 8 for p in bot.expansion_locations_list)
        ]
        threatened = any(
            u.can_attack_ground and any(u.distance_to(b) < 25 for b in ready) for u in enemies
        )
        verdict = assess_muta(
            site,
            frame=frame,
            config=self.config,
            ready_bases=len(ready),
            workers=bot.workers.amount,
            minerals=bot.minerals,
            gas=bot.vespene,
            army=bot.units.of_type({U.ROACH, U.ROACHBURROWED}).amount,
            threatened=threatened,
            local_aa=local,
            mobile_counter=mobile,
        )
        if bot.telemetry and (verdict != self.last_report or frame >= self.next_report):
            bot.telemetry.recorder.record(
                "muta_assessment",
                frame,
                verdict=verdict,
                advisory_only=True,
                target=list(site.position) if site else None,
                age_frames=frame - site.last_full_frame
                if site and site.last_full_frame >= 0
                else None,
                coverage=site.covered_now if site else False,
                confirmations=site.confirmations if site else 0,
                visible_workers=site.workers if site and site.covered_now else None,
                remembered_local_aa=local,
                remembered_mobile_counter=mobile,
                scope="live_observation_memory_not_omniscience",
            )
            self.last_report, self.next_report = verdict, frame + 224
        self.move_scout(bot, enemies, ready, frame)

    def move_scout(self, bot, enemies, bases, frame):
        if not bases or bot.time < 150 or self.losses >= 2:
            return
        overlords = bot.units(U.OVERLORD).ready
        if self.scout_tag is None:
            if len(bases) < 2 or len(overlords) < 2 or bot.supply_left < 8:
                return
            self.scout_tag = overlords.furthest_to(bot.start_location).tag
        scout = overlords.find_by_tag(self.scout_tag)
        if scout is None:
            self.scout_tag = None
            return
        danger = [
            u
            for u in enemies
            if (u.can_attack_air or u.type_id in SPECIAL_AA) and u.distance_to(scout) < 15
        ]
        if danger or scout.health_percentage < 0.75:
            self.retreat_until = frame + 672
        if frame < self.retreat_until:
            scout.move(min(bases, key=scout.distance_to).position)
            return
        target = (
            Point2(min(self.sites.values(), key=lambda s: s.last_full_frame).position)
            if self.sites
            else bot.enemy_start_locations[0]
        )
        if scout.distance_to(target) > 3:
            scout.move(target)
