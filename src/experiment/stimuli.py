"""Stimulus definitions: names, theoretical traces, and TCS parameters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

from .globals import (
    AMPLITUDES,
    BASELINE_TEMPERATURE,
    FAST_RATE,
    MIN_HOLD_MS,
    STIMULUS_DURATION_MS,
    STIMULUS_DURATION_S,
)

if TYPE_CHECKING:
    from poulet_py import TCSStimulus


class Family(str, Enum):
    FLAT = "flat"
    PULSE = "pulse"
    SLOW_UP_FAST_DOWN = "slow_up_fast_down"
    FAST_UP_SLOW_DOWN = "fast_up_slow_down"


@dataclass(frozen=True)
class StimulusDefinition:
    name: str
    family: Family
    amplitude: float
    direction: int  # +1 warm, -1 cool, 0 for flat
    delivery_duration_s: float

    @property
    def target(self) -> float:
        if self.family is Family.FLAT:
            return BASELINE_TEMPERATURE
        return BASELINE_TEMPERATURE + self.direction * self.amplitude

    def theoretical_trace(self, n_points: int = 500) -> tuple[np.ndarray, np.ndarray]:
        """Return (time_s, temperature) for schematic plotting."""
        if self.family is Family.FLAT:
            t = np.linspace(0, STIMULUS_DURATION_S, n_points)
            return t, np.full(n_points, BASELINE_TEMPERATURE)

        if self.family is Family.PULSE:
            return _pulse_trace(self.amplitude, self.direction, n_points)

        if self.family is Family.SLOW_UP_FAST_DOWN:
            return _slow_up_fast_down_trace(self.amplitude, self.direction, n_points)

        if self.family is Family.FAST_UP_SLOW_DOWN:
            return _fast_up_slow_down_trace(self.amplitude, self.direction, n_points)

        raise ValueError(f"Unknown family: {self.family}")

    def to_tcs_stimulus(self) -> TCSStimulus | None:
        """Build poulet_py TCSStimulus, or None for flat (no trigger)."""
        from poulet_py import TCSStimulus

        if self.family is Family.FLAT:
            return None

        baseline = BASELINE_TEMPERATURE
        target = self.target
        amp = self.amplitude

        if self.family is Family.PULSE:
            rise_rate = FAST_RATE
            return_speed = FAST_RATE
            rise_s = amp / rise_rate
            return_s = amp / return_speed
            hold_ms = max(
                MIN_HOLD_MS,
                int((STIMULUS_DURATION_S - rise_s - return_s) * 1000),
            )
            return TCSStimulus(
                surface=0,
                baseline=baseline,
                target=target,
                rise_rate=rise_rate,
                return_speed=return_speed,
                duration=hold_ms,
            )

        if self.family is Family.SLOW_UP_FAST_DOWN:
            # Slow ramp to peak at t = STIMULUS_DURATION_S, then fast return.
            # Duration is when the return phase starts (from trigger), not hold length.
            rise_rate = amp / STIMULUS_DURATION_S
            return_speed = FAST_RATE
            return TCSStimulus(
                surface=0,
                baseline=baseline,
                target=target,
                rise_rate=rise_rate,
                return_speed=return_speed,
                duration=STIMULUS_DURATION_MS,
            )

        if self.family is Family.FAST_UP_SLOW_DOWN:
            # Fast rise, tiny plateau, slow return ending at t = STIMULUS_DURATION_S.
            rise_rate = FAST_RATE
            rise_s = amp / rise_rate
            hold_s = MIN_HOLD_MS / 1000.0
            return_s = STIMULUS_DURATION_S - rise_s - hold_s
            return_speed = amp / return_s
            return_start_ms = max(MIN_HOLD_MS, int(round((rise_s + hold_s) * 1000)))
            return TCSStimulus(
                surface=0,
                baseline=baseline,
                target=target,
                rise_rate=rise_rate,
                return_speed=return_speed,
                duration=return_start_ms,
            )

        raise ValueError(f"Unknown family: {self.family}")


def _pulse_trace(amplitude: float, direction: int, n_points: int) -> tuple[np.ndarray, np.ndarray]:
    rise_s = amplitude / FAST_RATE
    return_s = amplitude / FAST_RATE
    hold_s = max(0.0, STIMULUS_DURATION_S - rise_s - return_s)
    peak = BASELINE_TEMPERATURE + direction * amplitude

    segments = [
        (0.0, rise_s, BASELINE_TEMPERATURE, peak),
        (rise_s, rise_s + hold_s, peak, peak),
        (rise_s + hold_s, STIMULUS_DURATION_S, peak, BASELINE_TEMPERATURE),
    ]
    return _piecewise_linear(segments, n_points)


def _slow_up_fast_down_trace(
    amplitude: float, direction: int, n_points: int
) -> tuple[np.ndarray, np.ndarray]:
    rise_s = STIMULUS_DURATION_S
    hold_s = MIN_HOLD_MS / 1000.0
    return_s = amplitude / FAST_RATE
    total_s = rise_s + hold_s + return_s
    peak = BASELINE_TEMPERATURE + direction * amplitude

    segments = [
        (0.0, rise_s, BASELINE_TEMPERATURE, peak),
        (rise_s, rise_s + hold_s, peak, peak),
        (rise_s + hold_s, total_s, peak, BASELINE_TEMPERATURE),
    ]
    return _piecewise_linear(segments, n_points)


def _fast_up_slow_down_trace(
    amplitude: float, direction: int, n_points: int
) -> tuple[np.ndarray, np.ndarray]:
    rise_s = amplitude / FAST_RATE
    hold_s = MIN_HOLD_MS / 1000.0
    return_s = STIMULUS_DURATION_S - rise_s - hold_s
    peak = BASELINE_TEMPERATURE + direction * amplitude

    segments = [
        (0.0, rise_s, BASELINE_TEMPERATURE, peak),
        (rise_s, rise_s + hold_s, peak, peak),
        (rise_s + hold_s, STIMULUS_DURATION_S, peak, BASELINE_TEMPERATURE),
    ]
    return _piecewise_linear(segments, n_points)


def _piecewise_linear(
    segments: list[tuple[float, float, float, float]], n_points: int
) -> tuple[np.ndarray, np.ndarray]:
    t_end = segments[-1][1]
    t = np.linspace(0, t_end, n_points)
    y = np.zeros(n_points)
    for t0, t1, y0, y1 in segments:
        mask = (t >= t0) & (t <= t1)
        if t1 == t0:
            y[mask] = y1
        else:
            frac = (t[mask] - t0) / (t1 - t0)
            y[mask] = y0 + frac * (y1 - y0)
    return t, y


def _family_delivery_duration(family: Family, amplitude: float) -> float:
    if family is Family.FLAT:
        return STIMULUS_DURATION_S
    if family is Family.PULSE:
        rise_s = amplitude / FAST_RATE
        return_s = amplitude / FAST_RATE
        hold_s = max(0.0, STIMULUS_DURATION_S - rise_s - return_s)
        return rise_s + hold_s + return_s
    if family is Family.SLOW_UP_FAST_DOWN:
        return STIMULUS_DURATION_S + MIN_HOLD_MS / 1000.0 + amplitude / FAST_RATE
    if family is Family.FAST_UP_SLOW_DOWN:
        return STIMULUS_DURATION_S
    raise ValueError(f"Unknown family: {family}")


def _make_named(family: Family, direction: int, amplitude: float) -> StimulusDefinition:
    if family is Family.FLAT:
        name = "flat"
    else:
        dir_label = "pos" if direction > 0 else "neg"
        name = f"{family.value}_{dir_label}_{int(amplitude)}"
    return StimulusDefinition(
        name=name,
        family=family,
        amplitude=amplitude,
        direction=direction,
        delivery_duration_s=_family_delivery_duration(family, amplitude),
    )


def build_stimulus_pool() -> dict[str, StimulusDefinition]:
    pool: dict[str, StimulusDefinition] = {}
    pool["flat"] = _make_named(Family.FLAT, 0, 0.0)

    for family in (Family.PULSE, Family.SLOW_UP_FAST_DOWN, Family.FAST_UP_SLOW_DOWN):
        for amplitude in AMPLITUDES:
            for direction in (1, -1):
                stim = _make_named(family, direction, float(amplitude))
                pool[stim.name] = stim

    return pool


STIMULUS_POOL: dict[str, StimulusDefinition] = build_stimulus_pool()
STIMULUS_NAMES: tuple[str, ...] = tuple(STIMULUS_POOL.keys())
