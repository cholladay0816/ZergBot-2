# Cliff vision and damage-source inference, November 5, 2026

**Decision: experimental, scenario-only. No production policy enabled.** The reusable inference model and isolated flyer controller are tested offline. The requested live premise (damage while the tank stays unseen) was not established in these trials. Do not treat tank removal or a lower loss count as proof of successful unseen-source inference.

## Observation contract

`threat_inference.py` accepts damage-time position and optional externally confirmed source bounds. Confirmed range bounds include weapon reach, unit radii, splash, projectile/observation delay, and attacker/victim movement uncertainty. An unconfirmed type never becomes a fact from damage amount. Without a confirmed source, the 14-unit radius is a bounded scouting budget, not an exhaustive attacker-location claim.

Terrain and damage-time visibility rank scouting areas. A currently visible cell is not excluded just because it is empty now: exclusion requires visibility and confirmed attacker absence over the relevant interval, plus appropriate detection for a potentially hidden source. A sampled grid, even with one remaining cell, never proves an exact location. Separate damage events are not intersected as though they necessarily have one attacker. High terrain is a hypothesis, not proof of siege fire.

Installed BurnySC2 7.3.0 computes `on_unit_took_damage` from previous/current health and shields; it supplies no attacker identity. The live scenario therefore never supplies a confirmed source type. Enemy orders/cooldowns and debug opponent state never enter the defender controller. See the [Blizzard raw protocol](https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/raw.proto) and [BurnySC2 implementation](https://github.com/BurnySc2/python-sc2/blob/develop/sc2/bot_ai_internal.py) (upstream link is not a version pin).

`vision_assist.py` samples normal map terrain/visibility at the damage observation, selects an available healthy flyer, avoids observed anti-air along a sampled route, and returns it after at most 224 loops (~10 game seconds), or earlier on danger. Unknown anti-air, collision-free routing, exhaustive source attribution and general competitive flyer-role assignment are not solved. The live harness wires this only to Hydra damage and an available Overseer; the pure inference model is reusable for other units.

## Reproducible setup and validity checks

AbyssalReefLE, installed SC2 5.0.17.98310, Python 3.14.10, burnysc2 7.3.0. Two normal-fog BotAI players; debug setup creates 12 Hydralisks, one Overseer and one sieged tank. Original town halls remain. No reveal-map, invulnerability or no-cooldown cheats. Tank commands use its own normal visibility. Defender uses only normal observations. Evaluator setup coordinates and attacker logs are separate from the policy.

Each run is capped at 45 game seconds / 120 wall seconds, game step 4, sequential, below-normal priority, CPUs 20-23. Matched approaches use seeds 1 and 2, identical setup and controls apart from the flyer policy. Startup observation phases vary by a few loops; these small unreplicated samples are not a stable effect estimate. Raw scenario `Tie` at the cap is not a full-match victory.

The first geometry exposed the tank before damage. Two stricter terrain searches found no suitable placement and failed before combat (software/setup failures, not defeats). Wider valid plateaus exposed the tank in the same observation as first damage. The final setup logs actual tank position/height: elevation 207 versus initial Hydra plateau 191 at approach 0; Hydra sight 9, tank sight 11 and tank range 13 from installed data. Despite initial separation, first impact and first normal tank visibility coincide. This observation does not prove a universal high-ground reveal rule.

## Complete run ledger

| Case | Revision | First damage / tank vision (loops) | Hydras alive / HP at cap | Tank death loop | Classification |
|---|---|---|---|---|---|
| cliff-controls-0-aa0-baseline | `e4a868f` | 21 / 21 | 10 / 779.4 | 373 | Tank visible by first damage; hidden-source premise not established |
| cliff-controls-0-aa0-micro | `e4a868f` | 21 / 21 | 12 / 810.3 | 371 | Tank visible by first damage; hidden-source premise not established |
| cliff-controls-1-aa0-baseline | `e4a868f` | 11 / 11 | 12 / 680.7 | 314 | Tank visible by first damage; hidden-source premise not established |
| cliff-controls-1-aa0-micro | `e4a868f` | 13 / 13 | 10 / 660.4 | 327 | Tank visible by first damage; hidden-source premise not established |
| cliff-corrected-0-aa0-micro | `9ad35ad` | 22 / 22 | 12 / 792.2 | 367 | Tank visible by first damage; hidden-source premise not established |
| cliff-corrected-1-aa0-micro | `9ad35ad` | 11 / 11 | 10 / 653.9 | 318 | Tank visible by first damage; hidden-source premise not established |
| cliff-0-aa0-baseline | `7dffebf` | 17 / 5 | 12 / 1044.7 | 30 | Tank visible by first damage; hidden-source premise not established |
| cliff-v2-0-aa0-baseline | `d0e995d` | None / None | - | - | Setup failure; no combat |
| cliff-v3-0-aa0-baseline | `b7733f0` | 21 / 21 | 10 / 526.9 | 397 | Tank visible by first damage; hidden-source premise not established |
| cliff-v4-0-aa0-baseline | `0aed15e` | None / None | - | - | Setup failure; no combat |
| cliff-v5-0-aa0-baseline | `cf8a227` | 19 / 19 | 11 / 789.6 | 365 | Tank visible by first damage; hidden-source premise not established |

The frozen `e4a868f` candidate started scouting after previously visible damage when the tank later faded from view. Approach 0 had 12 versus 10 survivors; approach 1 had 10 versus 12. These mixed outcomes do not validate the intended inference, and exposed a damage-time labeling bug. `9ad35ad` fixes that bug: damage with a plausible visible ground threat cannot later become unexplained merely because visibility disappears. This is conservative suppression, not confirmed attribution; an unrelated visible threat can suppress a useful mission. A new genuinely unexplained damage event can still trigger scouting.

Both corrected runs retained an untouched 200-HP Overseer and recorded zero command-conflict frames. Corrected candidate decision sequences:
- `cliff-corrected-0-aa0-micro`: 0: no_unexplained_damage
- `cliff-corrected-1-aa0-micro`: 3: no_unexplained_damage

No live anti-air abort test was completed because the core hidden-source setup was not established. Anti-air routing/low-health abort, stale evidence, unavailable flyer, unknown source, interval visibility/detection and mission timeout have offline tests. A corrected true hidden-source scenario, remembered possible attackers with explicit age/confidence, and broader integration remain next steps. Do not enable this policy based on these results.

## Validation and resources

270 offline tests passed; Ruff lint/format, compile, pip dependency checks, isolated wheel build and imports from extracted wheel passed. The first no-isolation build failed because setuptools was absent from the development environment; standard isolated build succeeded with setuptools 84.2.1 without changing global packages.

Across 11 recorded runs: sampled peak system CPU 34.8%; minimum available RAM 14.65 GiB. Resource guard outcomes: completed (including the two recorded setup failures; no resource-limit stop). Final free bytes: C 863,828,987,904; G 671,938,478,080; E 1,564,127,232. No owned SC2 process remained at the final check.

All raw artifacts and replays remain local under `G:\Github Projects\ZergBot-2\.local-matches`. Batch indices are `phase7-cliff-vision[-v2 through -v5]-batch.json`, `phase7-cliff-controls-batch.json`, and `phase7-cliff-corrected-batch.json`. Derived summary: `phase7-cliff-summary.json`. No raw replay/telemetry was published. The old protected SimTrader PIDs 16400 and 18472 were absent in the final host check; this task did not stop or change them, and their original running status cannot now be affirmed.

## Artifact provenance

- `cliff-controls-0-aa0-baseline`: revision `e4a868f18296b6e8aa1775a6de83297ab4075b8d`, folder `scenario-20261105T212230Z-cliff-baseline0`.
  - `player-1.json` SHA-256 `5060bc3d8898f5aa2f4f6dcadeba8a28aba3ffecae96f1fe3f8029fd4f113619`
  - `player-2.json` SHA-256 `a422474d17c586ff5b0b458f1d5d04bada327f1ddb14ebbfdacd22640118629b`
  - `scenario.SC2Replay` SHA-256 `d5d6b1a3cad42f8ba7e954e255949178e13f415e6ad04eecc974756456356e3a`
  - `settings.json` SHA-256 `7fd03152c5a4a3a90831455a3950dd7e100915d10f6f2bb12080f43dc0d510b5`
- `cliff-controls-0-aa0-micro`: revision `e4a868f18296b6e8aa1775a6de83297ab4075b8d`, folder `scenario-20261105T212256Z-cliff-micro0`.
  - `player-1.json` SHA-256 `49a251f3eb712e64093098d64a4951d7090064616f084257b246104914c0fe70`
  - `player-2.json` SHA-256 `14b2351f649bbc34522df17a9580e4766692f9130f99ba1792c3d62fed1772e7`
  - `scenario.SC2Replay` SHA-256 `fbedcdf60b782ac4cb91f04bbe8fe6245041150abcc4e8df27abfd702b403cc9`
  - `settings.json` SHA-256 `2491189225425eed92b9941bd1d300f2a03da536787685b5fdd1ea8d7538ccd3`
- `cliff-controls-1-aa0-baseline`: revision `e4a868f18296b6e8aa1775a6de83297ab4075b8d`, folder `scenario-20261105T212323Z-cliff-baseline1`.
  - `player-1.json` SHA-256 `dfe974d94a37208b617a722328859b5a4f1c2c3456e079e16ceb5dbcc444c44b`
  - `player-2.json` SHA-256 `6fe44fef0081b2ef6622deea0c61e513c711a6b4e82ebc7f05158a61b0eb7ddd`
  - `scenario.SC2Replay` SHA-256 `410f6b949933d2632aa9cdb0bac517142e4ce8e93a650841d4872f31b95abbbf`
  - `settings.json` SHA-256 `0e4106517dc46a964502a183729518b2f79ea917055b6688a8fbf3d377dd0ee6`
- `cliff-controls-1-aa0-micro`: revision `e4a868f18296b6e8aa1775a6de83297ab4075b8d`, folder `scenario-20261105T212349Z-cliff-micro1`.
  - `player-1.json` SHA-256 `d5c2cf1fe221eecd2b5c99c4882fe7a8ba921d491e85eebf80d3ff4c8937bba6`
  - `player-2.json` SHA-256 `9a5123a0ba6e5524896fa7e1a18788de205d5c7afe2cbee6085c072a450efee5`
  - `scenario.SC2Replay` SHA-256 `3be6500a2c16d5acfcb172f53493d83420bb9710e7438cf61600cd5a4772490a`
  - `settings.json` SHA-256 `56b559457e976f79941a9472f4693b12120e7233666063358b0d3cd0a8e6e8b8`
- `cliff-corrected-0-aa0-micro`: revision `9ad35ade530432c5917c1a069d2c932afa4a501e`, folder `scenario-20261105T212502Z-cliff-micro0`.
  - `player-1.json` SHA-256 `0f8e16a2dd7144cf6306cf62844458da0f4c718f2e2aca4a92bb19556141ecb7`
  - `player-2.json` SHA-256 `82974eaf818ed3ba54ed0f79cf848c7ec75f8a63a63a2ed128ac01a81a495d68`
  - `scenario.SC2Replay` SHA-256 `b7d521c98172567911d80f5f2e07761300c59aaa8044ac8a69db3107b0a5f201`
  - `settings.json` SHA-256 `2491189225425eed92b9941bd1d300f2a03da536787685b5fdd1ea8d7538ccd3`
- `cliff-corrected-1-aa0-micro`: revision `9ad35ade530432c5917c1a069d2c932afa4a501e`, folder `scenario-20261105T212528Z-cliff-micro1`.
  - `player-1.json` SHA-256 `e0fb6c82a21f261ccc663258a82b2abdd7b09312b677e7d293c85d195581111c`
  - `player-2.json` SHA-256 `0b2890dd43ea38480eafee45db91e5c8bea4a29f3af0e111c289580b348662b6`
  - `scenario.SC2Replay` SHA-256 `6184d281b69398cfda017039e16f3df4f5f031e951d835dd96d36865a2400950`
  - `settings.json` SHA-256 `56b559457e976f79941a9472f4693b12120e7233666063358b0d3cd0a8e6e8b8`
- `cliff-0-aa0-baseline`: revision `7dffebfc30d0d4b7bce534ea9ea132ada258287c`, folder `scenario-20261105T210511Z-cliff-baseline0`.
  - `player-1.json` SHA-256 `3d4601ffe9625c98c0770e420a8396ec2a33141ecabbb49da438243ff9173efe`
  - `player-2.json` SHA-256 `bc269e47e7ecbdc1749e1fe82eb4c4bbfe943ee5bae493e6a04d4fcebc67dea3`
  - `scenario.SC2Replay` SHA-256 `e75cf19d05090b9ceacb7133ab4f69a5856cf81733df0798bde5f9f33338eb0c`
  - `settings.json` SHA-256 `7fd03152c5a4a3a90831455a3950dd7e100915d10f6f2bb12080f43dc0d510b5`
- `cliff-v2-0-aa0-baseline`: revision `d0e995dc566eaaefce46a597d59a1510d9fa0d0c`, folder `scenario-20261105T210753Z-cliff-baseline0`.
  - `player-1.json` SHA-256 `d962d93524dda756a6fc4e44ce53b47b9eafbb43f8ffb46ce1b25a09c74c6231`
  - `player-2.json` SHA-256 `ba56a697fa071c62d68254523545f12fd8bb00ab36d6d83ef7a42e6a555712da`
  - `scenario.SC2Replay` SHA-256 `2524b4ad5c32a3221b44469347b5084be1d68c735664d5424b98b55b12b3fb2a`
  - `settings.json` SHA-256 `7fd03152c5a4a3a90831455a3950dd7e100915d10f6f2bb12080f43dc0d510b5`
- `cliff-v3-0-aa0-baseline`: revision `b7733f08dce6ce8ffc3cce6f101039a31f152312`, folder `scenario-20261105T211019Z-cliff-baseline0`.
  - `player-1.json` SHA-256 `093fd5fbcd03072265c9090a06e4e8ceda3e365151261391ee148ea3bf22b37f`
  - `player-2.json` SHA-256 `2028e68f08fd7d36c2ef264ad37447608e682b3871fca5a1980347580819a016`
  - `scenario.SC2Replay` SHA-256 `b6e566a73891264adf60fb276862a8c169521c8885b0a147600c148034346a08`
  - `settings.json` SHA-256 `7fd03152c5a4a3a90831455a3950dd7e100915d10f6f2bb12080f43dc0d510b5`
- `cliff-v4-0-aa0-baseline`: revision `0aed15e0f6084abd2344e857e231cad0bf01fc67`, folder `scenario-20261105T211221Z-cliff-baseline0`.
  - `player-1.json` SHA-256 `d962d93524dda756a6fc4e44ce53b47b9eafbb43f8ffb46ce1b25a09c74c6231`
  - `player-2.json` SHA-256 `ba56a697fa071c62d68254523545f12fd8bb00ab36d6d83ef7a42e6a555712da`
  - `scenario.SC2Replay` SHA-256 `9d003f49f01ead1801dbe2e6c9f66130fd2081c46384494e0bdff96ee96c9887`
  - `settings.json` SHA-256 `7fd03152c5a4a3a90831455a3950dd7e100915d10f6f2bb12080f43dc0d510b5`
- `cliff-v5-0-aa0-baseline`: revision `cf8a227f97c5a53a77ef8ac5089923c14fced663`, folder `scenario-20261105T212003Z-cliff-baseline0`.
  - `player-1.json` SHA-256 `ba881e3ebe3058fba1d359392d0e898dd40e3cd8501fd63a0da8041a16cd5d40`
  - `player-2.json` SHA-256 `f43c71facb5361b0195a6ad91fc30fe2a6230daccbb2c97ecde3bb8c3e67b6b9`
  - `scenario.SC2Replay` SHA-256 `7b90448c5707d67978022cd028bceb800a74755437a5a64a48e14e527af32d07`
  - `settings.json` SHA-256 `7fd03152c5a4a3a90831455a3950dd7e100915d10f6f2bb12080f43dc0d510b5`
