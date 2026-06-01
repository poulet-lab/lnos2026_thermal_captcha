# LNOS 2026 — Thermal Captcha

Public-outreach thermal perception game: feel temperature traces on a QST thermode, then pick the matching drawing from six options.

See **[PLAN.md](PLAN.md)** for full design and progress.

## Setup

**Python 3.11** (matches `poulet_py` requirement `>=3.10,<3.14`).

With micromamba:

```bash
micromamba create -f environment.yml -y
micromamba activate lnos2026_thermal_captcha
copy .env.example .env   # then edit TCS_PORT, MOCK_TCS, SECOND_MONITOR_OFFSET
```

Or with pip only:

```bash
pip install -r requirements.txt -e ../poulet_py[qst]
copy .env.example .env
```

## Before the event

Generate schematic answer images (once) into `reports/stimulus_traces/`:

```bash
python -m src.experiment.generate_schematics
```

## Run

Operator terminal (mock TCS by default):

```bash
python -m src.experiment.run
```

Menu:
- **1** Start game (opens Tkinter on second monitor)
- **2** Stimulus-trace ranking
- **3** Person score distribution
- **0** Exit

Set `MOCK_TCS=false` and `TCS_PORT=COMx` in `.env` for real hardware.

## Data

Trial responses append to `data/raw/responses.csv` (long format).

Session logs go to `data/other/logs/sessions.csv`.

## Tests

```bash
pytest
```
