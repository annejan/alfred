# clips/ — per-clip configuration & curated assets

One directory per music video. Everything that makes a clip *that* clip lives
here; the tools and engine in the repo root are shared and clip-agnostic.

```
clips/<name>/
  clip.json       config (see below) — the single source of truth per clip
  segments.json   curated song-section boundaries + song_len/video_len
  lyrics.json     [time, text] lines on the SID timeline
  picks.json      chosen video-frame timestamps per slot (optional)
  koala/          imgNN.kla + imgNN.png — the dithered images, one per segment
```

## Activating a clip

`tools/use_clip.sh <name>` points the repo-root working files
(`clip.json`, `segments.json`, `lyrics.json`, `picks.json`, `koala/`) at
`clips/<name>/` via symlinks (gitignored). All tools read the root, so this is
the only switch needed. Edits write straight through to `clips/<name>/`.

```sh
tools/use_clip.sh bjork      # then lyric_assets → gen_parts → build_demo → render_demo
```

## clip.json fields

| field | meaning |
|-------|---------|
| `name` | output basename (`~/Videos/<name>_c64.mp4`) |
| `video` | source `.webm` (at repo root, gitignored) |
| `sid` / `mp3` | the tune (PSID for the demo, mp3 for the preview render) |
| `lrc` | timed lyric source for `lrc_to_lyrics.py` (`""` if `lyrics.json` is hand-curated) |
| `title` / `disk_id` | d64 directory title + disk id |
| `beat` | seconds per beat — `segment.py` snaps cuts to it |
| `song_len` / `video_len` / `render_len` | SID length, video length, preview length (s) |
| `ratio` | LRC→SID time scale (1.0 if the LRC is already timed to the render) |
| `faderamp` | 5 C64 colours, trough→peak, for the lyric-sprite colour pulse |
| `abbr` | map long lyric lines → ≤24-char forms (`null` = let it word-split) |
| `build` | optional chorus build-up (`match`/`seq`/`resolve`) — see `lrc_to_lyrics.py` |

## Adding a clip

Drop the `.webm` + `.sid` (+ `.mp3`/`.lrc`) at the repo root, make
`clips/<name>/`, write its `clip.json`, then run the curation pipeline in
[`../docs/NEWCLIP.md`](../docs/NEWCLIP.md). Audio/video are not committed.
