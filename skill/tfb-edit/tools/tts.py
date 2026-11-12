#!/usr/bin/env python3
"""Step 1. script.txt -> raw.mp3 + raw-words.json with ElevenLabs (Sanchit's voice, word timestamps).
usage: python tts.py projects/<name> [--voice VOICE_ID] [--model eleven_multilingual_v2]"""
import argparse, base64, sys
import requests
from common import project, need, jsave

ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("--voice"); ap.add_argument("--model", default="eleven_multilingual_v2")
a = ap.parse_args()
P = project(a.project)
script = (P / "script.txt").read_text(encoding="utf-8").strip()
if not script:
    sys.exit("script.txt is empty")
key = need("ELEVENLABS_API_KEY"); voice = a.voice or need("ELEVENLABS_VOICE_ID")
r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_192",
                  headers={"xi-api-key": key, "Content-Type": "application/json"},
                  json={"text": script, "model_id": a.model, "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}}, timeout=300)
if r.status_code != 200:
    sys.exit(f"ElevenLabs error {r.status_code}: {r.text[:300]}")
d = r.json()
(P / "raw.mp3").write_bytes(base64.b64decode(d["audio_base64"]))
al = d.get("normalized_alignment") or d["alignment"]
chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
words, cur, s0 = [], "", None
for c, s, e in zip(chars, st, en):
    if c.isspace():
        if cur: words.append(dict(w=cur, s=round(s0, 3), e=round(prev_e, 3))); cur = ""
        continue
    if not cur: s0 = s
    cur += c; prev_e = e
if cur: words.append(dict(w=cur, s=round(s0, 3), e=round(prev_e, 3)))
jsave(P / "raw-words.json", words)
print(f"raw.mp3 + raw-words.json ({len(words)} words, {words[-1]['e']:.1f} s)")
