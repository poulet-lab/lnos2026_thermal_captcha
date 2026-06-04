# Experiment

Thermal Captcha operator and participant code.

## Entry point

```bash
python -m src.experiment.run
```

## Modules

| Module | Role |
|--------|------|
| `run.py` | Rich terminal menu |
| `game.py` | One-person session (10 trials) |
| `display.py` | Tkinter second-screen UI |
| `stimuli.py` | Stimulus pool + TCS parameters |
| `schematics.py` | Pre-render trace PNGs |
| `tcs_controller.py` | QST thermode (mock or real) |
| `thermal_traces.py` | Per-trial TCS trace CSV + PNG (real hardware only) |
| `stimulus_calibration.py` | Isolated all-stimulus TCS calibration run |
| `analyze_calibration.py` | Calibration / trace folder analysis report |
| `globals.py` | Paths, trial constants, TCS & monitor settings |
| `responses.py` | Append trials to CSV |
| `rankings.py` | Score / trace rankings |

Generate schematics before the event:

```bash
python -m src.experiment.generate_schematics
```

## Thermal traces (real TCS only)

When `MOCK_TCS = False`, each trial saves a temperature trace under `data/raw/thermal_traces/{environment}/person_{N}/`. The plot auto-selects the two channels with the largest temperature swing (on a typical 2-zone probe this is **s0 and s1**). Trace plot y-axis is fixed at **20–44°C**. The operator terminal prints per-channel debug stats after each trial. Mock mode skips trace saving.

## Stimulus calibration (hardware debugging)

Deliver all 24 non-flat stimuli in isolation (no participant UI), with a settle delay between each:

```bash
python -m src.experiment.stimulus_calibration
python -m src.experiment.stimulus_calibration --delay 5 --output data/raw/thermal_traces/calibration/my_run
```

Outputs go to `data/raw/thermal_traces/calibration/run_YYYYMMDD_HHMMSS/` (CSV, PNG, `manifest.json`, `calibration_report.csv`). Re-analyze an existing folder:

```bash
python -m src.experiment.analyze_calibration data/raw/thermal_traces/calibration/run_YYYYMMDD_HHMMSS
```

Windows shortcut: `scripts/run_stimulus_calibration.ps1`
