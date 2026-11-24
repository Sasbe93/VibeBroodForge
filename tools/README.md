# tools/

Run every tool **from the repository root** (paths such as `data/...`, `external/...` and `output/...` are relative to it).

| Folder | Purpose |
|---|---|
| `bw/` | Brood War checkers: ranked rules (`check_ranked_bw.py`, `bw_*`), campaign pre-release check (`predelivery_check.py`) and the mission checks it runs, terrain analysis helpers, quality metrics (`quality_metrics.py`), setup helpers (`build_isomtool.py`, `extract_tilesets.py`, `extract_vcod.py`) and `sim_windows_locks.py` (runs a BW tool on Linux under Windows' file locking, to catch MPQ handles kept open). |
| `bw/examples/` | Seven example missions with design notes (`docs/bw-example-missions.md`); `bw/example_mission.py` is the eighth. |
| `bw/features_demo/` | Feature demo map script, reachability and neutral-building scans. |
| `bw/scmdraft_harness/` | Real ScmDraft 2 open test under wine (Linux/WSL). |
| `ranked/bw/` | Ranked/melee map generator (`rankedlib.py`, `tricks.py`, ...), map diversity dice (`dice.py`, `dice_tables.md`) and small example scripts (`example_2p.py`, `example_4p.py`). |
| `lib/bw/` | `sclib.py` (BW scenario IO via eudplib, ISOM terrain via `isomtool`), `missionkit.py` (mission building blocks) and the isomtool C++ source. |

Delivery gate and helpers (repository root):
- `deliver.py`: the only supported way to hand over a map. Runs `predelivery_check.py` (ranked checks with
  `--ranked`), the provenance check, tests the design note for its required lines and English, measures the mission
  with `bw/quality_metrics.py` against `docs/quality-bar.md`, and packs `output/delivery/<map>_delivery.zip` with
  `GATE_REPORT.json` only when everything passes.
- `provenance.py`: provenance record CLI (`add-prompt`, `show`, `check`, `verify`, `stamp`, `campaign`, `redact`,
  `selftest`), see `docs/provenance.md`.
- `lib/check_summary.py`: classifies check outputs (FAIL / CRASH / WARN / OK).
- `bw/quality_metrics.py`: terrain variety, doodads, ramps and trigger/story richness compared with the reference band.
- `selftest_agent_setup.py`: AGENTS.md and the pointer files for each agent stay wired up; the gate's fixtures behave.
- Self-tests of single checks: `bw/selftest_objective_paths.py`, `bw/selftest_side_and_morph.py`,
  `bw/selftest_t1025_checks.py`.

Typical use:
```
python3 tools/bw/example_mission.py             # build the example mission into output/
python3 tools/bw/predelivery_check.py output/example_mission/Example_Mission.scx
python3 tools/bw/quality_metrics.py output/example_mission/Example_Mission.scx
python3 tools/bw/check_ranked_bw.py output/MyMap.scx
```
See `DEPENDENCIES.md` for what each tool needs and `external/README.md` for files you must provide yourself.

## Recent additions
- `ranked/bw/tricks.py`: building blocks for 3-player axis layouts (mirrorx + axis player) and catalogue tricks (backdoor lane, assimilator/egg pass with mineral-walk targets, temple stacks, neutral colonies, mirrored ramp pairs).

## Voice delivery
- `lib/voice_delivery.py`: VO markup v1 parser, free renderer (segments + silence, emotion presets, local stress via ffmpeg rubberband), line check, Voice_Script.md writer/reader. Spec: `docs/voice-delivery-markup.md`.
- `bw/check_voice_delivery.py`: FAIL voiced lines without delivery notes (also run by `predelivery_check.py`).
