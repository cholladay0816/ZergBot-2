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

At the Cannon-setup checkpoint: 190 offline tests and Ruff passed. All live runs remain sequential,
below-normal priority, CPUs 20-23, finite game/wall time, with resource guards. No changes
to SimTrader settings. Further results will append here with exact revision labels.

## Completed opening-supply comparisons

Baseline and buffer-2 runtime 137e5ee; refined buffer-4 runtime fd8a1fc. All other
production policy flags retain defaults (adaptive army/roach tech/queen recovery off).
Each race uses seed 1, Harder, 360 game seconds, 180 wall-second guard and step 4.
All nine runs reached unresolved caps; none is counted as a win. Supply-block samples
are five-second observations through 180 seconds, not exact blocked duration.

| Race | Variant | First drone complete | Natural submitted | Workers 4m/6m | Roaches 6m | Blocked samples / early samples |
|---|---|---:|---:|---|---:|---|
| Terran | baseline | 25.0 | 121.25 | 25/44 | 17 | 2/37 |
| Terran | buffer2 | 12.143 | 90.714 | 29/44 | 20 | 8/37 |
| Protoss | baseline | 25.0 | 121.071 | 25/51 | 13 | 2/37 |
| Protoss | buffer2 | 12.143 | 89.286 | 29/46 | 21 | 8/37 |
| Zerg | baseline | 25.0 | 124.107 | 26/44 | 17 | 2/37 |
| Zerg | buffer2 | 12.143 | 90.179 | 26/48 | 16 | 8/37 |
| Terran | refined-buffer4 | 12.143 | 90.714 | 26/44 | 18 | 3/37 |
| Protoss | refined-buffer4 | 12.143 | 121.607 | 29/53 | 12 | 3/37 |
| Zerg | refined-buffer4 | 12.143 | 90.179 | 26/44 | 18 | 3/37 |

The first-drone delay is fixed in both candidates, but later economy results are mixed.
Buffer 2 improves early worker counts while causing a two-minute supply block. Buffer 4
restores more lead time, with matchup/run variation still present. Neither is promoted
from capped economy probes alone. The next isolated hatch-first reservation tests the
late natural directly, retaining this refined supply rule and emergency fallbacks.

Evidence (full settings/comparison metrics in `.local-matches/phase4-opening-comparisons.json`):
- `20261104T204008Z-dc949d52` (137e5ee-opening-Terran-False), match JSON SHA256 `39a613a818a3c6347b08d56b7560a84aa3805cccf869d040d231dbb3e8014aad`.
- `20261104T204103Z-593d146c` (137e5ee-opening-Terran-True), match JSON SHA256 `2b4585bc6eb1b0f3411344b14276589f1f82efa94451087a3d6f4966c4fffc2d`.
- `20261104T204157Z-61d3be67` (137e5ee-opening-Protoss-False), match JSON SHA256 `7ba61b49d9c4b7dc472cba38e7637bf6bc45e886afe0737791ed30d1cf7fcd37`.
- `20261104T204252Z-acb55c25` (137e5ee-opening-Protoss-True), match JSON SHA256 `d9f837ebaec1af9af487b0dc32e6e027931045f7a56bbef102ef9b829696fd2b`.
- `20261104T204344Z-2be1ab6d` (137e5ee-opening-Zerg-False), match JSON SHA256 `5246a5a52f6bd4c0bcbb6a4a7fc55bb0ec79dd43095a9362eb01f529e9e985f7`.
- `20261104T204437Z-56565ae2` (137e5ee-opening-Zerg-True), match JSON SHA256 `a8e684263b60c96b6fcfaf132b7c4fc5091825d191b4df68f4fcf998f909a96d`.
- `20261104T205014Z-b8a59f41` (fd8a1fc-opening-refined-Terran), match JSON SHA256 `624f18f5b49ad67a3e21e4dc1fccafdeeb42fc3771d7942e59ed6f97d0566c1d`.
- `20261104T205109Z-6a3f6666` (fd8a1fc-opening-refined-Protoss), match JSON SHA256 `856cb8d5c75f7c4b3977833bc7d65406be4e1709c03264f5565bf42b9bae7a72`.
- `20261104T205203Z-5be96f7e` (fd8a1fc-opening-refined-Zerg), match JSON SHA256 `6dc12ca1540eba3917aa048ccfcfb19afe8e3b96c6f77051a561c3e1d4c80d16`.

## Queen recovery comparison

Frozen runtime 788407f634f35177f74745c1aa993d5f3724f227. Same repaired real-Probe
Cannon scenario, micro queen controller, seeds 1/2/3 and approaches 0/1/2, 120-second cap.
Only `--queen-recovery` changes. The baseline trace resumed ATTACK at about seven HP
after moving beyond the old direct-threat radius. The optional controller retains recovery
state by queen tag below 30% HP until 60% recovery, chooses pathable points outside
observed weapon ranges, and prunes dead tags. No enemy cooldown information is used.

| Approach/seed | Recovery | Queen survived | Final queen HP | Workers lost | Observed queen HP loss | Command conflicts |
|---|---|---|---:|---:|---:|---:|
| 0/1 | False | False | 0.00 | 0 | 170.42 | 0 |
| 0/1 | True | True | 64.66 | 0 | 132.56 | 0 |
| 1/2 | False | False | 0.00 | 0 | 170.45 | 0 |
| 1/2 | True | True | 46.48 | 0 | 151.49 | 0 |
| 2/3 | False | False | 0.00 | 0 | 170.40 | 0 |
| 2/3 | True | True | 64.61 | 0 | 132.54 | 0 |

