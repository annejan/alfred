# Lessons — hard-won gotchas building this demo

Non-obvious things that cost real time. Read before touching the engine,
the Spindle wiring, or the capture flow.

## Spindle / VIC

- **VIC bank: write `$dd02`, never `$dd00`.** Spindle's IRQ loader owns
  `$dd00` (IEC serial) and rewrites it constantly, so any bank bits you set
  there get clobbered → VIC reads the wrong bank (garbage). Select the bank
  via the DDR `$dd02`: `3d`=bank1 ($4000), `3e`=bank2 ($8000). (handbook 1.3)
- **`call_play` placeholder must be exactly 3 bytes.** `bit $0000` gets
  assembled by KickAss as the 2-byte zero-page `BIT`; pefchain patches the
  callmusic slot with a 3-byte `jsr PLAY`, so a 2-byte placeholder makes the
  patch clobber the next opcode → `$02 JAM` (CPU halt) at the first
  transition. Emit `.byte $2c,$00,$00` to lock it at 3 bytes.
- **No `'Z'` zero-page tag on the parts.** Every part legitimately reuses the
  same zp; declaring `'Z'` makes pefchain think consecutive parts conflict →
  it inserts blank fillers → a filler lands on the music page `$10` → fatal.
  Leave zp undeclared (loader only reserves `$f4-$f8`).
- **Alternate BOTH code page and VIC bank between consecutive parts**
  (even=$0800/bank1, odd=$0900/bank2). If consecutive parts share any page,
  pefchain can't double-buffer → blank fillers. One filler at the `--loop`
  point is normal and unavoidable.
- **`--music` keeps multiple files resident** until the next music loads
  (never, here). Used to keep SID + lyric engine + sprite data alive across
  all parts. `'I'` tags are belt-and-braces only.

## Koala converter

- A `.kla` is **10003 bytes**; the background byte is the **last** byte
  (offset 10002), NOT `$2711`/10001 (that's the last colour byte). Reading
  the wrong offset bakes a colour value into `$d021`.
- mkpef colour-data offset is **`$232a`** (9002 dec), not `$2342`.
- Dark video frames blow out to bright **cyan** if you pick the most-frequent
  colour as background (no dark-teal in the C64 palette). Force **black bg**.
- `INIT` the SID only on **part 0** (else every image transition restarts the
  tune).

## Lyric sprite engine

- 8 hires sprites = a **24-char** row (3 chars/sprite, 8px C64 charset). 4px
  squashed fonts are unreadable. Lines must be **<=24 chars**.
- Sprite shapes precomputed on host (`lyric_spr.bin`) → the 6502 engine is a
  pure memcpy. Shapes blitted to **both** VIC banks on a line change, plus
  re-blitted in each part's setup (the freshly-flipped bank has stale bytes).
- >28 lines overflow `$2a00`'s budget → 2nd region at **`$c000`** (engine
  picks by threshold; `lyric_assets.py` writes the count to `src/lyric_n.asm`).
- Timing from the `.lrc` is **studio-timed**, not SID-timed. Anchor first
  vocal (LRC 7.33s ↔ SID 12.1s) and scale by the vocal-span ratio (~1.169).

## VICE capture (the painful one)

- **x11grab can't read VICE's GL surface on Xvfb** (output is black). Offscreen
  capture via Xvfb is a dead end with this GTK/GL build.
- On the real display VICE **throttles rendering to ~1fps when its window is
  unfocused/occluded** → x11grab gets a near-static stream. **Focus + raise
  the window** (`wmctrl -i -a <id>` + `-b remove,below`) → it renders 50fps
  and x11grab works. Confirm with a 4s test (≈200 frames).
- Capture region = window `x,y+27` (skip menubar), `720x544` (skip status bar).
  Re-fetch geometry every run — the window moves.
