# Making a demo for another video clip

The pipeline (video → koala slideshow on song transitions + lyric sprites →
Spindle d64 → capture) is reusable. It's currently tuned to Björk; below are
the per-clip knobs and the step order. Copy this repo per clip, or branch.

## Inputs you need

1. **A SID** of the song (`human_behaviour.sid` slot). PSID, played 50Hz.
2. **The music video** (`.webm`/`.mp4`).
3. **Optional: a timed `.lrc`** for accurate lyric timing. Without it, derive
   onsets from a MIDI vocal track or place them by hand.

## Per-clip knobs (the hardcoded bits to change)

| file | what to change |
|------|----------------|
| `tools/extract_segments.py`, `tools/gen_candidates.py` | `VID = "..."` — the video filename |
| `tools/segment.py` | the **beat** (currently `bpm,beat,phase = 93.75,0.64,0` — set from the song's BPM) and CLI args `video_len song_len` |
| `tools/lrc_to_lyrics.py` | `LRC` path; the **anchor** `V0_LRC,S0_SID` (first-vocal time in LRC vs in the SID) and `RATIO` (SID-vocal-span ÷ LRC-vocal-span) |
| `tools/render_demo.py` | `SONG` length (or read it from `segments.json`) |
| `tools/gen_parts.py` | the `--music <sid>,,7c` filename, the pefchain `--title`/`--disk-id` |
| capture | window geometry (`wmctrl -lG`), the audio sink monitor (`pactl list sink-inputs` → VICE's sink → `.monitor`) |

Generic (no change needed): `photo_to_koala.py` (16-col palette), `gen_parts.py`
memory map / Spindle wiring, `lyric_assets.py`, `lyriceng.asm`. Lyric lines
must be **≤24 chars**; ≤49 lines (region1 `$2a00` + overflow `$c000`).

## Step order (the load-bearing sequence)

```sh
# 0. find the song length (SID has no length metadata): render long, autocorrelate
sidplayfp -w/tmp/x.wav -t560 -q song.sid
#    -> detect loop period = song_len (see the autocorr snippet in git history)

# 1. detect song sections -> image cut points
python3 tools/segment.py /tmp/x.wav <video_len> <song_len> --n 16 --target 14 --out segments.json

# 2. dithered candidate frames per section
python3 tools/gen_candidates.py

# 3. CURATE: pick the best candidate per slot (vision agents or by hand) ->
#    apply picks -> koala/imgNN.kla  (see git history for the picks workflow)

# 4. lyrics -> lyrics.json (<=24 chars/line, monotonic onsets)
python3 tools/lrc_to_lyrics.py

# 5. GENERATE PARTS, then build (ORDER MATTERS)
python3 tools/gen_parts.py      # regenerates src/pNN.asm + build_demo.sh + script_demo
bash build_demo.sh              # assembles parts + lyric engine, links the d64

# 6. capture (VICE) or offline render
python3 tools/render_demo.py    # deterministic MP4, no capture flakiness
```

**CRITICAL:** `build_demo.sh` only *assembles* the existing `src/pNN.asm`. After
editing `segments.json` (or any per-part value) you MUST re-run
`tools/gen_parts.py` first, or the parts keep stale timing. (This bit us on the
107 BPM rescale — see `docs/LESSONS.md`.)

## Tempo change shortcut

If you only re-render the SID at a different tempo (same song), don't redo
segments/curation — just rescale by the ratio `new_len/old_len`:
multiply every `segments.json` start/end (recompute `dur_frames`) and every
`lyrics.json` onset, then `gen_parts.py` + `build_demo.sh`.

See `docs/LESSONS.md` for the non-obvious traps (VIC bank via `$dd02`, the
3-byte `call_play` placeholder, no `'Z'` tag, capture focus/throttle/sink, …).
