#!/usr/bin/env python3
"""Step 6. plan.json + final.wav + words.json (+ broll/ avatar/ photos/ resource/) -> HyperFrames composition -> render -> SFX -> vN.mp4 -> checks.
usage: python build.py projects/<name> [--no-render] [--version N]
Missing media renders as a labelled placeholder, so a draft never blocks on assets."""
import argparse, html, os, platform, re, shutil, subprocess, sys
from common import SKILL, repo_root, project, jload, jsave, ff, exe, duration, chunk_captions, spoken

ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("--no-render", action="store_true"); ap.add_argument("--version", type=int)
A = ap.parse_args()
P = project(A.project)
plan = jload(P / "plan.json"); words = jload(P / "words.json")
HF = P / "hf"; AS = HF / "assets"; (AS / "m").mkdir(parents=True, exist_ok=True)
for f in ("package.json", "hyperframes.json"):
    shutil.copy(SKILL / "templates/hf" / f, HF / f)
shutil.copy(SKILL / "templates/hf/assets/gsap.min.js", AS / "gsap.min.js")
FONT = repo_root() / "fonts/HelveticaNeue-Bold.ttf"
if not FONT.exists():
    sys.exit(f"Font missing: put HelveticaNeue-Bold.ttf in {FONT.parent} (README, Fonts). The style needs exactly this font.")
shutil.copy(FONT, AS / "HelveticaNeue-Bold.ttf")
shutil.copy(P / plan.get("audio", "final.wav"), AS / "voice.wav")
DUR = round(duration(P / plan.get("audio", "final.wav")) + 0.05, 2)
INK, G, G2, NEON, MUTE, LINE = "#1A1F1C", "#2F6B55", "#4A9C7A", "#5BE39A", "#8A908A", "#1F2A24"
esc = lambda s: html.escape(str(s))

def media(rel, sid, w, h, kind="video"):
    """Copy a media file into assets; return its src or None if it isn't there yet."""
    if not rel: return None
    src = P / rel
    if not src.exists(): return None
    if kind == "img":
        try:
            from PIL import Image, ImageOps
            out = AS / "m" / f"{sid}.jpg"
            ImageOps.fit(Image.open(src).convert("RGB"), (w, h), centering=(0.5, 0.35)).save(out, quality=88)
            return f"assets/m/{sid}.jpg"
        except Exception as e:
            print("photo skipped:", rel, e); return None
    out = AS / "m" / f"{sid}{src.suffix.lower()}"; shutil.copy(src, out); return f"assets/m/{out.name}"

css = f"""@font-face{{font-family:HN;src:url(assets/HelveticaNeue-Bold.ttf)}}
*{{margin:0;padding:0;box-sizing:border-box}} html,body{{width:1080px;height:1920px;overflow:hidden}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;font-family:HN;color:{INK};background:radial-gradient(ellipse 70% 55% at 50% 42%,#FCFCFA 0%,#F4F5F2 55%,#E6E8E4 100%)}}
#grid{{position:absolute;inset:0;background-image:radial-gradient(circle,#D5D9D3 3px,transparent 3.5px);background-size:80px 80px;background-position:20px 20px;opacity:.9}}
.abs{{position:absolute}} .sc{{position:absolute;inset:0;visibility:hidden}}
.cap{{position:absolute;left:540px;transform:translateX(-50%);font-size:64px;letter-spacing:-1px;white-space:nowrap;visibility:hidden;z-index:40}}
.ph{{position:absolute;background:#26302B;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;gap:16px;color:#E8ECE9;text-align:center;padding:560px 110px 0}}
.ph .k{{font-size:28px;letter-spacing:8px;color:{NEON}}} .ph .f{{font-size:54px}} .ph .d{{font-size:32px;color:#AEB8B2;line-height:1.35}} .ph .n{{font-size:26px;color:#7F8B85}}
.avp{{position:absolute;background:rgba(255,255,255,.6);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;color:{MUTE}}}
.fill{{position:absolute;object-fit:cover}}
.card{{position:absolute;background:#fff;padding:14px;border-radius:26px;box-shadow:0 22px 50px rgba(31,42,36,.18)}} .card img,.card .pimg{{display:block;border-radius:16px;width:560px;height:700px;object-fit:cover}}
.pimg{{background:#E3E6E1;display:flex;align-items:center;justify-content:center;color:{MUTE};font-size:26px;text-align:center;padding:30px}}
.bar{{position:absolute;width:120px;height:500px;border-radius:18px 18px 0 0;background:linear-gradient(180deg,{G2},{G});transform-origin:50% 100%}}
.ava{{position:absolute;width:104px;height:104px;border-radius:50%;border:6px solid #fff;box-shadow:0 8px 18px rgba(31,42,36,.2);overflow:hidden;background:#E3E6E1}} .ava img{{width:100%;height:100%;display:block;object-fit:cover}}
.val{{position:absolute;font-size:46px;transform:translateX(-50%);white-space:nowrap}}
.lab{{position:absolute;font-size:36px;color:#4E554F;transform:translateX(-50%);white-space:nowrap}}"""
h = [f'<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920"><div id="grid"></div>',
     f'<audio id="voice" src="assets/voice.wav" data-start="0" data-duration="{DUR}" data-track-index="10" data-volume="1"></audio>']
