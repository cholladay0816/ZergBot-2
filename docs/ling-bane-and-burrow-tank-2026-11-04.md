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

## Completed ling/baneling results

All twelve runs destroyed the enemy tank and reached the game cap; these are scenario-objective successes, not full-match wins. No command conflicts or action errors were recorded. The candidate remains scenario-only and is not promoted.

| Approach / seed | Baseline lings / banes | Split lings / banes | Baseline / split survivor HP | Baseline / split opening mean nearest-neighbor distance |
|---|---|---|---|---|
| 0 / 1 | 7 / 0 | 7 / 0 | 235.2 / 238.6 | 0.73 / 1.68 |
| 1 / 2 | 7 / 1 | 7 / 0 | 262.2 / 235.4 | 0.73 / 1.76 |
| 2 / 3 | 7 / 0 | 8 / 0 | 231.9 / 270.5 | 0.75 / 1.81 |
| 0 / 11 | 7 / 2 | 10 / 0 | 298.6 / 350.0 | 0.72 / 1.90 |
| 1 / 12 | 7 / 1 | 8 / 1 | 262.0 / 306.7 | 0.72 / 1.77 |
| 2 / 13 | 7 / 2 | 4 / 0 | 291.9 / 140.0 | 0.72 / 1.85 |

Across six pairs, baseline retained 42 lings and 6 banes; splitting retained 44 lings and 1 bane. Spacing improved in every pair, but survivor outcomes were mixed, including a large regression at approach 2 / seed 13. Baneling disappearance can be self-detonation rather than enemy damage; the experiment does not equate every missing bane with a tank kill.

Opening spacing averages per-unit nearest-neighbor distances over retained tank-visible samples within the first 90 split frames. It does not measure continuous collision-free paths. Both policies recorded one frame with multiple ling/bane damage callbacks in each run; callback grouping is only splash-correlated evidence, not per-shell attribution.

The tank was last visible at 3.62-5.09 seconds under baseline versus 7.90-9.38 seconds under splitting, then absent at the next sample about 0.71 seconds later. The enemy own final roster confirms the tank did not survive. Visibility samples are not exact death timestamps. Splitting delayed engagement resolution. Baseline approach 0 / seed 1 also recorded 68.95 Hatchery damage; other runs recorded none.

## Completed roach timing matrix

Frozen runtime: `8ca5fa3` (full source SHA recorded in local batch index). Actual installed game is 5.0.17.98310, Python 3.14.10 and burnysc2 7.3.0. Each run used 120 game / 120 wall seconds, including real research wait.

| Case | Roach survived cap | Confirmed burrows / attempts | Own death observation |
|---|---|---|---|
| ready-single-1 | True | 4 / 4 | none |
| ready-single-11 | True | 4 / 4 | none |
| unresearched-single | False | 0 / 0 | ROACH at frame 105 |
| ready-double | False | 1 / 2 | ROACH at frame 2017 |
| ready-triple | False | 0 / 1 | ROACH at frame 1629 |
| ready-detected | False | 1 / 1 | ROACHBURROWED at frame 1718 |

All six trials exercised their requested research condition and recorded zero action errors/conflicting commands. Research submission was not treated as completion. Two undetected single-tank trials completed four burrow/recovery cycles each and survived. Successful burrows were observed four loops after the attempt (~0.179 seconds), an observation-resolution measurement rather than a universal engine latency.

Concrete single-tank seed 1 timeline: research submitted frame 5; actors spawned after observed research at 1609; first hit frame 1625 reduced 145 HP to 76; second hit frame 1677 left 7.889 HP. Burrow was attempted in that same observation and the burrowed form appeared at 1681. The first two hits were separated by 52 loops (~2.32 seconds). Healing during intervals means callback HP deltas can be slightly below the 69-point first hit. This supports the requested timing behavior for this isolated single-tank condition.

Two-tank exception: first impacts at 1625/1629 left 76/7.068 HP; Burrow at 1629 was confirmed at 1633. The roach later resurfaced from 116.773 HP (80% threshold) at frame 1981. A subsequent hit at 2013 left 48.615 HP and triggered another Burrow, but it died exposed at 2017 before confirmation. Roughly 116 HP cannot absorb a pair of roughly 69-point impacts. The observed overlap and morph window matter.

