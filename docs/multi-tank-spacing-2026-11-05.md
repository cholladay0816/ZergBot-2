# Ling/baneling splitting against multiple siege tanks

The user correctly identified overlapping splash as the relevant test. This wave compares the existing fixed-lane split with grouped attacks against two and three sieged tanks. It tests this implementation, not whether well-executed spacing can be valuable.

Frozen runtime `f00b5f4440065966c65fee5b2bb85adbbad6c1c9`. Each pair requests the same 12 lings, 4 banes, tank count, health/upgrades, debug spawn locations, approach and seed. Approaches 0/1/2 use seeds 1/2/3. Tanks use the same visible-cluster targeting controller. Normal fog is retained; attacker-owned cooldown/order data is evaluator-only. Each run lasts at most 45 game / 120 wall seconds, sequentially, below normal priority on CPUs 20-23. No production policy changed.

## Outcomes

Each entry is baseline -> split. All banelings were absent at the end of every case; some can disappear through self-detonation. A surviving ling without neutralizing the tanks is not a successful engagement.

| Tanks | Approach / seed | Surviving lings | Surviving ling HP | Tanks left | Remaining tank HP | All tanks destroyed at game seconds |
|---:|---|---|---|---|---|---|
| 2 | 0 / 1 | 6 -> 4 | 153.6 -> 140.0 | 0 -> 0 | 0.0 -> 0.0 | 7.72 -> 15.09 |
| 2 | 1 / 2 | 5 -> 3 | 152.2 -> 91.8 | 0 -> 0 | 0.0 -> 0.0 | 9.20 -> 18.62 |
| 2 | 2 / 3 | 3 -> 7 | 88.5 -> 211.5 | 0 -> 0 | 0.0 -> 0.0 | 13.62 -> 12.10 |
| 3 | 0 / 1 | 0 -> 1 | 0.0 -> 32.5 | 3 -> 3 | 346.0 -> 367.0 | not neutralized -> not neutralized |
| 3 | 1 / 2 | 2 -> 0 | 53.4 -> 0.0 | 0 -> 3 | 0.0 -> 271.5 | 23.12 -> not neutralized |
| 3 | 2 / 3 | 1 -> 0 | 11.4 -> 0.0 | 3 -> 3 | 266.0 -> 258.0 | not neutralized -> not neutralized |

Against two tanks, splitting regressed in two approaches and improved the third. Total surviving lings were 14 for both policies, but two split cases took roughly twice as long to neutralize the tanks. Against three tanks, baseline neutralized all tanks in one of three cases; splitting did so in none, and left only one ling total versus three under baseline. The policy stays disabled/scenario-only. These are six matched pairs, not a general win-rate study.

The split creates a bounded lateral deployment before engagement, but its delay can permit more volleys. That is a plausible mechanism, not proof of exact per-shot causality. Future candidates should compare a smaller lateral move while advancing and explicit multi-tank target assignment, with separate baneling handling. Do not promote a policy merely because its spacing statistic is larger.

## Splash-related observations and limits

| Tanks / approach | Policy | Mean opening nearest-neighbor distance | Recorded nonfatal HP loss | Damage observation frames | Multi-unit damage frames | Maximum recorded HP loss in one observation |
|---|---|---:|---:|---:|---:|---:|
| 2 / 0 | baseline | 0.75 | 199.4 | 2 | 2 | 139.7 |
| 2 / 0 | micro | 1.74 | 99.6 | 2 | 2 | 69.7 |
| 2 / 1 | baseline | 0.78 | 149.5 | 3 | 2 | 99.7 |
| 2 / 1 | micro | 1.87 | 149.4 | 5 | 4 | 69.7 |
| 2 / 2 | baseline | 0.74 | 149.2 | 2 | 2 | 129.4 |
| 2 / 2 | micro | 1.80 | 149.5 | 4 | 3 | 49.8 |
| 3 / 0 | baseline | 0.84 | 149.4 | 3 | 2 | 119.6 |
| 3 / 0 | micro | 1.91 | 179.1 | 6 | 2 | 99.5 |
| 3 / 1 | baseline | 0.79 | 159.3 | 3 | 2 | 119.6 |
| 3 / 1 | micro | 1.73 | 99.5 | 2 | 2 | 79.6 |
| 3 / 2 | baseline | 0.94 | 129.8 | 3 | 3 | 90.0 |
| 3 / 2 | micro | 1.84 | 119.7 | 5 | 2 | 59.9 |