js = ["const tl=gsap.timeline({paused:true});", "const V=(s,t)=>tl.set(s,{visibility:'visible'},t),H=(s,t)=>tl.set(s,{visibility:'hidden'},t);",
      "const POP=(s,t,to=1)=>tl.fromTo(s,{opacity:0,scale:to*.6},{opacity:1,scale:to,duration:.32,ease:'back.out(2.2)',immediateRender:false},t);",
      "const IN=(s,t)=>tl.fromTo(s,{opacity:0,y:16},{opacity:1,y:0,duration:.22,ease:'power3.out',immediateRender:false},t);"]
Z = {"photo_growth": 1, "chart": 1, "compare": 1, "resource": 1, "broll": 3, "host_full": 4, "split_hook": 5}
segs = sorted(plan["segments"], key=lambda s: (Z.get(s["type"], 1), s["start"]))
track = [20]
def vid(src, sid, a, b, box):
    track[0] += 1
    return (f'<video id="v{sid}" class="fill" src="{src}" muted playsinline data-start="{a}" data-duration="{round(b - a, 3)}" '
            f'data-track-index="{track[0]}" style="{box}"></video>')
def placeholder(sid, label, s, box, pad=None):
    b = s.get("broll", {})
    st = box + (f";padding-top:{pad}px" if pad is not None else "")
    return (f'<div class="ph" style="{st}"><div class="k">{esc(label)}</div><div class="f">{esc(b.get("film", ""))}</div>'
            f'<div class="d">{esc(b.get("scene", ""))}</div><div class="n">{s["end"] - s["start"]:.1f} s · drop {esc(b.get("file", ""))}</div></div>')
def avatar_ph(box, label):
    return f'<div class="avp" style="{box}"><div style="font-size:28px;letter-spacing:6px">{esc(label)}</div><div style="font-size:56px;color:{INK}">Sanchit</div></div>'
def word_time(token, after, fallback):
    for w in words:
        if w["s"] >= after - 0.02 and spoken(w["w"]).lower() == spoken(token).lower():
            return w["s"]
    return fallback

