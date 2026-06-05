#!/usr/bin/env bash
# Launch Thermal Captcha operator menu (micromamba env + python -m src.experiment.run).
# Use with a Desktop .desktop launcher — see README.md § Desktop shortcut (Linux).

set -euo pipefail

eval "$(micromamba shell hook -s bash)"
micromamba activate lnos2026_thermal_captcha

proj="$(cd "$(dirname "$0")/.." && pwd)"
cd "$proj"

git pull --ff-only
python -m src.experiment.run
