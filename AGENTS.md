# AGENTS.md - start here

You are an AI agent (Cursor, Claude Code, Codex, Copilot, Gemini, ...) using VibeBroodForge to build StarCraft: Brood
War content. This file is the single entry point; `CLAUDE.md`, `GEMINI.md`,
`.cursor/rules/vibebroodforge.mdc` and `.github/copilot-instructions.md` only point here. Open the **repository root**
as your workspace (agents read this file from the workspace root), and run every tool from the repository root.

## Mandatory for every map, mission or campaign
1. **Read before you build:** this file, `docs/lessons.md` (how agents got maps wrong before), `docs/bw-mission-rules.md`
   (rule index: which rules a check enforces and which are judgement), `docs/quality-bar.md`
   (what delivery quality means and what the tools cannot judge), then the guides for your task below.
2. **Plan before you build:** campaign outline, then a design note from `templates/Design_Note_template.md` next to
   the map (`Design_Note_<map>.md`), with every line the template marks as required. The design note is part of
   the delivery.
3. **Build with the repository's builders** (`tools/lib/bw/sclib.py` + `missionkit.py`). The examples show the
   pipeline only; your mission needs its own terrain, scenes, enemies, story and code, as rich as the plan
   (`docs/quality-bar.md`).
4. **Gate** (needs the self-review of step 6): `python3 tools/deliver.py output/<map>.scx` runs every check, the design-note completeness test and the
   quality metrics (`tools/bw/quality_metrics.py`), and packs `output/delivery/<map>_delivery.zip` only when all pass.
   **Deliver only that ZIP.** If the gate refuses, fix the map and run it again. Never deliver around the gate, never
   call a FAIL "known" or "existing", never edit a check to make your map pass, never copy the examples'
   `QUALITY_BAND_OK:` line.
5. **Play the opening:** `python3 tools/bw/opening_review.py output/<map>.scx --timeline` replays the first minutes
   in the trigger simulator with nobody moving and lists what fires when. Read it as the player: no enemies inside
   the start base at second 0, no rescuable beside hostile guards, no quest that is already done before it is
   announced, a sensible order of objectives, dialogue and waves. The gate runs it and packs `OPENING_REVIEW.txt`.
6. **Self-review:** fill `templates/Self_Review_template.md` as `Self_Review_<map>.md` next to the map: what the player
   sees at second 0, the cheapest path to every objective with every ability the player has, what happens after
   victory and defeat, every difficulty, each scripted mechanic per instance, softlocks, exceptions, what was not
   tested in game. Concrete names, places and times of this map; `tools/deliver.py` refuses a missing, unanswered,
   placeholder, generic or copied self-review.
7. **Independent review (recommended):** let a fresh agent that has not seen your work review the map with
   `docs/review-prompt.md` (checks, simulation and a manual player-view analysis; ranked faults, gaming signs, tool
   gaps). Fix what it finds before delivery.
8. **Report honestly:** say what was tested only statically or in simulation and what was not tested in-game.
9. **Feedback goes into the repository** (see "Feedback" below), not only into your own memory.
10. **Provenance record (`docs/provenance.md`):** before you build, log every user prompt that changes a map or
   campaign: `python3 tools/provenance.py add-prompt --map <map> --agent "<Cursor|Grok Bot|Claude Code|Codex|Dots|other:NAME>"
   --agent-version <v> --model <model> --model-version <v> --text-file <prompt.txt>` (`--campaign <folder>` for a
   prompt about a whole campaign folder, `--redact` when a prompt holds personal data). Before changing a map the user
   may have edited in an editor, run `python3 tools/provenance.py check <map> --record` and tell the user that a
   rebuild replaces their editor changes (a backup is kept next to the map). Maps not written by `sclib.Map.save` get
   `python3 tools/provenance.py stamp <map>`. Never switch the record off (`VIBEFORGE_PROVENANCE=0`) for a delivered map.
   Log the agent and model you really are; if you do not know a version, write `unknown`, never a guess.

## Never
- Never deliver an existing map as your result: old test maps, other agents' files, maps found anywhere on the
  machine, or a repository example. Build from scratch with the builders. The gate refuses test-map titles
  ('Chapter Test', 'Trigger Test', 'Test Map', the old 'VibeModForge' name), `EXAMPLE:` titles and maps whose
  provenance record has no build.
