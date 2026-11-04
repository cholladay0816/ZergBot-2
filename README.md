# ZergBot-2: autonomous unit rebuild

A StarCraft II Zerg bot with persistent per-roach agents. The new entry point uses
BurnySC2 7.3.0 and an isolated Python 3.14 environment. Python has no official LTS
edition: this checkout was tested with the installed **CPython 3.14.10** at
`G:\SimTraderRuntime\Python314\python.exe`. Installed 3.15.2 is excluded because
BurnySC2 7.3.0 declares `>=3.9,<3.15`. Project support is deliberately scoped to
3.14 until another version is tested. No system packages need replacing.

## Windows setup

In PowerShell, from this repository:

```powershell
& 'G:\SimTraderRuntime\Python314\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests zergbot2.py
```

`requirements-lock.txt` records the exact validated Windows environment. To reuse
those dependency versions, install it before installing this project with `-e .`.
The lock is platform/runtime specific, not a cross-platform guarantee.

Install StarCraft II and an official/otherwise trusted melee map separately.
On this host SC2 was found at `G:\StarCraft II` (versions Base97563 and Base98310),
and Abyssal Reef is now installed in `G:\StarCraft II\Maps\AbyssalReefLE.SC2Map`.
It was extracted after user license acceptance from Blizzard's official
`https://blzdistsc2-a.akamaihd.net/MapPacks/Ladder2017Season1.zip`.
Map SHA-256: `355bcb67a337d2fa603e63e887c9c2105d894c154c1a8796a683a1a6b530c176`. Nothing here downloads maps or launches the game on import.

```powershell
$env:SC2PATH = 'G:\StarCraft II'
.\.venv\Scripts\python.exe -m zergbot --map AbyssalReefLE --difficulty Hard
# Or: .\zergbot2.bat --map YourInstalledMap --difficulty Medium
```

Use `--help` without starting SC2. `--realtime` is optional; otherwise the game
runs at simulation speed. Map names must match an installed `.SC2Map` file.

## Architecture

- `config.py`: validated immutable health thresholds, population and step settings.
- `bot.py`: frame orchestration, objective selection and one dispatch point.
- `strategy.py`: conservative army-level defense/attack objectives.
- `economy.py`: workers, supply, gas, expansion, spawning pool, roach warren,
  Burrow research, queens/injects and roach production. At most one spending decision per step.
- `agents.py`: pure observations, persistent tag-indexed agent state, hysteresis,
  retry timing, and one-command-per-tag priority arbitration.
- `integration.py`: one batched ability query per frame, current SC2 observations,
  and current BurnySC2 command translation. No per-agent network calls.

Roaches enter recovery at **40% health**, burrow only when research is complete
and that individual unit reports the ability available, and emerge at **80%**.
Between thresholds they remain in recovery. If burrow is unavailable, an exposed
roach retreats toward the selected home objective; a burrowed roach waits
when emergence is unavailable. A pending morph vetoes other orders while awaiting the observed type change and
active morph-order completion, even when abilities disappear during the transition.
The gateway recognizes both exact and remapped active burrow/unburrow order IDs.
A configurable **64-game-frame timeout** bounds rejected/stalled attempts; after
timeout the agent retries an available morph or retreats if exposed (waits if hidden).
Continuous stale orders do not reset that timer. An eight-frame minimum command
interval also prevents rapid opposite transitions. The timeout is a conservative
controller default, not a measured live-game animation guarantee.
State follows the stable unit tag through `ROACH`/`ROACHBURROWED` transitions and
is pruned when the tag disappears. Commands do not imply a successful morph;
the following observations are authoritative. Survival intents override strategy,
including an explicit no-command veto while healing. Defaults use four-frame steps.

## Scope and next steps

This is a testable **roach-focused foundation**, not a claim of strategic parity
with the 2020 prototype. The original is preserved byte-for-byte in
`legacy/zergbot2.py` for porting/reference and is excluded from lint. Its old
multi-unit counter heuristic, ravager/lurker/infestor spells and scouting are not
enabled in the new runtime. Creep, dedicated anti-air composition, detector-aware escape,
tunneling claws, path-aware retreat, enemy memory and richer focus-fire/kiting
are follow-up work. The old prototype also lacked queens and creep support.

The initial economy makes a playable integration target but is not tuned for
competitive play. It has no dedicated anti-air strategy (queens can defend locally), and rallying healthy units to home
until the attack threshold can be strategically weak. Start with installed-map
smoke matches, record replays, then add a second unit agent through the same
arbiter before expanding the composition. Add action-result telemetry and
observed transition tests before introducing more spell/morph behavior.

