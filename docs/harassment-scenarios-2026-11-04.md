# Adept and offensive Hellion scenario evidence

These isolated 60-game-second scenarios are capped tests, not full-match victories. All actors use normal observations after debug setup. Python 3.14.10, burnysc2 7.3.0, installed SC2 5.0.17.98310, AbyssalReefLE, game step 4. Each game has a 120-second wall bound.

## Mechanic pilots

Revision c342ebc: the commit pilot observed an owned shade at frame 10 and a 15.76-unit Adept relocation at frame 170 (160 frames after first shade observation, about 7.14 game seconds). The cancel pilot issued the actually available CANCEL_ADEPTPHASESHIFT at frame 121 and observed shade disappearance with zero Adept displacement at frame 125. These are attacker-side evaluation facts; the defender never receives the cancellation plan. Worker losses were 3 and 2. Both players had zero conflicting command frames and no reported action errors.

## Shade warning posture

Frozen revision: `dff46c7e7d8e040416b8e9fe3f6347ca92dc8df6`.

| Case | Workers lost | Final mineral bank | Defender / attacker survivors | Guard samples | Command conflicts |
|---|---:|---:|---|---:|---:|
| shade-0-commit-False | 2 | 590 | {'LARVA': 6, 'QUEEN': 1, 'DRONE': 10, 'OVERLORD': 1} / {} | 0 | 0 |
| shade-0-commit-True | 2 | 595 | {'QUEEN': 1, 'DRONE': 10, 'LARVA': 6, 'OVERLORD': 1} / {'ADEPT': 1} | 13 | 0 |
| shade-0-cancel-False | 2 | 585 | {'DRONE': 10, 'LARVA': 6, 'OVERLORD': 1, 'QUEEN': 1} / {} | 0 | 0 |
| shade-0-cancel-True | 2 | 590 | {'LARVA': 6, 'DRONE': 10, 'OVERLORD': 1, 'QUEEN': 1} / {} | 7 | 0 |
| shade-1-commit-False | 3 | 550 | {'LARVA': 6, 'DRONE': 9, 'QUEEN': 1, 'OVERLORD': 1} / {} | 0 | 0 |
| shade-1-commit-True | 2 | 595 | {'DRONE': 10, 'LARVA': 6, 'QUEEN': 1, 'OVERLORD': 1} / {'ADEPT': 1} | 13 | 0 |
| shade-1-cancel-False | 2 | 590 | {'LARVA': 6, 'DRONE': 10, 'QUEEN': 1, 'OVERLORD': 1} / {} | 0 | 0 |
| shade-1-cancel-True | 2 | 590 | {'LARVA': 6, 'DRONE': 10, 'QUEEN': 1, 'OVERLORD': 1} / {} | 7 | 0 |
| shade-2-commit-False | 2 | 585 | {'LARVA': 6, 'DRONE': 10, 'OVERLORD': 1, 'QUEEN': 1} / {} | 0 | 0 |
| shade-2-commit-True | 2 | 580 | {'DRONE': 10, 'LARVA': 6, 'OVERLORD': 1, 'QUEEN': 1} / {'ADEPT': 1} | 13 | 0 |
| shade-2-cancel-False | 2 | 590 | {'DRONE': 10, 'LARVA': 6, 'OVERLORD': 1, 'QUEEN': 1} / {} | 0 | 0 |
| shade-2-cancel-True | 2 | 600 | {'DRONE': 10, 'OVERLORD': 1, 'QUEEN': 1, 'LARVA': 3} / {'ADEPT': 1} | 8 | 0 |

Evidence (local only; SHA256 of each player JSON):

