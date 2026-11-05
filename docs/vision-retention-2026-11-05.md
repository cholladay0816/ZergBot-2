# Retaining vision after firing-unit reveal, November 5, 2026

## Finding and decision

In these unmodified SC2 5.0.17.98310 observations, the firing elevated tank became a visible enemy unit at first damage even while its terrain cell remained fogged. Visibility then lapsed between firing episodes. The first baseline at position 0/seed 1 showed tank-visible intervals [25,69), [73,117), [121,165), followed by [277,377) game loops. Samples were four loops apart: the first intervals are approximately 1.96 seconds, not a claim of an exact universal engine duration. The attacker's own cooldown first rose at loop 22 and again at 70; this evaluator-only correlation supports temporary firing reveal. It never enters the Zerg policy.

Flyer assistance reliably improved terrain acquisition and continuity in the small matched set. It did not consistently improve tank-removal time, and Hydra survival was mixed. **Retain as an isolated experimental scenario controller; do not enable in the production bot.** This is remembered visible-threat assistance, not successful identification of an unobserved damage source. The separate conservative `threat_inference.py` / `vision_assist.py` path remains intact.

## Controller and information boundary

`vision_memory.py` stores only a normally visible ground threat's tag, last observed position and observation loop, near the own army. It prefers longer-range threats when choosing an initial target. It never reads hidden current positions, enemy cooldowns, setup coordinates or replay data. An unrefreshed observation expires after 112 loops (~5 seconds); a flyer assignment ends after at most 448 loops (~20 seconds).

The flyer starts at 80% health or better, approaches a stand-off point within its own nominal sight range, and checks actual normal terrain visibility. Observing a revealed enemy unit alone is not treated as sustained terrain vision. Once terrain vision is present, it holds; when the observed location is empty it returns without claiming that the enemy died. Low health, unsafe observed anti-air, army loss, stale information and timeouts end the assignment. Returning to the starting point is bounded retreat behavior, not a proof that every dynamic retreat route is safe. Mobile threats and general flyer-role allocation remain unvalidated.

The frozen benchmark was `47ed34e800a24ee27d5119d5de9505c188251279`. A subsequent, separately tested correction at `2941bac` includes normally visible enemy structures in the safety inputs as well as enemy units. No benchmark source was changed during a run. Static-AA route refusal has an offline regression; no live turret defense was exercised.

The normal observation boundary is documented in the [Blizzard raw protocol](https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/raw.proto). Enemy orders/cooldowns are not treated as available. The empirical unit-versus-terrain distinction and the failed earlier hidden-source setups are retained in the [cliff inference ledger](cliff-vision-inference-2026-11-05.md).

## Matched setup and results

AbyssalReefLE; 12 Hydralisks below an elevated stationary siege tank, one available Overseer, and normal player-2 spotting. `--vision-spotter` uses a debug-created player-2 Observer: this is a mixed-race isolated setup, not a standard Terran army composition. Its ordinary vision is shared only with its owner. It does not expose opponent state to Zerg. The AA probe adds two Marines. No reveal-map, invulnerability, no-cooldown, artificial damage or hidden observation filtering was used.

Each pair has identical geometry/counts/map/seed/settings except the flyer controller. Position 0 uses seeds 1 and 11; position 1 uses seeds 2 and 12. An additional position-0/seed-1 pair includes Marines. Five pairs / ten capped runs; 45 game seconds and 120 wall seconds maximum per run, step 4. Sequential below-normal execution with CPU affinity 20-23 and existing CPU/RAM guards. Two-client startup phases vary by a few loops; tiny survival/time differences cannot be attributed confidently from this sample.

All ten runs established the revised precondition: the tank was a visible enemy unit at first damage while its terrain was not visible. Times below are game seconds since first observed Hydra damage. Missing tank samples are counted at four-loop resolution until evaluator-observed tank death; interval endpoints are observation bounds. HP is aggregate surviving Hydra health at the 45-second cap, including regeneration.

