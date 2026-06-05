"""Project paths and constants."""

from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parents[2]

DATA_RAW = ROOT_PATH / "data" / "raw"
DATA_OTHER = ROOT_PATH / "data" / "other"
STIMULUS_TRACES_DIR = ROOT_PATH / "reports" / "stimulus_traces"
RESPONSES_CSV = DATA_RAW / "responses.csv"
THERMAL_TRACES_DIR = DATA_RAW / "thermal_traces"
THERMAL_TRACE_SAMPLING_HZ = 20.0
TRACE_PLOT_Y_MIN = 20.0
TRACE_PLOT_Y_MAX = 44.0
CALIBRATION_TRACES_DIR = THERMAL_TRACES_DIR / "calibration"

BASELINE_TEMPERATURE = 32.0
STIMULUS_DURATION_S = 2.0
STIMULUS_DURATION_MS = int(STIMULUS_DURATION_S * 1000)
AMPLITUDES = (1, 2, 3, 5, 6, 10)
TRIALS_PER_PERSON = 10
ROUND_PROGRESS_PAUSE_S = 1.0
CHOICE_FEEDBACK_PAUSE_S = 1.0
CHOICE_COUNT = 6

# Fixed schematic y-range so amplitudes are comparable across all traces.
SCHEMATIC_Y_MARGIN = 1.0  # °C padding above/below largest excursion
SCHEMATIC_Y_MIN = BASELINE_TEMPERATURE - max(AMPLITUDES) - SCHEMATIC_Y_MARGIN
SCHEMATIC_Y_MAX = BASELINE_TEMPERATURE + max(AMPLITUDES) + SCHEMATIC_Y_MARGIN

FAST_RATE = 300.0  # °C/s
MIN_HOLD_MS = 10

# --- Hardware and display (edit for your setup) ---

# Serial port for the QST thermode (Windows: COM3, Linux: /dev/ttyUSB0, etc.)
TCS_PORT = "COM10"

# Safety cap for stimulus temperature (°C)
TCS_MAXIMUM_TEMPERATURE = 45.0

# True = no hardware (testing / development); False = real thermode
MOCK_TCS = False

# True = real hardware test runs (ranked separately from LNOS event data)
TROUBLESHOOTING = False

# Which monitor shows the participant UI (0 = leftmost in Windows display order)
SECOND_MONITOR_INDEX = 1

# Fallback if monitor detection fails (match monitor [1]: 2048x1152 at x=1920)
SECOND_MONITOR_OFFSET = 1920
SECOND_MONITOR_WIDTH = 2048
SECOND_MONITOR_HEIGHT = 1152

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
