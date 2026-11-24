# Provenance record: prompts, agents, models, tool versions, human edits

Every map and campaign built with VibeBroodForge carries a hidden provenance record. Players never see it. Anyone can
read it from outside the game, and the maps stay normal, editable maps. The record answers:

- how many prompts went into this map or campaign, and what they were (or a hash if a prompt was redacted),
- which agent (Cursor, Grok Bot, Claude Code, Codex, Dots, ...) and which agent version wrote it, and with which AI
  model and model version,
- which tool version built it (**VibeBroodForge**, the StarCraft: Brood War tool), plus the git commit,
- every build by the tools (a *prompt edit*), kept apart from every *human edit* made in an editor.

Code: `tools/lib/forge_provenance.py` (library and build hooks), `tools/provenance.py` (CLI),
`tools/selftest_provenance.py` (self-test). The record format (`vibeforge-provenance/1`) is shared with the sister
project for the other game and with maps built before the split of the former VibeModForge repository; `show` reads
those older records too.

## For agents: the mandatory workflow

1. **Log every user prompt that changes a map or campaign, before you build.** Pass the prompt text as the user wrote it:

       python3 tools/provenance.py add-prompt --map output/<Map>/<Map>.scx \
           --agent "<Cursor | Grok Bot | Claude Code | Codex | Dots | other:NAME>" --agent-version <version> \
           --model <model id> --model-version <version or date> --text-file prompt.txt

   Use `--map` once per map the prompt touches, and `--campaign <folder>` for a prompt about the whole campaign folder. Agent and model are required. Write `unknown` only if you really cannot
   find out your version. Environment variables can supply them as defaults: `VIBEFORGE_AGENT`,
   `VIBEFORGE_AGENT_VERSION`, `VIBEFORGE_MODEL`, `VIBEFORGE_MODEL_VERSION`.
   Follow-up prompts that only answer your question count as prompts too. Do not log your own internal steps.
2. **Build as usual.** The writer embeds the record automatically: `tools/lib/bw/sclib.py: Map.save`. A build with no newly logged prompt is
   marked with a warning in the record.
3. **Maps not written by that writer** (fix copies, other tools, maps from the user) get the record with
   `python3 tools/provenance.py stamp <map>`. Stamping changes no map content. The fingerprint stays identical.
4. **Before you touch a map the user may have edited**, run `python3 tools/provenance.py check <map> --record`. This
   records the human edit before your build overwrites it. A rebuild over an edited map also records the edit and keeps a
   backup next to the map (`<map>.human-edited-<time>.<ext>`). The rebuild still replaces the human changes, so tell the user.
5. **Delivery:** `tools/deliver.py` runs `tools/provenance.py verify`. Without a record, with no logged prompt, or with an
   unrecorded human edit, the map is REFUSED. The gate report lists the prompt count, agents, models and tool versions.

## Where the record lives and whether editors keep it

| Format | Storage | Survives an editor save? |
|---|---|---|
| `.scx/.scm` | CHK section `VMFP` at the end of `staredit\scenario.chk` (StarCraft ignores unknown sections), plus MPQ file `vibeforge\provenance.json` | **Unknown.** ScmDraft 2 opens maps with the record (proven: real ScmDraft 2.0 0.9.10 under wine, `(ENGINE) Loaded map`). A save through ScmDraft could not be automated in our wine harness, because its file dialog does not respond, so we do not know whether it keeps unknown sections or extra MPQ files. StarEdit likely drops both. Map compressors such as TinyMap2 strip both on purpose. The reader takes whichever copy survives. If both are gone, the record is lost. The next tool run then sees a map without a record, and `verify` FAILs. |
| Campaign folder | `vibeforge_campaign_provenance.json` in the campaign folder, written by `tools/provenance.py campaign <folder>`. Prompts for the campaign as a whole are logged with `--campaign <folder>`. | Plain file next to the maps. |

The ledger is a sidecar file `<map>.provenance.json` next to the map in `output/` (git-ignored). It holds the same record
and collects prompts before the first build. The embedded copy is the one that travels with the map.