| Position / seed / AA | Terrain vision, baseline -> flyer (s) | Unseen tank sample loops, baseline -> flyer | Hydra survivors / HP, baseline -> flyer | Tank removal, baseline -> flyer (s) |
|---|---|---|---|---|
| 0 / 1 / none | 11.43 -> 5.54 | 124 -> 4 | 9 / 602.7 -> 9 / 607.6 | 15.76 -> 15.89 |
| 0 / 1 / Marines | 11.43 -> 5.54 | 112 -> 4 | 8 / 555.9 -> 9 / 522.7 | 17.68 -> 17.86 |
| 0 / 11 / none | 11.43 -> 5.54 | 76 -> 4 | 9 / 543.7 -> 11 / 623.6 | 16.61 -> 16.21 |
| 1 / 2 / none | 10.00 -> 5.54 | 12 -> 8 | 10 / 507.1 -> 9 / 470.3 | 13.66 -> 13.39 |
| 1 / 12 / none | 10.00 -> 5.54 | 12 -> 8 | 8 / 447.4 -> 9 / 483.9 | 13.57 -> 13.75 |

All tanks were removed, including every baseline. Terrain vision arrived in 5.54 seconds with the flyer versus 10.00-11.43 seconds without it. Across pairs, sampled visibility gaps totalled 28 loops with assistance versus 336 without; that is a continuity metric across five fights, not one uninterrupted timing measurement. Survivors totalled 47 versus 44, with three improved pairs, one equal and one worse. Removal times were mixed and close. These are exploratory scenario results, not full-match wins or proof of optimal play.

Every flyer remained at 200 HP. The Marine pair did not produce an abort decision, so it does not live-validate emergency retreat or show that unknown anti-air is safe. Both players recorded zero command-conflict frames and zero action errors across the frozen set. Hidden AA, static AA, moving/repositioning tanks, alternate maps and full competitive games require separate validation.

## Final-head validation and checks

Separate final-head smoke at `2941bacd6cedcab674e5a96d53c79323afa34b52`: position 1, seed 2, no Marines, exit 0; 8 Hydras and 1 flyer survived; tank death loop(s) [329]. Decisions: no_observed_threat, retain_observed_threat_vision, reacquire_observed_position, hold_sustained_vision, observed_location_clear, memory_finished. This run is not included in the paired totals above.

277 offline tests passed; Ruff lint/format, compile, dependency checks, wheel build and extracted-wheel imports passed under Python 3.14.10 / burnysc2 7.3.0. The experiment requires `--vision-retain`; competitive defaults are unchanged.

Example (use the external bounded supervisor/resource controls for repeated tests):

```powershell
.\.venv\Scripts\python.exe -m zergbot.scenarios --scenario cliff --vision-spotter --vision-retain --controller micro --approach 0 --seed 1 --game-time-limit 45
```

## Resources and artifacts

Sampled peak system CPU 55.6%; minimum available RAM 17.26 GiB. Raw telemetry/replays remain local under `G:\Github Projects\ZergBot-2\.local-matches`. Derived paired summary: `phase9-cliff-retain-summary.json`. All owned SC2 processes exited. Previously protected SimTrader PIDs 16400 and 18472 remain absent; this task did not stop or alter them. Final free bytes: C 863,767,080,960; G 671,917,633,536; E 1,564,127,232.

- `cliff-repeat-0-aa0-baseline`, seed 11, revision `47ed34e800a24ee27d5119d5de9505c188251279`, folder `scenario-20261105T214302Z-cliff-baseline0`; index `phase9-cliff-repeat-repeat-batch.json`.
  - `player-1.json` SHA-256 `ea753b865a6a145a6a760716bbb3fb918eb60df91fc281eec13315304ddec628`
  - `player-2.json` SHA-256 `95a80ec92af8d919f5dcdfa5a138fc34e45d090b0c2c641e5e8b8a7d9e2afc12`
  - `scenario.SC2Replay` SHA-256 `d2d2868439e6074d4d4cd3610518085699891e058a85ab2274fedc65de9b198c`
  - `settings.json` SHA-256 `3e133d1dab43e1b55a1d550d0e2d9f80d3cce1ba47ba2a22a2dd3e4a0849b3f8`
