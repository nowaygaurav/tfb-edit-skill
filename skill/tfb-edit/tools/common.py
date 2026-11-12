"""Shared helpers for the TFB edit tools (Windows + Mac). Standard library + requests only."""
import json, os, re, shutil, subprocess, sys, pathlib

SKILL = pathlib.Path(__file__).resolve().parent.parent          # .../skill/tfb-edit


def repo_root():
    """The repo root holds .env and fonts/. Walk up from cwd, then from the skill folder."""
    for start in (pathlib.Path.cwd(), SKILL):
        for p in [start, *start.parents]:
            if (p / ".env").exists() or (p / ".env.example").exists():
                return p
    return pathlib.Path.cwd()


def load_env():
    env = repo_root() / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def need(key):
    load_env()
    v = os.environ.get(key)
    if not v:
        sys.exit(f"{key} is missing. Put it in {repo_root() / '.env'} (see .env.example).")
    return v


def exe(name):
    """Find a program on PATH (handles npx.cmd on Windows)."""
    p = shutil.which(name) or shutil.which(name + ".cmd") or shutil.which(name + ".exe")
    if not p:
        sys.exit(f"'{name}' was not found. Install it (README, Setup) and open a new terminal.")
    return p


def run(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def ff(*args):
    run([exe("ffmpeg"), "-v", "error", "-y", *args])


def duration(path):
    out = subprocess.run([exe("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def project(arg):
    p = pathlib.Path(arg).resolve()
    if not p.is_dir():
        sys.exit(f"Project folder not found: {p}")
    return p


def jload(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def jsave(p, data):
    pathlib.Path(p).write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


# ---------- words + captions ----------
def spoken(word):
    """Caption text for one word: his exact word, no punctuation except apostrophes; 5.7 -> 5 point 7, 1,000 -> 1000."""
    w = word.strip()
    w = re.sub(r"(?<=\d),(?=\d{3})", "", w)
    w = re.sub(r"(\d)\.(\d)", r"\1 point \2", w)
    w = re.sub(r"[^\w'₹ ]", "", w)
    return w.strip()


def chunk_captions(words, max_words=4, max_chars=20, hard_chars=26, gap=0.35):
    """words: [{w,s,e}] -> [{text,s,e,off}] in 2-4 word chunks; never leaves one word alone."""
    merged = []   # "1" + ",000" -> "1,000"; "5" + ".7" -> "5.7" (some transcribers split numbers)
    for w in words:
        if merged and re.fullmatch(r"[.,]\d+[.,!?]?", w["w"].strip()) and re.search(r"\d$", merged[-1]["w"]):
            merged[-1] = dict(w=merged[-1]["w"] + w["w"].strip(), s=merged[-1]["s"], e=w["e"])
        else:
            merged.append(dict(w))
    toks = []
    for w in merged:
        t = spoken(w["w"])
        if not t:
            continue
        end = bool(re.search(r"[.,!?;:]$", w["w"].strip()))
        toks.append(dict(t=t, s=w["s"], e=w["e"], end=end))
    for t in toks:
        if t["t"] not in ("I", "I'll", "I'm", "SIP", "KID"):
            t["t"] = t["t"].lower() if not t["t"].isupper() or len(t["t"]) < 2 else t["t"]
    caps, cur = [], []
    for i, t in enumerate(toks):
        cur.append(t)
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        nn = toks[i + 2] if i + 2 < len(toks) else None
        text = " ".join(x["t"] for x in cur)
        orphan = nxt and (nxt["end"] or not nn) and len(text + " " + nxt["t"]) <= 28
        if not nxt or t["end"] or nxt["s"] - t["e"] > gap or (
                not orphan and (len(cur) >= max_words or len(text) >= max_chars or len(text + " " + nxt["t"]) > hard_chars)):
            caps.append(dict(text=text, s=cur[0]["s"], e=t["e"]))
            cur = []
    for i, c in enumerate(caps):
        c["off"] = min(caps[i + 1]["s"], c["e"] + 0.5) if i + 1 < len(caps) else c["e"] + 0.4
    return caps


def words_in(words, a, b):
    return " ".join(w["w"] for w in words if a - 0.01 <= w["s"] < b)
