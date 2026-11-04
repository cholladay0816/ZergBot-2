# November 4, 2026 experiments

All later paired runs use AbyssalReefLE, Hard Terran, four-frame steps, SC2 5.0.17.98310, Python 3.14.10 and BurnySC2 7.3.0. Both SC2 and Python gameplay seeds are recorded. Full telemetry/replays remain local.

Wave 1 retained queen injection, roach production reservation and guarded expansion. Its three candidates reached the 600-second cap versus two early baseline losses. Those early runs did not seed Python and remain exploratory.

Wave 2 retained projected supply buffering: midgame blocked-supply samples fell from 16.3/30.6/16.3% to 2.0/0/0% across three paired seeds. Seed 1 won earlier; seeds 2/3 remained capped.

Wave 3 did not promote worker squads. Across six seeds, baseline outcomes were 2 wins / 1 loss / 3 capped; candidate outcomes were 3 wins / 3 losses. A gain on seed 2 accompanied losses before the cap on seeds 3/5. Squads default off.

Final regroup threshold: 11; emergency escape duration: 0 frames; expansion search enabled: True. These settings reflect the retained policy; explicit CLI controls preserve experiments.

## Supply

Baseline `dbdba87+paired-gameplay-seed`; candidate `d222ede`.

| Seed | Baseline outcome / seconds | Candidate outcome / seconds |
| --- | --- | --- |
| 1 | Victory / 851.96 | Victory / 622.86 |
| 2 | Capped / 1200.00 | Capped / 1200.00 |
| 3 | Capped / 1200.00 | Capped / 1200.00 |

Comparison artifact SHA-256: ec3c408d3bb1e47e3cd5538ce0b3ac73448ceb66e2182fe67675ee462e0fe284.

Local evidence and source SHA-256 fingerprints: `.local-matches/wave2-supply/comparison.json`.

## Worker-defense squad

Baseline `d222ede`; candidate `1deb34e`.

| Seed | Baseline outcome / seconds | Candidate outcome / seconds |
| --- | --- | --- |
| 1 | Victory / 622.86 | Victory / 600.89 |
| 2 | Capped / 1200.00 | Victory / 896.43 |
| 3 | Capped / 1200.00 | Defeat / 1134.82 |
| 4 | Victory / 703.57 | Victory / 833.04 |
| 5 | Capped / 1200.00 | Defeat / 1016.25 |
| 6 | Defeat / 988.39 | Defeat / 1007.14 |

Comparison artifact SHA-256: 21b30c942f3141b32b0d8cf6a1c634eb58bbe9e0e67bd1c72c9820800599999d.

Local evidence and source SHA-256 fingerprints: `.local-matches/wave3-defenders-six-seeds/comparison.json`.

## Attack hysteresis

Baseline `dc1fbd0-control`; candidate `dc1fbd0-hysteresis`.

| Seed | Baseline outcome / seconds | Candidate outcome / seconds |
| --- | --- | --- |
| 1 | Victory / 622.86 | Victory / 688.93 |
| 2 | Capped / 1200.00 | Victory / 623.75 |
| 3 | Capped / 1200.00 | Capped / 1200.00 |

Comparison artifact SHA-256: a20a466c127daad000109a269c554f2e95e47492d98997f1fe8a9f8377671478.

Local evidence and source SHA-256 fingerprints: `.local-matches/wave4-hysteresis-pilot/comparison.json`.

## Burrow-damage escape without search

Baseline `dc1fbd0-hysteresis`; candidate `dc1fbd0-escape`.

| Seed | Baseline outcome / seconds | Candidate outcome / seconds |
| --- | --- | --- |
| 1 | Victory / 688.93 | Capped / 1200.00 |
| 2 | Victory / 623.75 | Victory / 689.82 |
| 3 | Capped / 1200.00 | Victory / 1160.89 |

Comparison artifact SHA-256: 0afe6ee13c660743fbb51f34ebc0f52b3b7d245151072c8d76e2350b7809c1f6.

