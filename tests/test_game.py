"""Tests for game helpers."""

from src.experiment.difficulty import Difficulty, stimulus_names_for_difficulty
from src.experiment.game import sample_choice_options, sample_trial_stimuli
from src.experiment.globals import CHOICE_COUNT, TRIALS_PER_PERSON
from src.experiment.stimuli import STIMULUS_POOL


def test_sample_trial_stimuli_count():
    trials = sample_trial_stimuli(Difficulty.HARD)
    assert len(trials) == TRIALS_PER_PERSON


def test_sample_trial_stimuli_respect_difficulty():
    trials = sample_trial_stimuli(Difficulty.EASY)
    allowed = {5, 10, 0}
    for stim in trials:
        assert stim.amplitude in allowed


def test_sample_choice_options():
    options = sample_choice_options("flat", Difficulty.MEDIUM)
    assert len(options) == CHOICE_COUNT
    assert "flat" in options
    assert len(set(options)) == CHOICE_COUNT


def test_sample_choice_options_respect_difficulty():
    options = sample_choice_options("pulse_pos_3", Difficulty.MEDIUM)
    allowed = set(stimulus_names_for_difficulty(Difficulty.MEDIUM))
    assert set(options).issubset(allowed)


def test_choice_options_never_include_wrong_amplitude():
    options = sample_choice_options("pulse_pos_1", Difficulty.HARD)
    for name in options:
        stim = STIMULUS_POOL[name]
        assert stim.amplitude in (0, 1, 2)
