"""Session and error logging."""

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

from .globals import DATA_OTHER, ROOT_PATH

LOGS_DIR_NAME = "logs"
SESSIONS_CSV = "sessions.csv"
FIELDNAMES = ("timestamp", "event", "script", "message")


def get_logs_dir() -> Path:
    logs_dir = DATA_OTHER / LOGS_DIR_NAME
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def _append_session_row(timestamp: str, event: str, script: str, message: str = "") -> None:
    try:
        logs_dir = get_logs_dir()
        csv_path = logs_dir / SESSIONS_CSV
        file_exists = csv_path.exists()
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow(
                {
                    "timestamp": timestamp,
                    "event": event,
                    "script": script,
                    "message": message,
                }
            )
    except OSError as e:
        print(f"Warning: could not write to session log: {e}", file=sys.stderr)


def log_script_event(event: Literal["start", "end"], script: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    _append_session_row(timestamp, event, script, "")


def log_error(script: str, message: str, traceback_str: str) -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    try:
        _append_session_row(timestamp_iso, "error", script, message)
        logs_dir = get_logs_dir()
        txt_path = logs_dir / f"{ts}_error.txt"
        txt_path.write_text(traceback_str, encoding="utf-8")
    except OSError as e:
        print(f"Warning: could not write error log: {e}", file=sys.stderr)
