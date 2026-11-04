"""Small, bounded hatch-first opening reservation with visible-threat fallback."""

from dataclasses import dataclass


@dataclass
class HatchFirstOpening:
    target_workers: int = 16
    max_hold_frames: int = 672
    latest_frame: int = 2688
    started_frame: int | None = None
    done: bool = False
    aborted: bool = False

    def reserve(self, *, frame, workers, bases, threatened):
        if bases >= 2:
            self.done = True
        if self.done or self.aborted:
            return False
        if threatened or frame >= self.latest_frame:
            self.aborted = True
            return False
        if workers < self.target_workers:
            return False
        if self.started_frame is None:
            self.started_frame = frame
        if frame - self.started_frame >= self.max_hold_frames:
            self.aborted = True
            return False
        return True
