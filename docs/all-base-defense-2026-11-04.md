# Ready-base defense experiment

The production code inspected at fc29564 considered army threats only within 25
of the first ready town hall. Economy already checked every ready town hall.
A natural or third attack could therefore request emergency production while
the army kept an offensive objective. This is a confirmed targeting inconsistency,
not proof that it caused the earlier forward army collapse.

The optional `--all-base-defense` candidate selects currently visible,
ground-capable ground threats near all ready bases. It preserves the existing
25-unit envelope and attack/regroup thresholds. It does not solve air-only
pressure or include hidden enemies. Small worker incursions retain bounded
worker-squad treatment when that existing option is enabled.

Simultaneous threats use deterministic base/target tags, a 112-frame base hold,
and a two-unit count margin before switching. Real combat pressure immediately
preempts a small worker incursion; vanished threats or destroyed bases release
the objective immediately. Count ranking is a heuristic, not combat-value scoring.
Recovery endpoints prefer an unthreatened base, without claiming that the path
or fog is safe. Existing high-priority recovery/morph vetoes remain authoritative.

The hypothesis is improved response to non-main attacks. Measure actual selected
base, first visible home pressure, base/worker losses and terminal outcome; a
longer defeat alone is not success. The new bounded `defense_objective` event is
recorded every 112 frames and tested through the real recorder and strict JSON.

Control: fc29564, existing hatch-first/adaptive/roach-tech options. Candidate:
same options plus all-base defense. Keep third-base reservation, siege spacing,
detector avoidance and worker-defense experiments disabled. Compare Harder
Terran seeds 1 and 2 at 1200 game / 300 wall seconds, sequentially under the
existing CPU, memory and protected-process guards. The feature stays off by
default pending results. Offline tests cover remote-base attacks, simultaneous
pressure, switching stability, disappeared threats/bases, worker handling,
recovery arbitration and the serialized event contract.

## Completed pair and interrupted batch

Frozen candidate: `2332a9a3db4120b6caa3fa3569815b69cdd46890`; control: `fc29564d46b50c7a8fb57fc48ec810206f7cdbc9`. Runtime source stayed immutable.

| Seed | Policy | Outcome | Game seconds | Workers lost | Bases lost | Roaches lost |
|---|---|---|---:|---:|---:|---:|
| 1 | control | Defeat | 887.5 | 61 | 3 | 177 |
| 1 | candidate | Defeat | 1041.4 | 56 | 3 | 277 |
| 2 | control | interrupted; no result | 615.0 last checkpoint | not scored | not scored | not scored |
| 2 | candidate | not started | - | - | - | - |

The tool execution was aborted during seed 2 control. Its raw checkpoint remains `in_progress`, with no result or replay completion inferred. The batch session and owned SC2 processes were subsequently absent. Do not count it as a defeat, cap or successful validation. The interrupted run was not restarted.

## Decision

Keep `--all-base-defense` off by default. The only completed pair is two defeats. Candidate survival increased by 153.9 game seconds, but all three bases were lost and raw roach losses rose from 177 to 277. Different match durations confound raw loss totals; neither longer survival nor fewer worker losses establishes better play. The planned two-seed comparison remains incomplete.

The candidate selected the natural during live checkpoints; early selected targets were visible SCV scouts. Existing worker-squad defense was disabled in both policies, so expanded coverage can also expand scout-driven army recalls. That is a hypothesis for further testing, not proven causality. The initial army collapse still requires separate engagement/composition work.

At six minutes both policies had 44 workers. At eight minutes control/candidate had 57/58 workers and three bases, so there was no major early worker advantage.

Final candidate evidence retains 23 selected-objective samples, 18 at a non-main base. These are retained samples, not duration counters or complete first-contact data: bounded event retention evicted earlier events. Unit-detail snapshot limits can omit a base even when the economy count includes it. Live policy uses only ordinary currently visible ground threats.

## Verification and local evidence

249 offline tests, Ruff lint/format, compile checks, dependency checks, an isolated source/wheel build, and imports of all 32 modules from the extracted wheel passed. The no-isolation build first failed because setuptools was absent from the runtime environment; the declared isolated build succeeded using setuptools 84.2.1 without changing global packages. GitHub reported zero check runs and zero Actions runs for the exact candidate commit; no CI pass is claimed.

- `20261104T233138Z-da369407`: match JSON SHA256 `ef5d151b8939e0152a2277114b1eb327f0a5164d4b0917e54ce766d0cab2d745`; replay SHA256 `3e13dc32497291f076a5c3f3f40a4e3498cc07216c6b17472719ab3f504325b2`.
- `20261104T233516Z-4edd2723`: match JSON SHA256 `63b6eaab535f5831939dfb9b3046c68314151eb130c700cb0fe0673da08faa2a`; replay SHA256 `6af7908284c520efc4d1b545cac2c0ab5f352b914a207537ff61c788509805ad`.
- Interrupted `20261104T233957Z-c39159cb`: checkpoint SHA256 `7e65b1301158829a4f24104a6d4cbb6ec730c8604ecc3ffa7f17835f8a1b8c43`; separate local interruption manifest `phase5-base-defense-interruption.json`.

The 2 completed supervisor reports show peak sampled host CPU 82.3% and minimum available RAM 7.49 GiB. No final supervisor report was available for the interrupted run, so those extrema do not cover it. Runs were sequential, below normal, CPUs 20-23, bounded to 1200 game / 300 wall seconds. Post-interruption inspection found no SC2 process and confirmed protected SimTrader PIDs 16400 and 18472 remained Normal.

Latest read-only free-space check: C: 893,487,955,968 bytes; G: 672,579,432,448 bytes; E: 1,564,127,232 bytes. No storage cleanup was performed. Full artifacts remain local.
