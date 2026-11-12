#!/usr/bin/env python3
"""B-roll / reference clips: download (or take a local file), trim, crop to the slot.
  python clip.py <url or file> --from 1:23.5 --to 1:25.0 --out projects/<name>/broll/broll-3.mp4 [--fit full|top] [--x 0.5]
--fit full = 1080x1920 (full screen), top = 1080x960 (split-screen top half). --x = horizontal focus 0..1 for the crop.
Audio is removed (the voiceover carries the reel)."""
import argparse, pathlib, re, subprocess, tempfile
from common import exe, ff

def secs(t):
    p = [float(x) for x in re.split(r"[:]", str(t))]
    return sum(v * 60 ** i for i, v in enumerate(reversed(p)))

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("--from", dest="a", required=True); ap.add_argument("--to", dest="b", required=True)
ap.add_argument("--out", required=True); ap.add_argument("--fit", choices=["full", "top"], default="full"); ap.add_argument("--x", type=float, default=0.5)
A = ap.parse_args()
a, b = secs(A.a), secs(A.b); out = pathlib.Path(A.out); out.parent.mkdir(parents=True, exist_ok=True)
W, H = (1080, 1920) if A.fit == "full" else (1080, 960)
src = A.src
with tempfile.TemporaryDirectory() as td:
    if re.match(r"https?://", src):
        tmp = pathlib.Path(td) / "dl.%(ext)s"
        lead = min(1.0, a)
        subprocess.run([exe("yt-dlp"), "-q", "--download-sections", f"*{a - lead:.2f}-{b + 1:.2f}", "-f", "bv*[height<=1080]+ba/b",
                        "--merge-output-format", "mp4", "-o", str(tmp), src], check=True)
        src = str(next(pathlib.Path(td).glob("dl.*"))); a, b = lead, lead + (b - a)
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}:(iw-{W})*{A.x}:(ih-{H})/2,fps=30,setsar=1")
    ff("-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", src, "-vf", vf, "-an", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", out)
print(f"{out} ({b - a:.2f} s, {W}x{H})")
