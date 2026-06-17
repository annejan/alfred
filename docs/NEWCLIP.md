# Making a demo for another video clip (config-driven)

The pipeline is driven by **`clip.json`** — a new clip = drop the inputs, edit
`clip.json`, run the steps. Work on a branch per clip (master=Björk,
`saturday`=Whigfield, …). All tools read `clip.json`; no tool edits needed.

## 1. Drop inputs in the repo root

- the music video (`.webm`/`.mp4`)
- the SID (`*.sid`, PSID, init $1000 / play $1003)
- a mastered MP3 of the SID render (loudnorm) — used as the render's audio
- a timed `.lrc`

## 2. Fill in `clip.json`

```json
{
  "name": "saturday_night",          // output: ~/Videos/<name>_c64.mp4
  "video": "….webm", "sid": "….sid", "mp3": "….mp3", "lrc": "….lrc",
  "title": "disk/name", "disk_id": "XX",   // pefchain disk dir
  "beat": 0.48,                       // 60/BPM — for segment beat-snapping
  "song_len": 217.1,                  // SID loop length (autocorr, see below)
  "video_len": 238.0,                 // ffprobe the webm
  "render_len": 218.0,                // mp3 duration (ffprobe)
  "ratio": 1.0,                       // LRC->SID time scale (see LESSONS)
  "abbr": { "LONG LINE …": "SHORTER", "SPLIT ME": null },  // null => word-split
  "build": { "match":"X X", "seq":["X","X X"], "resolve":"X" }  // optional chorus build, or omit
}
```

Detect `song_len` (SID has no length metadata):
```sh
sidplayfp -w/tmp/s.wav -t560 -q clip.sid    # then loop-autocorrelate the
# energy envelope @50Hz in the 100-330s band -> peak lag = song_len
```

## 3. Run the pipeline (from repo root)

```sh
python3 tools/segment.py /tmp/s.wav <video_len> <song_len> --n 16 --target 14 --out segments.json
python3 tools/gen_candidates.py            # 8 dithered koala candidates per slot
#   CURATE: a vision-agent workflow ranks the candidates per slot (see git
#   history: curate-* workflow) -> apply picks -> koala/imgNN.kla + picks.json
python3 tools/lrc_to_lyrics.py             # LRC -> lyrics.json (abbr/build/gaps applied)
python3 tools/lyric_assets.py              # font + uniq + order + onset + src/lyric_n.asm
python3 tools/gen_parts.py                 # regenerates src/pNN*.asm + build_demo.sh + script_demo
bash build_demo.sh                         # assembles parts + lyric engine -> out/human.d64
python3 tools/render_demo.py               # deterministic MP4 -> ~/Videos/<name>_c64.mp4
```

**Per-LRC iteration loop** (timing/text tweaks): just
`lrc_to_lyrics → lyric_assets → gen_parts → build_demo → render_demo`.

**CRITICAL:** `build_demo.sh` only *assembles* existing `src/pNN.asm`. After
editing `segments.json` / `clip.json` you MUST run `tools/gen_parts.py` first,
or parts keep stale timing/config.

## 4. Watch the lyric RAM budget

Lyric data lives above the SID. If the SID grows past `$3100`, relocate
FONT/UNIQ/ORDER/ONSET (in `src/lyriceng.asm` + the `--music` line in
`gen_parts.py`); keep `UNIQ < ORDER < ONSET < $4000`. `lyric_assets.py` prints
the byte sizes — UNIQ ≤ (ORDER−UNIQ) etc.

## 5. Real VICE capture (optional)

See `docs/LESSONS.md` — focus the window for 50fps, capture the sink monitor
VICE actually outputs to, start ffmpeg then autostart for the boot/load/run.
The deterministic `render_demo.py` is the reliable default.
