"""Tests for schematic generation."""

from pathlib import Path

from src.experiment.schematics import generate_all_schematics, render_schematic
from src.experiment.stimuli import STIMULUS_POOL


def test_render_schematic_creates_file(tmp_path: Path):
    stim = STIMULUS_POOL["pulse_pos_5"]
    out = tmp_path / "pulse_pos_5.png"
    path = render_schematic(stim, out)
    assert path.exists()
    assert path.stat().st_size > 0


def test_generate_all_schematics(tmp_path: Path):
    paths = generate_all_schematics(tmp_path)
    assert len(paths) == len(STIMULUS_POOL)
    for p in paths:
        assert p.exists()


def test_shared_ylim_makes_amplitudes_distinct():
    from src.experiment.globals import SCHEMATIC_Y_MAX, SCHEMATIC_Y_MIN

    _, neg10 = STIMULUS_POOL["pulse_neg_10"].theoretical_trace()
    _, neg5 = STIMULUS_POOL["pulse_neg_5"].theoretical_trace()
    assert neg10.min() < neg5.min()
    assert neg10.min() >= SCHEMATIC_Y_MIN
    assert neg5.max() <= SCHEMATIC_Y_MAX
