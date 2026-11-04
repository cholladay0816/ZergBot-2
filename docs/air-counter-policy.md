# Air counter policy: research versus implemented behavior

The requested [community counter matrix](https://andresmrm.gitlab.io/starcraft-2-counters/)
is Liquipedia-derived, not controlled 5.0.17 evidence. These are strategic hypotheses,
not optimal ratios. Installed costs, tech readiness, scouting age, economy and ground
support must gate any transition. Do not equate an air unit sighting with unlimited air production.

| Observed threat | Immediate defense / sustained candidate | Important limitation |
|---|---|---|
| Mutalisk | Queens/Spores; bounded Hydras with ground army, or existing Corruptors | Hydras cannot chase cliff harassment; avoid overinvestment against a few Mutas |
| Banshee | Queens/Spores, Hydras plus mobile detection | Hydras alone cannot solve cloak; Overseer availability matters |
| Void Ray | Hydras generally preferable to pure Corruptors | Armored Corruptors are vulnerable to anti-armor damage; positioning still matters |
| Phoenix | Grouped Hydras locally; Corruptors with substantial air investment and available Spire | Small Hydra groups can be lifted; Corruptors may not catch retreating Phoenix |
| Battlecruiser | Queens/Spores buy time; Corruptors for sustained mobile response | Preserve economy/ground defense and account for mobility; no universal ratio |
| Carrier | Corruptors targeting Carrier bodies, supported by ground army | Do not assume Hydra/Interceptor attrition wins; accompanying Void Rays change composition |
| Tempest | Mobile Corruptor response | Range, retreat paths and supporting army matter |
| Brood Lord | Corruptors; local stopgap anti-air if reachable | Ground-only forces cannot answer the source; support can punish approach |
| Liberator / LiberatorAG | Queens/Spores outside siege zones; Corruptors for sustained response | Hydras can punish exposed units but must not walk through Defender zones |
| Mixed air/ground | Preserve complementary air and ground roles | Never convert the whole army to a single counter based on one sighting |

## Current implementation gap

The opt-in adaptive controller currently uses a single bounded Hydra fallback (4-20)
for recent visible air and a separate visible-Immortal trigger. It does not implement
the full matrix, a Spire/Corruptor transition, mobile detection, or Liberator-zone avoidance.
Therefore it is not an optimal counter selector and stays disabled by default.
`LIBERATORAG` is explicitly listed among air threats, but the current memory path still
also requires `is_flying`; the installed observed sieged Liberator was flying. A future
typed policy should identify both Liberator forms regardless of that flag and regress it.
No frozen match source was changed to incorporate unvalidated research mid-comparison.

Next wave: retain typed sightings with age/confidence, emit a reasoned counter recommendation,
then separately test production prerequisites, detection, resource reserves and actual
engagements before enabling new spending. A recommendation alone is not implemented defense.

## Sources and age

- [Hydralisk coach analysis, 2017](https://swarmscblog.wordpress.com/2017/11/21/unit-spotlight-hydralisk/): historical strategic principles, not current numeric timings.
- [Blizzard Mutalisk tips](https://news.blizzard.com/en-us/article/5967866/game-guide-zerg-mutalisk-tips): historical warning about overbuilding Hydras for small harassment.
- [Standard ZvT guide, 2018](https://swarmscblog.wordpress.com/2018/09/01/standard-zvt-guide/): historical Queen/Spore defense principles.
- [LotV Corruptor reference](https://liquipedia.net/starcraft2/Corruptor_%28Legacy_of_the_Void%29) and [Liberator reference](https://liquipedia.net/starcraft2/Liberator).
- [Official 5.0.17 notes](https://news.blizzard.com/en-us/article/24309308/starcraft-ii-5-0-17-patch-notes): installed 5.0.17.98310 matches this live major patch; actual game data is authoritative for mechanics.