sfx_auto = []
for s in segs:
    sid, a, b, T = s["id"], s["start"], s["end"], s["type"]
    h.append(f'<div id="{sid}" class="sc" style="z-index:{Z.get(T, 1) * 10}">')
    # visible in [a,b] minus every window covered by a higher layer (moving a b-roll's in/out keeps this right)
    cov = sorted((max(a, o["start"]), min(b, o["end"])) for o in segs if Z.get(o["type"], 1) > Z.get(T, 1) and o["start"] < b and o["end"] > a)
    vis, cur = [], a
    for c0, c1 in cov:
        if c0 > cur + 1e-3: vis.append((cur, c0))
        cur = max(cur, c1)
    if cur < b - 1e-3: vis.append((cur, b))
    for v0, v1 in vis:
        js.append(f"V('#{sid}',{v0:.3f});" + (f"H('#{sid}',{v1:.3f});" if v1 < DUR else ""))
    if T == "broll":
        src = media(s["broll"].get("file"), sid, 0, 0)
        h.append(vid(src, sid, a, b, "left:0;top:0;width:1080px;height:1920px") if src else
                 placeholder(sid, f"B-ROLL · {sid}", s, "left:0;top:0;width:1080px;height:1920px"))
    elif T == "host_full":
        src = media(s.get("avatar"), sid, 0, 0)
        h.append(vid(src, sid, a, b, "left:0;top:0;width:1080px;height:1920px;object-position:50% 30%") if src else
                 avatar_ph("left:0;top:0;width:1080px;height:1920px", "AI AVATAR · FULL SCREEN"))
    elif T == "split_hook":
        src = media(s["broll"].get("file"), sid + "t", 0, 0)
        h.append(vid(src, sid + "t", a, b, "left:0;top:0;width:1080px;height:960px") if src else
                 placeholder(sid, "B-ROLL · TOP HALF", s, "left:0;top:0;width:1080px;height:960px", pad=120))
        av = media(s.get("avatar"), sid + "b", 0, 0)
        h.append(vid(av, sid + "b", a, b, "left:0;top:960px;width:1080px;height:960px;object-position:50% 25%") if av else
                 avatar_ph("left:0;top:960px;width:1080px;height:960px;border-top:5px dashed #B9BDB7", "AI AVATAR · BOTTOM HALF"))
        hk = s["hook"]; toks = hk["small"].split(); t = a
        h.append('<div class="abs" style="left:540px;top:760px;transform:translateX(-50%);white-space:nowrap;font-size:50px;color:#fff;text-shadow:0 4px 18px rgba(0,0,0,.55)" id="'
                 + sid + 'l1">' + " ".join(f'<span id="{sid}w{i}" style="opacity:0">{esc(w)}</span>' for i, w in enumerate(toks)) + "</div>")
        for i, w in enumerate(toks):
            t = word_time(w, t, a + i * 0.25); js.append(f"IN('#{sid}w{i}',{t:.3f});"); t += 0.05
        ta = word_time(hk["accent"], a, a + 1.5) - 0.06
        h.append(f'<div id="{sid}acc" class="abs" style="left:540px;top:850px;transform:translateX(-50%);font-size:230px;line-height:1;color:{NEON};text-shadow:0 0 40px rgba(91,227,154,.45),0 8px 26px rgba(0,0,0,.35);opacity:0;white-space:nowrap">{esc(hk["accent"])}</div>')
        js.append(f"POP('#{sid}acc',{ta:.3f});")
        if hk.get("strike_at"):
            sa = hk["strike_at"]; wpx = 140 * len(hk["accent"]) + 10
            h.append(f'<div id="{sid}st" class="abs" style="left:{540 - wpx // 2}px;top:955px;width:{wpx}px;height:16px;background:{INK};border-radius:8px;transform-origin:0 50%;box-shadow:0 0 0 4px #fff"></div>')
            js.append(f"tl.set('#{sid}st',{{scaleX:0}},0);tl.to('#{sid}st',{{scaleX:1,duration:.3,ease:'power2.inOut'}},{sa});tl.to('#{sid}l1',{{opacity:.35,duration:.25}},{sa});tl.to('#{sid}acc',{{opacity:.5,duration:.3}},{sa});")
        if hk.get("after"):
            h.append(f'<div id="{sid}af" class="abs" style="left:540px;top:1125px;transform:translateX(-50%);white-space:nowrap;font-size:54px;color:{INK};opacity:0">{esc(hk["after"])}</div>')
            js.append(f"IN('#{sid}af',{hk.get('strike_at', ta + .4) + .06:.3f});")
    elif T == "photo_growth":
        ph = s["photos"]; n = len(ph); span = (b - a) * 0.76
        for i, p in enumerate(ph):
            src = media(p.get("file"), f"{sid}p{i}", 560, 700, "img"); rot = [-3, 2, -2, 3, -1][i % 5]
            inner = f'<img src="{src}">' if src else f'<div class="pimg">photo · {esc(p.get("query", p.get("file", "")))}</div>'
            h.append(f'<div id="{sid}c{i}" class="card" style="left:252px;top:300px;opacity:0;transform:rotate({rot}deg)">{inner}</div>')
            t = a + span * i / max(n - 1, 1) * 0.92
            if i == 0: js.append(f"tl.set('#{sid}c0',{{opacity:1}},{a});")
            else:
                js.append(f"tl.fromTo('#{sid}c{i}',{{opacity:0,y:40}},{{opacity:1,y:0,duration:.28,ease:'power3.out',immediateRender:false}},{t:.3f});")
                js.append(f"tl.set('#{sid}c{i - 1}',{{opacity:0}},{t + .3:.3f});")
        h.append(f'<div id="{sid}age" class="abs" style="left:540px;top:930px;transform:translateX(-50%);font-size:54px;background:#fff;border-radius:40px;padding:6px 34px;box-shadow:0 10px 24px rgba(31,42,36,.15);z-index:5">age {s.get("age_from", 0)}</div>')
        a0, a1 = s.get("age_from", 0), s.get("age_to", 21)
        for k in range(a1 - a0 + 1):
            t = a + span * k / max(a1 - a0, 1)
            js.append(f"tl.set('#{sid}age',{{textContent:'age {a0 + k}'}},{t:.3f});tl.fromTo('#{sid}age',{{scale:1.15}},{{scale:1,duration:.12,immediateRender:false}},{t:.3f});")
        js.append(f"tl.to('#{sid}c{n - 1}',{{scale:.8,opacity:0,duration:.4,ease:'sine.inOut'}},{b - .43:.3f});tl.to('#{sid}age',{{opacity:0,duration:.2}},{b - .43:.3f});")
    elif T in ("chart", "compare"):
        bars = s["bars"]; nb = len(bars); BASE, HMAX = 960, 500
        xs = [200, 420, 640, 860] if nb == 4 else [380, 700] if nb == 2 else [round(160 + i * 760 / max(nb - 1, 1)) for i in range(nb)]
        h.append(f'<div class="abs" style="left:{xs[0] - 100}px;top:{BASE}px;width:{xs[-1] - xs[0] + 200}px;height:4px;background:#C9CDC7;border-radius:2px"></div>')
        seen = 0.0
        for i, bar in enumerate(bars):
            cx = xs[i]; ph = bar.get("photo", {}); src = media(ph.get("file"), f"{sid}a{i}", 200, 200, "img")
            img = f'<img src="{src}">' if src else ""
            h.append(f'<div id="{sid}b{i}" class="bar" style="left:{cx - 60}px;top:{BASE - HMAX}px"></div>'
                     f'<div id="{sid}t{i}" class="abs" style="left:0;top:{BASE}px;width:1080px;height:0"><div class="ava" style="left:{cx - 52}px;top:-104px">{img}</div>'
                     f'<div id="{sid}v{i}" class="val" style="left:{cx}px;top:-170px"></div></div>'
                     f'<div id="{sid}l{i}" class="lab" style="left:{cx}px;top:{BASE + 16}px;opacity:0">{esc(bar["label"])}</div>')
            js.append(f"tl.set('#{sid}b{i}',{{scaleY:0}},0);tl.set('#{sid}t{i}',{{opacity:0,y:0}},0);")
        M = max(b_["value"] for b_ in bars) if T == "compare" else None
        for i, bar in enumerate(bars):
            v, g = bar["value"], bar["grow"]; dec = 2 if round(v, 1) != v else 1; unit = bar.get("unit", "")
            app = bar.get("appear", bar.get("label_at", a + .05))
            js.append(f"tl.to('#{sid}l{i}',{{opacity:1,duration:.25}},{max(a, app) + .05:.2f});")
            Mi = M or max(bb["value"] for bb in bars[:i + 1])
            if T == "chart" and i:   # rescale earlier bars to the new max, older ones step back
                for j in range(i):
                    vj = bars[j]["value"]
                    js.append(f"tl.to('#{sid}b{j}',{{scaleY:{vj / Mi:.4f},duration:.6,ease:'power3.inOut'}},{app + .1:.2f});tl.to('#{sid}t{j}',{{y:{-HMAX * vj / Mi:.1f},duration:.6,ease:'power3.inOut'}},{app + .1:.2f});")
                js.append(f"tl.to([{','.join(repr(f'#{sid}b{j}') for j in range(i))}],{{opacity:.45,duration:.3}},{app:.2f});")
            d = 1.1 if T == "chart" else .85
            js.append(f"tl.set('#{sid}t{i}',{{opacity:1}},{g:.2f});tl.to('#{sid}b{i}',{{scaleY:{v / Mi:.4f},duration:{d},ease:'power2.out'}},{g:.2f});tl.to('#{sid}t{i}',{{y:{-HMAX * v / Mi:.1f},duration:{d},ease:'power2.out'}},{g:.2f});")
            js.append(f"const o{sid}{i}={{v:0}};tl.to(o{sid}{i},{{v:{v},duration:{d},ease:'power2.out',onUpdate:()=>{{document.getElementById('{sid}v{i}').textContent='₹'+o{sid}{i}.v.toFixed({dec})+'{unit}'}}}},{g:.2f});")
            nxt = bars[i + 1].get("appear", bars[i + 1]["grow"]) if i + 1 < nb else b
            if nxt - (g + d) > 1.2:   # a long hold needs motion
                js.append(f"tl.fromTo('#{sid}v{i}',{{scale:1}},{{scale:1.12,duration:.25,yoyo:true,repeat:1,ease:'sine.inOut'}},{g + d + .15:.2f});")
            if T == "chart": sfx_auto.append((g + d - .05, "coin_small"))
        if T == "chart":
            js.append(f"tl.to([{','.join(repr(f'#{sid}b{j}') for j in range(nb))}],{{opacity:1,duration:.3}},{b - .26:.2f});")
        if s.get("dim_first_at"):
            js.append(f"tl.to(['#{sid}b0','#{sid}t0'],{{opacity:.4,duration:.35}},{s['dim_first_at']});")
    elif T == "resource":
        src = media(s.get("file"), sid, 0, 0)
        h.append(f'<div id="{sid}card" class="abs" style="left:110px;top:330px;width:860px;height:660px;background:#fff;border-radius:34px;box-shadow:0 24px 50px rgba(31,42,36,.14);border:3px solid #E3E6E1;overflow:hidden">')
        if src:
            h.append(vid(src, sid, a, b, "left:0;top:0;width:860px;height:660px;object-fit:contain;background:#fff"))
        else:
            cols = s.get("columns", []); cw = 800 // max(len(cols), 1)
            h.append('<div class="abs" style="left:0;top:0;width:860px;height:96px;background:#F1F4F0;border-bottom:3px solid #E3E6E1"></div>')
            for c, name in enumerate(cols):
                x = 30 + c * cw
                h.append(f'<div id="{sid}h{c}" class="abs" style="left:{x}px;top:22px;width:{cw - 14}px;height:52px;border-radius:12px;font-size:32px;line-height:52px;text-align:center;color:#5F655F">{esc(name)}</div>')
                for r in range(4):
                    h.append(f'<div class="abs" style="left:{x + 12}px;top:{140 + r * 92}px;width:{cw - 38}px;height:24px;border-radius:12px;background:#EDF0EC"></div>')
            h.append(f'<div class="abs" style="left:0;top:560px;width:860px;text-align:center;font-size:26px;color:{MUTE};letter-spacing:4px">RESOURCE · DROP {esc(s.get("file", ""))}</div>')
            for c, t in s.get("marks", []):
                hl = "#E4EFE9" if c < 2 else G; fg = INK if c < 2 else "#fff"
                js.append(f"tl.to('#{sid}h{c}',{{background:'{hl}',color:'{fg}',duration:.2}},{t});tl.fromTo('#{sid}h{c}',{{scale:1.2}},{{scale:1,duration:.3,ease:'back.out(2)',immediateRender:false}},{t});")
        h.append("</div>")
        js.append(f"tl.fromTo('#{sid}card',{{opacity:0,y:60}},{{opacity:1,y:0,duration:.45,ease:'power3.out',immediateRender:false}},{a + .02:.2f});")
    h.append("</div>")

