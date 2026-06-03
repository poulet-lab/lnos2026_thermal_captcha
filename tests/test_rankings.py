"""Tests for rankings."""

from src.experiment.rankings import (
    is_first_player,
    score_comparison,
    score_distribution,
    stimulus_trace_ranking,
)
from src.experiment.responses import append_trial


def test_stimulus_trace_ranking(tmp_path, monkeypatch):
    from src.experiment import responses as resp_mod

    path = tmp_path / "responses.csv"
    monkeypatch.setattr(resp_mod, "RESPONSES_CSV", path)

    append_trial(1, 1, "flat", "flat", True, path=path)
    append_trial(1, 2, "pulse_pos_1", "pulse_pos_2", False, path=path)
    append_trial(2, 1, "flat", "flat", True, path=path)

    ranking = dict(stimulus_trace_ranking())
    assert ranking["flat"] == 2
    assert ranking.get("pulse_pos_1", 0) == 0


def test_score_comparison_excludes_current_person(tmp_path, monkeypatch):
    from src.experiment import responses as resp_mod

    path = tmp_path / "responses.csv"
    monkeypatch.setattr(resp_mod, "RESPONSES_CSV", path)

    for trial in range(1, 11):
        append_trial(1, trial, "flat", "flat", trial <= 8, path=path)
    for trial in range(1, 11):
        append_trial(2, trial, "flat", "flat", trial <= 6, path=path)
    for trial in range(1, 11):
        append_trial(3, trial, "flat", "flat", trial <= 8, path=path)

    above, same, below = score_comparison(8, exclude_person=3)
    assert same == 1  # person 1 only; person 3 excluded
    assert above == 0
    assert below == 1  # person 2 with 6

    dist = score_distribution(exclude_person=3)
    assert dist[8] == 1
    assert dist[6] == 1


def test_is_first_player(tmp_path, monkeypatch):
    from src.experiment import responses as resp_mod

    path = tmp_path / "responses.csv"
    monkeypatch.setattr(resp_mod, "RESPONSES_CSV", path)

    append_trial(1, 1, "flat", "flat", True, path=path)
    assert is_first_player(exclude_person=1) is True

    append_trial(2, 1, "flat", "flat", True, path=path)
    assert is_first_player(exclude_person=2) is False
    assert is_first_player(exclude_person=1) is False
