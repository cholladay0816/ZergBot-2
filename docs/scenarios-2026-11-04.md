# Controlled micro scenarios - November 4, 2026

These are isolated debug-setup experiments with normal fog, two actual BotAI players,
step 4, fixed seeds and finite game limits. Original town halls remain; no invulnerability,
no-cooldown or reveal-map cheats. Setup/scoring knowledge never enters defender decisions.
Reaper/ling/cannon runs last at most 90 game seconds; tank runs 45. A cap is not a victory.
All runs are sequential, below-normal priority and limited to CPUs 20-23 by the local supervisor.

The first 14-case paired batch uses frozen 02eb55f. A separately labeled 738eab5 rerun
changes only elapsed-frame telemetry scheduling: exact frame divisibility had omitted
tank spacing and construction snapshots on offset game frames. Do not infer missing
observations from the first batch. The earlier 979503f Reaper pilot exposed blocked
retreat paths and is excluded from controller comparisons; 02eb55f added pathable escape
choices and a bounded stop fallback.

## Reaper: three paired approaches

The same attacker controller faces both queen controllers. It queries its own cooldown
and KD8 availability, chooses low-health in-range workers when accessible, kites between
shots, retreats below 55% health and returns above 90%. Grenades use a bounded half-second
visible-motion estimate and legal range checks. The defender sees only ordinary visible
positions/effects and its own cooldown. KD8 is the installed library's `KD8CHARGE` fake effect.

| Approach/seed | Queen controller | Worker losses | Queen observed HP loss | Reaper observed HP loss | Observed charges | Reaper moving during own cooldown (observations) | Final mineral bank |
|---|---|---:|---:|---:|---:|---:|---:|
| 0/1 | baseline | 0 | 120.36 | 120.00 | 4 | 78 | 1020 |
| 0/1 | micro | 0 | 118.03 | 92.00 | 4 | 89 | 1020 |
| 1/2 | baseline | 0 | 102.36 | 124.00 | 4 | 74 | 1020 |
| 1/2 | micro | 0 | 115.09 | 88.00 | 4 | 91 | 1020 |
| 2/3 | baseline | 0 | 117.38 | 112.00 | 4 | 77 | 1020 |
| 2/3 | micro | 0 | 109.63 | 92.00 | 3 | 77 | 1020 |

All six runs preserved 12 workers and both combatants survived; four grenade attempts
were matched by four observed charge episodes per run. No conflicting per-unit command
frames were recorded. The optional queen micro did less Reaper damage in all three pairs
and worsened queen damage in one. It is **not promoted**. The Reaper repeatedly retreats
and re-engages; this is stronger than a stationary target but does not establish optimality.
No worker kills or worker HP damage occurred, so low-HP worker execution was not meaningfully
exercised. The attacker prefers a visible queen for grenades: optimal worker-cluster grenade
selection has not been demonstrated. Final mineral bank was 1020 in every Reaper run.
Idle/gather-order counts are only proxies: knockback can preserve a gathering order.
Bank equality is useful here because no defender spending occurs, but it does not prove
identical mining timing or quantify every knockback delay. Damage counters are observed
HP decreases, not exact attributed attacks; regeneration can make cumulative damage exceed HP.

## Rush and splash cases

