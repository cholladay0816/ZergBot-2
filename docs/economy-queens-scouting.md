# Economy, queens and scouting - November 4, 2026

This phase preserves baseline `25b8db7f7ce5d9fb88d38d3f670ae1c0c96481f1` and its local artifacts.
It is a bounded adaptive extension to the existing pool/roach opening, not a claim to implement
one universally best build order. Matchups, map, opponent pressure and installed balance matter.

## Patch and source context

- [Blizzard 5.0.17 notes](https://news.blizzard.com/en-us/article/24309308/starcraft-ii-5-0-17-patch-notes)
  restore 12 starting workers and roll back most 5.0.16 changes. Brief eight-worker-era guides
  are therefore not copied into this installed 5.0.17.98310 environment.
- [Blizzard 5.0.14 notes](https://news.blizzard.com/en-us/article/24162754/starcraft-ii-5-0-14-patch-notes)
  changed queen/hatchery mineral prices. Production uses the installed game data through
  `can_afford`, `train` and `build`; policy reserve thresholds are not hard-coded unit costs.
- [Blizzard Queen Tips](https://news.blizzard.com/en-us/article/5967865/game-guide-zerg-queen-tips)
  supports separate injection and defensive/creep responsibilities. This historical guide's
  old numerical inject timings are not used; current buffs and queried abilities decide readiness.
- [Blizzard Multiple Hatcheries](https://news.blizzard.com/en-us/article/5838585/game-guide-zerg-multiple-hatcheries)
  motivates extra safe production when resources exceed larva throughput. It is historical
  conceptual guidance, not a current exact timing prescription.
- [SC2 Swarm macro openings, 2018](https://swarmscblog.wordpress.com/2018/06/29/zerg-macro-openings/)
  describes early expansion, saturation and larva tradeoffs. Its historical opening timings
  are not a 2026 guarantee; the current bot retains its tested pool/roach foundation.
- [Blizzard Mutalisk Tips](https://news.blizzard.com/en-us/article/5967866/game-guide-zerg-mutalisk-tips)
  motivates worker-line harassment and counter scouting. Obsolete spell/mechanic details are
  not copied. [Railgan's replay-backed ZvZ two-base muta guide, 2020](https://lotv.spawningtool.com/build/119736/)
  is a matchup-specific historical transition example, not a universal ZvT/ZvP/ZvZ opening.

## Adaptive economy and production

`macro.py` contains testable policies. Resource bases are townhalls within eight map units of
known expansion sites. A production hatch away from those sites does not increase resource
base quotas or mineral saturation targets. Worker goals follow actual ready mineral/gas
capacity plus pending resource-base capacity, capped at 66 by default. The expansion trigger
uses attainable current capacity so limiting early extractors cannot strand the bot at 19 workers.

Gas construction scales with worker count and existing stockpiles. During gas surplus, at most
three eligible gas workers per eight iterations move to underfilled mineral lines; ordinary
worker redistribution is skipped on those frames to prevent conflicting worker commands.
Visible attacks reserve roach production before optional queen/tech spending. Supply remains
the first production safety check. One mineral/gas spending choice is made per step.

One additional macro hatch is allowed after three ready RESOURCE bases, at least 50 workers,
600 minerals and at most three larvae persist for 224 game frames without a visible home attack.
Pending hatcheries block duplicates. Placement must be on creep, away from resource-base sites,
and away from visible enemies; retries are bounded. The macro hatch gets its own inject queen.
This is a conditional throughput response, not an unconditional early hatch investment.

## Queen roles and command priorities

`queens.py` maintains one stable injector assignment per ready hatchery; dead queens/bases are
pruned and replacements selected by distance. Two extra queens become eligible after two
ready resource bases. Extra queens use a combined defense/creep role. Immediate danger can
override injection; otherwise injection queens reserve their energy and do not plant tumors.
Active casts/orders are preserved in calm conditions. Every queen receives at most one action
from this controller per step; no other module sends queen commands.

Roaches, queens and mature tumors share one batched ability query. Creep placement uses at most
one query/command per 32 frames across the group, validates placement, and respects cast distance.
Extra queens defend locally and rally toward base fronts. This is a bounded role foundation;
transfusion optimization and sophisticated multi-base reinforcement remain future work.

## Scouting and mutalisk assessment

`scouting.py` records only currently visible enemy units and structures. It remembers up to
eight observed mineral-line sites and 128 known anti-air threats, with explicit ages. One spare
overlord scouts after 150 seconds with two resource bases, at least two overlords and eight spare
supply. It retreats from observed anti-air or low HP; at most two confirmed scout losses are allowed.

A positive mutalisk assessment requires all nine mineral-line coverage probes currently visible,
two confirmations at least 112 frames apart, freshness within 448 frames, at least six visible
workers, no remembered nearby anti-air or major mobile counter, a ground-defense reserve, two
resource bases, 44 workers, and mineral/gas safety buffers of 600 each. Known defenses persist
for 2688 frames unless their destruction is observed. Missing vision is unknown, never proof
that defenses are absent. Coverage is sampled evidence, not exhaustive future safety.

The verdict is **advisory only**. No lair/spire/mutalisk spending or harassment orders are added
in this phase. A candidate verdict proposes a future controlled test; it does not certify an
unseen mineral line safe. Replay/observer information never feeds live scouting or decisions.
Default fallback continues the roach economy/defense plan. The report includes assessment
verdicts, evidence IDs, coverage, ages, visible workers and remembered risks.

## Controls

Use `python -m zergbot --help`. Options include `--opponent Terran|Protoss|Zerg`, `--workers`,
`--extra-queens`, `--extra-queens-after-bases`, `--macro-hatches`, `--macro-after-bases`,
`--macro-min-workers`, `--macro-min-minerals`, `--no-scouting`, and `--no-adaptive-economy`.
All effective policy values are recorded in `bot_config`; opponent race is recorded and
must match in paired comparisons. Setting extra queens or macro hatcheries to zero disables
those additions. Archived baseline runs use the original source, not an approximate flag preset.

## Evaluation

The phase uses sequential, below-normal-priority games with four-frame steps, Hard computer
opponents, 900-game-second and 240-wall-second limits, paired SC2/Python seeds, and unchanged
SimTrader settings. Two seeds per race are exploratory, not a stable win-rate estimate.
Comparisons and final decisions are recorded in the accompanying phase experiment ledger.
Failed software runs are preserved locally and excluded from outcome comparisons.
