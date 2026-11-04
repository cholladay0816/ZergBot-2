# Corrected tank-scenario scope and burrow timing

The requested splash-spacing case is friendly Zerglings/Banelings versus an enemy
Terran siege tank. The six later roach/tank/bio runs were a separate full-match-inspired
experiment. Their failure must not be used to reject the requested ling/bane policy.
Friendly and enemy units were not reversed; the earlier summary conflated scope.

The original `tank` scenario already uses 12 friendly lings and 4 banes against one
enemy sieged tank. Its earlier two-approach results were limited. This rerun freezes
1ea350b and compares grouped attacks against the existing 90-frame bounded split,
three approaches and seeds 1/2/3 plus 11/12/13. Each pair has identical units,
health, upgrades and placement; only controller changes. Normal fog remains.
Each run is bounded to 45 game / 120 wall seconds. Town halls remain, so a cap can
coexist with a destroyed tank; tank destruction is a scenario objective, not a match win.

## Additional roach hypothesis

A separate `burrow-tank` harness tests one roach against 1, 2 or 3 sieged tanks,
with actual Burrow research, an unresearched control, and optional Raven detection.
It supplies setup resources and a Pool, then uses the real Hatchery research action.
Actors spawn only after the upgrade appears in the owning player's observation.
No instant-research, cooldown or invulnerability cheat is used. The unresearched
case deliberately skips research. No competitive controller defaults change.

The roach initially holds in tank range. The existing production RoachAgent and
batched gateway handle health thresholds, burrow/recovery, morph protection and
unavailable-action retreat. It is a survival/latency test, not attack-move performance.
Tank own cooldown/order evidence is evaluator-only and never enters the roach policy.
The defender records actual HP, ability availability, observed orders, attempted
action, burrowed form and own death. Burrow is a command attempt until observed.
The default threshold is 40% and recovery threshold 80%; one observation every
four game loops is about 0.179 seconds. Delay and simultaneous impacts still matter.

Do not assume a researched burrow guarantees survival against detection, multiple
overlapping shots, splash from another target, unavailable actions or lethal damage
before the next observation. Measure these separately; this first targeted matrix
does not isolate splash onto an adjacent burrowed roach.

The new harness passed 255 offline tests plus lint/format before live execution.
Tests include real recorder allowlists/strict JSON, actual research readiness versus
submission, actor counts/ownership and unavailable research. Policies remain disabled
in the competitive bot pending appropriate evidence.
