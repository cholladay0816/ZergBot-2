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


## Bounded hatch-first opening

Frozen candidate `a8e182828b5bf28f12c593963022408bad3f4357` combines the refined
opening supply buffer with a natural-expansion reservation at 16 workers. The hold is
bounded to 30 game seconds and aborts on observed nearby ground pressure or Cannon/Pylon
threats. Placement remains validated by the game API. This is an adapted opening step,
not a literal implementation of a coach's full build. Both options remain off by default.

Three 360-game-second Harder probes, seed 1, compare with the refined supply-only probes:

| Opponent | Supply-only workers at 4 / 6 minutes | Hatch-first workers at 4 / 6 minutes |
|---|---:|---:|
| Terran | 26 / 44 | 32 / 47 |
| Protoss | 29 / 53 | 37 / 59 |
| Zerg | 26 / 44 | 31 / 54 |

All six-minute probes are unresolved caps, not wins. In the Terran hatch-first probe,
the natural command was submitted at 47.321 seconds; the foundation was observed at
56.429 seconds. Pool presence was first sampled at 90 seconds and the first queen
completed at 169.286 seconds. Start, sampled presence and completion are different metrics.
Opening execution still has substantial room for improvement.

Longer matched seed-1 comparisons use Harder, Abyssal Reef, step 4, 1200-game-second /
300-wall-second bounds, adaptive-army and roach-tech enabled on both sides. Prior control
is `02eb55f`; candidate adds opening-supply and hatch-first:

| Opponent | Prior control result / game seconds | Candidate result / game seconds |
|---|---|---|
| Terran | Defeat / 826.429 | Defeat / 887.500 |
| Protoss | Defeat / 978.393 | Victory / 612.143 |
| Zerg | Victory / 771.250 | Victory / 544.286 |

This is encouraging single-seed evidence, not a reliable win-rate estimate. A second-seed
paired comparison is required before considering promotion. Terran still loses: 117 own
burrowed-roach destruction events versus 20 observed emerge confirmations suggest that
recovery is often failing, with visible Missile Turrets and ground attackers in the match.
These are observations, not proof of each damage source or exact detection coverage at
every death. The previously mixed detection-escape policy remains off.

Raw evidence and hashes are indexed locally in
`.local-matches/phase4-hatch-first-evidence.json`:
- `20261104T205932Z-cee3d30e`: Terran, limit 360, Tie at 360.0; SHA-256 `2ebc2a764d542a70d6eaaeb57d506fe2bf6d81202d89459f2c7e098f486b300e`.
- `20261104T210026Z-49009f24`: Protoss, limit 360, Tie at 360.0; SHA-256 `ea637dada2985fea829e3daf2826aac86b4b8dbb988c965c297087c94c4d6e0a`.
- `20261104T210121Z-017498d0`: Zerg, limit 360, Tie at 360.0; SHA-256 `c2a61935a75d3f46e02221f783558539d2237795c9fd6bea9f652e13a9b01316`.
- `20261104T210636Z-b92a913f`: Terran, limit 1200, Defeat at 887.5; SHA-256 `5de475af84b26fb40844444833b43623ae8f77ca8a7e134943f97e8f6057b133`.
- `20261104T210948Z-cccfbb36`: Protoss, limit 1200, Victory at 612.143; SHA-256 `e435ede6d47ff764508ad18edc49987c0a0442f6088da8ea38b40fef1377f1af`.
- `20261104T211157Z-2eb2478d`: Zerg, limit 1200, Victory at 544.286; SHA-256 `d9471d10f21e9d6065db91ba3d1cce4e24a07d9914f1dcf0fe3485484c4aedf0`.

### Scenario cleanup ordering follow-up

Checkpoint `2341fd5` adds a cleanup barrier before actor spawning, followed by the existing
setup-ready barrier. Installed BurnySC2 obtains each player's initial observation before
its on_start, but the two startup coroutines execute concurrently. Therefore the earlier
single barrier did not itself prove that attacker worker cleanup preceded spawning the
scenario Probe. The new two-phase protocol enforces that ordering; its regression test
delays cleanup and verifies no spawn or gameplay can pass prematurely. This addresses a
possible race without claiming it occurred in older artifacts. 201 offline tests pass.
Live validation of this exact setup revision is pending separately from the match wave.


