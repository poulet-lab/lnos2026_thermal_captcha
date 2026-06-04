"""Tests for difficulty levels and amplitude filtering."""

from src.experiment.difficulty import (
    Difficulty,
    allowed_amplitudes,
    stimulus_names_for_difficulty,
)
from src.experiment.stimuli import STIMULUS_POOL


def test_allowed_amplitudes_exclusive_bands():
    assert allowed_amplitudes(Difficulty.EASY) == (5, 10)
    assert allowed_amplitudes(Difficulty.MEDIUM) == (3, 6)
    assert allowed_amplitudes(Difficulty.HARD) == (1, 2)


def test_easy_stimulus_pool():
    names = set(stimulus_names_for_difficulty(Difficulty.EASY))
    assert "flat" in names
    assert "pulse_pos_10" in names
    assert "pulse_pos_5" in names
    assert "pulse_pos_1" not in names
    assert "pulse_pos_3" not in names
    assert len(names) == 13


def test_medium_stimulus_pool():
    names = set(stimulus_names_for_difficulty(Difficulty.MEDIUM))
    assert "flat" in names
    assert "pulse_pos_3" in names
    assert "slow_up_fast_down_neg_6" in names
    assert "pulse_pos_10" not in names
    assert "pulse_pos_1" not in names
    assert len(names) == 13


def test_hard_stimulus_pool():
    names = set(stimulus_names_for_difficulty(Difficulty.HARD))
    assert "flat" in names
    assert "pulse_pos_1" in names
    assert "fast_up_slow_down_neg_2" in names
    assert "pulse_pos_10" not in names
    assert "pulse_pos_3" not in names
    assert len(names) == 13


def test_filtered_stimuli_exist_in_pool():
    for difficulty in Difficulty:
        for name in stimulus_names_for_difficulty(difficulty):
            assert name in STIMULUS_POOL
