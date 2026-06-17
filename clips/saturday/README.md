# saturday — Whigfield, *Saturday Night*

Eurodance, 1994. A SID cover of Whigfield's *Saturday Night* under 19 koala
frames from the video, with the (very repetitive) chorus driving the lyric
engine's orderlist hard.

| | |
|---|---|
| song | Whigfield — Saturday Night (3:37) |
| images | 19 koala, video-curated |
| lyrics | 66 lines / 18 unique |
| pulse | `faderamp [0,6,11,4,12]` — darker black→grey (matches the darker grade) |
| status | **done** — builds to `out/saturday_night.d64`, preview `~/Videos/saturday_night_c64.mp4` |

```sh
tools/use_clip.sh saturday
python3 tools/lyric_assets.py && python3 tools/gen_parts.py && ./build_demo.sh
python3 tools/render_demo.py
```

Clip-specific `clip.json` knobs:
- **`build`** — the hook *"SATURDAY NIGHT SATURDAY NIGHT"* is built up across
  repeats (`SATURDAY` → `SATURDAY SATURDAY` → … → resolves to `SATURDAY NIGHT`)
  instead of repeating the full line, and the lone 4-char `NIGHT` orphan is
  dropped (`lrc_to_lyrics.py`).
- **`abbr`** — long lines mapped to ≤24 chars; instrumental gaps get blanked so
  no line lingers.

Sources: `saturday_night.sid` / `.sng` / `.lrc` (+ original `Saturday Night.lrc`
and the `.mid`). `.mp3` / `.webm` not committed.
