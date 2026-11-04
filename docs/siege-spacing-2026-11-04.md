# Visible-siege cooldown spacing experiment

The retained Terran control loses its large forward roach army before home defense
fails. This wave tests a narrow micro hypothesis, not a new build or counter ratio.
Frozen source: `23106f2ac6770e47bdcdf4343d61f2c24505f821` (240 passing offline tests).

The optional `--roach-siege-spacing` policy uses only own weapon cooldown, own nearby
unit positions and currently visible sieged tanks. Tank threat distance uses installed
unit weapon/radius data. After a conservative eight-frame attack-commit guard, a
crowded roach may make a 1.5-unit lateral/backward spacing move during its own cooldown.
The policy never interprets enemy cooldown. Attack-ready units return to normal attack
orders. Existing burrow/recovery/morph protection at priority 100 overrides spacing
at priority 40. There are no additional per-unit network queries. Static path-grid
segment checks do not guarantee freedom from dynamic unit collisions.

The eight-frame guard is a conservative heuristic, not a measured animation-optimal
damage point. Spacing itself is not success: score actual engagement, enemy damage,
survivors and remaining health alongside movement and conflicts.

The isolated `roach-tank` scenario compares the same twenty roaches and a normal
vision-providing Overlord against two sieged tanks, eight Marines and four Marauders.
Original town halls remain. Both policies retain the same low-health unresearched-
Burrow fallback; no Burrow upgrade is granted. Tanks select visible roach clusters;
bio units select visible roaches. This scripted opposition focuses the roach engagement,
not optimal anti-scout or worker harassment play. Three approaches/seeds are paired;
45 game seconds and 120 wall seconds bound each case, under existing host resource guards.

The policy remains off by default. No full-match improvement has yet been established.

## Completed screen and decision

All twenty roaches died in all six cases. The candidate remains disabled; it failed the scenario screen, so no full-match spacing comparison was launched. A capped scenario is unresolved, not a win.

| Approach | Controller | Result | Enemy survivors (tank / Marine / Marauder) | Tank damage callbacks |
|---|---|---|---|---|
| 0 | baseline | cap | 1 / 2 / 1 | 255.0 |
| 0 | micro | cap | 1 / 1 / 2 | 165.0 |
| 1 | baseline | cap | 2 / 1 / 1 | 120.0 |
| 1 | micro | Result.Defeat | 2 / 4 / 1 | 90.0 |
| 2 | baseline | Result.Defeat | 2 / 1 / 2 | 105.0 |
| 2 | micro | Result.Defeat | 2 / 2 / 1 | 105.0 |

Spacing activated in every candidate case (70, 76 and 71 moves). Both players recorded zero command conflicts. One approach changed from a cap to defeat. Damage callbacks omit some fatal-frame damage and are not exact per-shot attribution or total enemy health removed. Normal automatic targeting after roach losses can hit remaining buildings/workers; terminal defeat includes that cleanup.

The movement controller does not establish a composition solution to supported siege. These results do not justify retuning its small spacing constants or promoting it into the normal build.

## Local evidence

- `scenario-20261104T231738Z-roach-tank-baseline0`
  - `player-1.json` SHA256 `92eea0fadc8cab5a61a2eba87892358eedcfebf5c331c962040b5fcda652465a`
  - `player-2.json` SHA256 `4a8cec59c08ea448d975a7cf07a2e6cc3934edfef7a424e4e8337d69157d51f7`
  - `scenario.SC2Replay` SHA256 `a70f41dca18854c91e220c6a0ca552d216c8ca8960ed82c730556a993685a1a8`
- `scenario-20261104T231809Z-roach-tank-micro0`
  - `player-1.json` SHA256 `dbc7644215f74c6c1de35bd1702bde4cdfbe37428bd0b85f09cde10b58f73cc3`
  - `player-2.json` SHA256 `4c506e904cd330c4c8c6847247ce69196af6ab99ea7a6b80b4b30ec66bef9fcf`
  - `scenario.SC2Replay` SHA256 `49595e79f6797327f694004aa227114d87f64bcf512ef704a1d47a3d77641e08`
- `scenario-20261104T231837Z-roach-tank-baseline1`
  - `player-1.json` SHA256 `f868a373a17f8ec70137f77b92aa9cd667ef872cf0646be085c66fe3ffeccaf1`
  - `player-2.json` SHA256 `91061b81a2033e12d887c9229cac47d6800e45ac4eb7af9f51390a9a113f573e`
  - `scenario.SC2Replay` SHA256 `5b186f3a4274bf0a66616fcc988ce92220e82a6acba0dbdd0f76c334afcd229f`
- `scenario-20261104T231906Z-roach-tank-micro1`
  - `player-1.json` SHA256 `92a73242037eba3f5549a9d45fc41b88e2c2f1f3a6475f86a2fbd86a816ba3c2`
  - `player-2.json` SHA256 `328f4cec1e31cd232e42e058ffbeaa92dac560fddbd267d5017138b83e5022af`
  - `scenario.SC2Replay` SHA256 `11e26b77790ab6fd4eaf868f97b4a86c0418b41e88bc411b988d671d8438de40`
- `scenario-20261104T231934Z-roach-tank-baseline2`
  - `player-1.json` SHA256 `2cb35b586b60417dd4a1dfcf6bf58739f8d567cf3b44a2c44fce0099e48f5781`
  - `player-2.json` SHA256 `5970d6b3f608cc097430c359d8c2ea409ead707265ff8e5ada5288aa5cf7efbc`
  - `scenario.SC2Replay` SHA256 `1ce36271fdd490ba5b0acb7bd37422bf3b9abc384f2245cc776494683c738e48`
- `scenario-20261104T232002Z-roach-tank-micro2`
  - `player-1.json` SHA256 `18f56ff43a6c47c3dd276b3ed2905268d6dc6fecb318c6277a03b9e00af999d7`
  - `player-2.json` SHA256 `43a9bc42f7e696ecb35da4e8e58ea559ce7fcfd913df81192f5749853434d125`
  - `scenario.SC2Replay` SHA256 `56406a41310f5331e423b4209de73008a8a3cc6c827a5d2198e1e41a2e41b1fc`

All 6 guarded runs completed. Peak sampled host CPU was 32.0%; minimum available RAM was 5.79 GiB. Runs used below-normal priority, CPUs 20-23, and the 45-game/120-wall-second bounds. Raw evidence remains local under `.local-matches`.

Scope clarification: these were friendly roaches versus tank/bio support, not the requested friendly ling/bane splash-spacing case. See [the corrected scope and follow-up tests](ling-bane-and-burrow-tank-2026-11-04.md); this failed roach experiment is not evidence against ling/bane splitting.