These are grouped observation callbacks, **not exact damage per shell**. The normal API does not provide a unique attacker/projectile damage event here. Fatal impacts can omit HP-loss callbacks, multiple tanks can hit within one observation interval, and baneling detonation complicates disappearance. Lower callback damage can accompany worse losses, as in two tanks / approach 0. Therefore survivor counts/HP and enemy neutralization are primary metrics.

The owned-unit death callback provides tank removal times at observation resolution (game step 4), rather than guessing death from enemy visibility. The normal roster spacing samples occur every 16 loops; the first tank volley can kill units before a complete initial roster sample. The setup commands request identical compositions, but later observed maximum roster counts are not a complete spawn audit. Exact first-volley damage and per-shell attribution remain measurement gaps. The derived known-target firing-cycle count is a lower bound: early victims may be absent from retained sampled tags, and order target metadata can be absent. It is not used as an exact shots-fired denominator.

Tank HP totals are the final owner-observed health of surviving tanks. They describe overall scenario damage, not exact damage credited to an individual ling/bane. Original workers/town halls remain; collateral damage is preserved in local evidence. Caps with surviving tanks remain unresolved/failed threat-removal cases, not wins.

Other AoE was not exercised in this wave. Storm, Disruptors and Hellion line splash need separate validated adversaries and geometry; these tank results do not establish their outcomes. The existing offensive Hellion diversion tests did not contain this ling/bane split and are not substituted for that validation.

## Validation and resource evidence

256 offline tests and Ruff lint/format passed before runtime freeze. All 12 supervisors completed with zero recorded action errors or command conflicts. Peak sampled host CPU 38.4%; minimum available RAM 9.02 GiB. No sustained guard stop occurred.

## Local artifact audit

- `scenario-20261105T000334Z-tank-baseline0` (multi-tank-2-approach0-seed1-baseline):
  - `player-1.json` SHA256 `a23822bea6affa7a72db3c3d8d93059dd821ad4b227a8f2bdfb207445f0d5a80`
  - `player-2.json` SHA256 `f37d0d1b545131e9a21c43d9412f9a18e4d0b23fc5a4c97635b72392b7b49e7e`
  - `scenario.SC2Replay` SHA256 `88fe9ce9a0869f486acaf840da1c64bbf2b885a3527a3d29286748633a6d6d4d`
- `scenario-20261105T000402Z-tank-micro0` (multi-tank-2-approach0-seed1-micro):
  - `player-1.json` SHA256 `b78d631351eef2c2facf8885d6f620b4470ed8baf21c6f0ed4f5d68ba93e8256`
  - `player-2.json` SHA256 `4f3cf00a89369588f45df701fe4cfe9b5a50686b04ebfeefbe8463471f67062c`
  - `scenario.SC2Replay` SHA256 `8a4490c8e59d32b8873630a4e952e42b75e36038d27beff716225e5fbe5d22e3`
- `scenario-20261105T000429Z-tank-baseline1` (multi-tank-2-approach1-seed2-baseline):
  - `player-1.json` SHA256 `3dec94c9464541bea8ce254781752b51b79e87468ba795a43f6e4b487f8b06c1`
  - `player-2.json` SHA256 `fd7e6c3ee34d02fda72f919abee6ddfb05c3534f62bbc334d16a050258f4f3cf`
  - `scenario.SC2Replay` SHA256 `c38a58e218c23955e55403835a948285358f72e6b24af516f8eda9868d1322ad`
- `scenario-20261105T000455Z-tank-micro1` (multi-tank-2-approach1-seed2-micro):
  - `player-1.json` SHA256 `509991d82fcca2a77fc59fdac872e26a57622fac7f795eee68689bf4bfd5550c`
  - `player-2.json` SHA256 `773664bef0ce60992a4866cc9c6e061f9cb341400f86b62be0449877adc10392`
  - `scenario.SC2Replay` SHA256 `d90442cee6182585df20e0c4184c72907c612c0c540748b1ae81a81139ff0567`
