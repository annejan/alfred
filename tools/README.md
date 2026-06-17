# tools/ — the config-driven pipeline

Every tool reads the active clip from the repo root (`clip.json`,
`segments.json`, `lyrics.json`, `koala/`) — switch clips with
`use_clip.sh <name>`. Nothing here is clip-specific; per-clip values live in
`clips/<name>/clip.json`.

## Build order (existing clip)

```sh
./use_clip.sh <name>      # activate
python3 lyric_assets.py   # lyrics.json → out/lyric_{font,uniq,order,onset}.bin + src/lyric_fade.asm + src/lyric_n.asm
python3 gen_parts.py      # segments.json + clip.json → src/pNN*.asm, script_demo, build_demo.sh
../build_demo.sh          # KickAss assemble + pefchain link → out/human.d64
python3 render_demo.py    # deterministic preview → ~/Videos/<name>_c64.mp4
```

## Curation (new clip / re-cut)

| tool | does |
|------|------|
| `segment.py` | Foote-style novelty on the SID render → beat-snapped section boundaries → `segments.json` |
| `gen_candidates.py` | per segment, dither K video frames to koala previews → `cand/` for ranking |
| `photo_to_koala.py` | one photo → C64 multicolor koala (.kla), full 16-col FS dither (`--bg/--contrast/--sat/--bright`) |
| `lrc_to_lyrics.py` | timed `.lrc` → `lyrics.json` (clean/abbreviate/split/dedup, gap-clear, optional chorus build) |

## Asset / build tools

| tool | does |
|------|------|
| `use_clip.sh` | repoint repo-root working symlinks at `clips/<name>/` |
| `lyric_assets.py` | font + unique-line table + orderlist + onsets + per-clip `faderamp` for the resident engine |
| `gen_parts.py` | one Spindle part per koala (double-buffered VIC banks), residency tags, the pefchain script |
| `render_demo.py` | numpy replica of the on-C64 result (koala timeline + font-render lyrics + pulse/bob) muxed with the mp3 |

The engine itself is `../src/lyriceng.asm` (resident at `$0c00`). See
[`../docs/LESSONS.md`](../docs/LESSONS.md) for the gotchas behind these.