kw = plan.get("keyword")
if kw:
    h.append(f'<div id="kw" class="abs" style="left:540px;top:1166px;transform:translateX(-50%);font-size:52px;height:72px;line-height:74px;color:#fff;background:{G};border-radius:16px;padding:0 26px;visibility:hidden;z-index:60">{esc(kw["text"])}</div>')
    js.append(f"V('#kw',{kw['from']});POP('#kw',{kw['from']});")

# ---- captions: exact words, one fixed home per case; dropped in the hook and where a visible chart number says the same thing
def top_seg(t):
    c = [s for s in segs if s["start"] - .01 <= t < s["end"]]
    return max(c, key=lambda s: Z.get(s["type"], 1)) if c else None
def chart_drop(c, s):
    if s["type"] not in ("chart", "compare"): return False
    for bar in s["bars"]:
        if bar.get("appear", s["start"]) - .3 > c["s"]: continue
        forms = {spoken(str(bar["value"])), str(bar["value"])}
        if "₹" in bar["label"]: forms.add(re.sub(r"\D", "", bar["label"]))
        if any(re.search(rf"(^| ){re.escape(f)}( |$)", c["text"]) for f in forms if f): return True
    return False
drops = set(plan.get("caption_drop", []))
for i, c in enumerate(chunk_captions(words)):
    s = top_seg(c["s"]); typ = s["type"] if s else "chart"
    if typ == "split_hook" or c["text"] in drops or chart_drop(c, s): continue
    if typ in ("broll", "host_full"):
        st = "top:1070px;color:#fff;text-shadow:0 3px 16px rgba(0,0,0,.6)"
    else:
        st = "top:1060px"
    h.append(f'<div id="cap{i}" class="cap" style="{st}">{esc(c["text"])}</div>')
    js.append(f"V('#cap{i}',{c['s']:.3f});IN('#cap{i}',{c['s']:.3f});H('#cap{i}',{c['off']:.3f});")
