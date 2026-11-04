# Queued controlled scenario waves

Status after the repeated worker-participation wave, November 4, 2026. These are
requested experiments, not completed validation or claims of optimal micro.

| Wave | Status | Required evidence |
|---|---|---|
| Pool / first-queen budget | Fixed c816d95 probes complete; timing gain too small with worker regression, stays off | Pool construction start/completion, queen production submission/completion, workers, then a separately controlled opening-rush survival check |
| Offensive ling diversion versus Hellions | Queued | Identical initial counts/upgrades/health/positions for grouped and split policies; actual flank traversal to observed workers; Hellions independently protect workers and select useful line-splash targets; worker damage/kills, ling losses, path progress, fallback |
| Defensive Hellion mineral-line rush | Six 2a58ff6 pairs completed with meaningful attacks and mixed queen results; micro remains off | Real worker access under varied approaches, queen protection and worker spacing, worker survival/HP/mineral collection, actual attacker survival; no exact splash attribution from HP loss alone |
| Adept shade harassment | Queued | Actual cast, owned shade movement, cancel/feint and expiry/commit trials; defender sees only normal visible shade/unit evidence; verified transfer, worker/queen outcomes and mining impact |

The first queen's 169-second observation was completion. SpawningTool's
[parser](https://github.com/StoicLoofah/spawningtool/blob/master/spawningtool/parser.py)
subtracts build time from UnitBornEvent to estimate the production start. Therefore the
reference's 1:59 queen entry is not a 1:59 completion benchmark. New instrumentation
separates command submission, observed construction start, and observed completion.

All waves retain frozen baseline/candidate sources, finite game/wall bounds, sequential
below-normal games, CPU affinity/resource guards and protected SimTrader workloads.
No hidden debug/evaluator state enters competitive decisions. Pathable endpoints and
query_pathing distances do not prove a collision-free route; progress must be observed.

Hellion splash-line scoring will be labeled a geometric heuristic: protocol weapon data
does not expose exact line-splash geometry. Baseline and split groups must start at the
same positions; spawning a pressure group behind workers would test an achieved flank,
not navigation. Defenders must not be scripted to abandon workers for a decoy.

Adept symbols must be verified against installed burnysc2 7.3.0 and live availability.
Expected upstream names: ADEPTPHASESHIFT_ADEPTPHASESHIFT, CANCEL_ADEPTPHASESHIFT,
CANCEL_ADEPTSHADEPHASESHIFT; ADEPTPHASESHIFT is a unit type, not a fake effect. A real
commit occurs by shade expiry, not an invented commit ability. Enemy shade disappearance
in fog does not prove cancellation or transfer. Attacker logs remain evaluator-only.
Multiple-caster association is uncertain because the raw protocol supplies no parent tag.