- `scenario-20261104T222724Z-adept-micro0`: player-1.json `a7a2b725c1a29715b5791ae4e2af22913d7301488e557d26848b2ecf71176dfd`; player-2.json `ef07764125bed8d4843842c3539ea646a50f40459ded63e7fc4dc1087f71f884`
- `scenario-20261104T222754Z-adept-micro0`: player-1.json `90947a315a2702cb5f730174d21dae6f5b455ee029b0ba57de28f7842226a7c1`; player-2.json `5e0e09136ee8dbd3f62c7f4df271db92a928a47b3c1cb522126c0c23392cbc51`
- `scenario-20261104T222823Z-adept-micro0`: player-1.json `29a0f836eba82c6ce19f9be65292e33277af105eff8872679633110ea5498f93`; player-2.json `baddd6267e30a476dcb337bfb1193dbd9c10eff78051102d061a7d9f6bf04f49`
- `scenario-20261104T222851Z-adept-micro0`: player-1.json `d874a7e21e67062fdd9b90cfab8aba57eb1833cbb2226540366ad448d11c1ab0`; player-2.json `2525c69a08abbe498daaf34517166d722ae8e5ef705bb1d1d2ac304e808c5cad`
- `scenario-20261104T222920Z-adept-micro1`: player-1.json `c9ae7b564451910b5175c5b6e665aa798f108eb5e88b558915120905b27d6dbd`; player-2.json `3c5b89f1d839a1ffa24622bd72bb054d86581bbcd1e7ab4bd62867874981b87f`
- `scenario-20261104T222948Z-adept-micro1`: player-1.json `c19f358ed85bf9cbd8ccd3d2a3b8bfec83ea7a3c6b9437ea07f3137e7a7a5e47`; player-2.json `1d773379f27a8fd31c42a3122bdd67d1cd5cd7a4612e31179a1a15a639298158`
- `scenario-20261104T223019Z-adept-micro1`: player-1.json `aa4e2f8e06e2fa11baa2a2a8c8b0895700cf5a328fd3ad94d21144286f5ddb2d`; player-2.json `b67bb993f1568a7ea9d4af60d67b5375dabe29112c9252f61b189ee1abe0472e`
- `scenario-20261104T223047Z-adept-micro1`: player-1.json `ca32a35bdda00a76a3244d5aefeef61a1ef0c2936d0f290d668cc3490c3c5911`; player-2.json `b78d711f8c8b09d9bada22dc3aee1f3ffa793a9256ab951e02076075aad31b5e`
- `scenario-20261104T223115Z-adept-micro2`: player-1.json `03ad54445e26610d0aa26c3ed4e52fdd7a3b29f0d4c062d20bd1be23c6a98c0f`; player-2.json `f3d39b7182d7c50fd205d06dce7f2bf285f4227c3dae381e41a13790cd94ec76`
- `scenario-20261104T223144Z-adept-micro2`: player-1.json `ba7db838acda74fbcff72f938caae3c6e53ff456b2fd4fbd187ae4a7fcb46816`; player-2.json `6a29cce81149193f06cd997052236fe39f3abc59d052d05c13adb52423d0f337`
- `scenario-20261104T223212Z-adept-micro2`: player-1.json `51ea480f980d3e01bf454ad52ffdf601800c8054fc9142755c769797369a2ea9`; player-2.json `be8ada0b46103f51f863726a8a90d28b7109222012559fa00667beb00c238070`
- `scenario-20261104T223241Z-adept-micro2`: player-1.json `b44f69066982f62a1321212d0a9167b8bf0a8dd0237a90cd9db4175976700124`; player-2.json `9061196fe588db1727a99d7d9cdcb56fc596eb9c4af9072521f3cd5b737354ef`

## Initial flank-only run: diversion setup defect

Frozen revision: `aa0745d7023908bf47628ffb8cfcc195cf5684f7`.

| Case | Workers lost | Final mineral bank | Defender / attacker survivors | Guard samples | Command conflicts |
|---|---:|---:|---|---:|---:|
| diversion-0-False | 7 | 355 | {'SCV': 5, 'HELLION': 2} / {'LARVA': 3, 'OVERLORD': 1} | 0 | 0 |
| diversion-0-True | 11 | 255 | {'HELLION': 2, 'SCV': 1} / {'LARVA': 3, 'OVERLORD': 1} | 0 | 0 |
| diversion-1-False | 6 | 405 | {'SCV': 6, 'HELLION': 2} / {'LARVA': 3, 'OVERLORD': 1} | 0 | 0 |
| diversion-1-True | 8 | 340 | {'SCV': 4, 'HELLION': 2} / {'LARVA': 3, 'OVERLORD': 1} | 0 | 0 |
| diversion-2-False | 12 | 150 | {'HELLION': 2} / {'LARVA': 3, 'OVERLORD': 1} | 0 | 0 |
| diversion-2-True | 11 | 250 | {'SCV': 1, 'HELLION': 2} / {'LARVA': 3, 'OVERLORD': 1} | 0 | 0 |

| Case | Distraction samples | Flank traversal samples | Tags reaching route stage 2 | Observed worker-attack samples | Hellion HP loss callbacks |
|---|---:|---:|---:|---:|---:|
| diversion-0-False | 0 | 0 | 0 | 132 | 0.0 |
| diversion-0-True | 0 | 128 | 12 | 175 | 0.0 |
| diversion-1-False | 0 | 0 | 0 | 118 | 0.0 |
| diversion-1-True | 0 | 103 | 12 | 160 | 0.0 |
| diversion-2-False | 0 | 0 | 0 | 171 | 0.0 |
| diversion-2-True | 0 | 103 | 12 | 214 | 0.0 |