js.append(f"tl.set({{}},{{}},{DUR});window.__timelines={{main:tl}};document.fonts.ready.then(()=>tl.seek(tl.time(),false));")
(HF / "index.html").write_text('<!doctype html><html lang="en" data-resolution="portrait"><head><meta charset="UTF-8"><meta name="viewport" content="width=1080, height=1920">'
    f'<script src="assets/gsap.min.js"></script><style>{css}</style></head><body>{"".join(h)}</div><script>{chr(10).join(js)}</script></body></html>', encoding="utf-8")

# ---- SFX cue list (money only, few, never stacked)
cues = plan.get("sfx", "auto")
cues = sorted(sfx_auto) if cues == "auto" else sorted((c["t"], c["sound"]) for c in cues)
kept = []
for t, snd in cues:
    if not kept or t - kept[-1][0] >= 0.4: kept.append((t, snd))
jsave(P / "sfx-cues.json", [dict(t=round(t, 3), sound=snd) for t, snd in kept])
ncap = sum(1 for x in h if 'class="cap"' in x)
print(f"composition ok: {len(segs)} segments, {ncap} captions, {len(kept)} sfx cues, {DUR} s")
if A.no_render: sys.exit(0)

npx = exe("npx")
r = subprocess.run([npx, "--yes", "hyperframes@0.8.106", "check"], cwd=HF, capture_output=True, text=True)
print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if "✗" in l or "Check " in l))
if "Check failed" in r.stdout + r.stderr:
    sys.exit("hyperframes check failed (lines above). Fix plan.json or ask Claude, then build again.")
