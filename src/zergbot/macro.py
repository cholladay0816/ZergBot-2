"""Pure adaptive economy policies; map/resource observations stay in the adapter."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MacroState:
    bases: int
    ready_bases: int
    hatcheries: int
    workers: int
    worker_capacity: int
    minerals: int
    gas: int
    larvae: int
    threatened: bool


def worker_target(state, config):
    if not config.adaptive_economy:
        return min(config.workers, 22 * state.bases)
    # Only actual mineral/gas capacity and pending RESOURCE bases count.
    capacity = state.worker_capacity + 16 * max(0, state.bases - state.ready_bases)
    return min(config.workers, max(16, capacity))


def extractor_target(state, config):
    if not config.adaptive_economy:
        return 2 * state.bases
    if state.workers < 32 or state.gas > max(400, state.minerals * 1.5):
        return max(1, state.ready_bases)
    return 2 * state.ready_bases


def queen_target(state, config):
    extra = config.extra_queens if state.ready_bases >= config.extra_queens_after_bases else 0
    return state.hatcheries + extra


class MacroHatchGate:
    def __init__(self):
        self.limited_since = None

    def ready(self, state, config, frame, existing_macro, pending_hatchery):
        eligible = (
            existing_macro < config.macro_hatches
            and state.ready_bases >= config.macro_after_bases
            and state.workers >= config.macro_min_workers
            and state.minerals >= config.macro_min_minerals
            and state.larvae <= config.macro_larva_limit
            and not state.threatened
            and not pending_hatchery
        )
        if not eligible:
            self.limited_since = None
            return False
        if self.limited_since is None:
            self.limited_since = frame
        return frame - self.limited_since >= config.macro_wait_frames