## Reading it from outside

- `python3 tools/provenance.py show <map>` prints the summary and every prompt, build and human edit. Add `--json` for the
  raw record. It also reports whether the map has changed since the last tool save.
- Without our tools: extract `vibeforge\provenance.json` with an MPQ tool, or read the `VMFP` section of
  `staredit\scenario.chk`. Each CHK section is a 4-byte name, a u32 length, then UTF-8 JSON.
- The format is JSON, `"format": "vibeforge-provenance/1"`. `summary.prompt_count` is the number of prompts.

## Prompt edits vs human edits

- **Prompt edits** are written by our tools on every build or stamp (`events[].type = build | stamp`). Each lists the
  prompt ids it follows from, the tool version, the commit and the content fingerprint it wrote.
- **Human edits** are detected, not logged. Editors do not tell us what someone did. Our tools store a fingerprint of the map
  at every tool save: per-CHK-section hashes grouped as terrain, units, doodads, triggers, briefing, strings,
  locations, players and settings, plus 32x32 terrain block hashes, unit counts per unit type and trigger counts.
  When a tool next opens the map (`check`, `stamp`, a rebuild, the delivery gate), a fingerprint mismatch becomes a
  `human_edit` event with a diff summary.
- **Limits, stated plainly:**
  - We cannot know who edited, when exactly, how many editor sessions there were, or the exact change. We only know which
    parts differ since the last tool save, with block or count detail where we have it.
  - Several editor sessions between two tool runs show up as one human edit.
  - A plain resave without changes can still change sections the editor re-serialises (ScmDraft may rewrite the
    string table). Those are reported as changes.
  - An agent that skips `add-prompt` cannot be caught directly. The record then shows builds with a "no prompt logged"
    warning, and the gate FAILs a map with zero prompts.
  - The record is not tamper-proof. Anyone with an MPQ tool can edit it. It is a log, not a signature.

## Versioning

- `VERSION` holds the VibeBroodForge version (semantic versioning `MAJOR.MINOR.PATCH`). It continues the numbering of the
  former VibeModForge repository: 0.9.0 introduced the record, 0.10.0 is the first release as its own repository.
- Bump PATCH for fixes, MINOR for new rules, checks or features, MAJOR for breaking changes to formats or workflows.
- The record stores `tools.tool` (`VibeBroodForge`), the version, the git commit and a `dirty` flag, so a build from
  uncommitted tools is visible. Records written before the split list `VibeModForge`, `VibeBroodForge` and
  `VibeWarForge` versions instead; `show` prints both kinds.

## Privacy

Prompts can contain private information, and the record travels with the map.
- By default, the prompt text is stored after a scrub that replaces e-mail addresses, access tokens and home-folder user names.
  Phone numbers, real names and addresses are NOT detected; use `--redact` for such prompts. The record marks the prompt `"redacted": "scrubbed"`.
- `add-prompt --redact` stores no text at all, only a SHA-256 hash and the length. Use it for any prompt with personal
  content.
- `tools/provenance.py redact <map> --prompt <id or number>` removes a prompt's text from the map and the ledger later.
- Never log secret story files or credentials as prompt text.

## Editability

The record does not change how the map plays or how editors treat it: the map keeps its standard sections. StarCraft ignores unknown sections,
and ScmDraft 2 opens the map.

Proven on our box: the self-test, `sclib.validate`, `predelivery_check.py` with identical results with and without
the record, and the ScmDraft 2 open test. Not proven: ScmDraft and StarEdit saves, and loading in the game itself.

## Self-test

    python3 tools/provenance.py selftest
    VBF_SELFTEST_SCX=path.scx python3 tools/provenance.py selftest   # also stamp a real map (a copy)

The self-test writes `.scx` maps through the same steps as `sclib.Map.save` and reads the records back. It then simulates
human edits (a terrain byte, an extra unit), checks that they are detected and recorded, checks the fallback to the MPQ
file when the CHK section is gone, and writes a campaign summary.
