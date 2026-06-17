"""Unit tests for the lyric pipeline (tools/lrc_to_lyrics.py).

Pure functions, no disk fixtures — the bug-prone bits: paren handling, recursive
word-wrap, abbreviation, choir flagging, time offset, blank-gap insertion."""
import lrc_to_lyrics as L


# ---- clean() -------------------------------------------------------------
def test_clean_strips_parens_by_default():
    assert L.clean("(Together)") == ""
    assert L.clean("Go (West) now") == "GO  NOW".replace("  ", " ")  # span removed, spaces collapsed
    assert L.clean("Hand in my hand, baby") == "HAND IN MY HAND BABY"


def test_clean_keep_parens_keeps_words():
    assert L.clean("(Together)", keep_parens=True) == "TOGETHER"
    assert L.clean("(Go West)", keep_parens=True) == "GO WEST"


# ---- fit() ---------------------------------------------------------------
def test_fit_short_passthrough():
    assert L.fit("HELLO", {}) == ["HELLO"]
    assert L.fit("", {}) == [""]


def test_fit_abbr_collapse_and_drop():
    assert L.fit("HE'S GOT HIS STRONG BELIEFS",
                 {"HE'S GOT HIS STRONG BELIEFS": "GOT HIS STRONG BELIEFS"}) == \
        ["GOT HIS STRONG BELIEFS"]
    assert L.fit("LA LA LA", {"LA LA LA": ""}) == []     # empty abbr drops the line
    assert L.fit("LA LA LA", {"LA LA LA": None}) == []   # None drops too


def test_fit_recursive_wrap_multiphrase():
    # the bug freed surfaced: several phrases crammed on one LRC line wrap fully
    out = L.fit("MY LOVE HAS GOT NO MONEY HE'S GOT HIS STRONG BELIEFS", {})
    assert out == ["MY LOVE HAS GOT NO MONEY", "HE'S GOT HIS STRONG", "BELIEFS"]
    assert all(len(x) <= L.MAXC for x in out)


def test_fit_abbr_applies_to_wrapped_tail():
    out = L.fit("MY LOVE HAS GOT NO MONEY HE'S GOT HIS STRONG BELIEFS",
                {"HE'S GOT HIS STRONG BELIEFS": "GOT HIS STRONG BELIEFS"})
    assert out == ["MY LOVE HAS GOT NO MONEY", "GOT HIS STRONG BELIEFS"]


# ---- parse_lrc() ---------------------------------------------------------
def test_parse_lrc_times_and_choir_flag():
    rows = L.parse_lrc("[00:10.50]Hello world\n[01:02.00](Together)\nnope\n")
    assert rows[0] == (10.5, "Hello world", 0)
    assert rows[1] == (62.0, "(Together)", 1)   # wholly-parenthetical -> choir
    assert len(rows) == 2                        # non-timestamped line ignored


# ---- build_lyrics() ------------------------------------------------------
def _clip(**kw):
    base = {"ratio": 1.0}
    base.update(kw)
    return base


def test_build_offset_and_choir_colour():
    rows = L.parse_lrc("[00:36.50]Come on come on come on\n[00:38.64](Together)\n")
    fix = L.build_lyrics(rows, _clip(lrc_offset=-4.5, keep_parens=True))
    by_text = {t: (round(st, 1), s) for st, t, s in fix}
    assert by_text["COME ON COME ON COME ON"][0] == 32.0   # 36.5 - 4.5
    assert by_text["TOGETHER"] == (34.1, 1)                # offset applied + choir style


def test_build_leading_blank_and_dedup():
    rows = L.parse_lrc("[00:10.00]Same line\n[00:12.00]Same line\n[00:14.00]Other\n")
    fix = L.build_lyrics(rows, _clip())
    assert fix[0] == (0.0, "", 0)                 # leading blank inserted
    texts = [t for _, t, _ in fix if t]
    assert texts.count("SAME LINE") == 1          # consecutive identical deduped


def test_build_keep_parens_default_strips_choir():
    rows = L.parse_lrc("[00:10.00](Together)\n[00:12.00]Lead line\n")
    fix = L.build_lyrics(rows, _clip())           # keep_parens defaults False
    texts = [t for _, t, _ in fix]
    assert "TOGETHER" not in texts                # parenthetical stripped to blank
