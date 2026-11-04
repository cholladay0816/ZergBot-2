# Economy, queen and scouting comparisons

Exploratory paired runs against the unchanged pre-phase baseline. Two seeds per race; capped outcomes are censored. Multiple bundled changes do not isolate causality.

Baseline `25b8db7f7ce5d9fb88d38d3f670ae1c0c96481f1`; frozen candidate `f8606cbd82a43ec83ad3283f9972a643e1a6d2f3`.

AbyssalReefLE, Hard, 900 game seconds, 240 wall seconds, step 4, paired SC2/Python seeds

| Race / seed | Variant | Outcome / seconds | Workers 360 / 600 | Max queens / tumors | Inject attempts | Action errors | Macro attempts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Protoss / 1 | baseline | Victory / 642.86 | 43 / 44 | 3 / 0 | 34 | 0 | 0 |
| Protoss / 1 | candidate | Victory / 617.68 | 44 / 60 | 5 / 42 | 39 | 0 | 1 |
| Protoss / 2 | baseline | Victory / 615.54 | 42 / 44 | 3 / 0 | 28 | 0 | 0 |
| Protoss / 2 | candidate | Victory / 596.25 | 45 / None | 5 / 74 | 36 | 0 | 1 |
| Terran / 1 | baseline | Victory / 622.86 | 44 / 44 | 3 / 0 | 29 | 0 | 0 |
| Terran / 1 | candidate | Victory / 625.71 | 44 / 56 | 5 / 73 | 36 | 0 | 0 |
| Terran / 5 | baseline | Victory / 739.29 | 42 / 45 | 3 / 0 | 42 | 1 | 0 |
| Terran / 5 | candidate | Capped / 899.82 | 44 / 59 | 5 / 104 | 62 | 1 | 0 |
| Zerg / 1 | baseline | Victory / 560.18 | 43 / None | 3 / 0 | 27 | 0 | 0 |
| Zerg / 1 | candidate | Victory / 537.50 | 44 / None | 5 / 43 | 26 | 0 | 1 |
| Zerg / 2 | baseline | Victory / 841.79 | 36 / 44 | 3 / 0 | 44 | 0 | 0 |
| Zerg / 2 | candidate | Victory / 530.00 | 45 / None | 5 / 39 | 25 | 0 | 0 |

`None` means the timed observation was unavailable, not zero. Tumors and queens are peak observed counts; inject/macro attempts do not prove every command completed.

Completed pairs: 6 / 6. Local evidence: `.local-matches/phase2-six-pairs/comparison.json`.
That JSON records input paths and SHA-256 fingerprints for every paired match.

## Scouting evidence

- Protoss seed 1: {'unknown_no_mineral_line': 37, 'unknown_stale_or_unseen': 24, 'unknown_incomplete_coverage': 2, 'blocked_low_worker_value': 1}
- Protoss seed 2: {'unknown_no_mineral_line': 46, 'unknown_stale_or_unseen': 12, 'unknown_incomplete_coverage': 3, 'blocked_low_worker_value': 1}
- Terran seed 1: {'unknown_no_mineral_line': 38, 'unknown_stale_or_unseen': 21, 'unknown_incomplete_coverage': 7, 'blocked_low_worker_value': 1}
- Terran seed 5: {'unknown_no_mineral_line': 33, 'unknown_stale_or_unseen': 21}
- Zerg seed 1: {'unknown_no_mineral_line': 42, 'unknown_stale_or_unseen': 12, 'unknown_incomplete_coverage': 1, 'blocked_known_anti_air': 1}
- Zerg seed 2: {'unknown_no_mineral_line': 43, 'unknown_stale_or_unseen': 9, 'unknown_incomplete_coverage': 3}

Positive assessments, if any, are advisory and do not trigger spending. Most unknown/blocked assessments can be correct under fog; missing coverage is never safety.

## Validation and decisions

The earlier smoke exposed a missing telemetry allowlist entry and an unattainable expansion trigger after limiting gas. Both were fixed and regression-tested before these comparisons. The failed run remains local and is excluded from outcomes. Final retention decisions follow the completed comparisons; consult the current README/configuration.

## Final checkpoint and progression probes

The frozen candidate won five of six Hard games, with one unresolved cap; baseline won all six.
Four candidate wins were earlier, Terran seed 1 was nearly unchanged, and Terran seed 5 regressed
to a cap. The requested stronger economy/queen foundation is retained for continued development,
not advertised as an overall win-rate improvement. The Terran regression remains unresolved.
Macro hatches were submitted in three frozen-candidate games; attempts are not completion proofs.
Macro counts in this table use retained events and may undercount if detailed events were evicted.

