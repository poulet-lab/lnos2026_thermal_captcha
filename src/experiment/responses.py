"""Trial response storage and person numbering."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .globals import DATA_RAW, ENVIRONMENT_MOCK_TCS, RESPONSES_CSV, current_environment

FIELDNAMES = (
    "timestamp",
    "environment",
    "difficulty",
    "person",
    "trial",
    "stimulus_type",
    "chosen",
    "correct",
)


def _normalize_row(row: dict[str, str]) -> dict[str, str]:
    if not row.get("environment"):
        row["environment"] = ENVIRONMENT_MOCK_TCS
    if "difficulty" not in row:
        row["difficulty"] = ""
    return row


def _migrate_responses_file(path: Path) -> None:
    if not path.exists():
        return
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        old_fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]

    if old_fieldnames == list(FIELDNAMES):
        return

    normalized = [_normalize_row(row) for row in rows]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in normalized:
            writer.writerow({field: row.get(field, "") for field in FIELDNAMES})


def _ensure_responses_file(path: Path = RESPONSES_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()
        return
    _migrate_responses_file(path)


def next_person_number(
    path: Path | None = None,
    *,
    environment: str | None = None,
) -> int:
    path = path or RESPONSES_CSV
    environment = environment or current_environment()
    _ensure_responses_file(path)
    max_person = 0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row = _normalize_row(row)
            if row["environment"] != environment:
                continue
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
    *,
    environment: str | None = None,
    difficulty: str = "",
) -> None:
    path = path or RESPONSES_CSV
    environment = environment or current_environment()
    _ensure_responses_file(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "environment": environment,
                "difficulty": difficulty,
                "person": person,
                "trial": trial,
                "stimulus_type": stimulus_type,
                "chosen": chosen,
                "correct": str(correct).lower(),
            }
        )


def load_responses(
    path: Path | None = None,
    *,
    environment: str | None = None,
) -> list[dict[str, str]]:
    path = path or RESPONSES_CSV
    if not path.exists():
        return []
    _ensure_responses_file(path)
    with open(path, newline="", encoding="utf-8") as f:
        rows = [_normalize_row(row) for row in csv.DictReader(f)]
    if environment is None:
        return rows
    return [row for row in rows if row["environment"] == environment]
