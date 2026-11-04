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

## Live results (complete)

| Case | Result / seconds | Third command / foundation / completion | 6m workers / roaches | 8m workers / roaches |
|---|---|---|---|---|
| third-control-Terran-1 | Defeat / 887.5 | 424.6 / 433.4 / 504.8 | 44 / 18+0 | 57 / 12+2 |
| third-candidate-Terran-1 | Defeat / 882.5 | 373.6 / 383.6 / 455.0 | 44 / 16+0 | 59 / 14+1 |
| third-control-Terran-2 | Defeat / 1013.0 | 505.7 / 512.5 / 583.9 | 44 / 20+0 | 44 / 21+2 |
| third-candidate-Terran-2 | Defeat / 908.2 | 460.4 / 467.5 / 538.9 | 44 / 20+0 | 44 / 10+2 |

Roach counts are exposed + burrowed; recovery-state units are not assumed battle-ready.
All four matches ended in defeat, with no caps or interruptions. The candidate completed its third about 50 and 45 seconds earlier, but lost about 5 and 105 seconds earlier. Earlier expansion alone did not improve the terminal result. Keep `third_base_reserve=False`; the experimental implementation is retained for auditability and controlled future work.

The first visible hostile combat unit near an observed surviving resource-base location appeared at 760/740 seconds in control/candidate seed 1 and 905/805 in seed 2. These are sampled home-pressure observations, not the first forward engagement or proof that those units caused the losses. Enemy workers are excluded from that metric.

The four supervisors completed normally in 191.6, 195.5, 231.8 and 201.8 wall seconds. Peak sampled system CPU was 20.7%; minimum sampled free RAM was 6.81 GiB. All retained the existing priority/affinity/resource controls. Observed game/wall ratios were approximately 4.4-4.6, including startup; no fixed speed multiplier is promised.

## Evidence

- `20261104T224327Z-7d186b1b`: match JSON SHA256 `fb61f9ca0f057e296c110378ffd2414f17caf5ab32691661a45d8cca01762914`; replay SHA256 `077c76b53e2dc52bb5fa83700ed5374eea002e4a05521e34c3d056a0188d2214`.
- `20261104T224639Z-13de934c`: match JSON SHA256 `60c06b68486f900a9570a04978d623d7e6935b51bd49cf98597e410a5e092a54`; replay SHA256 `f62aa697070ae62ff5c5fe2b6506fbec3434e9c4c8f35cf277cd9870768b6cdb`.
- `20261104T224954Z-962e545b`: match JSON SHA256 `553d3fc4e8b9a1afca812704b8f265108ad4ba3b440b00b31fa746f110df2dbb`; replay SHA256 `de15e079dc8560ab339b20469e243fbe0795c464957990fc08c85e0bf6ccbaa6`.
- `20261104T225346Z-784f1c06`: match JSON SHA256 `c940e60e4999bd2cc2a407227bb9df67e203763e110e8671ec1b3ae6f175003e`; replay SHA256 `a3119d19556b7771b3e65734baffdb51cc392e9d61a7f19cfb7444df859feb4a`.

Local comparison index: `.local-matches/phase4-third-budget-comparison.json`. Local midgame checkpoints preserve early events where the bounded final event buffer could evict them. Snapshot details can omit units at the configured cap; counts remain separate from positional detail. Mineral bank is not income.

## Replay recovery history

Post-game collection-score capture was added in 3f186d8. The first two-perspective analysis reached its original timeout after player 1 completed and player 2 reached 640 seconds; its partial file is preserved as `replay-perspective-2-partial-original-bound.json`. A single-player recovery option in 066bf93 completed the missing raw pass, then exposed a report-assembly error because the combined report requires two perspectives. ac412b5 fixes that path with a CLI-flow regression. Both completed first-control passes were combined offline without repeating SC2. Remaining analyses use a measured 300-second bound.

Current source passes 231 offline tests and lint. The frozen live candidate passed 229 tests before launch; the later changes concern post-game analysis only.

## Completed replay results

All eight player-perspective passes are complete. Each actual observed player ID matches its requested perspective, and each pass matches the corresponding replay SHA256. These observations are post-game evaluator inputs only, never competitive bot inputs.

| Case | Collected minerals at 6m | At 8m | At 10m |
|---|---:|---:|---:|
| third-control-Terran-1 | 7175 | 11130 | 15530 |
| third-candidate-Terran-1 | 7155 | 11375 | 16265 |
| third-control-Terran-2 | 7150 | 10885 | 14080 |
| third-candidate-Terran-2 | 7150 | 10840 | 14570 |

The candidate gained 245 / -45 collected minerals by 8 minutes and 735 / 490 by 10 minutes in seeds 1 / 2. This modest economic effect did not translate into wins. These are API cumulative collection values, not mineral-bank proxies.

In control seed 1, 36 roaches at 420 seconds included a group of 31 within six distance units of one member; all own positional details were retained at that sample. The army reached 40 roaches at 435 seconds, then fell to 14 exposed/burrowed roaches at 465. The opponent fielded Marines, Marauders and tanks. This supports investigating the forward engagement, not attributing the first collapse solely to dispersed reinforcements or the later home-defense failure. It does not establish exact per-shot splash causation.

At 600 seconds, the candidate replay samples omit 17 / 9 own unit details in seeds 1 / 2 because of the bounded detail cap. Full own type counts and score totals remain available, but positional density measures there are lower bounds. Opponent orders/cooldowns are read only from that opponent's separate own-perspective pass.

Local derived metrics: `.local-matches/phase4-third-replay-comparison.json`. Per-match `replay-analysis-report.md` and combined reports retain fuller evaluator evidence.

Replay-pass evidence hashes:

- `20261104T224327Z-7d186b1b/replay-perspective-1.json` SHA256 `b9e88a988e85f364fbfc8bc6897979cc52bd12cea5642ebb817382a0899853dc`.
- `20261104T224327Z-7d186b1b/replay-perspective-2.json` SHA256 `75aba2c5d504e6e093ee202a367149c23e0c74d4e86defe22bc09fc41c13d199`.
- `20261104T224639Z-13de934c/replay-perspective-1.json` SHA256 `4030c2e67ed110bc050d0ab9e9a87c914e3dbc36e46b80de688ca9fd3dbc32f9`.
- `20261104T224639Z-13de934c/replay-perspective-2.json` SHA256 `6772dc753bd83f89df98d32bf16554774451a7702744bc85d6da696d2555b66b`.
- `20261104T224954Z-962e545b/replay-perspective-1.json` SHA256 `e46ef3e35bee4927aeb470754acc682d8d232ccc089ff2d20479ea769de235d6`.
- `20261104T224954Z-962e545b/replay-perspective-2.json` SHA256 `5a570a7478fe439b800f46aa0b5741e01232623756fc50042edde871e48836e9`.
- `20261104T225346Z-784f1c06/replay-perspective-1.json` SHA256 `e3b6d9abca87a2259aeb0fc563bf269c43f254b17c0471ee8632bc41efed5806`.
- `20261104T225346Z-784f1c06/replay-perspective-2.json` SHA256 `65428b3b13f3a76e22ecf6d81da4838b4365a842a78e17bd783facd4274cddac`.
