# Adaptive build wave - November 4, 2026

Baseline: 529c2a909c4b0b20602978a0d5a40f5b7ac9e516. Latest official live patch checked
against Blizzard's news feed and notes: 5.0.17, matching installed 5.0.17.98310.
The 12-worker start is restored; eight-worker 5.0.16 timings are not applicable.
https://news.blizzard.com/en-us/feed/starcraft-2
https://news.blizzard.com/en-us/article/24309308/starcraft-ii-5-0-17-patch-notes

References are sequencing benchmarks, not a claim of current tournament-best strategy:
- PiG's popular historical ZvZ teaching all-in, April 2023, patch 5.0.11:
  https://lotv.spawningtool.com/build/175116/ . Its +1/speed coordination is useful;
  this candidate does not copy its fixed drone cut or make an unconditional all-in.
- Cypem's February 2026 12-worker training replays, not competitive win-rate evidence:
  https://lotv.spawningtool.com/build/201029/playable/ and
  https://lotv.spawningtool.com/build/201039/playable/ .
  Both support weapon/speed investment before discretionary Burrow.
- Cypem's February 7 ZvP roach/hydra demonstration: https://lotv.spawningtool.com/89666/ .
- Recent community roach/hydra/lurker outline still tagged 5.0.16:
  https://lotv.spawningtool.com/build/204804/ . No Lurker/spellcaster stack is copied.

Candidate flags: --roach-tech --adaptive-army. Both initially default off while measured.
At two ready resource bases, 32 workers and the defensive roach reserve, sequence Lair,
one Evolution Chamber, +1 missile and roach speed. Use installed costs/prerequisites and
normal API commands; reserve minerals only when the producer and gas are ready. Supply
and immediate ground defense precede tech. Burrow follows the primary upgrade starts.
The worker target stays adaptive rather than being permanently cut for a roach all-in.

One early ling pair scouts. A current locally visible worker pocket, few workers, no
observed nearby armed defenders, healthy scouts and a safe home can permit a ten-second
pressure window, with at most eight lifetime attempted lings. Missing vision is not
absence of defense. Abort on danger/damage; no endless reinforcement or economy lock.

Recent visible air attackers trigger a bounded Hydralisk target (4-20), a Lair-gated
Hydralisk Den and real anti-air units. Evidence expires after 60 game seconds. Support
hydras receive one command each and prioritize local air threats. Unseen production is
not inferred. This is a first counter-production foundation, not a complete composition solver.

Primary comparison: Harder T/P/Z seed 1 against the preserved baseline, 1200 game seconds,
300 wall seconds, identical map/patch/step/seeds. Inspect 4/5/6/8-minute economy, army,
upgrades, bank, supply and larva snapshots. Keep caps unresolved and preserve regressions.
The detector and damage-triggered escape experiments remain off.

## Measured results

The original opening remains in place. This wave adds researched upgrade and adaptation
sequencing, not a literal PiG/Cypem build. All new strategy flags remain off by default:
the evidence does not establish a reliable win-rate improvement.

The first live attempt at fdfbc95 failed on NumPy integer serialization. That is a software
failure, not a defeat, and is excluded below. Checkpoint 2b309d3 fixed serialization.
Its Terran game built a Hydra Den but no Hydralisks: cheaper production consumed the
available minerals. Checkpoint 979503f reserved counter-production minerals and added
visible Immortals as a light-unit counter trigger; its Protoss game reached 12 Hydralisks.
That did not produce a win. Checkpoint 02eb55f coordinates mixed-army attack strength,
adds Hydralisk range and waits for the primary roach upgrades before ordinary offense
(480-second fallback, emergency defense exempt). It is the frozen final candidate.
995b1cd restores old threat behavior when adaptation is disabled. 738eab5 only fixes
scenario telemetry sampling. Neither changes the enabled frozen candidate policy.

All listed games use Abyssal Reef, Harder AI, seed 1, step 4, 1200 game-second cap,
300 wall-second guard, installed 5.0.17.98310, Python 3.14.10 and BurnySC2 7.3.0.
Prior baseline runtime was 85e4165, preserved in baseline 529c2a9. One seed per race
is exploratory: survival time is not a win, and caps remain unresolved.

| Runtime | Opponent | Result | Game seconds | Max observed own Hydras |
|---|---|---|---:|---:|
| baseline | Terran | Defeat | 868.39 | 0 |
| baseline | Protoss | Defeat | 826.43 | 0 |
| baseline | Zerg | Defeat | 1041.25 | 0 |
| phase3-corrected-Harder-Terran | Terran | Defeat (completed) | 873.04 | 0 |
| phase3-corrected-Harder-Protoss | Protoss | Defeat (completed) | 1113.75 | 0 |
| 979503f-counters-Harder-Protoss | Protoss | Defeat (completed) | 941.79 | 12 |
| 02eb55f-final-Harder-Terran | Terran | Defeat (completed) | 826.43 | 3 |
| 02eb55f-final-Harder-Protoss | Protoss | Defeat (completed) | 978.39 | 11 |
| 02eb55f-final-Harder-Zerg | Zerg | Victory (completed) | 771.25 | 0 |

