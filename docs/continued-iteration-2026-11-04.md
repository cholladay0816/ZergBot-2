# Continued iteration: worker defense, Cannon setup and opening economy

The user extended iteration beyond the previous stopping point. Existing baseline and
all earlier experiments remain preserved; no new policy is described as optimal.

## Worker-defense duration wave

Hypothesis: the original ten-second worker pull expires while lings remain active.
In the earlier runs, many worker losses occurred after that deadline. Change only the
duration from 10 to 30 seconds, retaining six selected workers, the same queen controller,
low-health mineral-walk and normal visible observations. No production-bot integration.

Frozen corrected runtime: d3e09e2e9df4778d94aad64a02b1b35ebb8556a4.
The first 77e80bb run failed before a valid result because worker order AbilityId enums
were converted directly with int(). It is preserved as an incomplete software failure,
not a defeat. A regression with the actual SC2 enum now protects serialization.

Map Abyssal Reef, step 4, 90 game-second cap, 90 wall-second guard, normal fog;
approaches 0/1/2 use seeds 1/2/3 respectively. Both sides remain scripted adversaries.

| Approach/seed | Duration | Workers lost | Queen alive | Final minerals | Conflicting unit frames | Artifact |
|---|---:|---:|---|---:|---:|---|
| 0/1 | 10 | 7 | True | 385 | 0 | `scenario-20261104T203531Z-lings-micro0` |
| 0/1 | 30 | 2 | True | 780 | 0 | `scenario-20261104T203601Z-lings-micro0` |
| 1/2 | 10 | 6 | True | 430 | 0 | `scenario-20261104T203631Z-lings-micro1` |
| 1/2 | 30 | 3 | True | 700 | 0 | `scenario-20261104T203702Z-lings-micro1` |
| 2/3 | 10 | 3 | True | 675 | 0 | `scenario-20261104T203732Z-lings-micro2` |
| 2/3 | 30 | 5 | True | 550 | 0 | `scenario-20261104T203803Z-lings-micro2` |

Decision: **inconclusive; do not promote**. Losses change 7->2, 6->3 and 3->5.
The aggregate improves but one approach regresses. In that third pair, trajectories
already differ before ten seconds (the candidate loses workers at 6.52/7.95/9.38s,
baseline first loss 12.23s), before the changed duration can affect decisions.
This exposes run variability rather than proving that the duration caused every difference.
More paired repetitions are needed. Higher final mineral bank is a useful outcome here,
but it combines survival and mining interruption, not a normalized income measure.

## Cannon setup repair

Frozen runtime: c14be4bb3f839acf16ce533caf82c2d00c4c6c46. The previous harness searched
near the Zerg town hall, often on creep or outside actual Pylon power, and never issued
a Cannon build. The corrected harness queries a bounded 32-point neighborhood of the
actual completed Pylon, uses the game's placement response, and logs rejected/accepted
counts, construction progress, power, own cooldown and engaged target.

Live artifact: `scenario-20261104T203922Z-cannon-micro1` (seed 2, approach 1, 120-second cap).
At frame 539, six of 32 positions were legal; Probe issued the real Cannon build at
(153,32). At frame 1347 the Cannon was ready and powered, with cooldown 5.6289 and
engaged target queen tag 4354211841. Defender observed about 170.40 cumulative queen
HP loss and the queen died. All 12 workers survived. Both players reached the cap.

Decision: retain the harness correction, **not a successful defense claim**. This now
exercises a real Cannon/queen engagement. It does not yet demonstrate a complete worker-line
Cannon rush or optimized Probe/Pylon chains. The surviving workers are outside the proven
engagement, and exact per-hit damage attribution remains limited.

## Opening supply experiment

Baseline evidence from `20261104T201016Z-d6e6f8a5`: first new drone completes at 25s;
first two new Overlords complete at 25.9s and 48.4s; natural submitted at 121.25s.
The first Pool and Extractor appear by the 55s snapshot (presence, not completion).
First queen completes at 136.1s; two more around 238s. The opening supply buffer causes
the bot to save for an Overlord before spending its initial 50 minerals on a drone.

Frozen experiment: 137e5eea9abdbc1c5f97d2e52e1296b15f6783a1, optional `--opening-supply`.
On one ready base with supply cap at most 22, use a two-supply buffer: first drone, then
13-supply Overlord. Pending supply remains counted; normal multi-base/later buffering
resumes automatically. Existing Pool/gas/expansion/queen sequencing is unchanged, so this
is **not** a full hatch-first build. Defaults stay unchanged pending live comparison.
Six-minute Harder runs compare flag off/on for each race with matching seed 1. Their
caps are unresolved results used for economy measurements, not victories.

Current code checks: 190 offline tests and Ruff pass. All live runs remain sequential,
below-normal priority, CPUs 20-23, finite game/wall time, with resource guards. No changes
to SimTrader settings. Further results will append here with exact revision labels.