| Revision | Scenario | Approach/seed | Controller | Workers lost | Surviving lings/banes | Enemy units remaining | Pylon/Cannon attempts |
|---|---|---|---|---:|---|---|---|
| 02eb55f | lings | 1/2 | baseline | 12 | 0/0 | {'LARVA': 3, 'ZERGLING': 6, 'OVERLORD': 1} | 0/0 |
| 02eb55f | lings | 1/2 | micro | 12 | 0/0 | {'OVERLORD': 1, 'ZERGLING': 3, 'LARVA': 3} | 0/0 |
| 02eb55f | cannon | 1/2 | baseline | 0 | 0/0 | {} | 2/0 |
| 02eb55f | cannon | 1/2 | micro | 0 | 0/0 | {'PROBE': 1} | 2/0 |
| 02eb55f | tank | 0/1 | baseline | 0 | 7/0 | {} | 0/0 |
| 02eb55f | tank | 0/1 | micro | 0 | 7/0 | {} | 0/0 |
| 02eb55f | tank | 2/3 | baseline | 0 | 7/0 | {} | 0/0 |
| 02eb55f | tank | 2/3 | micro | 0 | 8/1 | {} | 0/0 |
| 738eab5 | cannon | 1/2 | baseline | 0 | 0/0 | {} | 2/0 |
| 738eab5 | cannon | 1/2 | micro | 0 | 0/0 | {'PROBE': 1} | 2/0 |
| 738eab5 | tank | 0/1 | baseline | 0 | 7/0 | {} | 0/0 |
| 738eab5 | tank | 0/1 | micro | 0 | 9/1 | {} | 0/0 |
| 738eab5 | tank | 2/3 | baseline | 0 | 7/1 | {} | 0/0 |
| 738eab5 | tank | 2/3 | micro | 0 | 9/3 | {} | 0/0 |

Six lings killed all 12 workers and the queen in both initial controllers. Micro killed
three lings versus none for baseline, but that is still a failed defense, not success.
The harness has one queen and no production reinforcements or worker surround controller;
it exposes that limitation rather than measuring a complete rush build response.

Cannon setup supplies a Forge and resources, then a real Probe attempts actual Pylon
construction and a powered Cannon. In the first pair Pylons took observed damage and
no Cannon command was attempted. This tests contested Pylon denial only, **not a validated
Cannon attack**. Surviving Probe in the micro case is not a demonstrated rush defeat.

Tank setup uses 12 lings and four banes against one sieged tank. Both controllers kill
the tank in all initial runs; splitting has a 90-frame engagement deadline, so indefinite
scattering cannot count as success. At approach 0 both retain seven lings/no banes;
at approach 2 baseline retains seven lings/no banes, micro eight lings/one bane. The latter
also allows about 69 observed Hatchery HP loss, a real tradeoff. Baneling disappearance
may be self-detonation, not a tank kill. No exact per-shell attribution is claimed.

### Corrected spacing/construction observations

- scenario-20261104T202331Z-cannon-baseline1: 12 construction samples; max observed Pylon progress 1.0, Cannon progress None.
- scenario-20261104T202401Z-cannon-micro1: 18 construction samples; max observed Pylon progress 1.0, Cannon progress None.
- scenario-20261104T202431Z-tank-baseline0: 5 engagement-window samples, mean nearest-neighbor distance 0.7300140077390193.
- scenario-20261104T202458Z-tank-micro0: 5 engagement-window samples, mean nearest-neighbor distance 1.7641195537424672.
- scenario-20261104T202524Z-tank-baseline2: 5 engagement-window samples, mean nearest-neighbor distance 0.7241484985715964.
- scenario-20261104T202553Z-tank-micro2: 5 engagement-window samples, mean nearest-neighbor distance 1.5023861718360092.

The corrected Cannon samples show completed Pylons but still no Cannon attempts or
observed Cannon progress. The setup never exercised a Cannon attack; placement/approach
needs correction in a later wave. No exact failure cause is asserted without placement
query telemetry.

## Reproduction and evidence

```powershell
.\.venv\Scripts\python.exe -m zergbot.scenarios --scenario reaper --controller micro --approach 1 --seed 2 --game-time-limit 90
```

Use the bounded supervisor for resource protection. Other scenario values: `lings`,
`cannon`, `tank`; controller `baseline` or `micro`; approaches 0/1/2. The tank policy is
scenario-only, not deployed to the competitive army. Every directory below contains
settings, both players' visibility-scoped JSON and the replay. Full artifacts stay local.
Repeated Burny connection-closed cleanup warnings after both results/replay writes are
not counted as gameplay failures; supervisor exit status and preserved terminations matter.