Offline tests cover boundaries, missing research/abilities, failed-action retries,
morph continuity, stale agents, command conflicts, the mocked SC2 boundary, actual SC2 Unit command enqueueing, and economy spending priorities.
These do not validate navigation, healing rates, actual server command acceptance,
or a complete match. An accelerated 180-game-second smoke run on SC2 **5.0.17.98310**, Hard Terran,
seed 1 completed at its time limit with a replay and no runtime/action errors.
Observed game time / full match wall time was **5.23x** (180s / 34.40s including
startup); this is a measurement, not a guaranteed multiplier. It verified startup,
economy and recording, but ended before roach micro/combat was exercised.

Primary API references:
- https://pypi.org/project/burnysc2/7.3.0/
- https://burnysc2.github.io/python-sc2/bot_ai/index.html
- https://burnysc2.github.io/python-sc2/unit/index.html


## Detailed match diagnostics

The normal launcher writes a unique directory under ignored `.local-matches/`:
`match.json` (structured evidence), `report.md` (evidence-linked findings/next
experiments), and `match.SC2Replay` when the client can save it. Full artifacts
stay local and are not committed. A caught failure writes a final report with its
exception class (not arbitrary exception text). Background checkpoints preserve
partial evidence every 30 wall seconds; abrupt process termination may lose the
latest interval. Startup failure may leave no replay. An artificial time-limit
Tie is distinguished from a completed competitive match.

```powershell
.\.venv\Scripts\python.exe -m zergbot --seed 1 --game-time-limit 600
.\.venv\Scripts\python.exe -m zergbot.report .local-matches\MATCH-ID\match.json
```

`--sample-frames` defaults to 112 game frames (~5 game seconds), `--max-events`
to 10,000 retained detailed events plus a separate 512-snapshot timeline, and `--no-diagnostics` disables capture/replays.
`DiagnosticConfig` also bounds per-frame events (128), damage details (16/frame),
unit details (96 per side/sample), and checkpoint cadence. Repeated movement and
attack attempts are counted but detailed only when decisions change; morph attempts
remain detailed. Ring-buffer eviction and truncation are explicitly reported.
There is at most one asynchronous disk-write task, never a growing write queue.
Measured instrumentation time excludes background serialization/disk I/O.

Evidence includes own resource/supply/production/upgrade timelines, counts,
positions, observed creation/destruction/morph events, roach reasons and recovery
state, command attempts, observed active orders and API action errors. Unit detail
includes buffs, cloak state, detector presence, terrain height, base weapon ranges,
and own cooldowns/targets/orders. Visible effects include owner, radius and positions.
Destruction events can include worker consumption for construction; they are not
automatically credited as combat kills.

Damage records describe observed own HP/shield loss and nearby visible candidate
attackers with current distance and terrain-height difference. These are **ambiguous
correlations**, not exact attribution: projectiles, spells, fog, regeneration,
self-damage and multiple attackers prevent universal causal reconstruction.
Fatal-frame loss callbacks may be absent. Range candidates use unupgraded base range
plus collision radii and a three-unit motion margin. Effect owner is not caster
identity; observing a buff/effect does not prove who cast it. Height differences
are not treated as a universal damage bonus.

Enemy detail is restricted to **currently visible units**. Enemy orders, cooldowns
and engaged-target fields are null because the protocol does not populate them.
Missing optional fields remain null; snapshots under fog are excluded. No enemy
economy, unseen casts, or total opponent visibility is invented. A separate post-game
replay pass with disabled fog expands evidence from both player perspectives;
it is never imported or fed into competitive decisions. Chat, environment variables,
credentials and arbitrary object/exception representations are not captured.

Reports propose controlled next experiments tied to event IDs. Compare the same
map, seed and difficulty, inspect replay alongside telemetry, change one behavior,
and compare multiple runs before drawing causal conclusions from win/loss results.


### Separate replay intelligence

```powershell
.\.venv\Scripts\python.exe -m zergbot.replay_analysis .local-matches\MATCH-ID\match.SC2Replay
```

This launches the installed matching SC2 build for two sequential player-perspective
post-game passes. Fog disabling is requested, but raw enemy entries can remain
visibility-limited. Outputs are `replay-perspective-1.json`,
`replay-perspective-2.json`, `replay-combined.json` and `replay-analysis-report.md`
beside the replay. The combined file joins each player's own evidence by exact frame.
Each player's economy/private orders are obtained in their own perspective, not
invented from enemy protocol defaults. Unit details, effects, upgrades and sampled
actions remain bounded (112-frame default step, 1,000 samples per pass, 192 detailed
units per sample, 180-second combined wall timeout). Use CLI options to change
those limits. Partial output records failure/timeout; sampled actions are not an
exhaustive cast log. This needs the matching installed game/data version and does
not replace exact causal damage instrumentation that the SC2 API does not expose.

