#!/usr/bin/env python3
"""Checks that this PC can run the TFB pipeline. usage: python doctor.py"""
import importlib, shutil, subprocess, sys
from common import repo_root, load_env
import os
ok = True
def row(name, good, fix=""):
    global ok
    ok &= good
    print(f"[{'OK' if good else 'MISSING'}] {name}" + ("" if good else f"  ->  {fix}"))
row(f"Python {sys.version.split()[0]}", sys.version_info >= (3, 9), "install Python 3.10+ from python.org (tick 'Add to PATH')")
for prog, fix in [("ffmpeg", "winget install Gyan.FFmpeg"), ("ffprobe", "comes with ffmpeg"), ("node", "winget install OpenJS.NodeJS.LTS"),
                  ("npx", "comes with Node"), ("yt-dlp", "winget install yt-dlp.yt-dlp  (or: pip install yt-dlp)")]:
    row(prog, bool(shutil.which(prog) or shutil.which(prog + ".cmd") or shutil.which(prog + ".exe")), fix)
for mod, pipn in [("requests", "requests"), ("PIL", "pillow"), ("numpy", "numpy"), ("cv2", "opencv-python")]:
    try: importlib.import_module(mod); row(f"python: {pipn}", True)
    except Exception: row(f"python: {pipn}", False, f"pip install {pipn}")
root = repo_root(); load_env()
row("font fonts/HelveticaNeue-Bold.ttf", (root / "fonts/HelveticaNeue-Bold.ttf").exists(), "put your HelveticaNeue-Bold.ttf in the fonts folder (README, Fonts)")
row(".env with ELEVENLABS_API_KEY", bool(os.environ.get("ELEVENLABS_API_KEY")), "copy .env.example to .env and fill it")
row(".env with ELEVENLABS_VOICE_ID", bool(os.environ.get("ELEVENLABS_VOICE_ID")), "Sanchit's voice id from ElevenLabs")
row("opencli (optional, Pinterest search only)", bool(shutil.which("opencli") or shutil.which("opencli.cmd")), "optional: npm i -g @jackwener/opencli + its Chrome extension")
print("\nAll set." if ok else "\nFix the MISSING lines above (opencli is optional).")