### Final candidate execution benchmarks

W = workers; R/H = roaches (including burrowed)/Hydralisks. These are observations, not prescribed timings.

| Opponent | Minute | W | R/H | Supply used/cap | Minerals/gas | Larva | Completed upgrades |
|---|---:|---:|---|---|---|---:|---|
| Terran | 4 | 25 | 5/0 | 50/60 | 45/230 | 0 | none |
| Terran | 5 | 36 | 6/0 | 64/76 | 100/390 | 0 | none |
| Terran | 6 | 44 | 12/0 | 93/100 | 65/346 | 1 | none |
| Terran | 8 | 56 | 12/0 | 101/148 | 430/996 | 0 | BURROW, GLIALRECONSTITUTION, ZERGMISSILEWEAPONSLEVEL1 |
| Protoss | 4 | 24 | 6/0 | 50/60 | 30/197 | 1 | none |
| Protoss | 5 | 34 | 7/0 | 65/76 | 0/377 | 2 | none |
| Protoss | 6 | 44 | 13/0 | 93/100 | 60/414 | 4 | none |
| Protoss | 8 | 43 | 38/0 | 144/172 | 105/597 | 0 | BURROW, GLIALRECONSTITUTION, ZERGMISSILEWEAPONSLEVEL1 |
| Zerg | 4 | 26 | 5/0 | 50/60 | 40/218 | 0 | none |
| Zerg | 5 | 37 | 6/0 | 64/76 | 120/418 | 0 | none |
| Zerg | 6 | 44 | 13/0 | 95/100 | 20/349 | 1 | none |
| Zerg | 8 | 50 | 25/0 | 115/164 | 255/928 | 0 | BURROW, GLIALRECONSTITUTION, ZERGMISSILEWEAPONSLEVEL1 |

### Evidence index

Full telemetry and replays remain local under `.local-matches`. Aggregate index: `phase3-match-comparisons.json`; comparison checks validate settings.

- `20261104T194654Z-6eed3131/match.json`: `1099c9e8c7b8110fb057ff58385864ce8c7b68af905ea5f843ca2c87af91c3f3` (phase3-corrected-Harder-Terran).
- `20261104T195107Z-3726adae/match.json`: `ade7fc77102f4a46ec66a330793b5a4f933811cec1d46095e5f1a74fc92914f4` (phase3-corrected-Harder-Protoss).
- `20261104T195658Z-4a43ccd0/match.json`: `70cc82be57b9e393fa792532d6b27fcd24dd82b308df5bff7e898d8fb05fa54c` (979503f-counters-Harder-Protoss).
- `20261104T201016Z-d6e6f8a5/match.json`: `e09bc904477c32d6d12c4386b630de2f44501a7589b71f2eb82e83c689239f62` (02eb55f-final-Harder-Terran).
- `20261104T201327Z-ade5eed0/match.json`: `aa321195cc4db36a0f6f3fb3b1daaa04aa0b5184dd6c99d3173c3be4758037bf` (02eb55f-final-Harder-Protoss).
- `20261104T201709Z-63ddc557/match.json`: `e2062a6b07abcda55b8d203878c4da87e1d7d443ab08251605041d6fbfe2bf99` (02eb55f-final-Harder-Zerg).

### Limits and next decisions

Hydralisks are a provisional accessible anti-air response, not a universal counter matrix.
Phoenix, capital air and supported siege compositions require different range, mobility,
cost and tech decisions. Do not promote this generic target rule as optimal. Enemy memory
expires after 60 seconds and only actual live sightings enter decisions; replay evidence
never enters the competitive policy. Mutalisk harassment remains a separate conservative
scouting assessment, not speculative spending. Detection/damage escape remain off.

The final frozen set is one victory (Zerg), two defeats (Terran/Protoss), and no caps.
This is not regular winning and does not justify raising difficulty. At four minutes the
candidate has only 24-26 workers; at five minutes it holds 377-418 gas with 0-120 minerals.
Existing gas rebalancing starts above max(400, 1.5 times minerals), so earlier allocation
is a testable next hypothesis, not an established single cause.

See the [researched air-counter matrix and implementation gaps](air-counter-policy.md).
The next wave should prioritize the measured losing engagements and economic execution,
then test matchup-specific counters and early-pressure defense across additional seeds.
The controlled [micro scenarios](scenarios-2026-11-04.md) expose failures as well as successes.