n = A.version or 1 + max([int(m.group(1)) for f in P.glob("v*.mp4") if (m := re.match(r"v(\d+)\.mp4$", f.name))] or [0])
raw = P / f"work-v{n}-nosfx.mp4"
env = dict(os.environ)
if platform.system() == "Darwin": env["PRODUCER_BROWSER_GPU_MODE"] = "hardware"
subprocess.run([npx, "--yes", "hyperframes@0.8.106", "render", ".", "--fps", str(plan.get("fps", 60)), "-q", "delivery", "-o", str(raw), "--quiet"], cwd=HF, env=env, check=True)
out = P / f"v{n}.mp4"
if kept:
    ins, fc, lab = [], [], []
    for k, (t, snd) in enumerate(kept):
        ins += ["-i", SKILL / "assets/sfx" / f"{snd}.wav"]; ms = int(t * 1000)
        fc.append(f"[{k + 1}]adelay={ms}|{ms}[s{k}]"); lab.append(f"[s{k}]")
    fc.append(f"[0:a]{''.join(lab)}amix=inputs={len(kept) + 1}:normalize=0[o]")
    ff("-i", raw, *ins, "-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[o]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", out)
    raw.unlink()
else:
    raw.replace(out)
print(f"rendered {out.name}")
py = sys.executable
subprocess.run([py, SKILL / "tools/jumpcheck.py", "check", out])
gfx = []   # graphics-only moments: 0.5 s steps not covered by b-roll / host / hook (full-bleed video is allowed to fill the frame)
for s in segs:
    if Z.get(s["type"], 1) != 1: continue
    t0 = s["start"] + .4
    while t0 < s["end"] - .2:
        if top_seg(t0) is s: gfx.append(round(t0, 2))
        t0 += 1.5
if gfx: subprocess.run([py, SKILL / "tools/safecheck.py", out, *map(str, gfx)])
