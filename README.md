# LNOS 2026 — Thermal Captcha

Public-outreach thermal perception game: participants feel temperature traces on a QST thermode, then pick the matching drawing from six options on a second monitor.

See **[PLAN.md](PLAN.md)** for design notes and progress.

---

## Requirements

| Item | Notes |
|------|--------|
| **Python 3.11** | Required by `poulet_py` (`>=3.10,<3.14`) |
| **micromamba** or **conda** | Recommended for environment setup |
| **poulet_py** | Sibling repo with QST thermode support — see below |
| **Second monitor** | Participant display (Tkinter fullscreen) |
| **QST thermode** (optional) | Only needed when `MOCK_TCS=false` |

---

## 1. Clone the repositories

This project expects **`poulet_py`** as a sibling folder (used by `environment.yml` and `requirements.txt`).

**Windows (PowerShell):**

```powershell
cd C:\Users\YOUR_USER\Documents\projects
git clone https://github.com/poulet-lab/lnos2026_thermal_captcha.git
git clone https://github.com/poulet-lab/poulet_py.git
```

**macOS / Linux:**

```bash
cd ~/projects
git clone https://github.com/poulet-lab/lnos2026_thermal_captcha.git
git clone https://github.com/poulet-lab/poulet_py.git
```

Expected layout:

```
projects/
├── lnos2026_thermal_captcha/   ← this repo
└── poulet_py/                  ← dependency (must be next to it)
```

If `poulet_py` lives elsewhere, install it manually after creating the environment (see [Alternative: pip only](#alternative-pip-only)).

---

## 2. Create the Python environment

### Option A — micromamba (recommended)

**Windows (PowerShell):**

```powershell
cd C:\Users\YOUR_USER\Documents\projects\lnos2026_thermal_captcha
micromamba create -f environment.yml -y
micromamba activate lnos2026_thermal_captcha
```

**macOS / Linux:**

```bash
cd ~/projects/lnos2026_thermal_captcha
micromamba create -f environment.yml -y
micromamba activate lnos2026_thermal_captcha
```

### Option B — conda

```bash
cd path/to/lnos2026_thermal_captcha
conda env create -f environment.yml
conda activate lnos2026_thermal_captcha
```

### Alternative: pip only

Use this if you do not use conda/micromamba. Adjust the path to your `poulet_py` clone.

**Windows:**

```powershell
cd C:\Users\YOUR_USER\Documents\projects\lnos2026_thermal_captcha
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e ..\poulet_py[qst]
```

**macOS / Linux:**

```bash
cd ~/projects/lnos2026_thermal_captcha
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ../poulet_py[qst]
```

### Linux: Tkinter

If the participant display fails to open, install the Tk package for your Python version, e.g.:

```bash
sudo apt install python3.11-tk
```

---

## 3. Configure environment variables

Copy the example file and edit it for your machine.

**Windows:**

```powershell
cd C:\Users\YOUR_USER\Documents\projects\lnos2026_thermal_captcha
copy .env.example .env
notepad .env
```

**macOS / Linux:**

```bash
cd ~/projects/lnos2026_thermal_captcha
cp .env.example .env
nano .env
```

Example `.env`:

```env
# Serial port for the QST thermode (Windows: COM3, Linux: /dev/ttyUSB0, etc.)
TCS_PORT=COM3

# Safety cap for stimulus temperature (°C)
TCS_MAXIMUM_TEMPERATURE=45

# true = no hardware (testing / development); false = real thermode
MOCK_TCS=true

# Which monitor shows the participant UI (0 = leftmost in Windows display order)
SECOND_MONITOR_INDEX=0

# Fallback horizontal offset if monitor detection fails (often = primary monitor width)
SECOND_MONITOR_OFFSET=1920
```

### Finding the right monitor settings

When you start a game, the operator terminal prints detected monitors and which one is used. If the window appears on the wrong screen:

1. Try `SECOND_MONITOR_INDEX=0`, then `1`, etc.
2. If detection fails, set `SECOND_MONITOR_OFFSET` to your primary monitor width in pixels (e.g. `1920` or `2560`).

---

## 4. Generate stimulus images (required once)

Trace PNGs are **not** stored in git. Generate them before the first run:

```bash
micromamba activate lnos2026_thermal_captcha
python -m src.experiment.generate_schematics
```

This writes 25 schematic PNGs to `reports/stimulus_traces/`.

---

## 5. Run the experiment

Activate the environment, then start the operator menu:

```bash
micromamba activate lnos2026_thermal_captcha
cd path/to/lnos2026_thermal_captcha
python -m src.experiment.run
```

**Menu:**

| Key | Action |
|-----|--------|
| **1** | Start game (opens participant display on second monitor) |
| **2** | Stimulus-trace ranking (which traces are easiest) |
| **3** | Person score distribution |
| **0** | Exit |

### Game flow (participant screen)

1. Title → Enter  
2. Instructions (DE / EN) → Enter  
3. “Ready to play?” → Enter  
4. 10 trials (green dot → thermode stimulus → pick 1 of 6 traces)  
5. Score + comparison with other players → Enter  
6. Thank-you screen → Enter  

The operator stays at the terminal menu; only the participant screen uses Enter and mouse clicks.

---

## 6. Real hardware (event day)

1. Connect the QST thermode and note the serial port (`COM3` on Windows, etc.).
2. Edit `.env`:

```env
MOCK_TCS=false
TCS_PORT=COM3
TCS_MAXIMUM_TEMPERATURE=45
```

3. Run a short test session with `MOCK_TCS=false` before participants arrive.
4. Use **Ctrl+C** in the operator terminal to halt the thermode safely if needed.

---

## 7. Run tests

```bash
micromamba activate lnos2026_thermal_captcha
cd path/to/lnos2026_thermal_captcha
pytest
```

---

## Data output

| Path | Content |
|------|---------|
| `data/raw/responses.csv` | One row per trial (person, stimulus, choice, correct) |
| `data/other/logs/sessions.csv` | Session start/end and errors |

These paths are created automatically when you run the game.

---

## Troubleshooting

**`ModuleNotFoundError: poulet_py`**  
Install the sibling repo: `pip install -e ../poulet_py[qst]` (from this project root).

**Participant window on wrong monitor**  
Adjust `SECOND_MONITOR_INDEX` and `SECOND_MONITOR_OFFSET` in `.env`; check monitor lines printed when a game starts.

**Missing trace images / choice screen error**  
Run `python -m src.experiment.generate_schematics`.

**Thermode not responding**  
Confirm `TCS_PORT`, drivers, and that no other program holds the serial port. Test with `MOCK_TCS=true` first.

**Display does not open (Linux)**  
Install `python3.11-tk` (or equivalent for your Python version).

---

## Project layout

```
lnos2026_thermal_captcha/
├── src/experiment/       # Game code (run, game, display, stimuli, TCS)
├── reports/stimulus_traces/   # Generated schematic PNGs
├── data/raw/             # responses.csv
├── tests/                # pytest suite
├── environment.yml       # micromamba / conda env
├── requirements.txt      # pip dependencies
└── .env.example          # copy to .env
```

More detail: [`src/experiment/README.md`](src/experiment/README.md).
