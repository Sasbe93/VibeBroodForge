# data/

Derived data the tools read, so they work without game files.

- `bw/`: Brood War tech tree, weapons and unit IDs (derived from BWAPI tables), plus tech checks and drawn tech-tree charts.
- `reference_metrics/bw/`: measurements of public ladder maps (sizes, rush distances, ramps, neutral buildings). Only numbers, no map content. Checkers use them as reference ranges.

The campaign-mission quality band (`tools/bw/quality_metrics.py`) is a small table inside the tool and in `docs/quality-bar.md`.

StarCraft and Brood War are trademarks of Blizzard Entertainment. No Blizzard assets are included.
