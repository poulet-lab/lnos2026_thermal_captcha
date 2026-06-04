"""Tests for stimulus definitions."""

import numpy as np
import pytest

from src.experiment.globals import (
    BASELINE_TEMPERATURE,
    FAST_RATE,
    MIN_HOLD_MS,
    STIMULUS_DURATION_MS,
    STIMULUS_DURATION_S,
)
from src.experiment.stimuli import STIMULUS_POOL, build_stimulus_pool


def test_pool_size():
    pool = build_stimulus_pool()
    # flat + 3 families * 6 amplitudes * 2 directions
    assert len(pool) == 1 + 3 * 6 * 2


def test_all_names_unique():
    pool = build_stimulus_pool()
    assert len(pool) == len(set(pool.keys()))


def test_flat_trace_constant():
    flat = STIMULUS_POOL["flat"]
    t, temp = flat.theoretical_trace()
    assert np.allclose(temp, BASELINE_TEMPERATURE)
    assert t[-1] == STIMULUS_DURATION_S


def test_pulse_reaches_target():
    stim = STIMULUS_POOL["pulse_pos_5"]
    _, temp = stim.theoretical_trace()
    assert stim.target == BASELINE_TEMPERATURE + 5
    assert np.max(temp) == pytest.approx(stim.target, abs=0.5)


def test_fast_up_slow_down_ends_at_baseline():
    stim = STIMULUS_POOL["fast_up_slow_down_pos_10"]
    t, temp = stim.theoretical_trace()
    assert t[-1] == pytest.approx(STIMULUS_DURATION_S, abs=0.01)
    assert temp[-1] == pytest.approx(BASELINE_TEMPERATURE, abs=0.5)


def test_slow_up_fast_down_rise_duration():
    stim = STIMULUS_POOL["slow_up_fast_down_neg_2"]
    t, temp = stim.theoretical_trace()
    # Peak should occur around 2s
    peak_idx = np.argmax(np.abs(temp - BASELINE_TEMPERATURE))
    assert t[peak_idx] == pytest.approx(STIMULUS_DURATION_S, abs=0.05)


def test_tcs_stimulus_for_pulse():
    stim = STIMULUS_POOL["pulse_pos_1"]
    tcs = stim.to_tcs_stimulus()
    assert tcs is not None
    assert tcs.baseline == BASELINE_TEMPERATURE
    assert tcs.target == BASELINE_TEMPERATURE + 1


def test_flat_has_no_tcs_stimulus():
    assert STIMULUS_POOL["flat"].to_tcs_stimulus() is None


def test_slow_up_fast_down_uses_rise_duration():
    stim = STIMULUS_POOL["slow_up_fast_down_pos_5"]
    tcs = stim.to_tcs_stimulus()
    assert tcs is not None
    assert tcs.duration == STIMULUS_DURATION_MS


def test_fast_up_slow_down_return_starts_after_short_plateau():
    stim = STIMULUS_POOL["fast_up_slow_down_neg_2"]
    tcs = stim.to_tcs_stimulus()
    assert tcs is not None
    rise_s = stim.amplitude / FAST_RATE
    hold_s = MIN_HOLD_MS / 1000.0
    expected_ms = max(MIN_HOLD_MS, int(round((rise_s + hold_s) * 1000)))
    assert tcs.duration == expected_ms
    assert tcs.duration < STIMULUS_DURATION_MS


def test_fast_up_slow_down_return_speed_fits_two_second_window():
    stim = STIMULUS_POOL["fast_up_slow_down_pos_10"]
    tcs = stim.to_tcs_stimulus()
    assert tcs is not None
    rise_s = stim.amplitude / FAST_RATE
    hold_s = MIN_HOLD_MS / 1000.0
    return_s = stim.amplitude / tcs.return_speed
    assert rise_s + hold_s + return_s == pytest.approx(STIMULUS_DURATION_S, abs=0.01)
