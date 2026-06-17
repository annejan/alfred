#!/usr/bin/env python3
"""Generic timed-.lrc -> lyrics.json on the SID timeline.

Parses a timed LRC, cleans/abbreviates to <=24 chars, word-wraps long lines,
flags choir (call-and-response) lines, dedups consecutive repeats, inserts
blank markers at instrumental gaps, caps to MAXLINES, and maps LRC time -> SID
time via clip.json `ratio` (scale) + `lrc_offset` (constant shift).

lyrics.json lines are [time, text, choir-flag]. clip.json knobs: ratio,
lrc_offset, keep_parens, abbr, build. Pure functions below are unit-tested;
main() does the file I/O. Run from the repo root: `python3 tools/lrc_to_lyrics.py`.
"""
import re, json, sys

MAXC, MAXLINES = 24, 150
GAP, HOLD = 4.0, 3.0


def clean(s, keep_parens=False):
    """Normalise an LRC line: uppercase, drop commas, collapse spaces. With
    keep_parens, keep the parenthetical words (the choir line) but drop the
    brackets; otherwise strip "(...)" spans entirely."""
    if keep_parens:
        s = s.replace('(', ' ').replace(')', ' ')
    else:
        s = re.sub(r'\(.*?\)', '', s)
    s = s.replace(',', '').upper().strip()
    return re.sub(r'\s+', ' ', s)


def fit(s, abbr, maxc=MAXC):
    """Wrap a phrase into <=maxc-char lines. `abbr` maps a phrase to a shorter
    form (or "" / None to drop it). Recurses so an LRC line that crams several
    phrases wraps fully; a tiny (<=4-char) trailing orphan is dropped."""
    if s in abbr:
        if not abbr[s]:
            return []
        s = abbr[s]
    if len(s) <= maxc:
        return [s]
    cut = s.rfind(' ', 0, maxc + 1)
    if cut <= 0:
        return [s[:maxc]]
    a, b = s[:cut], s[cut + 1:]
    rest = fit(b, abbr, maxc)
    if not rest and len(b) <= 4:
        return [a]
    return [a] + rest


def parse_lrc(text):
    """LRC text -> [(seconds, raw_text, choir_flag)]. choir = wholly-parenthetical."""
    rows = []
    for line in text.splitlines():
        m = re.match(r'\[(\d+):(\d+\.\d+)\]\s*(.*)', line)
        if not m:
            continue
        raw = m.group(3)
        sty = 1 if raw.lstrip().startswith('(') else 0
        rows.append((int(m.group(1)) * 60 + float(m.group(2)), raw, sty))
    return rows


def build_lyrics(rows, clip):
    """Turn parsed LRC rows + a clip config into the final [time, text, style] list."""
    keep = clip.get('keep_parens', False)
    abbr = clip.get('abbr', {}) or {}
    ratio = clip.get('ratio', 1.0)
    offset = clip.get('lrc_offset', 0.0)
    b = clip.get('build')
    SAT = b['match'] if b else None
    SEQ = b['seq'] if b else []
    RES = b['resolve'] if b else ""

    rows = [(t, clean(raw, keep), sty) for t, raw, sty in rows]
    # optional chorus build-up (repeated hook -> grows then resolves)
    c = 0
    for i, (t, txt, sty) in enumerate(rows):
        if SAT and txt == SAT:
            nxt = rows[i + 1][1] if i + 1 < len(rows) else ""
            if nxt == SAT:
                rows[i] = (t, SEQ[c % len(SEQ)], sty); c += 1
            else:
                rows[i] = (t, RES, sty); c = 0
        else:
            c = 0

    ent = []
    for t, txt, sty in rows:
        st = round(t * ratio + offset, 1)
        if st < 0:
            st = 0.0
        if not txt:
            ent.append((st, "", 0)); continue
        parts = fit(txt, abbr)
        if not parts:
            ent.append((st, "", 0)); continue
        for j, p in enumerate(parts):
            ent.append((round(st + 1.3 * j, 1), p, sty))

    # clear lingering text in instrumental gaps: blank ~HOLD s after a line that
    # is followed by a >GAP-second hole.
    gapped = []
    for i, (st, txt, sty) in enumerate(ent):
        gapped.append((st, txt, sty))
        nxt = ent[i + 1][0] if i + 1 < len(ent) else st + 999
        if txt and nxt - st > GAP:
            gapped.append((round(min(st + HOLD, nxt - 0.3), 1), "", 0))
    ent = gapped

    # dedup consecutive identical (same text AND style), keep time increasing
    ded = []
    for st, txt, sty in ent:
        if ded and ded[-1][1] == txt and ded[-1][2] == sty:
            continue
        ded.append((st, txt, sty))
    fix = []
    for st, txt, sty in ded:
        if fix and st <= fix[-1][0]:
            st = round(fix[-1][0] + 0.3, 1)
        fix.append((st, txt, sty))
    if fix and fix[0][0] > 0.5:
        fix = [(0.0, "", 0)] + fix
    # cap: drop interior blanks first, then shortest
    while len(fix) > MAXLINES:
        bi = [i for i, (_, t, _s) in enumerate(fix) if t == "" and 0 < i < len(fix) - 1]
        if bi:
            del fix[bi[len(bi) // 2]]
        else:
            j = min(range(1, len(fix)), key=lambda i: len(fix[i][1]) or 99); del fix[j]
    return fix


def main(argv):
    clip = json.load(open('clip.json'))
    rows = parse_lrc(open(clip['lrc'], encoding='utf-8').read())
    fix = build_lyrics(rows, clip)
    nchoir = sum(s for _, _, s in fix)
    maxc = max(len(t) for _, t, _ in fix)
    if '--dry' in argv:
        print(f"{len(fix)} lines ({nchoir} choir), max {maxc} chars (cap {MAXLINES})")
        for t, x, s in fix:
            print(f"  {t:6.1f} {'(C)' if s else '   '} {x}")
    else:
        json.dump({"comment": "LRC->SID (lines: [time, text, choir-flag])",
                   "lines": [[t, x, s] for t, x, s in fix]},
                  open('lyrics.json', 'w'), indent=1)
        print(f"{len(fix)} lines ({nchoir} choir), max {maxc} chars")


if __name__ == '__main__':
    main(sys.argv)
