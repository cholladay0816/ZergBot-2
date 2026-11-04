# ZergBot-2: autonomous unit rebuild

A StarCraft II Zerg bot with persistent per-roach agents, bounded match diagnostics,
and reproducible local experiments. The original prototype remains unchanged in
`legacy/zergbot2.py`; the new runtime is a roach-focused foundation, not feature
parity with its old ravager/lurker/infestor heuristics.

## Runtime and Windows launch

Validated on **CPython 3.14.10**, **BurnySC2 7.3.0**, and local SC2
**5.0.17.98310**. Python has no official LTS edition. The installed 3.15.2 is outside
BurnySC2 7.3.0's declared `>=3.9,<3.15` range, so project support is scoped to 3.14.
Use an isolated environment; no global package replacement is needed.

```powershell
& 'G:\SimTraderRuntime\Python314\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
$env:SC2PATH = 'G:\StarCraft II'
.\.venv\Scripts\python.exe -m zergbot --map AbyssalReefLE --difficulty Hard --seed 1 --game-time-limit 1200
```

The lock records this Windows/Python environment, not universal platform support.
`zergbot2.bat` is a compatibility launcher. `--help` does not start SC2; imports do
not launch it. Without `--realtime`, simulation advances as fast as the local game
and bot can process it. Acceleration is measured per match, never a guaranteed multiplier.

