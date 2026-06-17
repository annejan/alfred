# Alfred — a director for C64 music-video demos

> Named for Alfred Hitchcock: hand it a music video and it directs the whole
> production onto a Commodore 64.

A config-driven pipeline that turns a music video + a SID cover into a
single-sided C64 demo (Spindle 3.1 / pefchain): the tune plays while koala
images — frames lifted from the video and dithered to the C64 palette — are
streamed off disk and cut on the song's structural transitions, with a
resident lyric engine blitting the words as hardware sprites.

Companion to the Dutch-pun toolchain: **Martin Gaus** for the splatting, and
**[Jantje](https://github.com/annejan/jantje)** (Jantje Smit) which makes the
upstream inputs — `.sid` / `.sng` / (where possible) `.lrc` — from a MIDI. So
the chain is: MIDI → *Jantje* → SID/SNG/LRC → *Alfred* → C64 demo.

**Multi-clip.** Each clip lives in `clips/<name>/` — its `clip.json` + curated
`segments.json` / `lyrics.json` / `koala/` + its source media, and its own
README. The tools all read the repo root, so `tools/use_clip.sh <name>` just
repoints the root working symlinks at a clip and you build it. Three clips:

| clip | song | dir | status |
|------|------|-----|--------|
| Björk — *Human Behaviour* | `human_behaviour.sid` (4:19) | [`clips/bjork/`](clips/bjork/) | done |
| Whigfield — *Saturday Night* | `saturday_night.sid` (3:37) | [`clips/saturday/`](clips/saturday/) | done |
| GALA — *Freed from Desire* | `freed-from-desire.sid` (~3:17) | [`clips/freed/`](clips/freed/) | done |
| Ace of Base — *The Sign* | `the_sign.sid` (4:20) | [`clips/the_sign/`](clips/the_sign/) | done |

Renders land in `~/Videos/<name>_c64.mp4`; the disk image in `out/<name>.d64`.

## Build a clip

Needs KickAssembler + Spindle 3.1 binaries (reused from `../x2026`), Python 3
with Pillow/NumPy/SciPy, ffmpeg, and the source `.webm` + `.sid` (audio/video
not redistributed).

```sh
tools/use_clip.sh saturday      # or: bjork  — activate the clip
python3 tools/lyric_assets.py   # lyrics.json → font + uniq + order + onset bins
python3 tools/gen_parts.py      # → src/pNN*.asm, script_demo, build_demo.sh
./build_demo.sh                 # assemble (KickAss) + link the d64 (pefchain)
python3 tools/render_demo.py    # deterministic offline preview → ~/Videos/<name>_c64.mp4
```

To curate a **new** clip from scratch (segmentation, frame ranking, lyric
fitting, timing), see [`docs/NEWCLIP.md`](docs/NEWCLIP.md). Hard-won gotchas
are in [`docs/LESSONS.md`](docs/LESSONS.md).

## Layout

| path | what |
|------|------|
| `clips/<name>/` | per-clip config + curated assets (the authoritative copies) |
| `clip.json` etc. | root working **symlinks** → the active clip (gitignored) |
| `tools/` | the config-driven pipeline (see `tools/README.md`) |
| `src/lyriceng.asm` | resident lyric engine ($0c00): font-render + ORDER lookup |
| `src/pNN.asm` | generated Spindle parts (one per koala, double-buffered banks) |
| `out/<name>.d64` | the built demo (artifact) |

## How it works

- **Config-driven.** Everything per-clip (video, SID, lyric timing/ratio,
  abbreviations, chorus build-ups, song/video lengths) is in `clip.json`. The
  tools read it; nothing clip-specific is hard-coded.
- **Music** rides resident via Spindle's `--music` (PSID header stripped);
  part 0 installs the play routine with the `M` tag so pefchain calls it every
  frame — including during load gaps, so the SID never drops.
- **Images** are multicolor bitmaps. Even parts use VIC bank 1
  ($4000/$6000), odd parts bank 2 ($8000/$a000); pefchain preloads the next
  into the *other* bank while the current shows, then `setup` flips the bank
  (via `$dd02`, since Spindle owns `$dd00`).
- **Lyrics.** A resident engine at `$0c00` keeps a song-frame clock and, on
  each onset, renders `UNIQUE[ORDER[cursor]]` from the C64 charset into the
  live bank's 8 hires sprites (a 24-char row) — an orderlist-style lookup, so
  repetitive choruses cost no extra RAM. Lines pulse dark→light and bob.
- **Timing**: each part counts down its section length and raises an advance
  flag; the pefchain script waits on it, so cuts land on song transitions.

## Related

- **[Jantje](https://github.com/annejan/jantje)** — upstream: MIDI → SID / SNG / LRC.
- **[vice-macos (mcp-server)](https://github.com/barryw/vice-macos/tree/mcp-server)** —
  VICE MCP bridge, for capturing the real `.d64` running on the emulator
  (`render_demo.py` is the deterministic offline preview; see `AGENTS.md` and
  `docs/LESSONS.md`).
- Agent / contributor guide: [`AGENTS.md`](AGENTS.md).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
