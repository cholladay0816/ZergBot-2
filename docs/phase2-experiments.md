# Economy, queen and scouting comparisons

Exploratory paired runs against the unchanged pre-phase baseline. Two seeds per race; capped outcomes are censored. Multiple bundled changes do not isolate causality.

Baseline `25b8db7f7ce5d9fb88d38d3f670ae1c0c96481f1`; frozen candidate `f8606cb`.

AbyssalReefLE, Hard, 900 game seconds, 240 wall seconds, step 4, paired SC2/Python seeds

| Race / seed | Variant | Outcome / seconds | Workers 360 / 600 | Max queens / tumors | Inject attempts | Action errors | Macro attempts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Protoss / 1 | baseline | Victory / 642.86 | 43 / 44 | 3 / 0 | 34 | 0 | 0 |
| Protoss / 1 | candidate | Victory / 617.68 | 44 / 60 | 5 / 42 | 39 | 0 | 1 |
| Terran / 1 | baseline | Victory / 622.86 | 44 / 44 | 3 / 0 | 29 | 0 | 0 |
| Terran / 1 | candidate | Victory / 625.71 | 44 / 56 | 5 / 73 | 36 | 0 | 0 |
| Terran / 5 | baseline | Victory / 739.29 | 42 / 45 | 3 / 0 | 42 | 1 | 0 |
| Terran / 5 | candidate | Capped / 899.82 | 44 / 59 | 5 / 104 | 62 | 1 | 0 |

`None` means the timed observation was unavailable, not zero. Tumors and queens are peak observed counts; inject/macro attempts do not prove every command completed.

Completed pairs: 3 / 6. Local evidence: `.local-matches/phase2-six-pairs/comparison.json`.
That JSON records input paths and SHA-256 fingerprints for every paired match.

## Scouting evidence

- Protoss seed 1: {'unknown_no_mineral_line': 37, 'unknown_stale_or_unseen': 24, 'unknown_incomplete_coverage': 2, 'blocked_low_worker_value': 1}
- Terran seed 1: {'unknown_no_mineral_line': 38, 'unknown_stale_or_unseen': 21, 'unknown_incomplete_coverage': 7, 'blocked_low_worker_value': 1}
- Terran seed 5: {'unknown_no_mineral_line': 33, 'unknown_stale_or_unseen': 21}

Positive assessments, if any, are advisory and do not trigger spending. Most unknown/blocked assessments can be correct under fog; missing coverage is never safety.

## Validation and decisions

The earlier smoke exposed a missing telemetry allowlist entry and an unattainable expansion trigger after limiting gas. Both were fixed and regression-tested before these comparisons. The failed run remains local and is excluded from outcomes. Final retention decisions follow the completed comparisons; consult the current README/configuration.
