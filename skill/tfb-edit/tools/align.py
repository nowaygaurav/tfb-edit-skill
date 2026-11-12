#!/usr/bin/env python3
"""Step 2 (alternative). The editor uploads his own final audio: final.wav + script.txt -> words.json via ElevenLabs forced alignment.
usage: python align.py projects/<name> [--audio final.wav]"""
import argparse, sys
import requests
from common import project, need, jsave

ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("--audio", default="final.wav")
a = ap.parse_args()
P = project(a.project)
text = (P / "script.txt").read_text(encoding="utf-8").strip()
with open(P / a.audio, "rb") as f:
    r = requests.post("https://api.elevenlabs.io/v1/forced-alignment", headers={"xi-api-key": need("ELEVENLABS_API_KEY")},
                      files={"file": (a.audio, f)}, data={"text": text}, timeout=300)
if r.status_code != 200:
    sys.exit(f"ElevenLabs error {r.status_code}: {r.text[:300]}")
ws = [dict(w=w["text"].strip(), s=round(w["start"], 3), e=round(w["end"], 3)) for w in r.json()["words"] if w["text"].strip()]
jsave(P / "words.json", ws)
print(f"words.json ({len(ws)} words)")
