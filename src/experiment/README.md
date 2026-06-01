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
| `responses.py` | Append trials to CSV |
| `rankings.py` | Score / trace rankings |

Generate schematics before the event:

```bash
python -m src.experiment.generate_schematics
```
