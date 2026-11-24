# Campaign and mission design catalog (StarCraft: Brood War)

> **Game boundary:** this catalog is for StarCraft: Brood War only. Ideas, rules and checks from the other game are not ported here
> (no "adapted", no "analog", no substitute). A pattern is listed only when it was given for Brood War or explicitly
> requested for it.

> **You are always welcome to invent your own new ideas. You are NOT limited to these lists.**
> The lists are inspiration, not a menu. Every example below is only an example; build new variants, combine patterns,
> or design something that is in no list at all. Inventing is expected, copying an example 1:1 is the weak choice.
> When you invent something good, add it here (classified).
> **Always ask what makes a mission more challenging and more varied:** every objective, siege and
> defence should give the player decisions and pressure (enemy reactions, sub-goals, map changes), not only hit points.

## How to use and maintain the catalogs
- **Two separate catalogs.** Every idea is classified before it is listed:
  - **Gameplay:** changes what the player DOES or how the game reacts: objectives, defeat/victory rules, map
    mechanics, economy, tech, AI behaviour, time pressure, unit control, rewards. Test: "would it still matter with all
    dialogue removed?" -> gameplay.
  - **Story:** changes what the player LEARNS or FEELS: plot structure, characters, relationships,
    perspective, foreshadowing, themes, presentation. Test: "would it still work as a written short story?" -> story.
  - Mixed ideas are split: the gameplay half goes into the gameplay catalog, the story half into the story catalog, each
    entry naming its twin (`twin: S-x` / `twin: G-x`).
- **Every entry carries:** id, level (campaign / mission), classification, how it applies in Brood War (`yes` or
  `adapted: <how>`), and a source (Blizzard mission, custom campaign, playtest feedback, own invention). Ids are kept
  stable, so gaps in the numbering are normal.
- **Before adding an idea, verify the mechanic exists** against real sources (the StarEdit trigger help, the official campaign maps). If it does not fit, do not list
  it. Never invent a substitute.
- Adopted catalog items go into the design note like the existing campaign rules (campaign level) or
  mission design deviations (mission level). Catalog items never override a fixed rule (fixed rule).
- Examples in this file are illustrative only; invent new variants.
- **Praised ideas are options, not defaults:** when playtest feedback likes an idea, record it here as a pattern; do NOT put it (or a re-skinned copy of it) into every following mission. Use a praised pattern only when this mission's design clearly calls for it. **Variety rule:** consecutive missions must not share the same side pattern (e.g. after a thief/raider mission, no raids, ambush packs or wolf raids in the next one). Before building, list the side patterns of the last 2 missions in the design note and pick different ones.
- **Write every new feedback into the guides and this catalog in the same turn:** when feedback creates a reusable rule or a catalog idea, add it here (classified) and into every other fitting guide, plus a check where feasible, in the same turn. Do not wait to be asked.

---
## A. Gameplay design patterns
*Inspiration, not a menu: invent your own patterns freely; examples are illustrative only.*

### A1. Campaign level (gameplay)
| id | pattern (examples are illustrative only) | in SC:BW | source |
|---|---|---|---|
| G-C1 | **Escalating threat type:** each mission adds one new enemy mechanic (air, casters, siege, burrow/stealth...), the finale combines them | yes | design idea (gameplay half) |
| G-C2 | **Choices with mechanical consequences:** pick one of two side objectives; the choice changes a later mission (extra ally, weaker enemy base, other tech) | adapted: separate mission variants (the custom Empire Wars campaign ships T6a/T6b, T7a/T7b) | design idea; MORAL_CHOICES; twin S-C2 |
| G-C3 | **Story-gated tech unlocks:** new units/techs arrive through an in-world event (freed smith, captured plans, new ally) instead of silently | yes | design idea (gameplay half); twin S-C4 |
| G-C4 | **Pacing interludes:** short hero-only/no-base missions (escape, exploration, puzzle) between base missions | yes (installation missions) | design idea; NO_BASE_MISSIONS_ALLOWED_OFTEN / HERO_FOCUS |
| G-C5 | **Recurring locations with changed mechanics:** an earlier map returns with new terrain/state (burnt, fortified, flooded) and new objectives | yes | design idea (gameplay half); twin S-C1 |
| G-C6 | **Signature mechanic** across the campaign, introduced on first sighting | yes | SIGNATURE_MECHANIC |
| G-C9 | **Attack warnings as a campaign feature** (scouts, towers) | yes | ATTACK_WARNINGS |
| G-C10 | **Restricted tech** beyond normal unlock pacing | yes | RESTRICTED_TECH |

