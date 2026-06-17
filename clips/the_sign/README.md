# the_sign — Ace of Base, *The Sign*

1993 Swedish pop. High-contrast, well-lit video → crisp koala portraits (the
band members, dramatic monochrome faces).

| | |
|---|---|
| song | Ace of Base — The Sign (4:20 SID cover; MIDI repeats) |
| images | 21 koala, video-curated (one agent per slot over 8 candidates) |
| lyrics | 69 lines / 34 unique |
| pulse | `faderamp [0,6,14,3,1]` — blue→white |
| status | **done** — builds to `out/the_sign.d64`, preview `~/Videos/the_sign_c64.mp4` |

```sh
tools/use_clip.sh the_sign
python3 tools/lyric_assets.py && python3 tools/gen_parts.py && ./build_demo.sh
python3 tools/render_demo.py
```

Notes:
- The SID cover is 4:20 (the source MIDI repeats), longer than the 3:17 video,
  so the koala timeline maps the song (`song_len` 260) across the video
  (`video_len` 197.4); the vocal enters ~34s (long intro). `ratio` 1.0 — the
  LRC is timed to the SID render.
- 34 unique lyric lines — the most so far. This clip is why the resident layout
  moved `ORDER`/`ONSET` up to `$3800`/`$3880`, giving `UNIQ` room to `$37ff`
  (~53 unique lines) instead of overlapping at `$3600`.
- Provenance: `sid_build.cmd` (the Jantje MIDI→SNG→SID→mp3→LRC recipe).
