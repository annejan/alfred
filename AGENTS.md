# AGENTS.md — working in the Alfred repo

Alfred turns a music video + a SID cover into a single-sided C64 demo
(Spindle 3.1 / pefchain). Read this before changing things.

## Shape

- **Config-driven, multi-clip.** Each clip is `clips/<name>/`: `clip.json`
  (the single source of truth) + curated `segments.json` / `lyrics.json` /
  `picks.json` + `koala/` + its source media + a per-clip `README.md`.
- **Activation.** `tools/use_clip.sh <name>` repoints repo-root working
  *symlinks* (`clip.json`, the json, `koala/`, and the source media) at one
  clip. Every tool reads the repo root. The root symlinks are gitignored; the
  authoritative files live in `clips/<name>/`. Never edit the root symlinks —
  edit `clips/<name>/…`.
- **Upstream:** the `.sid`/`.sng`/`.lrc` are produced by
  [Jantje](https://github.com/annejan/jantje) from a MIDI.

## Build / rebuild an existing clip

```sh
tools/use_clip.sh <name>
python3 tools/lyric_assets.py     # lyrics.json -> font/uniq/order/onset bins + src/lyric_{fade,n}.asm
python3 tools/gen_parts.py        # segments.json + clip.json -> src/pNN*.asm, build_demo.sh, script_demo
./build_demo.sh                   # KickAss + pefchain -> out/<name>.d64
python3 tools/render_demo.py      # deterministic preview -> ~/Videos/<name>_c64.mp4
```

A new clip = curate `segments.json` (`tools/segment.py`), `koala/`
(`gen_candidates.py` → vision-rank → `photo_to_koala.py`), and `lyrics.json`
(`lrc_to_lyrics.py`). Full recipe: `docs/NEWCLIP.md`. Gotchas: `docs/LESSONS.md`.

## Frame-curation agent protocol

`gen_candidates.py` writes `cand/sNN_kKK.png` — K dithered koala previews per
segment (`cand/manifest.json` maps them). To pick images, fan out one agent per
slot: it Reads that slot's `k0..k7` previews and returns the best `k` (clearest
subject, strongest contrast, most iconic/on-theme for the song — avoid mush and
near-duplicates of adjacent slots). Collect picks into `clips/<name>/picks.json`,
then run `photo_to_koala.py` on the chosen frame per slot into `koala/imgNN.kla`.

## Conventions (do these)

- Commit/push only when asked. Branch off master if needed.
- Commit messages end with:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- `.mp3` and `.webm` are copyrighted recordings — gitignored everywhere, never
  committed. `.sid`/`.sng`/`.lrc`/`.mid` are committed under `clips/<name>/`.
- Per-clip lyric-sprite colour pulse is `clip.json` `faderamp` (5 C64 colours,
  trough→peak), `faderamp2` for choir/call-and-response lines; they flow to
  `src/lyric_fade.asm` and `render_demo.py`.
- C64/Spindle invariants: VIC bank via `$dd02` (Spindle owns `$dd00`);
  `call_play` placeholder must be the 3-byte `.byte $2c,$00,$00`; only `(zp),y`
  indirect-indexed addressing.
- Generated source is gitignored — only `src/lyriceng.asm` is hand-written.
  Don't commit `src/pNN*.asm`, `lyric_{n,fade}.asm`, `build_demo.sh`, `script_demo`.

## Tests & CI

- `pytest` (config in `pyproject.toml`, tests in `tests/`) covers the pure
  logic: lyric `clean`/`fit`/`build_lyrics`, koala `encode_koala`, and every
  `clips/*/clip.json` against its schema. Run: `pytest` from the repo root.
- `ruff check tools tests` must pass — the dense house style is preserved via
  `[tool.ruff.lint] ignore` (don't "fix" E7xx/E401/E501/SIM115); fix real bugs
  (F-codes, unused vars).
- GitHub Actions (`.github/workflows/ci.yml`) runs ruff + pytest on Python
  3.9/3.11/3.13. Keep build tools importable (file I/O under `main()`/
  `if __name__=='__main__'`) so their helpers stay unit-testable.

## On-emulator capture / verification

`render_demo.py` is the reliable deterministic preview. For a real-VICE capture
of the actual `.d64`, the bridge is the VICE MCP server:
<https://github.com/barryw/vice-macos/tree/mcp-server>. Capture caveats (Xvfb
GL, focus, pulse monitor sink) are in `docs/LESSONS.md`.