Evidence (local only; SHA256 of each player JSON):

- `scenario-20261104T223324Z-diversion-baseline0`: player-1.json `a1806d7b7b99e310a6c3b13dcc6df93f83d4e4dc3b08c86eeb546d81605ab1bf`; player-2.json `572e56623f5203f28376e43fea644ce2bbdfe28983e3e669280b09a0259ad073`
- `scenario-20261104T223352Z-diversion-baseline0`: player-1.json `b3c4219e0bf8a6d78fbea005acfb988e869779dfa264ef5fc271fd13f7a55ba3`; player-2.json `e12f399529cf2c78ae6690c72029304cf49448e44fc2d1206eec008619260170`
- `scenario-20261104T223420Z-diversion-baseline1`: player-1.json `081ed27dcb9e9e555e8f3e4a9f49b15016f2fbca780c848dc4ef2e067f4b7c09`; player-2.json `4be0100c1d1c3d2f66932313d9283eb4a5472a532313d38944e496a9d47c4ea4`
- `scenario-20261104T223449Z-diversion-baseline1`: player-1.json `fef9a9f56bf750d00a78621becac43e9b186fb01c18d1a119048dfa6f4488a47`; player-2.json `e1a9d5ae59d55b20c3660a2973bb0e76d2509f299de20da609964177399c382c`
- `scenario-20261104T223519Z-diversion-baseline2`: player-1.json `f60fe42bad10ecf31b637f613b0a0478a2de14d965d19be499e0d1931c527f18`; player-2.json `5590ed5313e067addb99a81760a70791bae5227a7b74b2f847d56d7d1192a83d`
- `scenario-20261104T223548Z-diversion-baseline2`: player-1.json `8d521983033eca7a1eedb6a9a01f8fed67a9a478d25c5748d15db42b0e9ed4c7`; player-2.json `c896c0c3422548719b2a5e0437af9366e542350032291dc5c13965a145e82938`

## Corrected offensive ling diversion

Frozen revision: `b6f7f4d542b5a900efcb8462dc0d6d0d936f02be`.

| Case | Workers lost | Final mineral bank | Defender / attacker survivors | Guard samples | Command conflicts |
|---|---:|---:|---|---:|---:|
| diversion-roles-0-False | 7 | 350 | {'SCV': 5, 'HELLION': 2} / {'LARVA': 3, 'OVERLORD': 1} | 0 | 0 |
| diversion-roles-0-True | 8 | 325 | {'SCV': 4, 'HELLION': 2} / {'OVERLORD': 1, 'LARVA': 3} | 0 | 0 |
| diversion-roles-1-False | 8 | 310 | {'HELLION': 2, 'SCV': 4} / {'LARVA': 3, 'OVERLORD': 1} | 0 | 0 |
| diversion-roles-1-True | 4 | 510 | {'SCV': 8, 'HELLION': 2} / {'LARVA': 3, 'OVERLORD': 1} | 0 | 0 |
| diversion-roles-2-False | 8 | 335 | {'SCV': 4, 'HELLION': 2} / {'LARVA': 3, 'OVERLORD': 1} | 0 | 0 |
| diversion-roles-2-True | 7 | 385 | {'HELLION': 2, 'SCV': 5} / {'LARVA': 3, 'OVERLORD': 1} | 0 | 0 |

| Case | Distraction samples | Flank traversal samples | Tags reaching route stage 2 | Observed worker-attack samples | Hellion HP loss callbacks |
|---|---:|---:|---:|---:|---:|
| diversion-roles-0-False | 0 | 0 | 0 | 99 | 0.0 |
| diversion-roles-0-True | 146 | 68 | 8 | 119 | 0.0 |
| diversion-roles-1-False | 0 | 0 | 0 | 136 | 0.0 |
| diversion-roles-1-True | 96 | 70 | 8 | 99 | 0.0 |
| diversion-roles-2-False | 0 | 0 | 0 | 164 | 0.0 |
| diversion-roles-2-True | 112 | 68 | 8 | 126 | 0.0 |

Evidence (local only; SHA256 of each player JSON):

