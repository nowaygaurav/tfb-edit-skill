#!/usr/bin/env python3
"""Safe-zone check on real render frames (his MANDATORY rule: content inside x 65–1015, y 270–1250, nothing at x>850 below y 1150).
Usage: ~/rembg-env/bin/python safecheck.py <video.mp4> <t1> <t2> ...   (exit 1 if any frame breaks it)
Content = anything that stands out from its own smoothed background (photos, text, labels), so paper vignettes,
grain, 1-px edge marks and the frame border don't count. For frames where he is on screen use it only on graphics-only moments."""
import sys, subprocess, numpy as np, cv2

def content_box(path, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    g = np.frombuffer(raw, np.uint8).reshape(1920, 1080).astype(np.float32)
    bg = cv2.GaussianBlur(g, (0, 0), 40)
    m = (np.abs(g - bg) > 28).astype(np.uint8)
    m[:12, :] = m[-12:, :] = 0; m[:, :12] = m[:, -12:] = 0          # frame border (filters, fringes)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))   # drops 1-px marks, grain
    m = cv2.dilate(m, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 400]
    if not keep: return None, 0
    xs0 = min(st[i, 0] for i in keep); ys0 = min(st[i, 1] for i in keep)
    xs1 = max(st[i, 0] + st[i, 2] for i in keep) - 5; ys1 = max(st[i, 1] + st[i, 3] for i in keep) - 5
    nogo = int(sum(((lab == i)[1150:1250, 850:]).sum() for i in keep))
    return (xs0 + 4, ys0 + 4, xs1, ys1), nogo

bad = 0
for t in sys.argv[2:]:
    box, nogo = content_box(sys.argv[1], float(t))
    if box is None: print(f"t={t}: no content"); continue
    x0, y0, x1, y1 = box
    ok = x0 >= 65 and x1 <= 1015 and y0 >= 270 and y1 <= 1250 and nogo == 0
    bad += not ok
    print(f"t={t}: content x {x0}–{x1}, y {y0}–{y1}, no-go px {nogo} → {'OK' if ok else 'OUTSIDE SAFE ZONE'}")
sys.exit(1 if bad else 0)