- Never game a check: no exception line (`*_OK:`, `INCOME_OK`) without a concrete reason, no copied triggers or
  waves to lift a metric, no dummy actions (e.g. ordering the player's own units) to satisfy a pattern. If a check
  is wrong, fix the check with a fixture and say so (`docs/lessons.md` C9).
- Never touch the user's PC or game without explicit permission. Before building content with new or changed units,
  heroes, buildings or abilities, ask how it gets tested (README "Ask the user how new content gets tested").
- Never deliver with a FAIL, and never hide one: say what failed, what was not tested in-game, and why.
- Never silently downgrade: if a required tool or data set is missing (isomtool, tileset files, edge-tts, ffmpeg),
  stop and tell the user what to install (`DEPENDENCIES.md`, `external/README.md`, `docs/bw-terrain-setup.md`). A
  fresh clone has none of them, and `tools/deliver.py` stops first. No rectangle-plateau terrain, no text-only
  missions as a fallback.
- Never commit Blizzard game files (tileset files, extracted assets) or generated maps (`output/` is git-ignored).

## Campaign mission (fixed workflow, in this order)
A request for "a mission", "a random mission" or "a map with a story" is a campaign mission.
1. **Campaign outline first.** Even a single mission gets a short chapter outline (where it sits, what came before and
   after). Pick patterns from `docs/campaign-design-catalog.md`.
2. **Design note** from `templates/Design_Note_template.md` (worked example: `templates/Design_Note_example_bw_mission.md`):
   story, objectives, `TARGET_DURATION:` (Normal length, Easy/Hard, and a time budget per objective), `REWARD_WHY:` per
   reward, map, flow, briefing and voice, `## Characters`. For every main and side objective write `OBJECTIVE_PATHS:`
   with the real path length, travel time, threats or waves, and why it is a challenge (and `ESCORT_ROUTE:` as well when
   there is an escort).
3. **Trace every path before building, against the planned duration.** Pathfind start to each target, a rescue there
   and back, and every attack wave to the player base (`tools/bw/path_tool.py`). Encounters scale with each objective's
   budget (about one per 1-2 minutes, and at least two on a rescue, reach or escort route). Survive/hold waves arrive
   about every 60-120 s from more than one direction. If the walk+fight estimate is below about a third of the budget,
   or the main objective can be finished before the first wave or path encounter, redesign the map or cut the declared
   duration. Draw the paths on the routes PNG. The checkers fail a missing TARGET_DURATION, a budget the path cannot
   fill, and a weak survive setup (`docs/bw-campaign-design.md`, predelivery check 51).
3a. **Shortcuts, pressure, tech per chapter.** Think through what the player's own units, buildings and abilities can
   do against each objective (lift a Barracks to the target, fly, drop, recall, cloak) and block or accept each vector
   (`OBJECTIVE_SHORTCUTS:` / `SHORTCUT_OK:`). Give attacks at least two independent sources, so killing one nearby base
   that is not the objective never ends all pressure (`PRESSURE_SINGLE_OK:` only by design). Restrict the tech tree to
   the chapter (`missionkit.tech_level`, `TECH_LEVEL:` line). Predelivery checks 52-54.
4. **Build on an example (structure only):** pick one of the BW example missions (`docs/bw-example-missions.md`:
   `tools/bw/example_mission.py` and `tools/bw/examples/`, every complexity level and mission type) and copy its
   STRUCTURE only: the build pipeline, the design-note sections and the trigger, voice and check conventions. Never copy
   its mission design (objective, map layout, start setup, enemy, story, rewards): every mission invents its own, uses a
   different example than the previous mission, and neighbouring missions follow the mission-type variety rule. They use
   `tools/lib/bw/sclib.py` and `tools/lib/bw/missionkit.py`. Read `docs/bw-campaign-design.md` and
   `docs/bw-map-design.md` first (terrain needs isomtool + tileset files: `docs/bw-terrain-setup.md`).
5. **Briefing** with speaking portraits, objectives and voiced lines (`Cast.brief` / `m.B`, `b_portrait`, `b_trans`).
6. **Every story line voiced:** edge-tts WAVs embedded in the map, in-mission lines as Transmissions, VO markup on every
   line (`docs/voice-delivery-markup.md`); Display Text only for status lines.
7. **Rewards make sense in the story:** the reward is what the objective yields in the story (freed prisoners join, a
   captured depot gives its resources, a saved scientist unlocks tech), with an in-world source the player sees
   (`REWARD_WHY:`). Side objectives vary (rescue, capture, protect, reach or hold, escort, ally, secret, or none); at
   most one destroy side objective per mission, never destroy side objectives in two neighbouring missions
   (`SIDE_OBJECTIVE:` lines). Destroy targets that can morph (Hatchery -> Lair -> Hive, Creep Colony, Spire) count the
   whole chain: `m.target_gone` / `m.target_stands` + `m.T_each` (`docs/bw-campaign-design.md`).
8. **Checks:** `python3 tools/bw/predelivery_check.py output/<map>.scx` (includes the story/briefing/voice checks,
   `check_map_design_bw.py`, cliff shape and rewards, the opening review, wave variety and the anti-gaming
   check), plus the placement check and trigger simulation (`tools/bw/placecheck.py`, `tools/bw/trigsim.py`; the
   example script runs all of them).
8b. **Opening review:** `python3 tools/bw/opening_review.py output/<map>.scx --timeline` (mandatory step 5 above).
8a. **Quality band:** `python3 tools/bw/quality_metrics.py output/<map>.scx` compares terrain, doodads, ramps,
   triggers, transmissions, briefing voice, spawns and orders with the reference band (`docs/quality-bar.md`). Four or
   more rows below the band refuse the map unless the design note explains why (`QUALITY_BAND_OK:`).
9. **Gate and deliver:** `python3 tools/deliver.py output/<map>.scx` (runs the predelivery check, the quality
   metrics and the design-note test, packs the map, design note, voice script, minimap and routes PNG). Deliver only its ZIP; say what was not
   tested in-game.

## Ranked / melee maps
`docs/bw-ranked-maps.md`, examples in `tools/ranked/bw/`, check `python3 tools/bw/check_ranked_bw.py MAP.scx`.
Gate: `python3 tools/deliver.py MAP --ranked`.

## Feedback (keep the quality in the repository)
The rules in this repository exist because a human playtester rejected earlier maps. Quality only carries over to the
next agent if it is written down here. When the user gives design or playtest feedback, in the same turn and
without being asked:
1. Game rule -> the fitting guide (`docs/bw-*.md`, catalogue).
2. Working mistake (how the agent worked) -> `docs/lessons.md`.
3. Measurable property -> a check (with a known-bad and a known-good fixture) wired into `predelivery_check.py`, and a design-note
   line in `templates/Design_Note_template.md` if the check reads one.
4. If an example mission breaks the new rule, fix the example too: examples get copied.
5. Run `python3 tools/selftest_agent_setup.py` and the selftests; commit in English.
Keep `AGENTS.md` the only full instruction file; pointer files stay pointers.