- `cliff-repeat-0-aa0-micro`, seed 11, revision `47ed34e800a24ee27d5119d5de9505c188251279`, folder `scenario-20261105T214328Z-cliff-micro0`; index `phase9-cliff-repeat-repeat-batch.json`.
  - `player-1.json` SHA-256 `f8cd0c282ec0a8c636aee347a37dd2879c93f8478b48279b6fb541a49dfb2efc`
  - `player-2.json` SHA-256 `fc5b84710ed6c872c47d1de0cc3e7e1d8f95dbbcdbec48b6cd459c6de22e6515`
  - `scenario.SC2Replay` SHA-256 `15665a1cc4a436a9fe7f34c3c4d5feb19ebf106b52eafa4695099f0dc1f87cb1`
  - `settings.json` SHA-256 `b0bf9b44664c0c5c9ea3cd576c4f05271932142a3cfda4409099413b6402a7a0`
- `cliff-repeat-1-aa0-baseline`, seed 12, revision `47ed34e800a24ee27d5119d5de9505c188251279`, folder `scenario-20261105T214355Z-cliff-baseline1`; index `phase9-cliff-repeat-repeat-batch.json`.
  - `player-1.json` SHA-256 `d7521687f2ba7ac0d6b22636caeccf8179f3efb296375b4c22f783ec6b825324`
  - `player-2.json` SHA-256 `f7026a24c847fb07de46b26be0cac28c19a499b97f7a4bb17a0185b757b924c7`
  - `scenario.SC2Replay` SHA-256 `204cf4f830073d747c21403596e6ca885c3d16f68abb014e55280f72ddf17f22`
  - `settings.json` SHA-256 `8612b436583722e4898112e074741cb41f3c2367d821b9f254646e54cb52f775`
- `cliff-repeat-1-aa0-micro`, seed 12, revision `47ed34e800a24ee27d5119d5de9505c188251279`, folder `scenario-20261105T214421Z-cliff-micro1`; index `phase9-cliff-repeat-repeat-batch.json`.
  - `player-1.json` SHA-256 `6591c647ea17efbfaf49d2415571fab6e201ddfb3ec24ce13be42f1ffa9a2c04`
  - `player-2.json` SHA-256 `c21e0d83781e1fcace83298c398c58e16936a5d8541cd0d8dfd438b36b8744a3`
  - `scenario.SC2Replay` SHA-256 `315e8194b6ca6231b510d77bed1fa6fb62f984fcc8d79b834dd34910d3f7917d`
  - `settings.json` SHA-256 `e006910d6357d26738c96ce363fb36aa6a2ac10ca28ce22e9b71a4aaf2c1ff0e`
- `cliff-retain-0-aa0-baseline`, seed 1, revision `47ed34e800a24ee27d5119d5de9505c188251279`, folder `scenario-20261105T214005Z-cliff-baseline0`; index `phase9-cliff-retain-batch.json`.
  - `player-1.json` SHA-256 `5ca771d57a19dd0b4fbe28911276adb97ace0f6f046e1186d2de6994304e3ad2`
  - `player-2.json` SHA-256 `f9329042f612786b44dc3c6e177c1ef30d0b5768ba4d12a72ce93f3493b9a148`
  - `scenario.SC2Replay` SHA-256 `0bee40aedbdbbdd914f09f2f2194926bc69e41e431ed072b67838ac92796d162`
  - `settings.json` SHA-256 `2cd22dc5912d3463105b0d2e88d873fb61fdc70281e2f5ac051b4ac393762ded`
- `cliff-retain-0-aa0-micro`, seed 1, revision `47ed34e800a24ee27d5119d5de9505c188251279`, folder `scenario-20261105T214031Z-cliff-micro0`; index `phase9-cliff-retain-batch.json`.
  - `player-1.json` SHA-256 `207839ff6221f6dee022472bd0c4986231e70de237e6018006f6cf88ff1369ff`
  - `player-2.json` SHA-256 `a2a1018fa0e511ef81f0a2d20a78c6e1900a42fc7124ace377d196a9cf8b563c`
  - `scenario.SC2Replay` SHA-256 `eee24ce44a85485761730136c72fd1b6d838cc110206b9fd326638de92861eac`
  - `settings.json` SHA-256 `15ed351aa009c6518f010e0a19960b7cea37ef424630ca1fb87f6317587a9d23`
