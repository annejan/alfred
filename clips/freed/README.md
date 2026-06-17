# freed — GALA, *Freed from Desire*

*"My love has got no money…"* — 1996 eurodance. Built end to end through the
config-driven pipeline.

| | |
|---|---|
| song | GALA — Freed from Desire (~3:17) |
| images | 16 koala, video-curated (one agent per slot over 8 candidates) |
| lyrics | 31 lines / 8 unique |
| pulse | `faderamp [0,6,14,3,1]` — blue→white |
| status | **done** — builds to `out/freed_from_desire.d64`, preview `~/Videos/freed_from_desire_c64.mp4` |

```sh
tools/use_clip.sh freed
python3 tools/lyric_assets.py && python3 tools/gen_parts.py && ./build_demo.sh
python3 tools/render_demo.py
```

Notes:
- The GALA video is dim and warm, so the koala grade is a sepia/red-brown palette
  (graded `--bright 1.35 --contrast 1.3 --sat 1.45`). To re-curate, re-run
  `gen_candidates.py` and re-rank, or hand-pick brighter frames into `picks.json`.
- `clip.json` `abbr` fixes two awkward lyric splits (the lone `BELIEFS` tail and
  the long `NA NA…` run). `ratio` 1.0 — the LRC is timed to the SID render.
- This clip surfaced two pipeline fixes (now upstream): the universal 4:3 crop in
  `gen_candidates.py` (the source is 5:4) and `use_clip.sh` symlinking the json
  before they exist so a fresh clip's output lands in `clips/<name>/`.