All three baseline queens died; all recovery queens survived. Both sides retained all
workers. These are capped engagements, not match victories or successful Cannon removal:
the completed Cannon remains. The improvement supports the specific critical-retreat
fix, not an assertion that a lone queen can win the duel. Recovery remains optional until
tested against mobile worker pressure and in complete matches, including inject impacts.
Full index and hashes: `.local-matches/phase4-queen-recovery-comparisons.json`.
- `scenario-20261104T204627Z-cannon-micro0` recovery=False.
- `scenario-20261104T204659Z-cannon-micro0` recovery=True.
- `scenario-20261104T204732Z-cannon-micro1` recovery=False.
- `scenario-20261104T204802Z-cannon-micro1` recovery=True.
- `scenario-20261104T204834Z-cannon-micro2` recovery=False.
- `scenario-20261104T204907Z-cannon-micro2` recovery=True.

## Mineral-side Reaper pressure

Frozen runtime be9b2a2c1f0b8d3e360840669bb6ab554a172e91. New optional mineral-side
debug ingress puts the Reaper behind/alongside the worker pocket rather than only at
the front of the queen. Setup refuses an invalid pathing point instead of silently
claiming a valid test. All three controllers face the same opportunity-scored attacker:
own ability readiness/range checks, current visible worker/queen coverage, a bounded
half-second motion estimate, own-cooldown kiting and health retreat/re-engagement.
No unseen enemy orders/cooldowns enter either policy. 90-second caps, step 4, seeds 1/2/3.

| Approach | Controller | Recovery | Workers lost | Worker HP loss | Lowest-HP worker selections / worker attack decisions | Injured-worker attack decisions | KD8 attempts / observed | Final minerals |
|---|---|---|---:|---:|---|---:|---|---:|
| 0 | baseline | False | 1 | 154.4 | 26/26 | 25 | 3/2 | 1000 |
| 0 | micro | False | 0 | 115.1 | 12/12 | 12 | 3/3 | 985 |
| 0 | micro | True | 0 | 114.7 | 12/12 | 12 | 3/3 | 975 |
| 1 | baseline | False | 0 | 114.6 | 13/13 | 13 | 2/2 | 965 |
| 1 | micro | False | 0 | 122.7 | 13/13 | 13 | 3/3 | 970 |
| 1 | micro | True | 0 | 131.2 | 14/14 | 14 | 3/3 | 980 |
| 2 | baseline | False | 0 | 114.9 | 13/13 | 13 | 3/3 | 975 |
| 2 | micro | False | 3 | 310.8 | 105/105 | 99 | 4/4 | 980 |
| 2 | micro | True | 0 | 118.9 | 13/13 | 13 | 3/3 | 990 |

The attacker now has actual worker-access opportunities and casts at worker clusters;
the baseline loses one worker on approach 0, and micro without recovery loses three on
approach 2. Reaper and queen survive every capped run. This is meaningful pressure but
does not establish optimal adversarial play. Grenade attempts remain distinct from
defender-observed episodes; absent confirmation is not counted as a successful cast/hit.
HP-loss counters and final unspent bank are observations, not exact damage attribution
or normalized mining efficiency.

Crucially, minimum sampled queen HP exceeds 118 in every run, above the 52.5-HP recovery
trigger. The zero-loss recovery-enabled group cannot be credited to a recovery action
that was never needed. Differences between equivalent effective controllers expose run
variability. The queen-micro policy is not promoted from this set.

### Setup synchronization

The installed library runs both BotAI participants concurrently. Checkpoint
1e38b08ee6382c6447cc868fff84d878d259c806 adds a two-player setup-ready barrier with a
15-wall-second timeout and explicit Python/NumPy seeding before the first game step.
Only readiness is shared; no hidden unit state enters decisions. Unit regression confirms
neither participant passes the barrier alone. Live pilot
`scenario-20261104T210528Z-reaper-micro2` records setup-ready at frame 0 for both players,
completes the cap with zero worker losses and three attempts/three observed charges.
This single pilot validates operation, **not bit-for-bit repeatability**. Subsequent
replicates must remain separately labeled from the asynchronous-setup results above.

Full per-run evidence/hashes: `.local-matches/phase4-reaper-ingress-comparisons.json`.
- `scenario-20261104T205445Z-reaper-baseline0`: Reaper movement during own cooldown observed 40 times; worker-targeted grenade attempts 2.
- `scenario-20261104T205515Z-reaper-micro0`: Reaper movement during own cooldown observed 66 times; worker-targeted grenade attempts 1.
- `scenario-20261104T205545Z-reaper-micro0`: Reaper movement during own cooldown observed 76 times; worker-targeted grenade attempts 1.
- `scenario-20261104T205616Z-reaper-baseline1`: Reaper movement during own cooldown observed 36 times; worker-targeted grenade attempts 1.
- `scenario-20261104T205646Z-reaper-micro1`: Reaper movement during own cooldown observed 73 times; worker-targeted grenade attempts 1.
- `scenario-20261104T205716Z-reaper-micro1`: Reaper movement during own cooldown observed 84 times; worker-targeted grenade attempts 1.
- `scenario-20261104T205745Z-reaper-baseline2`: Reaper movement during own cooldown observed 66 times; worker-targeted grenade attempts 1.
- `scenario-20261104T205815Z-reaper-micro2`: Reaper movement during own cooldown observed 67 times; worker-targeted grenade attempts 3.
- `scenario-20261104T205843Z-reaper-micro2`: Reaper movement during own cooldown observed 87 times; worker-targeted grenade attempts 1.