Post-comparison checkpoint `19307e2` observes macro eligibility every step, resets stale scarcity,
records separate resource/production base counts, and recognizes local air/structure threats for
queens. It reserves injection when a healthy nearby extra queen can defend. Checkpoint
`85e416570e29c88a7c4440d5475d8ba859a3f32f` adds explicit queen action targets. It also includes the
counter-tech/fog uncertainty assessment refinements. These later changes are not silently treated
as the source of the six-pair benchmark.

Five candidate wins across all races justified a limited Harder probe, not a stable win-rate claim.
Each probe uses one seed and a 1200-game-second/300-wall-second bound. Results below are separate
from the matched Hard comparison. Default difficulty remains Hard; no further automatic escalation.

| Validation/probe | Race | Difficulty | Seed | Outcome | Game seconds | Wall seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 85e4165-safety-Protoss | Protoss | Hard | 1 | Victory | 586.61 | 101.22 |
| 85e4165-Harder-Terran | Terran | Harder | 1 | Defeat | 868.39 | 175.71 |
| 85e4165-Harder-Protoss | Protoss | Harder | 1 | Defeat | 826.43 | 155.37 |
| 85e4165-Harder-Zerg | Zerg | Harder | 1 | Defeat | 1041.25 | 214.05 |

The final-head Hard Protoss smoke is only one paired validation, not a rerun of all six seeds.
The corrected macro gate need not fire if resources, larvae or threats fail its sustained conditions. No production hatchery was observed in the four final-runtime runs: peak observed resource bases were three and production hatcheries zero. The earlier frozen candidate did submit macro hatches; that is not claimed as live activation of the corrected timer.
Latest per-match resource-base/production-hatch observations are preserved in the local final evidence
index and each report. Air-threat controller tests include Phoenix pressure; live queen target events
only support the specific targets actually recorded, not blanket anti-air effectiveness.

Mutalisk assessments remained advisory. Unknown/blocked verdicts are reported honestly; there is
no automated spire/mutalisk purchase or harassment controller. A positive gate is tested offline,
not claimed as a live-game harassment success. Current scouting can fail to obtain complete fresh
mineral-line coverage; improving safe scouting is a concrete next step.

Final defaults: adaptive workers capped at 66, two extra queens after two resource bases, one
conditional macro hatch after three resource bases, scouting on, regroup 11, worker squads off,
emergency burrow escape off. Thresholds remain configurable; the preserved baseline is available
for comparison. No merged branch, global package replacement or unrelated workload changes.

Offline validation: 139 tests, Ruff lint/format, compileall, dependency checks, isolated wheel build,
built-wheel imports and CLI checks passed. Primary/current patch references and historical guide
limitations are documented in `economy-queens-scouting.md`.

Phase resource reports: 18; reasons {'completed': 18}; runtime exit codes {'1': 1, '0': 17}. Sampled host CPU peaked at 22.7%; available memory stayed above 11.09 GiB. The early fixed software failure is excluded from match comparisons; resource completion alone does not imply a successful game.

Local evidence: `.local-matches/phase2-final-evidence.json` and `.local-matches/phase2-six-pairs/comparison.json`. Comparison SHA-256: `a94e90add1a99d1b9d5e99400932912844dfb55286f21175d2c6ca8e093037da`. The evidence index includes all input paths/hashes and separates later probes from the frozen benchmark. Full replays/telemetry remain local.

## Extension: observed detection recovery experiment

Hypothesis: recovery under visible detection plus nearby ground attackers contributes to
burrowed-roach attrition. Frozen 85e4165 Harder seed-1 Terran/Protoss/Zerg runs recorded
153/126/227 own ROACHBURROWED destruction observations and 18/21/60 confirmed emergences.
Retained five-second detailed snapshots show Ravens/Overseers within a conservative 13-unit
analysis neighborhood of 41/97 burrowed-roach samples in Terran/Zerg; no Protoss detector was
visible. This is correlation, not proof of the damage source; detailed events were bounded/evicted.

Candidate `--avoid-detected-burrow` is opt-in. It requires a currently visible, completed detector
with positive reported detection range covering the roach and a visible ground attacker within
weapon range plus radii plus a conservative three-unit movement margin. It retreats exposed
recovering roaches, emerges hidden ones when available, preserves in-flight morph guards, and
holds retreat for 56 frames after the last risky observation. No unseen observers, scans, spells
or fog-of-war detection are inferred. This does not solve unanswerable air armies or all-base defense.

Primary metrics: completed win/defeat/cap outcomes, own roach destruction observations, confirmed
burrow/emergence counts, and decision activation. Compare against the existing frozen 85e4165
Harder seed-1 runs for all three races at 1200 game seconds/300 wall seconds, identical map,
SC2/Python seeds, versions and step size. Do not promote from a single favorable result.
Offline candidate validation: 150 tests and Ruff lint/format passed. Results pending.