- `scenario-20261104T200148Z-reaper-baseline0` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `db703b48aadc48bf6a87c6ae7a2938e80e6cb39d6aa88e862cab8f7decdead03`.
- `scenario-20261104T200218Z-reaper-micro0` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `438faa2a8cd4ef32cb118583e6040c4244b44615c3a291a88b3a81b992f8ca83`.
- `scenario-20261104T200248Z-reaper-baseline1` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `1d725f18420e2421d40bf22dbec30b452f2a40745fce51b58c53c6b1a3390429`.
- `scenario-20261104T200317Z-reaper-micro1` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `38afc2f3970ab6c3467c30f58c515ecfd8eb9c3e6239d3da28841049aa51c2aa`.
- `scenario-20261104T200347Z-reaper-baseline2` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `04665c1cf48b62f91cc49c64138fe9a99c61a53d0f19136f1de8df1abe0ff026`.
- `scenario-20261104T200415Z-reaper-micro2` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `907c28df82c4f7c2da8a7f31e5fea35d9484d2d50b2bda328fab7166b6d0a28a`.
- `scenario-20261104T200444Z-lings-baseline1` (02eb55f): defender `Result.Defeat`, attacker `Result.Victory`; player-1 SHA256 `ebc8509130f63b1f1e5d52430bf26a13c533f8cca7589a14bbb9d813b06da0f9`.
- `scenario-20261104T200510Z-lings-micro1` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `7edcc62bbb1db8e6cd3fa775aeb7ceeb57d5894218ac929f03909c14772f6148`.
- `scenario-20261104T200538Z-cannon-baseline1` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `ef720fc333aee3ba1d9cd50e250736ea12112361e035c95f3167b949a897dce4`.
- `scenario-20261104T200609Z-cannon-micro1` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `b5cecfd4d64b7c2e99d5e689b8dfa20ae325c8dc5897a34b1918bd93a2711c3f`.
- `scenario-20261104T200639Z-tank-baseline0` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `84066d23e5fe433cbac5912531afdd7c49bc7f37063414ce149cfaac0c703439`.
- `scenario-20261104T200706Z-tank-micro0` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `ae160a58730af4a8b6d9088ce7985207efeb7ec1e4f05765a16e0ce9ededb96c`.
- `scenario-20261104T200732Z-tank-baseline2` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `a2583b5ea2b0b3d067abd9187529a6563a4b9c0808cd40feba1820d227fbecd8`.
- `scenario-20261104T200758Z-tank-micro2` (02eb55f): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `59c7224d97a665f9f0e70cb4d646e13b185ab0044b8190782f34c56881a36f3e`.
- `scenario-20261104T202018Z-lings-micro0` (d9e324b): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `5ab038c17024c45a5c238127bc56995f5e9d07ce43face7d9d407b853cb4d11d`.
- `scenario-20261104T202048Z-lings-micro0` (d9e324b): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `d28ff03db45021db19ff75c8fe39e2334dd1479021adcad93727e5e3e1887785`.
- `scenario-20261104T202119Z-lings-micro1` (d9e324b): defender `Result.Defeat`, attacker `Result.Victory`; player-1 SHA256 `2e30806fbe004a6830e21a7934a5af33f96561fc0978f302884d96685d430465`.
- `scenario-20261104T202147Z-lings-micro1` (d9e324b): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `4206fc1ee5a0d12523224066d82bdabb0a0b471403ed0cb7d77a363af66e87e3`.
- `scenario-20261104T202217Z-lings-micro2` (d9e324b): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `583fa304d1f3fc7e860d66e25a6abfc49f5c713c2b1697423fa10dd6c66a1a06`.
- `scenario-20261104T202246Z-lings-micro2` (d9e324b): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `6f349d83fd45af3cb32ae12378a4132462d9b70bab0a511916ab63e63de0814f`.
- `scenario-20261104T202331Z-cannon-baseline1` (738eab5): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `0916e0efcae6bed362ac1ec6e9a143b0b0f82ac5793828fc557da9bba8a13e64`.
- `scenario-20261104T202401Z-cannon-micro1` (738eab5): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `ca8e267eaf77147ee59113393b37fd7d29a2f596aeb3f45049a5e514065c4e8d`.
- `scenario-20261104T202431Z-tank-baseline0` (738eab5): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `8f1603495cd741b528579db751134a9553c0b207dfe0be22b877612bb38345c1`.
- `scenario-20261104T202458Z-tank-micro0` (738eab5): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `e237af110b15f7e749f31384a4f1639fa9273b8a44c417b034d975a35645b7b6`.
- `scenario-20261104T202524Z-tank-baseline2` (738eab5): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `7be57f3868db9af6fbd7c76ae17e98c4e7540f1c85ba5165378ec6e57230b357`.
- `scenario-20261104T202553Z-tank-micro2` (738eab5): defender `Result.Tie`, attacker `Result.Tie`; player-1 SHA256 `cedf51df730a56f8c31093048d5ddd351b3f12999b2ea154099dc7f123d3c560`.

