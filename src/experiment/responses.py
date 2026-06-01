"""Trial response storage and person numbering."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .globals import DATA_RAW, RESPONSES_CSV

FIELDNAMES = ("timestamp", "person", "trial", "stimulus_type", "chosen", "correct")


def _ensure_responses_file(path: Path = RESPONSES_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()


def next_person_number(path: Path | None = None) -> int:
    path = path or RESPONSES_CSV
    _ensure_responses_file(path)
    max_person = 0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                max_person = max(max_person, int(row["person"]))
            except (KeyError, ValueError):
                continue
    return max_person + 1


def append_trial(
    person: int,
    trial: int,
    stimulus_type: str,
    chosen: str,
    correct: bool,
    path: Path | None = None,
) -> None:
    path = path or RESPONSES_CSV
    _ensure_responses_file(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "person": person,
                "trial": trial,
                "stimulus_type": stimulus_type,
                "chosen": chosen,
                "correct": str(correct).lower(),
            }
        )


def load_responses(path: Path | None = None) -> list[dict[str, str]]:
    path = path or RESPONSES_CSV
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
