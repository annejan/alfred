#!/bin/bash
# Activate a clip: point the repo-root working files at clips/<name>/.
# The config-driven tools (lrc_to_lyrics, segment, lyric_assets, gen_parts,
# gen_candidates, render_demo) all read from the repo root, so switching clips
# is just repointing these symlinks. Edits write through to clips/<name>/.
#   tools/use_clip.sh bjork | saturday
set -e
cd "$(dirname "$0")/.."
name="$1"
dir="clips/$name"
[ -d "$dir" ] || { echo "no such clip: $dir" >&2; ls clips/ >&2; exit 1; }
for f in clip.json segments.json lyrics.json picks.json; do
    [ -e "$dir/$f" ] && ln -sfn "$dir/$f" "$f"
done
ln -sfn "$dir/koala" koala
echo "active clip: $name  ($(python3 -c "import json;c=json.load(open('clip.json'));print(c['title'],c['name'])"))"
