# Bounded third-base budget experiment

## Hypothesis registered before results

The two retained Terran opening-loss artifacts, `20261104T210636Z-b92a913f` and
`20261104T212058Z-871f92c7`, first sampled 44 workers on two bases without a pending
Hatchery at 325 and 310 seconds. All 20 and 42 such snapshots, respectively, had
less than 275 minerals. Third-base commands arrived at 424.643 and 505.714 seconds.
This supports a mineral-reservation gap; it does not establish that the gap caused
the defeats. Continuous discretionary production follows an affordability-only
expansion gate in the code.

The candidate preserves the existing expansion worker threshold, exactly two ready
resource bases, no pending Hatchery and a base limit allowing a third. It requires
at least the configured defensive reserve of healthy exposed roaches/hydras within
35 of a ready resource base, no observed ground-capable attackers within the existing
home-threat envelope, and no visible enemy structures within 25 of a ready base.
It holds only discretionary worker/roach spending for at most 224 frames (10 game
seconds), with a 672-frame cooldown after release. Supply, emergency production,
adaptive counters, queens and tech retain their existing priority. Pressure, lost
eligibility, placement failure or timeout releases the hold. Actual affordability
comes from installed game data through `can_afford`, not a hard-coded mineral cost.

The option is `--third-base-reserve`; its default remains false. This wave does not
change attack/regroup thresholds, multi-base army targeting, or detection avoidance.

## Frozen comparison

- Control: `cfaef3180a65e903f09ddc56384c2b88d5a27a48`.
- Candidate: `7a12d8745125836331cf7435d2ce7ce6ea067d85`.
- Both: Harder Terran, AbyssalReefLE, seeds 1 and 2, game step 4,
  `--opening-supply --hatch-first --adaptive-army --roach-tech`.
- Candidate alone adds `--third-base-reserve`.
- Sequential 1200-game-second / 300-wall-second bounds, below-normal priority,
  affinity CPUs 20-23, existing CPU/RAM/disk guards and protected SimTrader workloads.
- 229 offline tests and lint passed before launch. New reservation telemetry passes
  the real recorder allowlist and strict JSON serialization boundary.

Score command attempt, actual Hatchery foundation/completion, worker count and income,
army at first visible contact, and terminal result. Earlier expansion by itself is not
success. Keep capped, interrupted and defeated runs distinct. Limited paired samples
and observed variation under fixed seeds restrict any win-rate conclusion.
