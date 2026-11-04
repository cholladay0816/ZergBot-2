# Ready-base defense experiment

The production code inspected at fc29564 considered army threats only within 25
of the first ready town hall. Economy already checked every ready town hall.
A natural or third attack could therefore request emergency production while
the army kept an offensive objective. This is a confirmed targeting inconsistency,
not proof that it caused the earlier forward army collapse.

The optional `--all-base-defense` candidate selects currently visible,
ground-capable ground threats near all ready bases. It preserves the existing
25-unit envelope and attack/regroup thresholds. It does not solve air-only
pressure or include hidden enemies. Small worker incursions retain bounded
worker-squad treatment when that existing option is enabled.

Simultaneous threats use deterministic base/target tags, a 112-frame base hold,
and a two-unit count margin before switching. Real combat pressure immediately
preempts a small worker incursion; vanished threats or destroyed bases release
the objective immediately. Count ranking is a heuristic, not combat-value scoring.
Recovery endpoints prefer an unthreatened base, without claiming that the path
or fog is safe. Existing high-priority recovery/morph vetoes remain authoritative.

The hypothesis is improved response to non-main attacks. Measure actual selected
base, first visible home pressure, base/worker losses and terminal outcome; a
longer defeat alone is not success. The new bounded `defense_objective` event is
recorded every 112 frames and tested through the real recorder and strict JSON.

Control: fc29564, existing hatch-first/adaptive/roach-tech options. Candidate:
same options plus all-base defense. Keep third-base reservation, siege spacing,
detector avoidance and worker-defense experiments disabled. Compare Harder
Terran seeds 1 and 2 at 1200 game / 300 wall seconds, sequentially under the
existing CPU, memory and protected-process guards. The feature stays off by
default pending results. Offline tests cover remote-base attacks, simultaneous
pressure, switching stability, disappeared threats/bases, worker handling,
recovery arbitration and the serialized event contract.
