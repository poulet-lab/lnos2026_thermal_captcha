"""Tests for game helpers."""

from src.experiment.game import sample_choice_options, sample_trial_stimuli
from src.experiment.globals import CHOICE_COUNT, TRIALS_PER_PERSON


def test_sample_trial_stimuli_count():
    trials = sample_trial_stimuli()
    assert len(trials) == TRIALS_PER_PERSON


def test_sample_choice_options():
    options = sample_choice_options("flat")
    assert len(options) == CHOICE_COUNT
    assert "flat" in options
    assert len(set(options)) == CHOICE_COUNT
