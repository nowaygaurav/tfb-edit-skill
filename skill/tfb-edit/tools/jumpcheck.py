#!/usr/bin/env python3
"""jumpcheck.py: frame-by-frame check for slivers: one or a few frames of a shot squeezed between two cuts
(his rule 2026-11-07: a layout switch 1 frame off a chop cut shows one stray frame, which reads as a sloppy edit).
  python3 jumpcheck.py cuts <video>            -> list hard cuts (frame, time) as JSON (used on raw.mp4 for snapping)
  python3 jumpcheck.py check <video> [maxf=5]  -> every cut pair closer than maxf frames = SLIVER (exit 1 if any)
Cut = a frame whose difference from the previous frame jumps far above the local motion level."""
import sys, json, subprocess, numpy as np

def diffs(path, w=64, h=114):
    fps = eval(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", path],
                              capture_output=True, text=True).stdout.strip())
    # a --fps 60 render of 30 fps footage shows every footage frame twice, which reads as a "sliver" pair everywhere
    # (2026-11-11: 26 false slivers). Check on the footage's own 30 fps grid; animations still switch on those frames.
    vf = f"fps=30,scale={w}:{h},format=gray" if fps > 30 else f"scale={w}:{h},format=gray"
    fps = min(fps, 30)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", vf, "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.int16)
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))          # d[i] = change from frame i to i+1
    return np.concatenate([[0.0], d]), fps

def cuts(path, k=3.5, floor=4.0):
    d, fps = diffs(path); out = []
    for i in range(1, len(d)):
        lo, hi = max(1, i - 8), min(len(d), i + 9)
        local = np.median(np.concatenate([d[lo:i], d[i + 1:hi]])) if hi - lo > 2 else 0
        if d[i] > max(floor, k * local + 1.5): out.append(dict(frame=i, t=round(i / fps, 3), score=round(float(d[i]), 1)))
    return out, fps

def cadence(path, w=270, h=480, thr=0.6):
    """Print one row per second: M = the picture changed from the previous frame, . = held. Read at the file's own fps.
    Footage at 30 fps in a 60 fps render = even .M.M; a page that only moves every 3rd-4th frame (...M...M) = JITTER
    unless it is a stepped move on purpose (flickerStack, lensStream). Run after every render (his rule 2026-11-11)."""
    fps = eval(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", path],
                              capture_output=True, text=True).stdout.strip())
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.int16)
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2)); n = int(round(fps))
    for s0 in range(0, len(d), n):
        row = "".join("M" if x > thr else "." for x in d[s0:s0 + n])
        held = max((len(r) for r in row.split("M")), default=0)
        print(f"{s0 / fps:6.2f}s {row}{'   <- holds ' + str(held) + ' frames' if held >= 3 else ''}")


if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "cadence":
    cadence(sys.argv[2]); sys.exit(0)
if __name__ == "__main__":
    mode, path = sys.argv[1], sys.argv[2]
    cs, fps = cuts(path)
    if mode == "cuts":
        print(json.dumps(cs)); sys.exit(0)
    maxf = int(sys.argv[3]) if len(sys.argv) > 3 else 5; bad = []
    for a, b in zip(cs, cs[1:]):
        if b["frame"] - a["frame"] < maxf: bad.append((a, b))
    for a, b in bad:
        print(f"SLIVER {b['frame']-a['frame']} frame(s) at {a['t']:.3f}s -> {b['t']:.3f}s (scores {a['score']}, {b['score']})")
    print(f"{len(cs)} cuts, {len(bad)} slivers in {path}")
    sys.exit(1 if bad else 0)