Three-tank exception: observed combined damage at frame 1625 was 137.966 HP, leaving 7.034 HP. The controller issued Burrow, but death was observed at 1629 before a burrowed form. This is not evidence of an omitted command or army-order override.

Detection exception: with an enemy Raven, Burrow attempted at 1670 was confirmed at 1674; death was observed as ROACHBURROWED at 1718. Burrowing did not remove targetability. The detector-escape experiment remains disabled; demonstrating detection danger does not prove that older escape policy improves full matches.

The unresearched case attempted the production retreat fallback and died at frame 105 without a Burrow attempt. Availability/research are real prerequisites. Tank-owned cooldown and target data remain evaluator-only. No enemy cooldown is injected into live roach decisions.

## Decision and next bounded hypotheses

Do not claim that tanks can never kill researched roaches. A single undetected tank was handled in both tested seeds, but overlapping impacts and detection produced deaths. Next candidates are a visible-threat-based safe resurfacing budget and preemptive positioning against concentrated siege, tested separately. No production thresholds or defaults changed here. Adjacent-target splash, upgraded weapons/armor, moving fights, bio support and larger formations remain unisolated in this timing matrix. The tank can redirect onto buildings while the roach is hidden; roach survival is not base-defense success.

For ling/bane spacing, the present fixed lane spread is insufficiently reliable. A future policy should separately test preserving banes and reducing the engagement delay rather than optimizing spacing alone.

## Resource and verification record

All 18 supervisors completed under existing sequential, below-normal, CPUs 20-23 controls. Peak sampled host CPU was 57.7%; minimum available RAM was 8.30 GiB. No sustained safety-limit stop occurred.

255 offline tests, Ruff lint/format and isolated package build passed. The final extra test assertion exercises tank telemetry through the real recorder/strict JSON contract; it does not change the frozen runtime. Full artifacts remain local, including both players, settings, replays and resource reports.

## Artifact audit

- `scenario-20261104T234643Z-tank-baseline0` (ling-bane-tank-0-seed1-baseline):
  - `player-1.json` SHA256 `3a1e2b227a2dce26a022bdc15de12fa9213649013085d8747e042dcaf18a1a78`
  - `player-2.json` SHA256 `d466fb61d860d1e7a0ec3da3ca9e756f2cc97aa0d7af2192f5c2499d19185547`
  - `scenario.SC2Replay` SHA256 `eaec7851699106d502ff6a33b5c7f4aa1e37eb1e24612140a291ee88635c7c5e`
- `scenario-20261104T234709Z-tank-micro0` (ling-bane-tank-0-seed1-micro):
  - `player-1.json` SHA256 `16964a4fc89a185d8c10bd120ae8ba890027051101260dc27b97dd7b5821d07a`
  - `player-2.json` SHA256 `13fcc6e0b581f11126f1a7632255d9e15835a854815e565b803b6b6b8fae1a5a`
  - `scenario.SC2Replay` SHA256 `2b8f62077bec9b40b0d88eb4b5decdc6fdf06779802b339ba9642fe2985d0dd5`
- `scenario-20261104T234735Z-tank-baseline1` (ling-bane-tank-1-seed2-baseline):
  - `player-1.json` SHA256 `9323de0fadfc16a22f6383024769a984d9c871d779e533627d8a05ab1c9234b7`
  - `player-2.json` SHA256 `c95d5c0e8c7d1a8069fb4d3dd29aad97ec77df482f30ad9f833afd9c0e91fdeb`
  - `scenario.SC2Replay` SHA256 `49c0525ae566e8bb3b1b8e9d182e2301304c6435f625b5a63e69f68aa7feddb3`
