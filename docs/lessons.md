# Lessons: how agents get these maps wrong

Read this before every build or fix, and again before answering design or playtest feedback. The guides
(`docs/bw-*.md`, `docs/campaign-design-catalog.md`) hold the game rules; this file holds the **working mistakes** that
produced bad maps in the past, and the rule that prevents each one. Every lesson here came from a real delivered map
that a human playtester rejected.

## Working process
- **P1 Feedback goes into the repository in the same turn.** When the user corrects a map or the way you work, write
  the rule into the fitting guide (game rule), into this file (working mistake), and into a check where the property
  can be measured. Without being asked. A rule that lives only in an agent's private memory is lost for the next
  agent (`AGENTS.md` "Feedback").
- **P2 This repository is StarCraft: Brood War only.** Rules from another game (also from the sister project VibeWarForge for Warcraft III) are not
  copied in unless the user gives them for Brood War. Never write "feature X does not exist in this game" notes into
  a guide or check; a catalogue pattern that does not apply is left out.
- **P3 Future maps only.** A new rule applies to maps built after it. Never rebuild or "fix" a map that was already
  delivered unless the user asks for that exact map.
- **P4 Fix scope = what was marked.** When the user circles specific spots, change only those. Ask when it is unclear
  which mission or map is meant.
- **P5 Show understanding before rebuilding** when the user is frustrated about a repeated issue: say what went wrong
  and why, then fix.
- **P6 Praise is not a default.** A pattern the user liked goes into the catalogue as an option. Neighbouring
  missions never share the same side pattern.
- **P7 Name checks by what they check** and describe a check by its effect in replies, not by its internal name.

## Proof and checks
- **C1 Static checks are not proof.** A check that reads the map is a prediction. State the proof level honestly
  for every claim: static, simulated, or seen in the game. Build runtime tests (trigger simulation with `tools/bw/trigsim.py`, the real ScmDraft open test) where possible, and say what
  was not tested in-game.
- **C2 Tests must prove what the player can do** (clicks, real orders), not script selection; otherwise mark WATCH
  with a manual instruction.
- **C3 Test setups must not change what is measured.** A test map or simulation keeps every property the measured
  behaviour depends on; say what the setup changed.
- **C4 Check the whole class, not only the reported case.** When fixing one unit, map or trigger, ask which others
  share the property.
- **C5 Repeated bugs need hard checks** that measure the real property, not a proxy. Before writing a check, find what
  the game actually reads (reference maps made with the real editors) and test the check against a known-bad and a
  known-good map. Examples: add-on attachment is a unit link, not a position; "opens in ScmDraft" was a parser of
  our own that passed while ScmDraft refused the map, so run the real tool at least once.
- **C6 A check's allow-list must come from game data, not from the generator.** Ids for tiles, doodads and units are
  verified against Blizzard maps of the same tileset or the game's data. If the generator and the check share one
  wrong assumption, the check approves the bug.
- **C7 A known FAIL blocks delivery.** Never report a FAIL as "existing" or "known" and deliver anyway. Run
  `python3 tools/deliver.py MAP` and deliver only what it packs.
- **C8 Verify engine semantics from real sources**, never from memory or from your own earlier phrasing: StarEdit
  help and staredit.net for triggers and AI scripts, OpenBW for engine behaviour. Mark anything unverified as
  unverified.

## Mission design from the player's view
- **D1 Judge every objective by its paths and the planned duration** (`TARGET_DURATION:`, `OBJECTIVE_PATHS:`):
  trace start to target, the return, every wave; count encounters against the time budget. A short, empty rescue or
  a survive timer that ends before the first wave is a FAIL. Main and side objectives both count.
- **D2 Check objectives against the player's own means**, not only walking routes: lift-off, flyers, transports,
  recall, cloak. Block every shortcut or accept it in the note (`OBJECTIVE_SHORTCUTS:`, `SHORTCUT_OK:`).
- **D3 Pressure from at least two independent sources.** If one nearby enemy base feeds every wave and the AI,
  killing it early ends the mission's tension.
- **D4 Restrict the tech tree to the chapter** (`TECH_LEVEL:`). An early mission with the full tree is a FAIL.
- **D5 Rewards come from the world.** Before adding a reward, name the in-world source the player sees (a cache,
  freed prisoners who join, a captured depot, a grateful ally) in `REWARD_WHY:`. No flat minerals or gas for
  unrelated deeds; no ranking of reward types, the reward follows from the objective.
- **D6 An alliance is more than a flag.** List everything an ally has (vision both ways, allied victory, no friendly
  fire, AI behaviour) and attach it to the moment the alliance starts in the story, not to mission start.
- **D7 Destroy targets can morph.** A Hatchery that becomes a Lair is not destroyed; count the whole chain
  (`m.target_gone` / `m.target_stands` + `m.T_each`). Side objectives vary; at most one destroy side objective
  per mission.

## Never copy a previous mission
- **N1 Examples give structure, never design.** Copy the build pipeline, the design-note sections and the check
  conventions of an example. Never copy its objective, layout, start setup, enemy, story, rewards, decoration or
  its `QUALITY_BAND_OK:` line (the examples are small on purpose; a real mission reaches the band in
  `docs/quality-bar.md`).
- **N2 Start setups are a design decision** (`START_SETUP:`), measured against the reference and the last two
  missions, never a copied block (a template base with towers and ready units means the player never builds).
- **N3 Measure, do not assume, shapes from references.** "Two depths" in a mineral line was accepted as staggered
  while every line was a flat column; measure the real shape mix of reference maps.

## Economy and AI
- **E1 Every computer player with a base runs its town AI at a location centred on its own hall from mission
  start**, or its workers never mine (predelivery check 48).
