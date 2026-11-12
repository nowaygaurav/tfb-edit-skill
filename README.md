# TFB edit skill (Trust Fund Baby reels, Sanchit's AI avatar)

Claude Code skill + tools that turn a script into a finished reel in the locked TFB style:
split-screen hook → b-roll beats → infographic beats (real photos + charts) → Sanchit full screen → resource.

## Setup (Windows, once)
1. Install: Python 3.10+ (tick "Add to PATH"), Node LTS, ffmpeg, yt-dlp, Claude Code.
   `winget install Python.Python.3.12 OpenJS.NodeJS.LTS Gyan.FFmpeg yt-dlp.yt-dlp`
2. Copy this folder anywhere (e.g. `C:\tfb-edit-skill`), open PowerShell there and run:
   `powershell -ExecutionPolicy Bypass -File .\install.ps1`
3. Fill `.env`: `ELEVENLABS_API_KEY` (needs **Text to Speech** + **Forced Alignment** permissions) and `ELEVENLABS_VOICE_ID` (Sanchit's voice).
4. Font: `fonts\HelveticaNeue-Bold.ttf` must be there (exact name).
5. `python skill\tfb-edit\tools\doctor.py` → everything OK.

## Daily use (all in the Claude Code chat, opened in this folder)
1. Make `projects\<name>\script.txt`, tell Claude: **"make the audio for <name>"** → voice + chop → `final.wav`.
   (Already have final audio? Put it in as `final.wav` and say **"align it"**.)
2. **"give me the edit sheet"** → open `projects\<name>\edit-sheet.html` (double-click). Play segments, change in/out, type commands, add links.
   Press **Copy notes for Claude** and paste in the chat.
3. Drop assets: b-roll → `broll\broll-N.mp4` (or ask Claude: "download this clip <url> from 1:20 to 1:23 for broll-3"),
   avatar renders → `avatar\`, photos → "get photos from Pinterest", resource recording → `resource\`.
4. **"build v1"** → `v1.mp4` (+ checks). Notes → v2, v3…

Optional: Pinterest *search* needs OpenCLI + its Chrome extension logged in to Pinterest. Pin links work without it.
