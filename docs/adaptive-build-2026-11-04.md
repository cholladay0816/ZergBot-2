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
