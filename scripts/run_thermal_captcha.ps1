# Launch Thermal Captcha operator menu (micromamba env + python -m src.experiment.run).
# Use with a Desktop shortcut — see README.md § Desktop shortcut (Windows).

$ErrorActionPreference = 'Stop'

micromamba activate lnos2026_thermal_captcha

$proj = Split-Path -Parent $PSScriptRoot
Set-Location $proj

git pull --ff-only
python -m src.experiment.run
