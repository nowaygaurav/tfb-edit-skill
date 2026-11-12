#!/usr/bin/env python3
"""Real images (and video pins) from Pinterest.
  python pinterest.py <pin url> [<pin url> ...] --out projects/<name>/photos [--names g0,g1,...]
  python pinterest.py --search "indian parents holding newborn" --out projects/<name>/photos/_search [--n 8]
Pin URLs: images come from the pin's original-size image, video pins via yt-dlp. --search needs OpenCLI + Chrome logged in to Pinterest (README)."""
import argparse, json, pathlib, re, subprocess, shutil, sys
import requests
from common import exe

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
ap = argparse.ArgumentParser(); ap.add_argument("pins", nargs="*"); ap.add_argument("--out", required=True)
ap.add_argument("--names"); ap.add_argument("--search"); ap.add_argument("--n", type=int, default=8)
a = ap.parse_args()
out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)

def get_image(url, dest):
    r = requests.get(url, headers=UA, timeout=30); r.raise_for_status(); dest.write_bytes(r.content)

if a.search:
    oc = shutil.which("opencli") or shutil.which("opencli.cmd")
    if not oc:
        sys.exit("--search needs OpenCLI (README, Pinterest search). Without it, open Pinterest, copy pin links and pass them here.")
    raw = subprocess.run([oc, "pinterest", "search-pins", a.search, "-f", "json"], capture_output=True, text=True, encoding="utf-8").stdout
    pins, _ = json.JSONDecoder().raw_decode(raw[raw.index("["):])
    n = 0
    for p in pins:
        u = p.get("imageUrl", "")
        if not u or u.endswith(".gif"): continue
        try: get_image(u, out / f"s{n:02d}.jpg"); n += 1
        except Exception: continue
        if n == a.n: break
    print(f"{n} images in {out} (pick the right one, rename it to the plan's file name)")
    sys.exit(0)

names = a.names.split(",") if a.names else []
for i, pin in enumerate(a.pins):
    name = names[i] if i < len(names) else f"pin{i:02d}"
    page = requests.get(pin, headers=UA, timeout=30).text
    m = re.search(r'"(https://i\.pinimg\.com/originals/[^"]+\.(?:jpg|jpeg|png|webp))"', page) or re.search(r'<meta property="og:image" content="([^"]+)"', page)
    if '"video_list"' in page or ".m3u8" in page:
        subprocess.run([exe("yt-dlp"), "-q", "-o", str(out / f"{name}.%(ext)s"), pin], check=False)
        print("video pin ->", name); continue
    if not m:
        print("no image found on", pin); continue
    ext = m.group(1).rsplit(".", 1)[-1].split("?")[0]
    get_image(m.group(1), out / f"{name}.{ext if ext != 'jpeg' else 'jpg'}")
    print("image ->", out / f"{name}.{ext}")
