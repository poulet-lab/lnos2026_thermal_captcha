"""Tests for response storage."""

import csv
from pathlib import Path

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


def test_append_and_load(tmp_path: Path):
    path = tmp_path / "responses.csv"
    append_trial(1, 1, "flat", "flat", True, path=path)
    rows = load_responses(path)
    assert len(rows) == 1
    assert rows[0]["person"] == "1"
    assert rows[0]["correct"] == "true"
