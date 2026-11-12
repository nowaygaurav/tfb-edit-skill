# TFB edit skill, Windows installer. Run in PowerShell from the repo folder:  powershell -ExecutionPolicy Bypass -File .\install.ps1
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$dest = Join-Path $env:USERPROFILE ".claude\skills\tfb-edit"
Write-Host "Installing the skill to $dest"
New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
# a junction keeps the skill linked to this repo, so 'git pull' updates it
cmd /c mklink /J "$dest" "$repo\skill\tfb-edit" | Out-Null
Write-Host "Installing Python packages"
python -m pip install --upgrade requests pillow numpy opencv-python yt-dlp
if (-not (Test-Path "$repo\.env")) { Copy-Item "$repo\.env.example" "$repo\.env"; Write-Host "Created .env, fill in the ElevenLabs key and voice id" }
New-Item -ItemType Directory -Force -Path "$repo\projects" | Out-Null
python "$repo\skill\tfb-edit\tools\doctor.py"
