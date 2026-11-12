#!/usr/bin/env python3
"""Step 3. plan.json + words.json -> edit-sheet.html (one self-contained file, double-click to open, no server).
Each segment: play button, editable in/out, words in range, Claude's reasoning, asset spec, editor command box, reference links.
'Copy notes for Claude' puts every change on the clipboard to paste into the chat.
usage: python editsheet.py projects/<name>"""
import json, re, sys
from common import project, jload, words_in

P = project(sys.argv[1])
plan = jload(P / "plan.json"); words = jload(P / "words.json")
renders = sorted(P.glob("v*.mp4"), key=lambda f: int(re.sub(r"\D", "", f.stem) or 0))
media = renders[-1].name if renders else plan.get("audio", "final.wav")
LABEL = {"split_hook": "SPLIT-SCREEN HOOK", "broll": "B-ROLL", "host_full": "SANCHIT FULL SCREEN", "photo_growth": "MOTION GRAPHIC · photos",
         "chart": "MOTION GRAPHIC · chart", "compare": "MOTION GRAPHIC · compare", "resource": "RESOURCE"}
segs = sorted(plan["segments"], key=lambda s: s["start"])
def nwords(types):
    return sum(len(words_in(words, s["start"], s["end"]).split()) for s in segs if s["type"] in types)
summary = dict(hook=nwords({"split_hook"}), host=nwords({"host_full"}), broll=sum(1 for s in segs if s["type"] == "broll"),
               mg=sum(1 for s in segs if s["type"] in {"photo_growth", "chart", "compare"}), res=sum(1 for s in segs if s["type"] == "resource"))
def spec(s):
    out = []
    if s.get("broll"): b = s["broll"]; out.append(f"Clip: {b.get('film','')} · {b.get('scene','')} · must show: {b.get('visible','')} · file: {b.get('file','')}")
    if s.get("avatar"): out.append(f"Avatar render: {s['avatar']}")
    if s.get("hook"): k = s["hook"]; out.append(f"Text hook: \"{k.get('small','')}\" + big \"{k.get('accent','')}\"" + (f" + \"{k['after']}\"" if k.get("after") else ""))
    for p in s.get("photos", []): out.append(f"Photo {p.get('file','')}: {p.get('query','')}")
    for b in s.get("bars", []): out.append(f"Bar {b['label']} → {b['value']}{b.get('unit','')}" + (f" · photo: {b['photo'].get('query','')}" if b.get("photo") else ""))
    if s["type"] == "resource": out.append(f"Resource file: {s.get('file','')}")
    return out
data = dict(title=plan.get("title", P.name), media=media, words=words, summary=summary,
            segs=[dict(id=s["id"], type=s["type"], label=LABEL.get(s["type"], s["type"]), start=s["start"], end=s["end"], why=s.get("why", ""), spec=spec(s)) for s in segs])
HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Edit sheet</title><style>
:root{--bg:#F4F5F2;--card:#fff;--ink:#1A1F1C;--mute:#6B716B;--line:#E1E4DF;--g:#2F6B55;--gs:#E4EFE9}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:14px 22px;display:flex;gap:18px;align-items:center;flex-wrap:wrap}
h1{font-size:19px;margin:0 12px 0 0}.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:6px 12px;font-size:13px}.stat b{font-size:16px;margin-right:4px}
#player{width:100%;max-width:300px;border-radius:12px;background:#000}main{display:grid;grid-template-columns:320px 1fr;gap:22px;padding:18px 22px}
aside{position:sticky;top:86px;align-self:start}button{font:inherit;border:1px solid var(--line);background:var(--card);border-radius:9px;padding:7px 12px;cursor:pointer}
button.pri{background:var(--g);border-color:var(--g);color:#fff}.seg{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:12px}
.seg.on{border-color:var(--g);box-shadow:0 0 0 2px var(--gs)}.top{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.badge{font-size:11px;letter-spacing:1px;font-weight:600;border-radius:6px;padding:3px 8px;background:var(--gs);color:var(--g)}
.badge.broll,.badge.split_hook{background:#26302B;color:#5BE39A}.badge.host_full{background:#EDE7F6;color:#5B3E96}
input[type=number]{width:84px;font:inherit;border:1px solid var(--line);border-radius:8px;padding:4px 6px}.changed{border-color:#D08A2B!important;background:#FFF6E9}
.words{margin:8px 0;font-family:Georgia,serif;font-size:16px}.why{color:var(--mute);font-size:13px}.spec{font-size:13px;margin:6px 0 0;padding-left:16px}
textarea,input.links{width:100%;font:inherit;border:1px solid var(--line);border-radius:9px;padding:8px;margin-top:8px}textarea{min-height:52px}
.drop{border:1.5px dashed var(--line);border-radius:9px;padding:6px 10px;margin-top:8px;font-size:13px;color:var(--mute)}.drop.over{border-color:var(--g)}
#copied{color:var(--g);font-size:13px;margin-left:6px}
</style></head><body>
<header><h1 id="t"></h1><div id="stats" style="display:flex;gap:8px;flex-wrap:wrap"></div><span style="flex:1"></span>
<button class="pri" id="copy">Copy notes for Claude</button><span id="copied"></span></header>
<main><aside><video id="player" controls playsinline></video><div style="font-size:12px;color:var(--mute);margin-top:6px">Playing: <span id="mname"></span>. ▶ on a segment plays just that part.</div>
<textarea id="general" placeholder="General notes for the whole video (new segments, pacing, anything)"></textarea></aside>
<section id="list"></section></main>
<script>
const D=__DATA__;const KEY='es:'+D.title+':'+D.media;const st=JSON.parse(localStorage.getItem(KEY)||'{}');
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){}};
document.getElementById('t').textContent=D.title;document.getElementById('mname').textContent=D.media;
const pl=document.getElementById('player');pl.src=D.media;let stopAt=null;pl.ontimeupdate=()=>{if(stopAt!==null&&pl.currentTime>=stopAt){pl.pause();stopAt=null}};
const S=D.summary;document.getElementById('stats').innerHTML=[[S.hook,'words in split-screen hook'],[S.host,'words Sanchit full screen'],[S.broll,'b-roll phrases'],[S.mg,'motion-graphic beats'],[S.res,'resource']].map(([n,l])=>`<span class="stat"><b>${n}</b>${l}</span>`).join('');
const wordsIn=(a,b)=>D.words.filter(w=>w.s>=a-0.01&&w.s<b).map(w=>w.w).join(' ');
const list=document.getElementById('list');
D.segs.forEach(s=>{const o=st[s.id]||(st[s.id]={start:s.start,end:s.end,cmd:'',links:'',files:''});
 const el=document.createElement('div');el.className='seg';el.innerHTML=`<div class="top"><span class="badge ${s.type}">${s.label}</span><b>${s.id}</b>
 <button class="play">▶ play</button><label>in <input type="number" step="0.01" class="a" value="${o.start}"></label><label>out <input type="number" step="0.01" class="b" value="${o.end}"></label><span class="dur" style="color:var(--mute);font-size:13px"></span></div>
 <div class="words"></div><div class="why">Claude's plan: ${s.why}</div><ul class="spec">${s.spec.map(x=>`<li>${x}</li>`).join('')}</ul>
 <textarea class="cmd" placeholder="Editor command for this part (what edit you want here)">${o.cmd}</textarea>
 <input class="links" placeholder="Reference image / clip links (comma separated)" value="${o.links}">
 <div class="drop">Drop reference files here (put the files in the project's refs/ folder too): <span class="files">${o.files}</span></div>`;
 const A=el.querySelector('.a'),B=el.querySelector('.b'),W=el.querySelector('.words'),U=el.querySelector('.dur');
 const upd=()=>{o.start=+A.value;o.end=+B.value;A.classList.toggle('changed',o.start!==s.start);B.classList.toggle('changed',o.end!==s.end);W.textContent='"'+wordsIn(o.start,o.end)+'"';U.textContent=(o.end-o.start).toFixed(2)+' s';save()};
 A.oninput=B.oninput=upd;upd();
 el.querySelector('.play').onclick=()=>{document.querySelectorAll('.seg').forEach(x=>x.classList.remove('on'));el.classList.add('on');pl.currentTime=o.start;stopAt=o.end;pl.play()};
 el.querySelector('.cmd').oninput=e=>{o.cmd=e.target.value;save()};el.querySelector('.links').oninput=e=>{o.links=e.target.value;save()};
 const dr=el.querySelector('.drop');dr.ondragover=e=>{e.preventDefault();dr.classList.add('over')};dr.ondragleave=()=>dr.classList.remove('over');
 dr.ondrop=e=>{e.preventDefault();dr.classList.remove('over');const n=[...e.dataTransfer.files].map(f=>f.name);o.files=[o.files,...n].filter(Boolean).join(', ');el.querySelector('.files').textContent=o.files;save()};
 list.appendChild(el)});
const g=document.getElementById('general');g.value=st._general||'';g.oninput=()=>{st._general=g.value;save()};
document.getElementById('copy').onclick=async()=>{const L=[`EDIT SHEET NOTES · ${D.title} · watched ${D.media}`];
 D.segs.forEach(s=>{const o=st[s.id];const ch=[];if(o.start!==s.start||o.end!==s.end)ch.push(`timing ${s.start}–${s.end} → ${o.start}–${o.end}`);
  if(o.cmd.trim())ch.push('command: '+o.cmd.trim());if(o.links.trim())ch.push('links: '+o.links.trim());if(o.files.trim())ch.push('files (in refs/): '+o.files.trim());
  if(ch.length)L.push(`- ${s.id} (${s.label}, ${s.start}–${s.end}): `+ch.join(' | '))});
 if((st._general||'').trim())L.push('- general: '+st._general.trim());if(L.length===1)L.push('- no changes');
 const txt=L.join('\n');try{await navigator.clipboard.writeText(txt)}catch(e){const t=document.createElement('textarea');t.value=txt;document.body.appendChild(t);t.select();document.execCommand('copy');t.remove()}
 document.getElementById('copied').textContent='Copied. Paste it in the Claude chat.'};
</script></body></html>"""
(P / "edit-sheet.html").write_text(HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
print(f"edit-sheet.html ({len(segs)} segments, playing {media}) · hook {summary['hook']} words · host full {summary['host']} words · {summary['broll']} b-roll · {summary['mg']} motion graphics")
