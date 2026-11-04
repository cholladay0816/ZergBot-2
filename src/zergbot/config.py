from dataclasses import dataclass


@dataclass(frozen=True)
class BotConfig:
    burrow_health: float = 0.40
    emerge_health: float = 0.80
    retry_frames: int = 8
    morph_timeout_frames: int = 64
    burrow_escape_frames: int = 0
    avoid_detected_burrow: bool = False
    queen_tactical_micro: bool = False
    queen_recovery: bool = False
    adaptive_army: bool = False
    roach_tech: bool = False
    opening_supply: bool = False
    hatch_first: bool = False
    opening_readiness: bool = False
    third_base_reserve: bool = False
    tech_min_workers: int = 32
    workers: int = 66
    defensive_roaches: int = 6
    supply_buffer_min: int = 8
    supply_buffer_per_base: int = 4
    supply_buffer_max: int = 16
    expansion_retry_frames: int = 224
    attack_roaches: int = 12
    regroup_roaches: int = 11
    worker_defenders: int = 0
    search_expansions: bool = True
    adaptive_economy: bool = True
    extra_queens: int = 2
    extra_queens_after_bases: int = 2
    macro_hatches: int = 1
    macro_after_bases: int = 3
    macro_min_workers: int = 50
    macro_min_minerals: int = 600
    macro_larva_limit: int = 3
    macro_wait_frames: int = 224
    creep_interval_frames: int = 32
    scouting: bool = True
    scout_fresh_frames: int = 448
    scout_defense_memory_frames: int = 2688
    muta_min_workers: int = 44
    muta_min_minerals: int = 600
    muta_min_gas: int = 600
    max_bases: int = 3
    game_step: int = 4
    random_seed: int = 1

    def __post_init__(self) -> None:
        if not 0 < self.burrow_health < self.emerge_health <= 1:
            raise ValueError("Require 0 < burrow_health < emerge_health <= 1")
        if (
            min(
                self.retry_frames,
                self.morph_timeout_frames,
                self.workers,
                self.tech_min_workers,
                self.defensive_roaches,
                self.supply_buffer_min,
                self.supply_buffer_per_base,
                self.supply_buffer_max,
                self.expansion_retry_frames,
                self.attack_roaches,
                self.regroup_roaches,
                self.max_bases,
                self.game_step,
            )
            < 1
        ):
            raise ValueError("Counts and frame intervals must be positive")
        if min(self.worker_defenders, self.burrow_escape_frames) < 0:
            raise ValueError("Experimental controls must be nonnegative; zero disables")
        if min(self.extra_queens, self.macro_hatches) < 0:
            raise ValueError("Extra production counts must be nonnegative")
        if (
            min(
                self.extra_queens_after_bases,
                self.macro_after_bases,
                self.macro_min_workers,
                self.macro_min_minerals,
                self.macro_larva_limit,
                self.macro_wait_frames,
                self.creep_interval_frames,
                self.scout_fresh_frames,
                self.scout_defense_memory_frames,
                self.muta_min_workers,
                self.muta_min_minerals,
                self.muta_min_gas,
            )
            < 1
        ):
            raise ValueError("Economy/scouting thresholds must be positive")
        if not 0 <= self.random_seed < 2**32:
            raise ValueError("Seed must be a uint32")
        if self.regroup_roaches >= self.attack_roaches:
            raise ValueError("Regroup threshold must be lower than attack threshold")
        if self.supply_buffer_min > self.supply_buffer_max:
            raise ValueError("Supply buffer minimum must not exceed maximum")
