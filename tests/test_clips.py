"""Validate every clips/<name>/clip.json against the schema the tools assume.

No heavy deps — just checks the configs are well-formed so a build won't fail
deep inside ffmpeg/KickAss on a typo."""
import glob
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIPS = sorted(glob.glob(os.path.join(ROOT, "clips", "*", "clip.json")))

REQUIRED = {"name", "video", "sid", "mp3", "lrc", "title", "disk_id",
            "beat", "song_len", "video_len", "render_len", "ratio"}


def test_at_least_one_clip():
    assert CLIPS, "no clips/*/clip.json found"


@pytest.mark.parametrize("path", CLIPS, ids=lambda p: os.path.basename(os.path.dirname(p)))
def test_clip_config(path):
    c = json.load(open(path))
    assert set(c) >= REQUIRED, f"missing keys: {REQUIRED - set(c)}"

    assert isinstance(c["name"], str) and c["name"]
    for k in ("beat", "song_len", "video_len", "render_len", "ratio"):
        assert isinstance(c[k], (int, float)) and c[k] >= 0, k

    # colour ramps: 5 valid C64 colour indices each
    for k in ("faderamp", "faderamp2"):
        if k in c:
            assert isinstance(c[k], list) and len(c[k]) == 5, k
            assert all(isinstance(v, int) and 0 <= v <= 15 for v in c[k]), k

    # abbr maps str -> (str | null); build, if present, has the 3 fields
    for key, val in (c.get("abbr") or {}).items():
        assert isinstance(key, str)
        assert val is None or isinstance(val, str)
    if c.get("build"):
        assert {"match", "seq", "resolve"} <= set(c["build"])

    # disk id is short (Spindle/d64 limit)
    assert len(c["disk_id"]) <= 5
