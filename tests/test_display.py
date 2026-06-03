"""Tests for results display text."""

from src.experiment.display import format_comparison_lines
from src.experiment.globals import TRIALS_PER_PERSON


def test_perfect_score_hides_above_line():
    lines = format_comparison_lines(TRIALS_PER_PERSON, above=2, same=1, below=5)
    assert len(lines) == 2
    assert "or more correct" not in "\n".join(lines)
    assert "same as you" in lines[0]


def test_zero_score_hides_below_line():
    lines = format_comparison_lines(0, above=3, same=0, below=4)
    assert len(lines) == 2
    assert "or less" not in "\n".join(lines)
    assert "1 or more correct" in lines[0]


def test_mid_score_shows_all_lines():
    lines = format_comparison_lines(8, above=2, same=1, below=3)
    assert len(lines) == 3
    assert "9 or more correct" in lines[0]
    assert "same as you (8)" in lines[1]
    assert "7 or less" in lines[2]
