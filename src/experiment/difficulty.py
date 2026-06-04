"""Difficulty levels and amplitude filtering for game sessions."""

from __future__ import annotations

from enum import Enum

from .stimuli import STIMULUS_POOL, Family, StimulusDefinition


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


DIFFICULTY_AMPLITUDES: dict[Difficulty, tuple[int, ...]] = {
    Difficulty.EASY: (5, 10),
    Difficulty.MEDIUM: (3, 6),
    Difficulty.HARD: (1, 2),
}


def allowed_amplitudes(difficulty: Difficulty) -> tuple[int, ...]:
    return DIFFICULTY_AMPLITUDES[difficulty]


def stimulus_names_for_difficulty(difficulty: Difficulty) -> tuple[str, ...]:
    """Stimulus names eligible for trials and choice foils at this difficulty."""
    amps = set(allowed_amplitudes(difficulty))
    names: list[str] = []
    for name, stim in STIMULUS_POOL.items():
        if stim.family is Family.FLAT or stim.amplitude in amps:
            names.append(name)
    return tuple(sorted(names))


def stimuli_for_difficulty(difficulty: Difficulty) -> tuple[StimulusDefinition, ...]:
    return tuple(STIMULUS_POOL[name] for name in stimulus_names_for_difficulty(difficulty))


def difficulty_label(difficulty: Difficulty) -> str:
    amps = allowed_amplitudes(difficulty)
    amp_text = ", ".join(f"±{a}" for a in amps)
    return f"{difficulty.value} ({amp_text} °C)"