Local evidence and source SHA-256 fingerprints: `.local-matches/wave5-escape-pilot/comparison.json`.

## Expansion search

Baseline `dc1fbd0-hysteresis`; candidate `46b2eb0-search`.

| Seed | Baseline outcome / seconds | Candidate outcome / seconds |
| --- | --- | --- |
| 1 | Victory / 688.93 | Victory / 688.93 |
| 2 | Victory / 623.75 | Victory / 623.75 |
| 3 | Capped / 1200.00 | Victory / 907.50 |

Comparison artifact SHA-256: 1b96e30af38a8bca820f063545efe75506a048a43fe2c316289edfbbbad9f5be.

Local evidence and source SHA-256 fingerprints: `.local-matches/wave6-search-pilot/comparison.json`.

## Experimental aggressive stack versus supply baseline

Baseline `d222ede`; candidate `46b2eb0-search`.

| Seed | Baseline outcome / seconds | Candidate outcome / seconds |
| --- | --- | --- |
| 1 | Victory / 622.86 | Victory / 688.93 |
| 2 | Capped / 1200.00 | Victory / 623.75 |
| 3 | Capped / 1200.00 | Victory / 907.50 |
| 4 | Victory / 703.57 | Victory / 859.29 |
| 5 | Capped / 1200.00 | Defeat / 1056.43 |
| 6 | Defeat / 988.39 | Defeat / 1130.54 |

Comparison artifact SHA-256: 3ce6e4a3a82865a400187586519e0d12c1973834e82d64645e1b07226390a63f.

Local evidence and source SHA-256 fingerprints: `.local-matches/final-stack-six-seeds/comparison.json`.

## Interpretation limits

Capped outcomes are censored; extra wins and extra losses must both be reported. Damage/caster attribution remains ambiguous. Replay analysis of the losing worker-squad seed 3 joined 228 exact frames from two own-player perspectives, confirming late army/economy imbalance without pretending raw enemy visibility was omniscient. Sample/detail caps and missing historical counters limit micro metrics.

## Final keep and opt-in decisions

Queen injection, production reservation, guarded expansion and projected supply buffering remain enabled. Invalid hatchery placement was absent in the later paired comparisons; guarded exact placement and retry throttling address the observed earlier rejection without suppressing error reporting.

The regroup-six attack candidate was initially retained after a three-seed pilot, then demoted to opt-in after the six-seed stack check: four wins and two losses versus two wins, one loss and three capped baseline games. Seeds 1/4 won slower, and seed 5 changed from capped to a loss. The default regroup threshold is restored to 11; `--regroup-roaches 6` reproduces the candidate. These mixed results do not establish a stable win-rate gain.

Emergency burrow escape remains off: it traded the seed-1 win for a cap, slowed seed 2, and converted seed 3 from capped to a win. Worker squads also remain off after their six-seed tradeoffs.

Expansion search remains enabled. Its isolated three-seed comparison held the regroup-six configuration fixed: seeds 1/2 reproduced their wins and seed 3 changed from capped to Victory at 907.50 seconds. Seed 3 recorded a visibility-confirmed waypoint transition at frame 19644. The final conservative regroup-eleven/search combination has not received a full six-seed comparison; that interaction is an explicit next validation step. The table titled experimental aggressive stack records the tested candidate, not a six-seed claim for final defaults.

Full JSON, replays and resource samples remain ignored/local. The public ledger contains aggregate outcomes and provenance only. A launcher signature error was corrected before the search pilot; its failed pre-game artifact remains local and is excluded from comparisons. No failed or incomplete run is counted as a game loss or win.

Final-default smoke: seed 1 reached the 600-game-second cap in 100.58 wall seconds under a 150-second wall bound, with regroup 11, search enabled, squads 0 and escape 0. This is a successful bounded runtime check, not a win. Evidence: .local-matches/20261104T175402Z-db992622/match.json and match.SC2Replay. Its source uses the final configuration and passed 115 offline tests.