The longer live Hard-Terran seed-1 test ended in a normal **Defeat** after
476.07 observed game seconds / 55.66 wall seconds (~8.55x including startup).
It recorded nine actual burrows, six actual resurfacing transitions, and Burrow
research at 218.57s. One hatchery placement was rejected with
`CantBuildLocationInvalid`; no Python exception occurred. Retained evidence showed
large mineral stockpiles and worker-heavy larva allocation before combat. These
are starting points for controlled economy experiments, not proof of a single
cause of defeat. Full match/replay/resource artifacts remain local.


## Controlled economy candidate

The first candidate addresses evidence from the seed-1 baseline: worker-first
larva allocation, no queen injects, and a rejected expansion during an invasion.
It produces one queen per ready base, injects idle eligible queens into unbuffed
bases (one reservation per base per step), and shares the existing batched ability
query. Larva production maintains six roaches before optional workers once at least
20 workers exist; visible ground attacks raise the reserve to the attack threshold.
Pending and burrowed roaches count toward the reserve. This is a deliberately small
production policy, not a complete build-order or queen micro system.

Expansions check the exact canonical location, reject nearby visible ground enemies
or enemy structures, and retry at most every 224 game frames (~10 seconds). Blocked
attempts do not starve other production. The game can still reject an otherwise
valid order if conditions change before execution; those errors remain recorded.
Inject attempts and expansion decisions are included in diagnostics.

Experiment protocol: compare unchanged commit `624e407` with the candidate on
AbyssalReefLE, Hard Terran, seeds 1/2/3, four-frame steps, `realtime=False`, a
600-game-second cap and 180-wall-second cap. Runs are sequential, below-normal
priority on logical CPUs 20–23, with system CPU/memory contention monitoring.
Primary metrics fixed before candidate runs: roaches at 240/360 seconds, sampled
larva availability, mineral accumulation, supply blocking and outcome/survival.
Also inspect inject attempts, morph confirmations and action errors. This bundled
candidate cannot isolate the contribution of each change; three seeds are an
exploratory check, not a reliable win-rate estimate. Full baseline and candidate
artifacts remain local and unchanged.


Wave 1 exploratory result (baseline `624e407`, production candidate `b1ceca7`):
all three candidate seeds reached the 600-second cap; baseline seeds 1/2 lost at
476.07/476.61 seconds and seed 3 reached the cap. Seeds 1/3 had 6/6 roaches at
240 seconds and 12/8 at 360, versus 0/1 and 0/1 in the baseline. Seed 2's early
timeline was evicted by the detail-event cap; it is reported as missing, not zero.
An independent bounded snapshot buffer now protects economy evidence from combat
event bursts, and lifetime morph-confirmation counters survive detail eviction.
Seed 1's midgame blocked-supply sample rate increased from 0% to 12.2%, and seed 3's
from 0% to 20.4%. Earlier supply is therefore the next controlled hypothesis.
These are capped exploratory runs, not demonstrated wins or isolated causal effects.


Wave 2 hypothesis: the higher larva throughput made the old four-supply overlord
trigger too late. The candidate reserves 8/12/16 projected free supply at one/two/
three ready bases, accounts for pending overlords, and never queues redundant
supply beyond the 200 cap. Only the supply policy changes in this wave. Compare
seeds 1/2/3 against `dbdba87`, now with a 1,200-game-second/300-wall-second cap so
the earlier ten-minute censored outcomes can develop. Primary metric is blocked-
supply sample fraction from 120–360 seconds; also track army, minerals and outcomes.


Reproducibility correction: the earlier exploratory runs set SC2's game seed but
did not seed Python's random placement choices inside BurnySC2. `--seed` now also
seeds Python/NumPy at `on_start`, after process/port initialization. Diagnostics
record `python_seed` and effective bot configuration; the comparison tool rejects
different gameplay steps or Python seeds. Future matched experiments also apply
this initialization to preserved baseline code through the local test harness.
Earlier results remain exploratory; fixed seeds do not promise bit-for-bit server
determinism. No host-wide or SimTrader random state is changed.


