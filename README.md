# VibeBroodForge

Guides, design rules, generators and checkers for making **StarCraft: Brood War** content: campaign missions and
ranked/melee maps.

This repository contains **no finished maps or campaigns** and **no Blizzard assets**. It contains what you need to
build and verify your own.

**AI agents: start with [`AGENTS.md`](AGENTS.md)** (fixed workflow per task, checks that must pass). Open the repository
root as your workspace so your agent loads it, read [`docs/lessons.md`](docs/lessons.md) and
[`docs/quality-bar.md`](docs/quality-bar.md), and deliver only what `python3 tools/deliver.py MAP` packs.

**Terrain needs two things you provide yourself:** the `isomtool` binary (built from `tools/lib/bw/isomtool_src`)
and the tileset files from your own StarCraft install. Without them map generation stops with an error; there is no
fallback. Setup: [`docs/bw-terrain-setup.md`](docs/bw-terrain-setup.md).

> **Formerly VibeModForge.** This repository was split out of the VibeModForge repository (which covered Brood War
> and Warcraft III together) with its full Git history. The Warcraft III part lives on in the sister project
> [VibeWarForge](https://github.com/Sasbe93/VibeWarForge). Maps built before the split carry provenance records that
> name VibeModForge; the tools here still read them.

## Contents
| Folder | What |
|---|---|
| `docs/` | Design guides and rules: map design (general), campaign design, example missions, ranked maps, terrain setup, quality bar, provenance, voice delivery markup. |
| `tools/` | Checkers, generators and libraries (see `tools/README.md`). |
| `data/` | Derived data: stock tech trees of Terran, Zerg and Protoss as JSON + PNG charts, reference map metrics (see `data/README.md`). |
| `catalogues/` | Ranked-map feature catalogue. |
| `templates/` | Design note template and a worked example. |
| `external/` | Empty: place third-party/Blizzard files here yourself (see `external/README.md`). |
| `output/` | Generated files (git-ignored). |

## Quick start
```
git clone https://github.com/Sasbe93/VibeBroodForge.git && cd VibeBroodForge
python3 -m pip install -r requirements.txt
# build isomtool and extract the tilesets first: docs/bw-terrain-setup.md
python3 tools/bw/example_mission.py              # example campaign mission with voiced briefing, built and checked
python3 tools/bw/examples/ex_relay_watch.py      # more examples: docs/bw-example-missions.md
python3 tools/ranked/bw/example_2p.py            # example melee map
```
The example missions show the structure of a mission (build pipeline, design note, triggers, voice, checks) at every
complexity level and for several mission types. They are deliberately small and sit below the quality band in
`docs/quality-bar.md`. Copy the structure only, never the mission design: each new mission invents its own objective,
map, start setup, enemy, story and rewards.
Always run tools from the repository root. Read the matching guide in `docs/` before building; the checkers enforce
the rules written there.

## Windows setup
The tools are developed on Linux; the pipeline also runs natively on Windows (WSL2 works too, see
`docs/bw-terrain-setup.md`). On Windows:
- Python 3.10+ from python.org; run the commands with `py` (or `python`) instead of `python3`.
- **Turn on Python's UTF-8 mode once:** `setx PYTHONUTF8 1` (then open a new terminal). Without it, Python reads and
  writes text files in the ANSI code page (cp1252) and non-ASCII text in design notes, voice scripts and check output
  turns into mojibake or crashes; `sclib` prints a warning when it is off.
- `py -m pip install -r requirements.txt`. edge-tts is called as `edge-tts` when it is on PATH, otherwise as
  `py -m edge_tts`, so pip's `Scripts` folder does not have to be on PATH.
- FFmpeg with ffprobe on PATH, e.g. `winget install --id Gyan.FFmpeg -e --scope user`.
- isomtool: git, CMake 3.24+ and a C++20 compiler (e.g. WinLibs MinGW-w64 GCC via
  `winget install BrechtSanders.WinLibs.POSIX.UCRT`, or Visual Studio 2022), then `py tools\bw\build_isomtool.py --casclib-dll`.
  Tilesets: `py tools\bw\extract_tilesets.py --casc "C:\Program Files (x86)\StarCraft"`. VCOD:
  `py tools\bw\extract_vcod.py <any map you own>`. Details: `docs/bw-terrain-setup.md`.
- Not available natively: the real ScmDraft 2 open test (`tools/bw/scmdraft_harness`, runs ScmDraft under wine on
  Linux/WSL; on Windows `check_scmdraft_open.py` reports the static result and asks you to open the map in ScmDraft
  yourself).
- Map files are locked while a tool has them open (Windows error 32). The tools release every MPQ handle before the
  map is opened again; when you change a tool, check it on Linux with `tools/bw/sim_windows_locks.py`.

## Dependencies
See `DEPENDENCIES.md`. The checkers run with Python packages plus isomtool, the tileset files, edge-tts and ffmpeg.
Reference maps are not needed: their measurements are bundled in `data/reference_metrics/`.

## Legal
- License: MIT, see `LICENSE`.
- StarCraft and Brood War are trademarks of Blizzard Entertainment. This project is not affiliated with or endorsed by
  Blizzard. No game files are included.

## License

VibeBroodForge is released under the MIT License (see `LICENSE`). If you fork, copy or modify it, please keep the
copyright notice including the link to the original repository, so changes can be traced back to it.

## Ask the user how new content gets tested (required step)
Before building a mission that contains new or changed units or abilities (unit settings, upgrades, renamed heroes
with changed stats), the agent must ask the user whether all new content should be tested before the map is
delivered, and offer two options:
- **A – the agent tests in-game itself.** Only if the user explicitly grants access to their PC and the game. Without
  that explicit permission, never touch the user's machine.
- **B – a test map the user plays.** A small map built with `tools/lib/bw/sclib.py` that places every new or changed
  unit against fitting targets, so the user can check it in a few minutes.

Record the answer in the design note; if the user declines testing, say in the delivery that the new content is
untested in-game.
