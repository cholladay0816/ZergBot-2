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


class OpeningBudget:
    """One bounded reservation per opening stage; observations close each stage."""

    def __init__(self, hold_frames=448):
        self.hold_frames = hold_frames
        self.started = {}
        self.closed = set()

    def reserve(self, stage, *, frame, needed, eligible, latest_frame):
        if not needed or frame >= latest_frame:
            self.closed.add(stage)
        if stage in self.closed or not eligible:
            return False
        self.started.setdefault(stage, frame)
        if frame - self.started[stage] >= self.hold_frames:
            self.closed.add(stage)
            return False
        return True


class ThirdBaseBudget:
    """Short mineral hold with release/cooldown; never reserves through pressure."""

    def __init__(self, hold_frames=224, cooldown_frames=672):
        self.hold_frames = hold_frames
        self.cooldown_frames = cooldown_frames
        self.started = None
        self.next_frame = 0
        self.reason = "idle"

    def release(self, frame, reason):
        self.started = None
        self.next_frame = frame + self.cooldown_frames
        self.reason = reason

    def reserve(self, *, frame, needed, eligible, safe):
        if not needed:
            self.started = None
            self.reason = "not_needed"
            return False
        if not eligible or not safe:
            if self.started is not None:
                self.release(frame, "unsafe" if not safe else "ineligible")
            return False
        if frame < self.next_frame:
            return False
        if self.started is None:
            self.started = frame
            self.reason = "holding"
        if frame - self.started >= self.hold_frames:
            self.release(frame, "timeout")
            return False
        return True