## Two-seed full opening comparison

The frozen `02eb55f` control and `a8e1828` candidate use the same adaptive-army and
roach-tech options. Only the candidate enables opening-supply and hatch-first. Queen
recovery, tactical queen micro, and detection/damage burrow escape remain disabled.
Harder AI, Abyssal Reef, seeds 1/2, step 4, 1200 game seconds / 300 wall seconds per run.

| Race | Seed | Control | Candidate | 4-minute workers, control -> candidate |
|---|---:|---|---|---|
| Terran | 1 | Defeat 826.4s | Defeat 887.5s | 25 -> 32 |
| Terran | 2 | Defeat 813.4s | Defeat 1013.0s | 22 -> 31 |
| Protoss | 1 | Defeat 978.4s | Victory 612.1s | 24 -> 32 |
| Protoss | 2 | Defeat 932.0s | Victory 607.1s | 24 -> 27 |
| Zerg | 1 | Victory 771.2s | Victory 544.3s | 26 -> 34 |
| Zerg | 2 | Victory 529.1s | Victory 549.8s | 22 -> 33 |

The economic probes above used supply-only controls and are separate from these full
adaptive-army comparisons. Do not combine their six-minute worker counts as if the army
policy were identical. These two seeds are exploratory evidence, not a general win-rate
estimate. Terran remains unresolved; longer survival is not a win. No difficulty increase
or universal opening claim follows. Existing defaults remain unchanged.

Reproduce the stronger-opening candidate explicitly:

```powershell
.\.venv\Scripts\python.exe -m zergbot --map AbyssalReefLE --difficulty Harder --seed 1 --game-time-limit 1200 --opening-supply --hatch-first --adaptive-army --roach-tech
```

Full match evidence and hashes:
- `20261104T201016Z-d6e6f8a5` (Terran seed 1, control): SHA-256 `e09bc904477c32d6d12c4386b630de2f44501a7589b71f2eb82e83c689239f62`; dropped detail events 0.
- `20261104T201327Z-ade5eed0` (Protoss seed 1, control): SHA-256 `aa321195cc4db36a0f6f3fb3b1daaa04aa0b5184dd6c99d3173c3be4758037bf`; dropped detail events 0.
- `20261104T201709Z-63ddc557` (Zerg seed 1, control): SHA-256 `e2062a6b07abcda55b8d203878c4da87e1d7d443ab08251605041d6fbfe2bf99`; dropped detail events 478.
- `20261104T210636Z-b92a913f` (Terran seed 1, candidate): SHA-256 `5de475af84b26fb40844444833b43623ae8f77ca8a7e134943f97e8f6057b133`; dropped detail events 656.
- `20261104T210948Z-cccfbb36` (Protoss seed 1, candidate): SHA-256 `e435ede6d47ff764508ad18edc49987c0a0442f6088da8ea38b40fef1377f1af`; dropped detail events 0.
- `20261104T211157Z-2eb2478d` (Zerg seed 1, candidate): SHA-256 `d9471d10f21e9d6065db91ba3d1cce4e24a07d9914f1dcf0fe3485484c4aedf0`; dropped detail events 158.
- `20261104T211806Z-c74cc2f5` (Terran seed 2, control): SHA-256 `f85c44eb849566a11b1c9472c34aba4da6cad50b51d2edee1265f9ebf4bf3db0`; dropped detail events 0.
- `20261104T212058Z-871f92c7` (Terran seed 2, candidate): SHA-256 `536bc1b2239242a78569349d584021d882417edb97b90278a1290b694291ab3b`; dropped detail events 2031.
- `20261104T212454Z-84a8f245` (Protoss seed 2, control): SHA-256 `464af478e063bde65c03b07aaf1a9bdf55167a435e2f2b410c1d8dbfb7e3c714`; dropped detail events 0.
- `20261104T212816Z-c7105c6f` (Protoss seed 2, candidate): SHA-256 `af1a79e06bcf4a42d935f4bd4226a0bd410de5733a200abc61564d6318c05e5c`; dropped detail events 0.
- `20261104T213025Z-e81e1c18` (Zerg seed 2, control): SHA-256 `b3c432208fccd9ee6b5eb1cacd56f1d14c9ca3b66de0ea3e3060cdc7346ed690`; dropped detail events 0.
- `20261104T213200Z-2c6f5f10` (Zerg seed 2, candidate): SHA-256 `2d6a34251d7f80ff3b0375ac52a8b652b6d185fb17023638acf3f67b77b29fc6`; dropped detail events 0.