- `scenario-20261105T000521Z-tank-baseline2` (multi-tank-2-approach2-seed3-baseline):
  - `player-1.json` SHA256 `c672a6be597ef0e62d6312c4116de267fed54c8d8bc96684610dc754432749e7`
  - `player-2.json` SHA256 `18ec41707315bf6583afed81c8cb97c8f0b7a2f9dbf52057a1911f4477fe201d`
  - `scenario.SC2Replay` SHA256 `8163fa4fd6fab16c5ba0db447f8628ac226886143a4d9001756d208f087a26a8`
- `scenario-20261105T000548Z-tank-micro2` (multi-tank-2-approach2-seed3-micro):
  - `player-1.json` SHA256 `f351ab269d28e020da0b7112ad0a33654cab5a2db8de89ff05df8b4f5d6c1971`
  - `player-2.json` SHA256 `220e76a98bbe8572babddb6dea1be68f040f2fae821a3995bd50415cba59101e`
  - `scenario.SC2Replay` SHA256 `f347685d6078fbe93af4a5ab87a8c3fbb9d5795041dcf62d8048bcece481472c`
- `scenario-20261105T000614Z-tank-baseline0` (multi-tank-3-approach0-seed1-baseline):
  - `player-1.json` SHA256 `faab1393f952ad2ea926bb1bba3925b812e7793064a43727f00654e6ee2df7c0`
  - `player-2.json` SHA256 `921f40c42080a315621c2b9a013c94e699e187a5299d720894f43e66e30bfb32`
  - `scenario.SC2Replay` SHA256 `0c5cba30a059d7e5e27abaf72275bcc9297b2e61891531a47246f1e88e5cbe1c`
- `scenario-20261105T000639Z-tank-micro0` (multi-tank-3-approach0-seed1-micro):
  - `player-1.json` SHA256 `e31a1013dd703268dcab52b541d1d0205e2ecd204b42aef9625e72904aa1231b`
  - `player-2.json` SHA256 `86ea9c663b43300938e0b48b534fb925e7b80585325bccdbe4ae3d3e9f7d15c9`
  - `scenario.SC2Replay` SHA256 `a2139b58c14edca5414c8a673dcf8d3f532daebd8b9f11874b695e00776583b5`
- `scenario-20261105T000705Z-tank-baseline1` (multi-tank-3-approach1-seed2-baseline):
  - `player-1.json` SHA256 `65e13360080fd60a80555fc406fb4449cfb4ffecca032279edc71bad5035710e`
  - `player-2.json` SHA256 `5064e8608f299c2e7d6504bce3de341322c3e413aedd148db327a207a1003081`
  - `scenario.SC2Replay` SHA256 `dc8783d54dd98a4653a295c78a899f58f97459148ef9281a8d2870c9484d62bf`
- `scenario-20261105T000733Z-tank-micro1` (multi-tank-3-approach1-seed2-micro):
  - `player-1.json` SHA256 `383a85729d1c534ca8bc6a8ea2151fa7f66d4e28145532a72ee0e6a96b876386`
  - `player-2.json` SHA256 `e83bcd52b76b762c07736ecec99fef2cdce15c42e520604785c7fdc71ce8a557`
  - `scenario.SC2Replay` SHA256 `17ee2a7307b1319df968424666fccc531218ec66ca601872c5d22266ded0de64`
- `scenario-20261105T000800Z-tank-baseline2` (multi-tank-3-approach2-seed3-baseline):
  - `player-1.json` SHA256 `974d0d10aa7982977fdda88b48f8d811c078e0e69a28502c2c9eea72899c7fdb`
  - `player-2.json` SHA256 `49fca06c13d8211b2d0dbe089655e0127f4ba24f1bdc381f390c76742b5ea437`
  - `scenario.SC2Replay` SHA256 `008a9005ddadf798100455d999678f8f22bf19b8c025cf96b611dae2e223bbf4`
- `scenario-20261105T000826Z-tank-micro2` (multi-tank-3-approach2-seed3-micro):
  - `player-1.json` SHA256 `97c0a330b1c18eab2f3d4afb3306cb7fd4c36c78ebf8bc5830958f52de22d5c5`
  - `player-2.json` SHA256 `3b35fb7a0bfdee5fce31027b11788808deb3b2f22dfc03875f2bed3e559fd643`
  - `scenario.SC2Replay` SHA256 `08ad622d749d061aa1acf3411df6c95afd52756a7043957ea695d29144c074e3`