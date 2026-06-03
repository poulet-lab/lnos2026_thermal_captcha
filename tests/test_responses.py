"""Tests for response storage."""

import csv
from pathlib import Path

from src.experiment.globals import ENVIRONMENT_LNOS, ENVIRONMENT_MOCK_TCS
from src.experiment.responses import append_trial, load_responses, next_person_number


def test_next_person_starts_at_one(tmp_path: Path):
    path = tmp_path / "responses.csv"
    assert next_person_number(path) == 1


def test_next_person_increments(tmp_path: Path):
    path = tmp_path / "responses.csv"
    append_trial(1, 1, "flat", "flat", True, path=path)
    append_trial(1, 2, "pulse_pos_1", "pulse_pos_1", True, path=path)
    append_trial(2, 1, "flat", "pulse_pos_1", False, path=path)
    assert next_person_number(path) == 3


def test_next_person_is_per_environment(tmp_path: Path):
    path = tmp_path / "responses.csv"
    append_trial(1, 1, "flat", "flat", True, path=path, environment=ENVIRONMENT_MOCK_TCS)
    append_trial(1, 1, "flat", "flat", True, path=path, environment=ENVIRONMENT_LNOS)
    append_trial(7, 1, "flat", "flat", True, path=path, environment=ENVIRONMENT_MOCK_TCS)
    assert next_person_number(path, environment=ENVIRONMENT_MOCK_TCS) == 8
    assert next_person_number(path, environment=ENVIRONMENT_LNOS) == 2


def test_append_and_load(tmp_path: Path):
    path = tmp_path / "responses.csv"
    append_trial(1, 1, "flat", "flat", True, path=path, environment=ENVIRONMENT_MOCK_TCS)
    rows = load_responses(path)
    assert len(rows) == 1
    assert rows[0]["person"] == "1"
    assert rows[0]["environment"] == ENVIRONMENT_MOCK_TCS
    assert rows[0]["correct"] == "true"


def test_migrate_legacy_csv_without_environment(tmp_path: Path):
    path = tmp_path / "responses.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=("timestamp", "person", "trial", "stimulus_type", "chosen", "correct"),
        )
        writer.writeheader()
        writer.writerow(
            {
                "timestamp": "2026-06-03T12:00:00",
                "person": 5,
                "trial": 1,
                "stimulus_type": "flat",
                "chosen": "flat",
                "correct": "true",
            }
        )

    append_trial(6, 1, "flat", "flat", True, path=path, environment=ENVIRONMENT_MOCK_TCS)
    rows = load_responses(path, environment=ENVIRONMENT_MOCK_TCS)
    assert len(rows) == 2
    assert all(row["environment"] == ENVIRONMENT_MOCK_TCS for row in rows)
    assert next_person_number(path, environment=ENVIRONMENT_MOCK_TCS) == 7
