# Run isolated TCS stimulus calibration (all 24 ramp/pulse stimuli, no game UI).
# See src/experiment/README.md

$ErrorActionPreference = 'Stop'

micromamba activate lnos2026_thermal_captcha

$proj = Split-Path -Parent $PSScriptRoot
Set-Location $proj

git pull --ff-only
python -m src.experiment.stimulus_calibration @args
