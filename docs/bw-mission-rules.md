# Brood War mission rules (index)

These rules come from playtests and map reviews. `docs/bw-campaign-design.md` explains most of them in detail; this
file lists every rule in short form with how it is enforced, including the ones that were missing from the guides.

Tags:
- **[check: name]**: `tools/bw/predelivery_check.py` (number) or `tools/deliver.py` enforces it, statically or in the
  trigger simulation. A passing check is not proof of the player experience; read the map as a player too.
- **[judgement]**: no check measures it. Decide it, write it into the design note, and answer it in the self-review
  (`templates/Self_Review_template.md`).

Rule levels (precedence from top): fixed rules > mission design (a per-mission deviation with a reason) > campaign
rules (optional per campaign) > classic standards (Blizzard defaults).

## Planning and story
- **A random mission starts with a chapter outline** of the whole campaign (premise, factions, heroes, every chapter
  with place, goal, new tech, story beat); build the chosen chapter to its position. [judgement]
- **Declare the campaign tone**: `TONE: <serious | grim | heroic | dark comedy | ...> :: comic characters allowed
  yes/no :: why`. A comic-relief character only when the tone allows it; vary the tone between campaigns. [judgement]
- **Tileset changes need a story reason the player hears**: plan `TILESET: M<n> <tileset> :: in-world place` per
  chapter, and explain a new place in the briefing or opening lines, not only in the design note. [judgement]
- **StarCraft terms only**: never Warcraft words in StarCraft text. [judgement]
- **Names must not sound like famous StarCraft or Warcraft characters** unless the story connects them. [judgement]
- **Characters that stay with the player**: an audible tic tied to the story (a count that changes at a turning
  point), humour that comments on the hero's choice, a personal stake the hero keeps, recurring relationships with
  friction. Options, not a checklist. [judgement]
- **Briefings**: short gaps between speakers (the next line within about a second), objectives shown at the start.
  [check: voice delivery notes; gaps judgement]
- **Each chapter unlocks more tech than the previous one**, and every enabled unit has its prerequisites (a Lurker
  needs Burrow). [check: 31 tech progression, check_tech, 24 core abilities, 54 tech_restriction]
- **Important allied or enemy heroes get their own player slot and colour**, allied and scripted exactly like their
  faction. Exception `HERO_COLOR_SHARED: <hero> :: reason`. [check: 42 hero_own_color]

## Objectives and pressure
- **Judge every objective by its paths and the planned duration** (`TARGET_DURATION`, `OBJECTIVE_PATHS`).
  [check: 51 objective_paths]
- **Check objectives against the player's own means**: lift-off, flyers, transports, Recall, Nydus, cloak.
  [check: 52 objective_shortcuts]
- **A defended liftable building is defended at a place**: a defeat on 'Command Center == 0 anywhere' with ground-only
  waves is won by lifting off and waiting, when that building is the only way to lose. [check: 52 lift off]
- **Pressure from two or more independent sources.** [check: 53 enemy_base_pressure]
- **Waves vary and grow, and come from somewhere**: 3+ compositions, escalation, no spawn out of nowhere beside the
  player. [check: 58 wave_variety, spawn_source]
- **Nothing after the victory**: no waves or story scheduled after the hard victory. [check: 60 post_victory]
- **Side objectives vary**; at most one destroy side objective per mission and never in neighbouring missions.
  [check: 50 side_objective_variety]
- **Destroy targets survive morphing**: conditions cover the whole morph chain. [check: 49 destroy_target_morph_chain]
- **Rewards make sense in the story** (`REWARD_WHY`). [check: 59 check_gaming income_ok_masks_quest; fit judgement]
- **Do not drive the player's army**: timed triggers never order the player's units outside a cutscene.
  [check: 59 player_army_hijack, 13 event cameras]

## Opening, AI and allies
- **The opening is fair**: no armed enemy beside the start at second 0, no rescuable under fire, no objective done
  by idling. [check: 55-57 opening review, run by deliver.py]
- **Computer bases run their AI from the first second**, at a location exactly on the town hall, from a trigger owned
  by that player; preplaced computer workers mine. Exception `AI_IDLE_OK`. [check: 48 computer_ai_started,
  ai_workers_mining]
- **Only real Brood War AI script ids.** [check: 48 ai_script_valid]
- **An alliance is more than the flag**: vision both ways, allied victory, starting exactly when the story's alliance
  starts (`ALLIANCE_STARTS`). [check: 35 ally_shared_vision]
- **Story moments are visible from their first line** (`SCENE_VIEW`). [check: 45 scene_location_visible]
- **Start setups are a design decision** (`START_SETUP`), never a copied block. [check: 44 start_setup_variety]

## Map and editor
- **Terran add-ons are linked, not just placed.** [check: check_addon_attached]
- **Mineral lines follow Blizzard formations**, hall gaps as Blizzard's. [check: 43 mineral_line_shape, 21 hall gap]
- **The map opens in ScmDraft 2** (named doodad slots only). [check: 34 scmdraft_open]
- **No three equal, straight, parallel lava or cliff bands with one gap each**; vary ground and doodads. [judgement]

## Testing and proof
- **Challenge "not testable" first** (place terrain, fitting targets, set energy); every remaining WATCH needs a
  written reason. [judgement]
- **Run the real tool once**: a check that claims "opens in X" must have been run against X with a known-bad and a
  known-good map. [judgement]

## Delivery
- **Never deliver an existing or foreign map**, never game a check, honest provenance. [check: deliver.py
  foreign_map, 59 check_gaming, provenance]
- **Self-review and independent review**: fill `Self_Review_<map>.md` (deliver.py refuses a missing or generic one)
  and let a fresh agent review the map with `docs/review-prompt.md`. [check: deliver.py self_review]
