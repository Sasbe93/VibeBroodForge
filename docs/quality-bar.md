# Quality bar: what a deliverable mission looks like

The checks find known mistakes. They do **not** make a map good, and a map with 0 FAIL can still be dull. This page
says what "delivery quality" means here, how much of it a tool can measure, and what an agent has to judge itself.

## Where the quality of the reference missions came from
The reference Brood War missions built with this repository were not produced by one prompt and an example. Each one
has a mission-specific build script on `tools/lib/bw/sclib.py` and `missionkit.py` (terrain, start setup, enemy
towns and AI, waves, briefing, voiced transmissions, rewards), was iterated over playtest rounds, and every round of
feedback became a rule in the guides and a check. The library code is in this repository, the per-mission build
scripts are not. The example missions (`docs/bw-example-missions.md`) show the **structure** of a mission and pass
every check, but they are deliberately small: they sit below the measured band in five to eight rows and carry a
`QUALITY_BAND_OK:` line that only the examples may use. Copying an example and stopping there produces exactly the
thin map a playtester rejects.

So: plan the mission first (outline, design note, paths, duration, shortcuts, pressure, tech level), then write a
build script of your own that is as rich as the plan, then run the gate. Expect many build-check-fix rounds.

## Measured reference band
`python3 tools/bw/quality_metrics.py MAP.scx` measures the rows below; `tools/deliver.py` refuses a mission with 4
or more rows below the band unless the design note explains why (`QUALITY_BAND_OK: <reason>`, for example a short
no-base hero mission on a small map). Below the band is a prompt to look again, not proof of bad quality. A
`QUALITY_BAND_OK:` line copied from an example is refused.

Band measured on three delivered campaign missions built with this repository (Badlands and Desert, 128x128):
M6 Sluice Gates, M7 The Poisoned Well, BK6 The Hollow Crowns. Minimum = what the references reach (BK6 is the one
reference below a row: it has almost no doodads); typical = the median of the three (doodad types: the mean of M6 and M7).

| Row | What it says | Minimum | Typical | M6 | M7 | BK6 | Weak agent maps (for contrast) |
|---|---|---|---|---|---|---|---|
| ground_types_used | flat terrain types that cover at least 0.5% of the map | 5 | 6 | 6 | 6 | 6 | 4, 4 |
| distinct_doodad_types | different doodads (tile doodads and placed sprites) | 30 | 44 | 36 | 51 | 4 | 34, 36 |
| ramp_groups | walkable places where the ground level changes (ramps) | 3 | 8 | 3 | 8 | 10 | 2, 2 |
| triggers | triggers in the mission | 80 | 91 | 91 | 81 | 180 | 49, 22 |
| trigger_actions | trigger actions (story, waves, objectives, AI glue) | 700 | 747 | 711 | 747 | 2377 | 443, 319 |
| transmissions | voiced in-mission lines (Transmission actions) | 20 | 25 | 25 | 23 | 31 | 13, 10 |
| briefing_voice_lines | voiced briefing lines (Play WAV / Transmission in the briefing) | 5 | 6 | 6 | 6 | 6 | 3, 4 |
| spawn_actions | Create Unit actions (waves, reinforcements, rewards) | 100 | 160 | 123 | 160 | 803 | 40, 10 |
| order_actions | Order actions (attack waves, escorts, retreats) | 80 | 106 | 86 | 106 | 557 | 30, 8 |

Information only (printed, not part of the band): doodad tiles per 1,000 tiles, placed doodad sprites, elevation
levels, walkable share, objective updates, AI script runs, pre-placed units, computer players, map size.

The "weak agent maps" are two missions another agent built from this repository without the workflow below; the
playtester judged them too easy and "so-so" in map and mission design. They are 8 rows below the band; the
references are 0, 0 and 1 rows below, which is why the refusal starts at 4. The example missions are 5 to 8 rows
below (small on purpose, see above).

## Anti-gaming (how the metrics resist a map built for the numbers)
A map can be tuned to pass checks without being better for the player. The tools count only what the player meets:
- **Only triggers reachable before the victory count.** `opening_review.dead_triggers` runs the idle trigger
  simulation to the hard victory; triggers that can only run later (and switch chains whose setters are all dead) are
  left out of wave_variety, quality_metrics, the path tool's waves and objective_paths. Check 60 post_victory FAILs
  dead triggers that create enemy units.
- **Identical waves count once.** quality_metrics de-duplicates triggers that differ only in a switch number or a
  copy marker (`dedupe`); wave_variety counts distinct compositions, not wave triggers.
- **Exceptions need a concrete reason and are listed.** Every `*_OK` line needs 4+ words and no placeholder
  (check 59 exception_reason; `tools/deliver.py` refuses thin reasons) and the gate lists every exception line in
  `GATE_REPORT.json`; name them in your report.
- **Many metrics exactly at the floor is a warning.** When half or more of the band rows sit within 10 % above their
  minimum, quality_metrics prints `WARN on_floor` and the gate repeats it: a map tuned to the floor of every row is
  built for the metric.
- **Self-review and independent review.** `Self_Review_<map>.md` (template `templates/Self_Review_template.md`) must
  answer every question with concrete names, places and times of the map (`tools/lib/self_review.py`); a fresh agent
  reviews the map with `docs/review-prompt.md` before delivery.
Limits: dead-trigger detection relies on the idle simulation's hard victory (a victory that needs player action
leaves every trigger counted); the floor warning is a prompt, not proof.

## What the agent must judge (no tool can)
Before running the gate, look at the minimap PNG and the routes PNG and answer these in the design note's flow
section. Be honest; "fine" is not an answer.
- **Looks:** Does the terrain read as a place or as stripes and blobs? Are there long straight cliff, lava or water
  bands with one gap? Are doodads placed with a purpose, or is the map bare between the bases?
- **Paths:** For every objective, what does the player meet on the way, and what can they do to skip it (lift-off,
  flyers, drops, recall)?
- **Pressure:** Where does pressure come from, and does it survive the first enemy base the player can reach?
- **Pacing:** What happens in minutes 0-3, 3-10, 10+? Where is the first real decision?
- **Difference:** What makes this mission unlike the previous one and unlike the example it was built from?

## What is still not enforced
- Visual beauty and "feel": metrics catch thin maps, not ugly ones.
- Fun and fairness in real play: trigger simulation and the ScmDraft open test get closer, a human playtest is the
  proof.
- Story quality and voice acting beyond the structural checks.
State these limits when you deliver.

## Known gaps in the repository itself
- The example missions pass every check but sit below the band (they are small on purpose). A full reference
  mission at band level is not in the repository; its build script is mission-specific.
- The band rests on three missions on two tilesets; re-measure it when more missions at that level exist (keep
  `tools/bw/quality_metrics.py` and this page in sync).
