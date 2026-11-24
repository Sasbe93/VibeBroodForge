# external/ (not shipped)

Third-party or Blizzard files the tools can use. Nothing here is committed. Create the folders as needed.

| Path | What | How to get it |
|---|---|---|
| `external/refmaps/bw/set/` | Reference ladder maps (`*.scx`/`*.scm`) | Download current ladder map packs (e.g. from nydus.gg / the ASL map pool); only for recalibration |
| `external/bwapi/` | BWAPI source (unit/weapon tables) | `git clone https://github.com/bwapi/bwapi`; only to rebuild `data/bw/*.json` |
| `tools/lib/bw/isomtool_src/external/Chkdraft`, `RareCpp`, `StormLib`, `CascLib` | C++ libraries for isomtool (all MIT) | `python3 tools/bw/build_isomtool.py` clones the tested commits, builds with CMake (Linux, macOS, Windows/MinGW or MSVC) and installs `tools/lib/bw/isomtool` (`isomtool.exe` on Windows); `--casclib-dll` also builds the CascLib library for `extract_tilesets.py --casc`. Manual steps: `docs/bw-terrain-setup.md`. Required for all BW terrain work |
| `tools/lib/bw/tileset/` | BW tileset files (`badlands.cv5/.vx4ex/.vr4/.wpe`, `.vf4` optional, ...) | `python3 tools/bw/extract_tilesets.py --casc <StarCraft folder>` (needs the CascLib library from `build_isomtool.py --casclib-dll`) or `--from-folder <CascView export>`, see `docs/bw-terrain-setup.md`. Required for all BW terrain work |
| `external/bw/vcod_seeds.txt` | StarEdit VCOD seed table (needed by `tools/lib/bw/sclib.py` to write maps) | `python3 tools/bw/extract_vcod.py <any .scx/.scm you own>`; or set `BW_VCOD_SEEDS` |

Environment overrides: `BW_VCOD_SEEDS`, `ISOMTOOL` (isomtool binary, default `tools/lib/bw/isomtool[.exe]`).
