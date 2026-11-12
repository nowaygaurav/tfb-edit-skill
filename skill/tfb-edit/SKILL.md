---
name: tfb-edit
description: Trust Fund Baby reel pipeline for the editor. Use when the editor says "make the audio", "generate the voice", "chop the audio", "give me the edit sheet", "build v1", "render", "apply the notes", "get photos from Pinterest", "download this clip", or drops a script, a final audio file, b-roll clips, avatar renders or edit-sheet notes for a TFB (Sanchit's AI avatar) reel. Locked style: split-screen hook, b-roll beats, infographic beats with real photos + charts, host full screen, built in HyperFrames.
---

# TFB edit skill (locked style, 2026-11-12)

Sanchit is never filmed. Every reel = his ElevenLabs voice + his AI avatar renders + this edit. You (Claude) run the pipeline; the **editor** steers through the edit sheet and chat. Everything happens in chat; the only file the editor opens is `edit-sheet.html`.

**Read before any first draft:** `rules/hierarchy.md`, `rules/minimalism.md`, `rules/audio.md`, `rules/style.md`, `rules/moodboard.md`, and the last 20 lines of `rules/learning-log.md`.

## Where things live
- Skill: this folder (`tools/`, `rules/`, `templates/`, `assets/sfx/`).
- Repo root: `README.md`, `.env` (keys, never committed), `fonts/HelveticaNeue-Bold.ttf` (the editor installs it, never committed).
- One folder per reel: `projects/<name>/` with `script.txt`, `raw.mp3`, `final.wav`, `words.json`, `plan.json`, `edit-sheet.html`, `broll/`, `avatar/`, `photos/`, `resource/`, renders `v1.mp4`, `v2.mp4`… (never overwrite a render).

Run tools as `python <skill>/tools/<tool>.py …` (on Windows `py` also works). All paths below are relative to the repo root.

## The workflow (always in this order)
1. **Voice.** Editor gives the script → `tools/tts.py projects/<name>` (needs `script.txt`) → `raw.mp3` + `raw-words.json` (ElevenLabs, with timestamps).
2. **Chop.** `tools/chop.py projects/<name>` cuts fillers (um, uh, erm, hmm, ah) and squeezes pauses longer than 0.35 s down to 0.15 s → `final.wav` + `words.json` (re-timed). If the editor uploads his own final audio instead: save it as `final.wav` and run `tools/align.py projects/<name>` (ElevenLabs forced alignment against `script.txt`) → `words.json`.
3. **Edit sheet.** Read `words.json`, decide the flow (rules below), write `plan.json`, then `tools/editsheet.py projects/<name>` → `edit-sheet.html`. Tell the editor in chat: the breakdown (how many words in the split-screen hook, how many on host full screen, how many phrases are b-roll, how many are motion graphics) and the b-roll list to download.
4. **Editor pass.** He opens `edit-sheet.html`, plays each segment, changes in/out times, types commands, adds image links, presses **Copy notes for Claude** and pastes it in chat. Apply every change to `plan.json`. Each command is also a lesson: write the rule into `rules/` and a line into `rules/learning-log.md` (replace an old rule, don't stack).
5. **Assets.** B-roll: `tools/clip.py <url or file> --from … --to … --out projects/<name>/broll/broll-N.mp4 [--fit full|top]`. Photos: `tools/pinterest.py <pin urls…> --out projects/<name>/photos` or `--search "query"` (needs OpenCLI, see README). Avatar renders go in `avatar/` with the names in `plan.json`. Missing files render as clear placeholders; never block on them.
6. **Build.** `tools/build.py projects/<name>` → `hf/index.html` → HyperFrames render → SFX mixed → `vN.mp4` → checks (`safecheck.py`, `jumpcheck.py`). Fix every flag before delivery; never explain a flag away without measuring it. Then regenerate the edit sheet so its play buttons use the new render.
7. Repeat 4–6 for v2, v3… until the editor approves.

## plan.json (what you write, the editor changes through the sheet)
Segment types, z-order low → high: `photo_growth`, `chart`, `compare`, `resource` (infographics, on the paper background) → `broll` → `host_full` → `split_hook`. A higher segment covers lower ones in its time window, so a chart can span 7–23 s while b-roll beats sit on top of it; moving a b-roll's in/out never breaks the chart.
See `examples/kid-reel/plan.json` for every field. Key fields: `start`, `end`, `why` (your reasoning, shown in the sheet), `broll` (`file`, `film`, `scene`, `visible`), `avatar`, `hook` (`small`, `accent`, `after`, `strike_at`), `bars` (`label`, `value`, `photo`, `appear`, `grow`), `photos` (`file`, `query`), `keyword`, `sfx`.

## Locked style (short version; full rules in rules/)
- **Hook = split screen:** complementary b-roll on top (feel the line), Sanchit's avatar below, kinetic text hook on the split line (small words + one huge accent word, built word by word, strike-through allowed). No captions in the hook; the text hook carries it.
- Then mix: b-roll beats, infographic beats (real photos + motion, charts with numbers to compare), host full screen (CTA). Something new every 1–3 s; a hold over ~1.5 s needs motion.
- **Hear / read / see complement, never repeat.** The visual must explain the line with the caption covered. A number shown on a chart drops the caption chunk that says it.
- **Captions:** his exact words, Helvetica Neue Bold, 2–4 words, one fixed home per case: b-roll / host → white with shadow, top ≈ y 1070; infographic → ink, band top ≈ y 1060 (graphic stays in y 330–1030). No punctuation on screen except apostrophes.
- **Safe zone:** everything inside x 65–1015, y 270–1250, nothing at x > 850 below y 1150.
- **Less is more:** "would it still make sense without this?" → cut. No sources, legends, disclaimers.
- **Sound:** voice = information, SFX = feeling. Money sounds only, few, never two at once, no whooshes. Default: one soft coin as each chart number lands.
- **CTA keyword** big under the caption band from the word to the end.
- **Numbers:** only the ones in the script. Never invent figures.