- `cliff-retain-1-aa0-baseline`, seed 2, revision `47ed34e800a24ee27d5119d5de9505c188251279`, folder `scenario-20261105T214057Z-cliff-baseline1`; index `phase9-cliff-retain-batch.json`.
  - `player-1.json` SHA-256 `d3ad1af1f782db6cf17228809e114c24aeb91ccad0dc90474fbe826a589b90f4`
  - `player-2.json` SHA-256 `242a0a1fd8a3606e59463023b630b182b7c8a1924a6922bc7143c6116d4f2816`
  - `scenario.SC2Replay` SHA-256 `ce0ead0cf2803a826f656e5b6eb2f9f74ea236f0e80a4f406a5ff56998288304`
  - `settings.json` SHA-256 `2cf09a1f750393993b9015fdaa09e6976d266ab75dd9077f3b058785f8da3a45`
- `cliff-retain-1-aa0-micro`, seed 2, revision `47ed34e800a24ee27d5119d5de9505c188251279`, folder `scenario-20261105T214124Z-cliff-micro1`; index `phase9-cliff-retain-batch.json`.
  - `player-1.json` SHA-256 `7fb670d5353401e17723133e44bdf3d6f9b8dac4569eba03f3a8912d1c31adf7`
  - `player-2.json` SHA-256 `f601a4cd007adf4ce6a10b6637e91018cb4968cfb21ab32b2a6d41a3164716e0`
  - `scenario.SC2Replay` SHA-256 `dcea56057cda9c719c953a012b436ee8dd2eebbc0a48f5619a9f7e407582c98e`
  - `settings.json` SHA-256 `0d1d15f0c5ff4236cf17b9400f51b27e77ccfc1c02f39fdcb31a8a84a7937622`
- `cliff-retain-0-aa1-baseline`, seed 1, revision `47ed34e800a24ee27d5119d5de9505c188251279`, folder `scenario-20261105T214150Z-cliff-baseline0`; index `phase9-cliff-retain-batch.json`.
  - `player-1.json` SHA-256 `9b9dfe65b627d0b5ed784c8eea02fefe74b5f805b8a60d6c231963a68adf30e1`
  - `player-2.json` SHA-256 `5f25454b53a1155e77610be3d3a7f3ff09c8c0968c30ba84b4d17c0bcdd8df70`
  - `scenario.SC2Replay` SHA-256 `d5aec942a89393ee32e608aff024bd5ba053a050633b5aeab8a4e373368aa596`
  - `settings.json` SHA-256 `8ef6ddbdd234951bb6eb6d45fd8c795e284ae69dec4ec804160a34027208b3ba`
- `cliff-retain-0-aa1-micro`, seed 1, revision `47ed34e800a24ee27d5119d5de9505c188251279`, folder `scenario-20261105T214216Z-cliff-micro0`; index `phase9-cliff-retain-batch.json`.
  - `player-1.json` SHA-256 `9ddafbd493de2340b02ac965b868357999b36c5cc39679dab1a6ed6ab13a4b81`
  - `player-2.json` SHA-256 `08cb8bc1ff1cb7a3e743a8dbdb73182d0d5d89a8611f9f9dd33ea88e8519b21f`
  - `scenario.SC2Replay` SHA-256 `dbaafdfb11b33c55b904356f896e37d0311e8d9bfba2b9865a3dbc4bbcb192b4`
  - `settings.json` SHA-256 `3c65578a40ef3ba9821e295f36f7c5b7e288e90457e44616d0d4122b79e55710`
- `cliff-final-1-aa0-micro`, seed 2, revision `2941bacd6cedcab674e5a96d53c79323afa34b52`, folder `scenario-20261105T214602Z-cliff-micro1`; index `phase9-validation-batch.json`.
  - `player-1.json` SHA-256 `8cf52c4f54229c66824d2dce8e06504af67e5ffd436be839ea0de22fb198d499`
  - `player-2.json` SHA-256 `a329418975775a89f69de39a70ae131a1f7f5fa18d6cf5310abbabd458c6ac89`
  - `scenario.SC2Replay` SHA-256 `a49afe4e1b93d2644dba37af3701bf2d9dac33fb033834baca0268b286bbb387`
  - `settings.json` SHA-256 `0d1d15f0c5ff4236cf17b9400f51b27e77ccfc1c02f39fdcb31a8a84a7937622`
