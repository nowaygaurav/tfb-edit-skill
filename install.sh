#!/bin/sh
# Mac/Linux installer: sh install.sh
set -e
repo="$(cd "$(dirname "$0")" && pwd)"; dest="$HOME/.claude/skills/tfb-edit"
mkdir -p "$HOME/.claude/skills"; rm -rf "$dest"; ln -s "$repo/skill/tfb-edit" "$dest"
python3 -m pip install --upgrade requests pillow numpy opencv-python yt-dlp
[ -f "$repo/.env" ] || cp "$repo/.env.example" "$repo/.env"
mkdir -p "$repo/projects"; python3 "$repo/skill/tfb-edit/tools/doctor.py"