Detailed events are bounded, so some matches omit individual events after reaching the
configured retention limit; aggregate counters and explicit outcomes are retained. Missing
detail is not evidence that an action did not occur. Full local comparison index:
`.local-matches/phase4-opening-full-comparisons.json`.

### Worker-release correction awaiting isolated comparison

`4b323d541c6d6181aca39317eedb84f2c8297b6b` fixes a scenario-only command-ownership bug:
after defense expires, the worker receives one gather command and leaves the controlled
set. Previously it remained in that set and received gather again each subsequent frame,
which could interrupt cargo returns. A regression verifies release happens exactly once
while the threat remains visible. This is independent of the opening match source.
202 offline tests and lint/format checks pass. Live pairs use the same two-phase setup
barrier on both sides (`2341fd5` control, `4b323d5` correction).


## Worker release: live command fix, mixed survival

Frozen control `2341fd5` and correction `4b323d5`, normal fog, two-phase startup barrier,
six lings, one queen, twelve starting workers, 10-second defense window, 90-second cap.
Both sides retain the same queen controller and six-worker participation limit.

| Approach | Version | Workers lost | Gather-release commands | Final mineral bank | Workers in last pre-expiry sample |
|---|---|---:|---:|---:|---:|
| 0 | control | 8 | 565 | 310 | 9 |
| 0 | candidate | 2 | 18 | 825 | 12 |
| 1 | control | 6 | 513 | 455 | 10 |
| 1 | candidate | 9 | 18 | 305 | 10 |
| 2 | control | 10 | 479 | 180 | 9 |
| 2 | candidate | 9 | 12 | 310 | 8 |

All runs finish their caps, with the queen alive and zero conflicting-unit frames. Both
startup phases are recorded at frame 0. Repeated gather commands decrease sharply,
supporting the command-ownership correction. Survival remains mixed; notably approach 0
already differs before expiry. Startup synchronization does not prove deterministic
trajectories, and the loss differences cannot all be credited to the release fix. Mineral
bank is an observation, not an exact measure of mining interruption or unit collision.
The correction is retained in the scenario harness; no production worker-defense default
is enabled from these outcomes. The next isolated hypothesis is whether six selected
defenders leave too many workers exposed against six lings. Checkpoint `6b9664d` exposes
a bounded 1-12 participation parameter, default six, with regression coverage for the
cap and CLI rejection of an unbounded pull. It does not change competitive match policy.

Evidence index: `.local-matches/phase4-worker-release-comparisons.json`, including replay
and both-player hashes. Defender artifact hashes:
- `scenario-20261104T213421Z-lings-micro0`: `40b5212ac27abd0fc9b72f54ad635514ac82c423c18dbed90b366bf729c5cd77`.
- `scenario-20261104T213452Z-lings-micro0`: `fdc7d659cb8341f9b480b528edc6bdca8c2c76e0947aa7798781861d74d9ff4f`.
- `scenario-20261104T213522Z-lings-micro1`: `0930621ca93fcf7e8c8a12f953ab14b081bc1fd4564e1a8f49c0e75ddd649033`.
- `scenario-20261104T213552Z-lings-micro1`: `7b7bf1013f326d5fe176bdfcbb1408e551d0baae0be34dd6053706db8cfa47a3`.
- `scenario-20261104T213623Z-lings-micro2`: `24264115c9edb440e28626985f336bb3d8bef5d3e0a3ef5a6f7432aca264f3e1`.
- `scenario-20261104T213653Z-lings-micro2`: `5a954779541e5b66544353aab9f8f1d90a4d571ba3dd186485aaa1eabfda13f4`.