- `scenario-20261104T234801Z-tank-micro1` (ling-bane-tank-1-seed2-micro):
  - `player-1.json` SHA256 `293dc5d651e3f2de986d81ff4f1ff6e00396ee198a26adac5cc63b5ee4f7d795`
  - `player-2.json` SHA256 `e7f473c9bce4bb998bc09a32855b51abea23cdf1695642fdeb466fad54634ecf`
  - `scenario.SC2Replay` SHA256 `78e4842f943e5df6beccc89f3a2fc9fd5eac01aebed386a4158cbde0fe91436e`
- `scenario-20261104T234828Z-tank-baseline2` (ling-bane-tank-2-seed3-baseline):
  - `player-1.json` SHA256 `a807fff984ab579996c516df7e2f4e79064c0a7b765d498dea447b56cdb1abad`
  - `player-2.json` SHA256 `1c934c3551b19f6511d1dd5c18fd4efefc0fd26d83904784500b79eda7b9fd6b`
  - `scenario.SC2Replay` SHA256 `d87977dcda041c405ea8c90aeae54de3015034b435fb239295afb1dc88b2cc25`
- `scenario-20261104T234854Z-tank-micro2` (ling-bane-tank-2-seed3-micro):
  - `player-1.json` SHA256 `93182dd653699d62b1ea3208a10a20bfe89d62a3bd43f8dd8302a150dc6f4fb5`
  - `player-2.json` SHA256 `0bdf22331d6f4c4c08ac130f2bdebb29dacc36cb2d36f9ecbaaaeae98e903bd2`
  - `scenario.SC2Replay` SHA256 `369951f72124b937ae9d6ac46f805fe4aafb1a847699f7da2b1749ba18b33d99`
- `scenario-20261104T234920Z-tank-baseline0` (ling-bane-tank-0-seed11-baseline):
  - `player-1.json` SHA256 `3ad35ad2378b24baabba2bfbcb04e7de4f411e7b54b5146c15869da5c5736aba`
  - `player-2.json` SHA256 `23b7c49605514b6a4392b74448a94f13b044eccecf0bb108d3c6eaaa2a68b6bc`
  - `scenario.SC2Replay` SHA256 `b54caa2e6bc03a073604ecf4a6e58fdf67ad439d3137bb8f79c99c49485892f3`
- `scenario-20261104T234947Z-tank-micro0` (ling-bane-tank-0-seed11-micro):
  - `player-1.json` SHA256 `cc2cc0d79c5712563e445b25e4818b932e1f38889f4e5ae0491616a764c34a0b`
  - `player-2.json` SHA256 `74af9f0feaf4113f0cb7d1aff6314a55cd5ced822b566152bd975f96d7e571dd`
  - `scenario.SC2Replay` SHA256 `8d4ce971f6592df90d48f0d2cc319eac234e705a2cfe226ce8a7df02e535b179`
- `scenario-20261104T235015Z-tank-baseline1` (ling-bane-tank-1-seed12-baseline):
  - `player-1.json` SHA256 `8aabbf6ae084f2d4566d96b7502f02dd20b8e955cc717ae74dc9793afab98b4e`
  - `player-2.json` SHA256 `1954909e6a02216145aa89106e8478ef6a979d5d055e78e9c5b67f9cc862ddc8`
  - `scenario.SC2Replay` SHA256 `a77f992c29952885e99ff9c0482bad4fbe409f94fa7b894405a7a0e35ca276dd`
- `scenario-20261104T235044Z-tank-micro1` (ling-bane-tank-1-seed12-micro):
  - `player-1.json` SHA256 `20d915b1d902af8f713ef843d052b817d55c545bcf087799c8d8d74b759fb429`
  - `player-2.json` SHA256 `f1bc8f3b397a2176e2b0b538e19c35ddd1965e43bd3e7ee126df302459058d4f`
  - `scenario.SC2Replay` SHA256 `fb841f05ebcdc79488cd6a10208dc511c2920cf06ec85479a517d9cf24868e61`
- `scenario-20261104T235110Z-tank-baseline2` (ling-bane-tank-2-seed13-baseline):
  - `player-1.json` SHA256 `d6e90f545d0fff222970c560b0dbd7e45cecc48ac78c0a35cf086885bcd8f3db`
  - `player-2.json` SHA256 `2f9d208409142d5dc95803ca092a94e2757fe1e282e7007585c9e166a4189919`
  - `scenario.SC2Replay` SHA256 `111e61bfc961c547e6f1433f68e17fb4444e52059a34a8f4b81d63725d30f7db`