## Bounded worker-defense follow-up

Frozen d9e324b, scenario-only `--worker-safety`: up to six healthy workers engage
visible local ground threats, workers below 45% HP mineral-walk toward the local patch
furthest from observed attackers, and the pull expires after 224 frames (10 game seconds).
Mining restoration owns its worker command for the frame. This is an experiment, not
a production worker manager or a claim that a ten-second expiry is always safe.
The queen micro controller stays identical in both sides of each pair.

| Approach/seed | Worker safety | Workers lost | Surviving enemy lings | Queen alive | Final mineral bank | Worker defend/evacuate commands | Conflicting unit frames |
|---|---|---:|---:|---|---:|---|---:|
| 0/1 | False | 12 | 1 | False | 150 | 0/0 | 0 |
| 0/1 | True | 10 | 0 | True | 180 | 171/43 | 0 |
| 1/2 | False | 12 | 5 | False | 155 | 0/0 | 0 |
| 1/2 | True | 10 | 0 | True | 180 | 220/34 | 0 |
| 2/3 | False | 12 | 3 | False | 150 | 0/0 | 0 |
| 2/3 | True | 6 | 0 | True | 450 | 208/38 | 0 |

The three paired runs reduced worker losses from 12/12/12 to 10/10/6, preserved the queen and eliminated all attacking lings. No conflicts were recorded. This is a repeated but incomplete improvement: most workers still die in two cases, so the optional policy remains scenario-only. These worker results are separate from the initial 14 cases and do not change the frozen Harder comparison. Bank comparisons include unequal survival durations when a base is destroyed; they are not normalized income rates.

## Trace examples and interpretation

In `scenario-20261104T200317Z-reaper-micro1`, both players' frame-29
`own_command` records are MOVE commands while their own cooldowns are positive:
queen 14.627 and Reaper 13.782. The separate movement counters establish actual observed
movement, not only attempted commands. At frame 25 the attacker attempts KD8 at predicted
position (156.051172, 25.983203); defender observes a charge at frame 37 at
(156.051025, 25.983154). The tiny positional discrepancy validates cast/effect location
correlation, **not** prediction quality or whether the grenade hit a moving target.

Across all six Reaper traces there are zero recorded in-range worker target opportunities.
Baseline approaches 0/1/2 have 1/2/3 observations with the Reaper within five units of a
worker, all with the queen within seven; micro approaches have none. This supports local
interception geometry in this setup but does not prove universal worker-line coverage.
Low-health worker selection exists in the controller but was not exercised by a real
worker-kill opportunity. A future adversary must vary mineral-line ingress and worker
target access, not merely repeat queen duels. Queen-first grenade preference remains a limit.

Repeated fixed-seed runs can still differ in engine trajectories: the initial and later
ling baselines differ in surviving enemy count. Matched settings reduce confounding but
do not imply bit-for-bit deterministic play.

Damage events do not identify exact attackers or individual splash hits. Enemy weapon
cooldowns are unavailable to the defender and never treated as zero/ready. Debug setup
and full two-player scoring remain separate from normal competitive observations.
