#!/usr/bin/env python3
"""Step 2. raw.mp3 + raw-words.json -> final.wav + words.json.
Cuts filler words and squeezes long pauses; words.json is re-timed to the new audio (no re-alignment needed).
usage: python chop.py projects/<name> [--max-gap 0.35] [--keep-gap 0.15] [--fillers um,uh,erm,hmm,ah]"""
import argparse, re
from common import project, jload, jsave, ff, duration

ap = argparse.ArgumentParser(); ap.add_argument("project")
ap.add_argument("--max-gap", type=float, default=0.35); ap.add_argument("--keep-gap", type=float, default=0.15)
ap.add_argument("--fillers", default="um,uh,erm,hmm,ah,uhh,umm")
a = ap.parse_args()
P = project(a.project)
src = P / "raw.mp3"; words = jload(P / "raw-words.json")
FILL = set(a.fillers.split(","))
keep = [w for w in words if re.sub(r"[^\w]", "", w["w"].lower()) not in FILL]
total = duration(src)
# speech islands: merge words whose gap is short; pad each island a little so consonants aren't clipped
PAD = 0.04
isl = []
for w in keep:
    s, e = max(0, w["s"] - PAD), min(total, w["e"] + PAD)
    if isl and s - isl[-1][1] <= a.max_gap:
        isl[-1][1] = e; isl[-1][2].append(w)
    else:
        isl.append([s, e, [w]])
# rebuild: islands joined with keep-gap silence, words re-timed
segs, out, t = [], [], 0.0
for i, (s, e, ws) in enumerate(isl):
    if i: t += a.keep_gap
    for w in ws:
        out.append(dict(w=w["w"], s=round(t + (w["s"] - s), 3), e=round(t + (w["e"] - s), 3)))
    segs.append((s, e, t)); t += e - s
parts, labels = [], []
for i, (s, e, _) in enumerate(segs):
    parts.append(f"[0]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={max(0, e - s - 0.015):.3f}:d=0.015[a{i}]")
    labels.append(f"[a{i}]")
    if i < len(segs) - 1:
        parts.append(f"anullsrc=r=44100:cl=mono,atrim=0:{a.keep_gap}[g{i}]"); labels.append(f"[g{i}]")
fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1,aformat=channel_layouts=mono[o]"
ff("-i", src, "-filter_complex", fc, "-map", "[o]", "-ar", "48000", "-ac", "2", P / "final.wav")
jsave(P / "words.json", out)
print(f"final.wav {duration(P / 'final.wav'):.2f} s (was {total:.2f} s), cut {len(words) - len(keep)} fillers, {len(isl)} speech blocks")
