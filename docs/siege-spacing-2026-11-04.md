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
