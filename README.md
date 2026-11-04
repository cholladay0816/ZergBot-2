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
but no maps were found in its `Maps` directory or the user's standard Documents
map directory. Nothing here downloads maps or launches the game on import.

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
  Burrow research and roach production. At most one spending decision per step.
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
enabled in the new runtime. Queens, injects, creep, anti-air, detector-aware escape,
tunneling claws, path-aware retreat, enemy memory and richer focus-fire/kiting
are follow-up work. The old prototype also lacked queens and creep support.

The initial economy makes a playable integration target but is not tuned for
competitive play. It has no anti-air response and rallying healthy units to home
until the attack threshold can be strategically weak. Start with installed-map
smoke matches, record replays, then add a second unit agent through the same
arbiter before expanding the composition. Add action-result telemetry and
observed transition tests before introducing more spell/morph behavior.

Offline tests cover boundaries, missing research/abilities, failed-action retries,
morph continuity, stale agents, command conflicts, the mocked SC2 boundary, actual SC2 Unit command enqueueing, and economy spending priorities.
These do not validate navigation, healing rates, actual server command acceptance,
or a complete match. **No live match has been run in this refactor session.**

Primary API references:
- https://pypi.org/project/burnysc2/7.3.0/
- https://burnysc2.github.io/python-sc2/bot_ai/index.html
- https://burnysc2.github.io/python-sc2/unit/index.html
