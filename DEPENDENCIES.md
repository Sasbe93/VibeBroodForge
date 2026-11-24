# Dependencies

Classes: **(a)** shipped in this repo or freely installable · **(b)** not shippable, users obtain it themselves (see `external/README.md`) · **(c)** replaced by bundled derived data (precomputed metrics/JSON) so the tool runs without the original.

| Tool / area | Dependency | Class | Notes |
|---|---|---|---|
| All Python tools | Python 3.10+, numpy, scipy, pillow | (a) | `pip install -r requirements.txt` |
| map IO (`tools/lib/bw/sclib.py`, `tools/bw/*`, `tools/ranked/bw/*`) | eudplib | (a) | pip (or wheel from its GitHub releases) |
| terrain generation (`sclib`, ISOM) | `isomtool` binary | (a)+(b) | Source shipped in `tools/lib/bw/isomtool_src` (our `main.cpp`, CMake file and `icu_min/` UTF converters); `tools/bw/build_isomtool.py` fetches Chkdraft mapping core, RareCpp, StormLib and CascLib (all MIT) into `isomtool_src/external/` and builds with CMake 3.24+ on Linux, macOS or Windows. ICU (Unicode license) is used when installed, otherwise `icu_min/`. Nothing third-party is committed |
| terrain / seams / resback / check_ranked_bw | tileset files (`*.cv5 *.vf4 *.vx4 *.vr4 *.wpe`) | (b) | Blizzard data; extract from your own StarCraft install (CASC) into `tools/lib/bw/tileset/` (`tools/bw/extract_tilesets.py`) |
| real ScmDraft 2 open test (`check_scmdraft_open.py --real`) | ScmDraft 2 + wine + Xvfb (`tools/bw/scmdraft_harness`) | (b) | Linux/WSL only; on native Windows only the static part runs |
| tech checks (`data/bw/tech/check_tech.py`, `core_tech.py`) | tech tree | (c) | `data/bw/tech/bw_techtree.json` bundled |
| `data/bw/tech/build_json.py`, `build_weapons.py`, `tools/bw/unit_damage.py`, `catalogues/bw_features/gen.py` | BWAPI source tables | (b)/(c) | Output (`bw_techtree.json`, `bw_weapons.json`, `bw_unit_ids.json`, catalogue) bundled; rebuild needs a BWAPI checkout |
| ranked checks (thresholds) | Ladder reference maps | (c) | `data/reference_metrics/bw/*.json`; maps only needed to recalibrate (`external/refmaps/bw`) |
| `tools/bw/features_demo/neutral_scan.py` | Ladder reference maps | (b)/(c) | Result bundled as `neutral_scan.json` |
| voiced dialogue (`sclib.Map.voice`, briefing and in-mission transmissions) | `edge-tts` (LGPLv3 client of Microsoft's online Edge Read Aloud service; the CLI on PATH or `python -m edge_tts`), `ffmpeg`/`ffprobe` on PATH, internet access | (a) | `pip install edge-tts`; see "Voiced dialogue for Brood War" below (output rights) |
| Quality metrics (`tools/bw/quality_metrics.py`) | BW tileset files | (b) | Same tileset files as terrain generation; the reference band is bundled in the tool and `docs/quality-bar.md` |

## Voiced dialogue (tools/lib/bw/sclib.py)
- Engine: `sclib.Map.voice(...)` calls the `edge-tts` command line tool (https://github.com/rany2/edge-tts, LGPLv3, `pip install edge-tts`), which sends the text to Microsoft's online Edge "Read Aloud" text-to-speech service and returns an mp3. `ffmpeg`/`ffprobe` then cut, master and convert it to the 22.05 kHz mono WAV that is embedded in the map (`staredit\wav\<key>.wav`) and played by the briefing (Play WAV) and in-mission Transmission actions. It needs an internet connection; there is no API key.
- Voices: any `edge-tts --list-voices` name (e.g. `en-GB-RyanNeural`); per speaker `voice`, `pitch`, `rate` and an optional ffmpeg filter `fx` (radio, echo).
- Output rights (honest status, checked against public statements): edge-tts itself is LGPLv3 software, but that licence covers the client code, not the audio. Microsoft has not published terms that grant redistribution or commercial use of audio generated through Edge Read Aloud / edge-tts; Microsoft Q&A moderators answer that this is "not explicitly confirmed" and point to Azure AI Speech for commercial use (e.g. learn.microsoft.com/en-us/answers/questions/6007729 and /6073502). Treat maps with edge-tts voices as fine for personal, non-commercial fan use; for anything sold or monetised, re-voice the lines with an engine whose licence grants output use (Azure AI Speech under its terms, or a local open model whose licence grants output use). The VO markup in `Voice_Script_<map>.md` makes re-voicing a rebuild, not a rewrite.
- Voice delivery notes (`tools/lib/voice_delivery.py`): ffmpeg built with the `rubberband` filter for pitch/tempo on stressed words (falls back to asetrate/atempo).
