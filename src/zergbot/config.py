from dataclasses import dataclass


@dataclass(frozen=True)
class BotConfig:
    burrow_health: float = 0.40
    emerge_health: float = 0.80
    retry_frames: int = 8
    morph_timeout_frames: int = 64
    workers: int = 44
    defensive_roaches: int = 6
    supply_buffer_min: int = 8
    supply_buffer_per_base: int = 4
    supply_buffer_max: int = 16
    expansion_retry_frames: int = 224
    attack_roaches: int = 12
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
                self.defensive_roaches,
                self.supply_buffer_min,
                self.supply_buffer_per_base,
                self.supply_buffer_max,
                self.expansion_retry_frames,
                self.attack_roaches,
                self.max_bases,
                self.game_step,
            )
            < 1
        ):
            raise ValueError("Counts and frame intervals must be positive")
        if not 0 <= self.random_seed < 2**32:
            raise ValueError("Seed must be a uint32")
        if self.supply_buffer_min > self.supply_buffer_max:
            raise ValueError("Supply buffer minimum must not exceed maximum")
