"""Project paths and constants."""

from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parents[2]

DATA_RAW = ROOT_PATH / "data" / "raw"
DATA_OTHER = ROOT_PATH / "data" / "other"
STIMULUS_TRACES_DIR = ROOT_PATH / "reports" / "stimulus_traces"
RESPONSES_CSV = DATA_RAW / "responses.csv"

BASELINE_TEMPERATURE = 32.0
STIMULUS_DURATION_S = 2.0
STIMULUS_DURATION_MS = int(STIMULUS_DURATION_S * 1000)
AMPLITUDES = (1, 2, 5, 10)
TRIALS_PER_PERSON = 10
CHOICE_COUNT = 6

# Fixed schematic y-range so amplitudes are comparable across all traces.
SCHEMATIC_Y_MARGIN = 1.0  # °C padding above/below largest excursion
SCHEMATIC_Y_MIN = BASELINE_TEMPERATURE - max(AMPLITUDES) - SCHEMATIC_Y_MARGIN
SCHEMATIC_Y_MAX = BASELINE_TEMPERATURE + max(AMPLITUDES) + SCHEMATIC_Y_MARGIN

FAST_RATE = 300.0  # °C/s
MIN_HOLD_MS = 10

# --- Hardware and display (edit for your setup) ---

# Serial port for the QST thermode (Windows: COM3, Linux: /dev/ttyUSB0, etc.)
TCS_PORT = "COM3"

# Safety cap for stimulus temperature (°C)
TCS_MAXIMUM_TEMPERATURE = 45.0

# True = no hardware (testing / development); False = real thermode
MOCK_TCS = True

# True = real hardware test runs (ranked separately from LNOS event data)
TROUBLESHOOTING = False

# Which monitor shows the participant UI (0 = leftmost in Windows display order)
SECOND_MONITOR_INDEX = 0

# Fallback horizontal offset if monitor detection fails (often = primary monitor width)
SECOND_MONITOR_OFFSET = 1920

ENVIRONMENT_MOCK_TCS = "mock_tcs"
ENVIRONMENT_TROUBLESHOOTING = "troubleshooting"
ENVIRONMENT_LNOS = "lnos"


def current_environment() -> str:
    """Label for the active run mode; drives CSV tagging and within-mode rankings."""
    if MOCK_TCS:
        return ENVIRONMENT_MOCK_TCS
    if TROUBLESHOOTING:
        return ENVIRONMENT_TROUBLESHOOTING
    return ENVIRONMENT_LNOS