### A2. Mission level (gameplay)
| id | pattern (examples are illustrative only) | in SC:BW | source |
|---|---|---|---|
| G-M1 | **Two ways to the goal** (loud gate vs hidden path with creeps) | yes | design idea |
| G-M2 | **Environment as a weapon** (explosive barrels, collapsing dam, capturable towers) | adapted: neutral buildings/units + triggers | design idea |
| G-M3 | **Timed window events** (interceptable caravan, prisoner transport) | yes | design idea; Blizzard Human05 |
| G-M4 | **Enemy reacts to the player** (reinforces another base, changes route) | yes (AI scripts/triggers) | design idea |
| G-M5 | **Exploration rewards** (hidden merchant, buff shrine, optional mini-boss) | adapted: the reward the find yields in the story (rescuables, units, tech, a stored cache) | design idea |
| G-M6 | **Defense phase with warning countdown** before a big wave | yes (Desperate Alliance "Survive for 30 minutes") | design idea; Blizzard |
| G-M8 | **Allied AI with its own agenda**, consequences if it falls | yes | design idea |
| G-M9 | **Multi-phase finale** (break wards -> boss -> escape/reinforcements) | yes | design idea |
| G-M10 | **Expert bonus objective** (lose no hero, save all villagers) with a small reward | yes | design idea |
| G-M11 | **No-base start, then base building** (see section C) | yes (Revolution, Norad II) | Blizzard |
| G-M12 | **Installation / maze mission**, no buildings, defeat on losing all units | yes (Jacobs Installation, Amerigo, Escape from Aiur) | BW campaigns |
| G-M13 | **Bring X to the beacon / exit** (escort, smuggle, escape) | yes (Egression, Escape from Aiur) | Blizzard |
| G-M14 | **Base takeover by a hero action** (reach a beacon/assassinate a commander, the base switches to the player) | yes (Revolution: Kerrigan at the Antigan Command Center) | Blizzard SC1 Terran 5 |
| G-M15 | **Protect a special structure for a time, then strike** | yes (Agent of the Swarm: Chrysalis 10 min) | Blizzard |
| G-M16 | **Infest/capture an enemy building** as the objective | yes (Agent of the Swarm: infest Raynor's CC) | Blizzard |
| G-M17 | **Island map that forces air/transport play** (drops, detection duels) | yes (Revolution, Agent of the Swarm) | Blizzard |
| G-M18 | **Cloak/detection duel** (enemy comsats/turrets vs cloaked strike force, energy management) | yes | Revolution walkthroughs |
| G-M19 | **Hero survives only until the base exists** (hero-death defeat switched to building defeat at the transition) | yes | Blizzard |
| G-M20 | **Conquest-as-objective / anti-stall pressure** (destroying everything also wins; late increasing waves stop stalling) | yes | Blizzard SC2 |
| G-M32 | **Rewards with an in-world source (fixed rule):** never flat minerals/gas or units for an unrelated deed (minerals for killing three Zerglings, gas for building a Nydus Canal). The reward comes from something the player sees: a guarded cache or loot, a grateful ally who pays or joins, a captured base/mine/depot, a rescued unit, seized convoy cargo, unlocked tech. Design note line `REWARD_WHY: <objective> :: <reward> :: <in-world source the player sees>` (examples only) | yes (predelivery check 41) | playtest feedback |


---
## B. Story / plot design patterns
*Inspiration, not a menu: invent your own story devices freely; examples are illustrative only.*

### B1. Campaign level (story)
| id | pattern (examples are illustrative only) | in SC:BW | source |
|---|---|---|---|
| S-C1 | **Recurring places as a narrative thread** (the rescued village returns changed) | yes | design idea (story half); twin G-C5 |
| S-C2 | **Branching consequences in the plot** (who lives, who betrays) | adapted: separate mission variants | design idea (story half); twin G-C2 |
| S-C3 | **Recurring antagonist** escapes once or twice and grows stronger | yes | design idea |
| S-C4 | **Tech arrives through story** (freed smith, defector, captured plans) | yes | design idea (story half); twin G-C3 |
| S-C5 | **Perspective switch** (a mission from the enemy's or a side character's view) | yes (BW episodes switch factions) | design idea |
| S-C6 | **Hero relationships develop** (trust, conflict, betrayal instead of plain orders) | yes | design idea |
| S-C7 | **End-of-mission teaser** of the next threat | yes | design idea |
| S-C8 | **Escalation narrative** (each threat feels bigger; the finale pays it off) | yes | design idea (story half); twin G-C1 |
| S-C10 | **Keepsakes** that matter emotionally (amulet of a fallen friend) | yes | design idea (story half); twin G-C17 |
| S-C11 | **Guest hero** present for one mission (departs or dies by story) | yes | mission design (story-driven) |

### B2. Mission level (story)
| id | pattern (examples are illustrative only) | in SC:BW | source |
|---|---|---|---|
| S-M1 | **Intro concept follows the mission's story** (march, arrival by ship, flashback, raid under way, enemy view, almost no intro) | yes | BW campaign practice |
| S-M2 | **In-world reason for scripted behaviour** | yes | fixed rule, story side |
| S-M3 | **Dying words / doubt seeded by a defeated enemy** | yes | own campaign |
| S-M4 | **Transmission interrupt** (a line is cut off mid-sentence by an attack) | yes (BW "Requesting... aargh!") | own BW campaign |
| S-M-ROSTER | **Roster plausibility:** every enemy unit type has a story reason to be there (faction, clan, region, plot); no stock filler from another race or culture; the signature unit tells who the enemy is (examples only) | — | yes | — | playtest feedback; twin G-M27 |

## Sources
- BW mission patterns G-M11..G-M20: StrategyWiki Agent of the Swarm, Norad II, Desperate Alliance, Escape from Aiur; StarCraft fandom wiki Revolution.

## Rule: planned duration and objective paths
The planned length of a mission and the real paths of every objective are judged before building.

- Declare the intended Normal duration (and Easy/Hard) and a time budget per objective: `TARGET_DURATION: <Normal minutes> :: <Easy/Hard> :: <objective>=<minutes>; ...`.
- Trace every main and side (or required and optional) objective on the real walkable path before building: `OBJECTIVE_PATHS: <objective> :: <path(s) with length and travel time> :: <threats / waves and directions> :: <why it is a challenge>`.
- Walking is only a small part of the budget. Path encounters scale with it: about one real encounter or decision point per 1-2 minutes of that objective's time, and a rescue, reach or escort route still has at least two threat sources (an additional baseline, not a replacement for the budget). Survive/hold waves arrive about every 60-120 seconds, from more than one direction. The first real pressure arrives in the first 2-4 minutes.
- FAIL when TARGET_DURATION is missing or incomplete, when the walk+fight estimate is below about a third of the budget, when there are fewer encounters than the budget asks for, or when the main objective can be finished before the first wave or path encounter. `OBJECTIVE_PATHS_EASY_OK: <reason>` waives the difficulty rules, not a missing duration line.

Check: predelivery check 51, `tools/bw/check_objective_paths.py` (`docs/bw-campaign-design.md`).

## Rule: objective shortcuts, enemy-base pressure, tech per chapter
- Shortcuts: think through what the player's own units, buildings and abilities (lift-off, flyers, drops, Recall, cloak, burrow, building on the spot)
  can do against each reach/rescue/capture objective; block each vector or
  accept it. `OBJECTIVE_SHORTCUTS:` / `SHORTCUT_OK:`.
- Pressure: at least two independent attack sources; no single early-reachable enemy base that is not the objective
  may switch off every wave and the AI. `PRESSURE_SINGLE_OK:` only by design.
- Tech: hand the tech tree out chapter by chapter; early chapters restrict it. `TECH_LEVEL: <early|mid|late|full> :: <chapter> :: <what and why>`.
Checks: predelivery checks 52-54 (`docs/bw-campaign-design.md`).