- `scenario-20261104T235136Z-tank-micro2` (ling-bane-tank-2-seed13-micro):
  - `player-1.json` SHA256 `da64ef48f5e22b7c9568dba6f223262ffaec9e65f9ad58749611a138035f3826`
  - `player-2.json` SHA256 `bd34c8c939208bbceba1cd18fcaabf2a3e279e13d5672f82f19cf39058490d4b`
  - `scenario.SC2Replay` SHA256 `35735bca5d1e597dda847432ddb7742778e3515d7d883e5073beb5f233b4fe50`
- `scenario-20261104T235232Z-burrow-tank-micro1` (ready-single-1):
  - `player-1.json` SHA256 `b4d00f978933453dd2d57502797b248768e5d132b19011b7d9c23f1141c81e5d`
  - `player-2.json` SHA256 `b2383e7db4fa1f3838057920ff575ac2433b26b7c1f62a0d1747b8a1000705bb`
  - `scenario.SC2Replay` SHA256 `d5be9709508eddd486090b72b3e50a07ade67a63d33d007a140c3907c33998d3`
- `scenario-20261104T235304Z-burrow-tank-micro1` (ready-single-11):
  - `player-1.json` SHA256 `14335054e066b82944dede002b9dd13d2e4ce70185391b6fba61ca94e1fec567`
  - `player-2.json` SHA256 `56d91c4b83fa75a6a0b87b1c28d251ff40cd2d0ffde5b8587c4a9c387be50819`
  - `scenario.SC2Replay` SHA256 `54f55aaf5da1992eaa303f84ba58391264dc1fc4c1357cd864090c2b63b55848`
- `scenario-20261104T235336Z-burrow-tank-micro1` (unresearched-single):
  - `player-1.json` SHA256 `1d01b46b8450b2d3dcea39412ea22e9357fa6a62847fe5ffe8169785018b8ee5`
  - `player-2.json` SHA256 `e9bf4e70e65c7f31a8d5aa885be430ba68c202ca940295eae8e7d37cd2ec1300`
  - `scenario.SC2Replay` SHA256 `9e3b0176a2f2593069db4d677b22591ea3778365311348055e253b31f0650337`
- `scenario-20261104T235407Z-burrow-tank-micro1` (ready-double):
  - `player-1.json` SHA256 `507316c11ec6a1cd9770e5c6a9b36b84d1b282a79a84e24c53f5c315deaed4de`
  - `player-2.json` SHA256 `bc033ae5ebc13dea6d9f5bb0e017225c00303cdaed427b3defdf4b29442de68e`
  - `scenario.SC2Replay` SHA256 `2af0624d9d5247025bdc4aba9653a8d0c1673d47b298bda61dcb7e2b1d48b871`
- `scenario-20261104T235439Z-burrow-tank-micro1` (ready-triple):
  - `player-1.json` SHA256 `6dc77a7041e813ada309ec5d2b3a86c2f677aacf8eeb4e41774457309244f44e`
  - `player-2.json` SHA256 `6ec3efdfaa2a6f26573b29f0dc0e320e9c7f411c922de1a18d95054e1235220a`
  - `scenario.SC2Replay` SHA256 `1e10c2d820c1cffe1356e76e2a658090daa2bf3d9b4d8fa846b297643b259447`
- `scenario-20261104T235510Z-burrow-tank-micro1` (ready-detected):
  - `player-1.json` SHA256 `41a40c42de46972e19125e0831b58a254baf36a83465d324d809e186d73815a5`
  - `player-2.json` SHA256 `2f89d069bbdd7ded7e5cd8c24003c7f86277e44b8075e4bf1fb93369c7427bad`
  - `scenario.SC2Replay` SHA256 `c22f7b50a30946992e73b1f54d2704cfae79f06407e2e99d5240195c976447b3`