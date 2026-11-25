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

- **C9 Never game the checks.** A check measures a property; satisfying its pattern without the property is a
  hidden FAIL. Seen in a review map built with this repository (t1031): an `INCOME_OK` comment in the rescue-quest
  trigger hid the quest's unit hand-over from the reward check; six timed camera triggers ordered the player's own
  Zealots to the front only so the event-camera check saw a "scripted effect" (and so took the army out of the
  player's hands); 34 copies of one wave trigger lifted the quality metric to its floor. Every exception line needs
  a concrete reason; copies count once; orders of the player's units are no scene effect (predelivery checks 13, 58,
  59). If a check is wrong, say so and fix the check with a fixture in the repository; never work around it in the map.
- **C10 Play the opening before you deliver.** Run `python3 tools/bw/opening_review.py MAP.scx --timeline` and read
  what the player meets in the first minutes. The t1031 map had 13 enemy Marines and Firebats inside the player's
  base at second 0, the rescue Probe standing on an enemy Marine, and the player's own start Probe fulfilling the
  rescue quest at second 0, 120 s before it was announced. All static checks were green on those points.
- **C11 Only real Brood War ids.** The t1031 map ran the AI script `TAIM`, which does not exist: the enemy never
  started, its workers stood idle. AI script ids come from `data/bw/aiscripts.json` (game data), never from memory.
- **C12 The provenance record is honest.** Log the agent and model you really are, with versions. If you do not know
  your model version, write `unknown`; never guess or copy a model name (t1031 named a model the user had not used).

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
- **D8 Objectives start far from the player and later than second 0.** A rescue, reach or destroy target 2 tiles from
  the Nexus is no objective; a threat cluster counts once even when the way out and the way back pass it; a Bring
  condition that the player's start units already meet fires before the quest is announced (checks 51, 57).
- **D9 Waves vary and grow.** Plan wave compositions per stage (new unit types, more units, other directions);
  one copied wave for the whole mission is monotonous (check 58).
- **D10 Rescued and handed-over units keep their kit.** A rescued High Templar with every spell disabled is
  useless; units the player gains use the player's tech settings (check 24).
- **D11 Destroy objectives against the player's flyers.** If the player can field a flyer that attacks ground, every
  side of the target needs anti-air in reach, or the objective is a free air raid (check 52).
- **D12 Nothing after the victory.** Waves scheduled after the hard victory never play; they only inflate wave counts
  and metrics (t1036: won at 720 s, 28 triggers later). Check 60 FAILs them and the metrics ignore them.
- **D13 Defend the place, not a building that can fly.** 'Command Center == 0 anywhere' with ground-only waves is won
  by lifting off and waiting. Use a Bring at a location or send flying attackers (check 52, lift off).
- **D14 Waves come from somewhere.** Units created out of nowhere 20 tiles from the base, 39 times, feel like a
  cheat. Spawn at an enemy building, a gate or a drop ship, 30+ tiles away (spawn_source).
- **D15 Do not drive the player's army.** Timed triggers that order the player's units every 90 s, or pause the game
  for dialogue again and again, take the mission away from the player (player_army_hijack, event cameras).
- **D16 The alliance starts when the story says.** Vision given at mission start because a truce flag was set
  there showed the ally's area before the pact; attach vision to the trigger of the story's alliance moment.
- **D17 Computer AI starts on its hall.** A town script run at the centre of a large box beside the base left the
  workers idle; run it at a location on the town hall from the first second (check 48).
- **D7 Destroy targets can morph.** A Hatchery that becomes a Lair is not destroyed; count the whole chain
  (`m.target_gone` / `m.target_stands` + `m.T_each`). Side objectives vary; at most one destroy side objective
  per mission.

## Never copy a previous mission
- **C13 Run the real tool once.** An "opens in the editor" check was a strict parser of its own and passed while the
  editor refused the map. Before trusting a static proxy, run the real editor or game against a known-bad and a
  known-good map.
- **C14 Check what the game reads, not a proxy.** Add-ons placed beside a building passed a position check while
  they were not attached; the game reads the unit link. Find the real property in reference maps first.
- **N0 Never deliver an existing map as your result.** Old test maps, maps of other agents, files found anywhere on
  the machine, and the repository examples are not your work. Build every mission from scratch with the builders
  (`sclib.py` + `missionkit.py`). An old instrumented test map (title "Chapter Test (Main Run)") still passed many
  static checks in a review (t1032), so the checks alone do not catch a foreign map. The gate refuses test-map
  titles, `EXAMPLE:` titles and maps whose provenance record has no build.
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