Abyssal Reef was installed at `G:\StarCraft II\Maps\AbyssalReefLE.SC2Map` from
[Blizzard's official 2017 Season 1 pack](https://blzdistsc2-a.akamaihd.net/MapPacks/Ladder2017Season1.zip)
after the user accepted its AI and Machine Learning License. Map SHA-256:
`355bcb67a337d2fa603e63e887c9c2105d894c154c1a8796a683a1a6b530c176`.

## Economy, queens and scouting extension

The next phase adds capacity-aware workers (up to 66), extra queen roles, conditional macro
hatcheries, and conservative live scouting. Mutalisk viability is advisory only; no speculative
transition is purchased. See [policy, controls and dated build-order references](docs/economy-queens-scouting.md)
and [phase results](docs/phase2-experiments.md) for measured behavior and limitations.

## Current behavior

- Roaches recover at 40% HP and normally resurface at 80%, with separate thresholds
  to prevent oscillation. Research and each unit's queried capabilities gate burrow.
- A morph attempt is not completion. Active orders/type observations protect the
  transition, including temporary ability disappearance. A 64-frame timeout handles
  rejected/stalled transitions; an eight-frame retry interval prevents rapid retries.
- Stable unit tags preserve agent identity through burrow/unburrow; absent tags are
  pruned. Survival orders and an explicit no-command veto outrank army orders.
- Queens inject available unbuffed bases. Production reserves roaches before optional
  workers, accounts for pending units, and buffers projected supply. Expansions check
  exact placement and visible threats, throttle retries, and do not starve production.
- Army launch threshold is 12 healthy exposed roaches; current regroup threshold is
  **11**. Worker-defense squads are **off** after mixed six-seed results.
- Emergency emergence after observed HP loss while already buried uses a current
  escape duration of **0 frames** (disabled).
  It does not infer a detector or attacker from HP loss; legitimate morph guards
  still apply. See the experiment journal for its measured tradeoffs.
- Expansion-site search is **enabled**. When known
  enemy structures are gone, it can sweep static map sites instead of camping at
  the enemy start. Advancement requires actual vision and a nearby healthy roach;
  sites are hypotheses, not unseen enemy facts. `--search-expansions` and
  `--no-search-expansions` explicitly select this behavior.

Controls are explicit and recorded in each match's `bot_config`:
`--worker-defenders 0` disables squads; `--regroup-roaches 11` restores the original
12-unit attack/retreat trigger; `--burrow-escape-frames 0` disables emergency escape.
Positive squad size/escape duration opt into those policies. Game steps default to
four frames. `--seed` seeds both SC2 and Python/NumPy gameplay choices after startup.
Fixed seeds improve repeatability without promising bit-for-bit engine determinism.

## Architecture

| Module | Responsibility |
| --- | --- |
| `config.py` | Validated immutable runtime/policy settings |
| `bot.py` | Frame orchestration, objectives and lifecycle callbacks |
| `strategy.py` | Army posture and optional bounded worker-defense assignments |
| `search.py` | Bounded, visibility-gated search of known map expansion sites |
| `economy.py`, `macro.py` | Adaptive capacity, spending, production and expansion gates |
| `queens.py` | Persistent inject assignments, defense and bounded creep actions |
| `scouting.py` | Live scouting memory and advisory mutalisk feasibility |
| `agents.py` | Pure per-unit state/decisions and one-command-per-tag arbitration |
| `integration.py` | SC2 translation and one batched ability query for roaches/queens |
| `telemetry.py`, `diagnostics.py` | Explicit observation fields, bounded capture/checkpoints |
| `combat_report.py`, `report.py`, `compare.py` | Readable evidence, regeneration and matched comparisons |
| `replay_analysis.py`, `replay_combined.py` | Separate post-game player-perspective analysis |

Unit agents make no network calls. Current BurnySC2 unit calls enqueue commands
directly; the gateway does not enqueue them a second time through `BotAI.do`.

## Diagnostics and visibility

Every normal run creates an ignored `.local-matches/MATCH-ID/` directory containing
`match.json`, `report.md`, and a replay when saving is possible. Full match artifacts
stay local. Reports link findings to event IDs and propose concrete next experiments.

Capture includes economy/supply/production/upgrade timelines, own and visible enemy
counts/positions, creation/destruction/morph observations, per-unit decisions/reasons,
capabilities, attempted commands, active orders and action rejections. Unit details
include buffs, cloak, detection fields, terrain height and base weapon ranges. Enemy
orders/cooldowns/engaged-target fields remain unknown; optional proto fields remain
null, and fog snapshots are excluded. Destruction observations can include consumed
or morphing units and are not automatically combat kill credits.

Damage evidence is own observed HP/shield loss with nearby visible candidate attackers,
current distances, terrain differences and effects. Candidates are **correlations**,
not exact causes: splash, spells, projectiles, fog, regeneration and multiple attackers
limit attribution. Fatal-frame loss can be absent. Effects expose owner/radius/positions,
not necessarily caster identity. No universal high-ground damage bonus is invented.

Defaults retain 10,000 detail events plus 512 independent timeline snapshots, sampled
every 112 game frames. Per-frame events, damage scans and unit details are capped.
Repeated orders are counted but not all written in detail; morph attempts remain
detailed. Lifetime bounded counters preserve morphs, decision changes and destruction
observations across event eviction. Coverage/drops are explicit. There is at most
one background write, checkpointed every 30 wall seconds; abrupt termination may
lose the newest interval. Measured instrumentation time excludes background I/O.

Startup failures are distinguished from game losses even when the library returns
`Defeat`; failures return a nonzero CLI exit and cannot enter performance comparisons.
Structured capture excludes chat, credentials, environment variables, arbitrary
object representations and exception text. `--no-diagnostics` disables capture/replays.

```powershell
.\.venv\Scripts\python.exe -m zergbot.report .local-matches\MATCH-ID\match.json
.\.venv\Scripts\python.exe -m zergbot.replay_analysis .local-matches\MATCH-ID\match.SC2Replay --wall-timeout 240
```

Replay analysis uses the installed matching SC2 build in two sequential player
perspectives. Although fog disabling is requested, tested raw enemy entries remained
visibility-limited. `replay-combined.json` therefore joins each player's **own** economy,
counts, upgrades and capped unit/order details at identical frames, validating replay
SHA-256/build/step provenance. Missing frames remain null. These post-game views never
feed competitive decisions and are not an exhaustive cast log or exact damage account.
Partial replay passes retain their own failure/timeout artifacts.

## Validation and remaining work

The November 4, 2026 checkpoint passed **214 offline tests**, lint/format checks,
compilation, dependency checks and wheel validation. Tests cover pure decisions,
morph continuity/timeouts, capability fallbacks, command arbitration, real SC2 command
construction, economy priorities, diagnostic bounds/privacy, replay provenance, CLI
failures and comparison semantics. Live accelerated games separately exercised startup,
production and actual burrow/resurface transitions. Offline tests are not live-game proof.

[Experiment decisions and paired results](docs/experiments-2026-11-04.md) distinguish
retained changes from rejected candidates. Capped games are unresolved, not wins.
Small seed sets are exploratory and do not establish a stable win rate or isolate
every cause. Local tests were sequential, below-normal priority and resource-bounded.

Remaining bottlenecks include mineral/gas balance, anti-air composition, upgrades,
multi-base defense, retreat path choice, scouting/enemy memory, creep, focus fire and
kiting. The original prototype's broader unit/spell logic has not been ported.

Primary API references: [BurnySC2 7.3.0](https://pypi.org/project/burnysc2/7.3.0/),
[BotAI](https://burnysc2.github.io/python-sc2/bot_ai/index.html),
[Unit](https://burnysc2.github.io/python-sc2/unit/index.html),
[Blizzard protocol](https://github.com/Blizzard/s2client-proto).

Experimental visible-detector recovery is available via `--avoid-detected-burrow` and defaults off.
Its three matched Harder race probes yielded two defeats and one unresolved cap, so it was not
promoted. It requires observed detection coverage and a nearby ground threat; it cannot infer
unseen detectors or exact damage sources. See the [phase ledger](docs/phase2-experiments.md).

## Adaptive build and controlled micro validation

The latest optional wave adds `--roach-tech`, `--adaptive-army`, and
`--queen-tactical-micro`. They remain off pending broader evidence. See the
[dated build references and matched results](docs/adaptive-build-2026-11-04.md)
and [controlled scenario evidence and limitations](docs/scenarios-2026-11-04.md).
Hydralisks are not assumed to counter every air composition. The scenario harness
is isolated from competitive decisions and does not establish perfect micro.

Continued opening and survival experiments are documented in the
[continued iteration ledger](docs/continued-iteration-2026-11-04.md).
`--opening-supply`, `--hatch-first`, and `--queen-recovery` remain off by default.
Their capped economy/scenario probes are separate from full-match win evidence.
