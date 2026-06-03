"""Tests for bilingual UI strings."""

from src.experiment.ui_strings import (
    BILINGUAL_SEPARATOR_MARKER,
    bilingual,
    comparison_results_text,
    first_player_results_text,
    format_comparison_bilingual,
    instructions_screen_text,
    ready_screen_text,
    thanks_screen_text,
    title_screen_text,
)
from src.experiment.globals import TRIALS_PER_PERSON


def test_bilingual_orders_german_first():
    text = bilingual("Deutsch", "English")
    assert text.index("Deutsch") < text.index(BILINGUAL_SEPARATOR_MARKER)
    assert text.index(BILINGUAL_SEPARATOR_MARKER) < text.index("English")


def test_title_screen_is_bilingual():
    title, body = title_screen_text()
    assert title == "Thermal Captcha"
    assert "Drücken Sie Enter" in body
    assert "Press Enter to start" in body
    assert body.index("Drücken Sie Enter") < body.index("Press Enter to start")


def test_instructions_screen_layout():
    text = instructions_screen_text()
    assert text.index("Anleitung") < text.index("grünen Punkt")
    assert text.index("Drücken Sie Enter zum Fortfahren") < text.index(BILINGUAL_SEPARATOR_MARKER)
    assert text.index(BILINGUAL_SEPARATOR_MARKER) < text.index("Instructions")
    assert text.index("Instructions") < text.index("green dot")
    assert text.index("green dot") < text.index("Press Enter to continue")
    assert text.count(BILINGUAL_SEPARATOR_MARKER) == 1


def test_ready_screen_bilingual():
    text = ready_screen_text()
    assert "Sind Sie bereit" in text
    assert "Are you ready to play Thermal Captcha" in text
    assert text.index("Sind Sie bereit") < text.index(BILINGUAL_SEPARATOR_MARKER)
    assert text.index(BILINGUAL_SEPARATOR_MARKER) < text.index("Are you ready")


def test_thanks_screen_bilingual():
    text = thanks_screen_text()
    assert "Vielen Dank" in text
    assert "Thanks for playing Thermal Captcha" in text
    assert text.index("Vielen Dank") < text.index(BILINGUAL_SEPARATOR_MARKER)
    assert text.index(BILINGUAL_SEPARATOR_MARKER) < text.index("Thanks for playing")


def test_perfect_score_hides_above_line_bilingual():
    text = format_comparison_bilingual(TRIALS_PER_PERSON, above=2, same=1, below=5)
    assert "or more correct" not in text
    assert "oder mehr richtig" not in text
    assert "dasselbe Ergebnis" in text
    assert "same as you" in text


def test_zero_score_hides_below_line_bilingual():
    text = format_comparison_bilingual(0, above=3, same=0, below=4)
    assert "or less" not in text
    assert "oder weniger" not in text


def test_first_player_results_bilingual():
    text = first_player_results_text(7)
    assert "Sie haben 7 von 10" in text
    assert "You got 7 out of 10" in text
    assert "erste Person" in text
    assert "first person" in text
    assert "Drücken Sie Enter zum Fortfahren" in text
    assert "Press Enter to continue" in text


def test_comparison_results_bilingual():
    text = comparison_results_text(8, above=2, same=1, below=3)
    assert "8 von 10" in text
    assert "8 out of 10" in text
    assert "9 oder mehr" in text
    assert "9 or more" in text
    assert "same as you (8)" not in text
    assert "same as you" in text
    assert "Drücken Sie Enter zum Fortfahren" in text
    assert "Press Enter to continue" in text
