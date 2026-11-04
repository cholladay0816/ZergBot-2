# Phase 3 validation and handoff

Final code checkpoint: d9e324b619c0f9bb82c8022e07323a59166f6fd9.
Frozen full-match runtime: 02eb55f7c7a47bb153e942adc213946ccdea6ef6.
Branch: feature/autonomous-unit-refactor. No merge or force push.

## Checks

- 185 offline tests passed, Ruff lint and format passed (52 Python files).
- Compilation and pip dependency checks passed.
- Isolated source and wheel builds passed with declared setuptools build dependency
  (resolved 84.2.1). The first `--no-isolation` attempt correctly failed because setuptools
  was absent from the project runtime; the declared isolated build succeeded without
  changing global packages.
- Built-wheel imports of bot, scenario and worker policy passed from a temporary extraction
  with editable source lookup removed. CLI help/import checks passed.
- Runtime: Python 3.14.10, burnysc2 7.3.0, pytest 9.2.0, Ruff 0.17.3, build 1.6.1.
  Python has no official LTS; installed 3.15.2 is outside this library's supported range.
- Live SC2 build 5.0.17.98310; official Abyssal Reef map retained with SHA256
  355bcb67a337d2fa603e63e887c9c2105d894c154c1a8796a683a1a6b530c176.

## Decisions

Final Harder comparison: one Zerg victory, Terran/Protoss defeats, no caps. Prior baseline
lost all three. One seed per race does not establish a stable improvement, and Terran
survival regressed. New tech/adaptive-army/queen-micro options stay disabled. No difficulty
increase. Existing baseline, previous phase experiments and full artifacts are preserved.

Reaper micro preserves workers but underperforms baseline damage; no perfect-micro claim.
Worker-defense follow-up improves all three ling pairs but still loses 6-10 workers;
scenario-only. Full Cannon defense remains unexercised. Tank splitting remains a scenario
experiment with mixed tradeoffs. See linked ledgers for exact observations and hashes.

## Resource evidence

This hour's supervisor records: 34 runs, peak sampled total-system CPU
70.0%, minimum sampled available memory 6.59 GiB.
Sampling is not a guarantee about unsampled peaks. Tests are sequential, below-normal,
affinity CPUs 20-23, with sustained CPU/memory and wall-time guards. Full JSON index:
`.local-matches/phase3-resource-summary.json`. The initial telemetry serialization
failure is retained as a software failure, not a game defeat. No protected SimTrader
process settings were changed; PIDs 16400 and 18472 remain the protected workloads.

## Deliverables

- [Build references, frozen comparisons and 4/5/6/8-minute observations](adaptive-build-2026-11-04.md)
- [Micro scenarios, paired results, limitations and artifact hashes](scenarios-2026-11-04.md)
- [Air counter research and current implementation gaps](air-counter-policy.md)
- Local aggregate JSON: `phase3-match-comparisons.json`, `phase3-scenario-comparisons.json`,
  `phase3-worker-batch.json`, `phase3-sampling-batch.json`, `phase3-resource-summary.json`.

Full replay/telemetry contents remain local under `.local-matches`; only source, tests
and evidence summaries are published. Current limits: early mineral/gas allocation,
supported siege/capital air, mobile detection, better worker protection, stronger Reaper
worker access, actual Cannon attack setup, and broader repeated-seed validation.