- `scenario-20261104T223645Z-diversion-baseline0`: player-1.json `e5266728ddc87bc8887c2fb3358cc41c963d5a687f94569004a24a4b712619d2`; player-2.json `331735b488136333ff7e6d91deae4f4d33dae3a0b91145e8bfc8a17efbb05573`
- `scenario-20261104T223714Z-diversion-baseline0`: player-1.json `6ade220fbf83d37bbd98ae33e9c9c72f6580be05039d986ce590428ccc11753e`; player-2.json `c1203881ed37963bfd6aec7283b31cf8679113e8cd0f5d4aa9ce2c0074ac5682`
- `scenario-20261104T223742Z-diversion-baseline1`: player-1.json `06a742f9b6546c3932a98a95078c356a13e399cc6d4f56f21733092b03ad383b`; player-2.json `1de691e503458375dceec857e44253969ef9a55de3f872b9f0af6d12be12c08f`
- `scenario-20261104T223810Z-diversion-baseline1`: player-1.json `6c4756b55f8e9156076faa484b22c8da574585f0e07f0c649df5fa7a841f032d`; player-2.json `09f5e028eae81941527647a23bbd4d37a3877a05582520d77ef3c595a14d642e`
- `scenario-20261104T223839Z-diversion-baseline2`: player-1.json `d30875d3fe66f324faeac3a1017448d99b9100afb4064518353f13f2f335ad2c`; player-2.json `a7eb606f8addfec13d0f926fb96fc5ee93b60d443f0d60b386791c5d379e5950`
- `scenario-20261104T223907Z-diversion-baseline2`: player-1.json `063b173b64f09c2cfa58733281a3658bc98cb3488f424d78f7ac8ed32ae3e4a2`; player-2.json `531be99c9a42c4362cce444294c259ebc91a810a22ac12599907d84f3a221085`

## Decisions

Shade warning posture reduced losses by one worker in one of six paired cases: committed-transfer losses 2/3/2 became 2/2/2, while cancelled-transfer losses stayed 2/2/2. This limited result does not justify a competitive default. All twelve runs verified the intended actual cast/commit or cancellation, with no action errors or conflicting unit frames.

The first diversion revision assigned roles before the spawned lings appeared in observations. Its split runs therefore exercised a flank-only policy with zero distraction-role samples, not the requested tactic. Revision b6f7f4d waits for observed lings; the added empty-observation regression test checks that four roles are actually assigned. Preserve the initial evidence as a setup defect and separately label the corrected comparisons.

## Interpretation limits

Mineral bank is an observed collection proxy in these no-production scenarios, not a direct measurement of mining time lost. Damage callbacks can omit fatal-frame damage. Enemy weapon cooldowns are never treated as known. Line-overlap targeting is a geometric heuristic, not an engine splash forecast. A pathing distance is not a route or proof of safety.

The diversion changes only ling policy: twelve lings start together in both cases against two worker-anchored Hellions and twelve workers. Four lings can distract while eight traverse a side route, with a 628-frame bound before regrouping into worker pressure. The Hellions prioritize visible threats near their worker line and do not automatically chase a remote decoy. This is a scripted adversary and does not establish optimal play.

Both options remain isolated scenario experiments; neither is enabled in the competitive bot.


## Retention and resource decision

Corrected diversion worker kills were 7/8/8 grouped versus 8/4/7 split. All twelve
lings died and both Hellions survived in every case. The eight flank lings reached
route stage 2 in each split run, and real distraction decisions occurred; this is
an exercised but mixed/regressive candidate, not a recommended default. The earlier
flank-only runs are not valid diversion results. No Hellion HP loss callback was
recorded; the decoys drew some targeting opportunities without damaging the Hellions.

The shade guard also left the Adept alive in both approach-2 cases where the control
killed it. Combined with the small worker-survival difference, this reinforces keeping
the guard off. These are baseline controllers and narrow geometry experiments, not
optimal adversarial play or proof of general rush safety. Neither optional policy is
connected to the competitive bot. Fixed seeds did not eliminate observed run variation.

Across these 26 runs (two Adept pilots, twelve guard cases, six initial flank-only cases,
six corrected diversion cases), all supervisors completed normally. Peak sampled CPU
was 66.9%; minimum sampled free RAM was 4.23 GiB. No resource stop occurred. All owned
SC2 processes exited after the batch. Protected SimTrader PIDs 16400 and 18472 retained
Normal priority. Sampling cannot prove zero transient workload impact.

Reproduce isolated cases, preserving outputs between runs:

```powershell
.venv/Scripts/python.exe -m zergbot.scenarios --scenario adept --adept-mode commit --controller micro --approach 0 --game-time-limit 60
.venv/Scripts/python.exe -m zergbot.scenarios --scenario adept --adept-mode cancel --controller micro --approach 0 --shade-guard --game-time-limit 60
.venv/Scripts/python.exe -m zergbot.scenarios --scenario diversion --controller baseline --approach 0 --game-time-limit 60
.venv/Scripts/python.exe -m zergbot.scenarios --scenario diversion --controller baseline --approach 0 --ling-split --game-time-limit 60
```

The local supervisor adds the finite wall bound, hidden below-normal processes, CPU
affinity and resource stops; the raw CLI commands above do not install those host controls.