Wave 3 candidate hypothesis: a small worker incursion near the main can repeatedly
redirect the entire army between home and the enemy objective. A persistent squad
of at most two nearby healthy roaches now handles at most two visible enemy workers;
the remaining army retains its normal objective. Larger or combat-unit incursions
still request full defense. Dead, recovering and distant defenders are replaced;
per-unit recovery/morph vetoes retain priority. This does not yet defend every
expansion or estimate unseen threats. Evaluate paired seeds against the retained
supply policy, measuring outcomes and army-objective/defense switching.

Combat reports group retained HP/shield-loss observations by game minute, with multiple/no-candidate counts and event references. Effect, buff and cloak counts are sampled appearances, not distinct casts or proven causes. Bounded lifetime decision-change and destruction-observation counters survive detail eviction. These counters are absent (unknown) in older artifacts.


Wave 2 retained result (three paired SC2/Python seeds, 1,200-second cap): sampled
supply-block fractions at 120-360 seconds fell from 16.3/30.6/16.3% to 2.0/0/0%.
Both variants won seed 1 (851.96s baseline, 622.86s candidate) and reached the cap
on seeds 2/3. Roaches at 360s were 8/11/8 versus 8/9/8. Seed 2 held more minerals
and fewer roaches, so this supports improved supply availability without claiming
uniform production improvement or a stable win-rate advantage. No invalid hatchery
placements occurred in these six runs. The local wave2-supply comparison preserves
source artifact paths and hashes. Larger supply buffers are retained for later waves.


Wave 4 candidate hypothesis: the single 12-healthy-roach attack threshold recalls
the whole army as soon as one member is wounded or burrows. In supply-candidate
seed 2, retained evidence recorded 656 healthy army-retreat decisions after 400
seconds, often eleven at the same frame. The candidate launches at twelve healthy
roaches and keeps attacking until six or fewer remain healthy and exposed. Local
survival vetoes and immediate base defense still apply. Compare matched outcomes
and healthy retreat transitions, rather than assuming fewer retreats means better
combat. Missing/burrowed units cannot hold the offensive posture alive.


Wave 5 candidate hypothesis: waiting to heal is unsafe when a buried roach is
actually losing HP. Defender seed 2 retained 341 damage observations on buried
roaches and 78 buried-roach destruction observations. The candidate responds to an
HP decrease across two consecutive buried observations by requesting emergence,
then retreating for a bounded 112-frame escape interval before considering another
burrow. It does not infer a detector, caster or attacker from that HP loss. Missing
emerge capability waits safely, and legitimate morphs retain their transition
guard. Compare outcomes and buried losses against the preceding retained policy;
escaping can itself expose a unit to more damage, so this remains experimental.


Replay visibility validation: on SC2 5.0.17, requesting `disable_fog=True` did not
make enemy raw-unit entries omniscient in a player-perspective pass. Do not treat
an empty enemy list as an empty enemy army. The replay analyzer now joins each
player's own observations at identical frames into `replay-combined.json`, with
replay SHA-256/build/step validation. This provides both private economies, full own
counts and capped own unit/order details without feeding them to the live bot.
Missing player frames remain null. Older artifacts' `opponent_counts_fog_disabled`
field means returned visible enemies despite its misleading old name; schema 2
renames it `visible_opponent_counts`. Neither view establishes exact damage causes.


Experimental controls are explicit and recorded in each match's `bot_config`:
`--worker-defenders 0` disables the squad, `--regroup-roaches 11` reproduces the old
12-unit attack/retreat trigger, and `--burrow-escape-frames 0` disables emergency
escape. Positive squad size / escape duration opt into those experiments. The
worker squad is not promoted after mixed held-out results; emergency escape stays
off until its live comparison. The default six-roach regroup threshold is the
next active candidate, not yet a retained performance claim.

Wave 3 six-seed decision: do not promote the worker-defense squad. The baseline produced 2 wins, 1 loss and 3 capped games; the candidate produced 3 wins and 3 losses. It gained seed 2 but lost seeds 3/5 before the cap, and was slower in seed 4. Capped games are unresolved outcomes, so these data do not establish a better win rate. The squad defaults to zero; its opt-in implementation remains available for later investigation.



Endgame search candidate: the hysteresis seed-3 run ended capped with 72 roaches
repeatedly attacking the cleared enemy starting location. `--search-expansions`
opts into a deterministic sweep of known map expansion sites when the army is on
offense, there are no local defense threats and no known enemy structures. A site
advances only when actually visible and a healthy exposed roach is nearby, with a
112-frame dwell guard. These are candidate locations, not unseen enemy intelligence;
known structures and survival orders retain priority. The experiment stays off by
default until live evaluation and cannot solve unreachable flying buildings.