- **Audio: capture the monitor of the sink VICE actually outputs to.** It
  follows the *default* sink, which changes when the user switches output
  device (e.g. to Bluetooth → `bluez_output.*.monitor`). Find it via
  `pactl list sink-inputs` (VICE's `Sink:` id) → that sink's `.monitor`.
  A wrong/empty monitor gives a silent track (`-91 dB`). Any other audio
  playing to that sink **bleeds into the recording** — silence everything else.
- If audio came out silent, you can re-mux the clean rendered SID wav
  (`sidplayfp -w`) with `-itsoffset <demo-start-s> -stream_loop -1` instead of
  recapturing (alignment = the boot+load lead, ~13s).
- **To capture the boot/load/run:** start `ffmpeg` first, then fire
  `vice_autostart` ~1.5s later. For a clean power-on boot screen, hard-reset
  via MCP (`vice_machine_reset` mode `hard`) — it survived here, though the
  skill warns it can crash the mcp build (relaunch if so).
- **Launching VICE headless is flaky.** `run_in_background` is sandboxed
  without X (instant exit); pass `DISPLAY=:0 XAUTHORITY=...` and just retry —
  it's intermittent.

## Offline render fallback

`render_demo.py` composites the koala frames + a faithful replica of the
lyric-sprite animation + the SID wav into a clean 50fps MP4 in ~26s — no
capture flakiness. Pixel-faithful minus the authentic VICE border/scanlines.

## Lyric engine v2 (font-render + lookup) — Saturday Night

- **Font-render beats precomputed shapes.** Storing precomputed sprite shapes
  caps line count (~28-41) by RAM. Instead ship the C64 charset (512B) + a
  text table and render each line's 8 sprites on a line change → unlimited
  lines, tiny RAM. The blit fills bank1's sprite block then copies to bank2.
- **`lda (GP),x` is NOT a valid 6502 mode** — only `(zp),y` and `(zp,x)` exist.
  KickAss mis-assembled it → sprite noise. Render glyph rows with `(GP),y`
  (Y=row) and advance the dest pointer by 3 per row.
- **Repetition = an ORDER table** (onset → unique-line index, like a tracker
  orderlist). 77 lyric lines → 22 unique + a 77-byte order list. Cheap, scales
  to any repetitive song.
- **LRC timing: RATIO=1 when the LRC is already timed to the render/mp3.** Only
  scale (e.g. studio-BPM/SID-BPM) when the LRC is timed to a *different*
  recording. Check a known landmark (first sung hook) against the LRC time.
- **Clear lingering text in instrumental gaps:** if a line is followed by a
  >4s hole, insert a blank ~3s after it so it doesn't hang the whole break.
- **Chorus build-up:** a run of a repeated chorus line can be shown as a
  teasing build ("X" → "X X" → "X NIGHT" …) that resolves to the full line on
  the last of the run (`build` in clip.json).
- **Colour pulse, not white-hold.** Holding the lyric colour at white looks
  flat; pulse the luminance via the sine table (`faderamp`, e.g.
  black→blue→dkgrey→purple→grey) so the letters breathe dark↔light. A black
  trough doubles as a fade in/out.
- **SID size pushes the lyric data.** A bigger SID ($1000-$3005) overlapped the
  old $2a00 lyric region → mkpef "overlapping files". Lyric data now sits at
  $3100+ (FONT/UNIQ/ORDER/ONSET); relocate if the SID grows further.
- **Everything per-clip is in `clip.json`** (video/sid/mp3/lrc/title/beat/
  song_len/ratio/abbr/build). A new clip = drop files + edit clip.json + run.
  See `docs/NEWCLIP.md`.

## Multi-clip + engine v3 (Björk → … → Go West)

- **Multi-clip layout.** Each clip is `clips/<name>/` (config + curated json +
  koala + source media + README). `tools/use_clip.sh <name>` repoints the
  repo-root working symlinks; every tool reads the root. Always symlink the
  json *before* they exist, or a fresh clip's `segment.py`/`lrc_to_lyrics.py`
  output strands a real file at the gitignored root instead of writing through.
- **Per-clip d64.** `out/<name>.d64`, not a shared `out/human.d64`, or one
  clip's build clobbers another's disk image.
- **Generated source is not tracked.** Only `src/lyriceng.asm` is hand-written;
  `src/pNN*.asm`, `lyric_n.asm`, `lyric_fade.asm` (and `build_demo.sh`,
  `script_demo`) are emitted per clip and gitignored — otherwise stale parts
  (a 23-part clip's `p16`-`p22`) linger after a 16-part build.
- **Universal 4:3 crop.** `gen_candidates`/koala extraction must crop to the
  largest 4:3 region that *fits* (`crop=min(iw,ih*4/3):min(ih,iw*3/4)`); the old
  16:9-assuming crop produced an invalid (too-wide) rect on a 5:4 source (GALA).
- **Recursive word-wrap.** A real LRC crams several phrases on one timestamped
  line ("My love has got no money He's got his strong beliefs"). `fit()` must
  wrap *recursively* (and apply `abbr` per chunk), else the tail stays >24 and
  gets truncated on the 24-char sprite row.
- **LRC timing = `ratio` × t + `lrc_offset`.** A supplied "official" LRC can be
  a few seconds off the SID render. Two reference points from the user ("come
  on" 0:32, "Together" 0:34) pin a constant `lrc_offset` (Go West: -4.5s).
- **Call-and-response colour.** `keep_parens` keeps the `(...)` choir words and
  flags them; the engine renders choir lines with `faderamp2` and lead lines
  with `faderamp` via a per-line `STYLE` table + a `FADEPTR` (Go West: lead
  blue, choir red). Make a hue read regardless of pulse phase by keeping the
  ramp in-hue (`[0,6,6,14,14]` blue, `[0,2,2,10,10]` red) — a ramp through
  cyan/yellow/white reads as the wrong colour at its peak frame.
- **Resident lyric layout has a ceiling.** FONT/UNIQ/ORDER/ONSET/STYLE all live
  in `$3100-$3fff` (below the VIC banks at `$4000+`), so capacity is bounded:
  `24*NUNIQ + 4*NLINES` must fit ~3328 bytes. Current map (UNIQ `$3300`, ORDER
  `$3b00`, ONSET `$3c00`, STYLE `$3e00`) holds ~85 unique / ~150 lines. The
  residency tag `'P'/'I' $31,$3f` must cover all of it.
- **Tests + CI.** Pure logic (lyric `clean`/`fit`/`build_lyrics`, koala
  `encode_koala`, clip.json schema) is unit-tested (`tests/`, `pytest`); GitHub
  Actions runs `ruff` + `pytest` on 3.9/3.11/3.13. Keep build tools importable
  (side-effects under `main()`/`__main__`) so they can be tested.
