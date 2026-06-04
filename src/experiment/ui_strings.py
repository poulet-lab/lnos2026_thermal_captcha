"""Bilingual UI strings (German on top, English on bottom)."""

from __future__ import annotations

from typing import TypeAlias

from .globals import TRIALS_PER_PERSON

BilingualBlock: TypeAlias = tuple[str, str]
TitledBilingualSection: TypeAlias = tuple[tuple[str, str], tuple[str, str]]
ResultsBilingualSection: TypeAlias = tuple[tuple[str, str], tuple[str, str]]

# Visible marker when bilingual text is flattened to a string (e.g. tests).
BILINGUAL_SEPARATOR_MARKER = "─" * 48

GAME_NAME = "Thermal Captcha"

PRESS_ENTER_START_DE = "Drücken Sie Enter zum Starten"
PRESS_ENTER_START_EN = "Press Enter to start"

INSTRUCTIONS_TITLE_DE = "Anleitung"
INSTRUCTIONS_TITLE_EN = "Instructions"

INSTRUCTIONS_BODY_DE = (
    "Während Sie den grünen Punkt sehen, achten Sie auf das, was Sie auf Ihrer Haut "
    "durch den Thermostimulator spüren.\n\n"
    "Anschließend sehen Sie sechs Zeichnungen — klicken Sie auf die, die am ehesten "
    "dem entspricht, was Sie gerade gespürt haben."
)
INSTRUCTIONS_BODY_EN = (
    "When you see the green dot, pay attention to what you feel "
    "on your skin through the thermal stimulator.\n\n"
    "You will then see six drawings — click the one that looks most "
    "like what you just felt."
)

PRESS_ENTER_CONTINUE_DE = "Drücken Sie Enter zum Fortfahren"
PRESS_ENTER_CONTINUE_EN = "Press Enter to continue"

READY_DE = (
    "Sind Sie bereit, Thermal Captcha zu spielen? "
    "Drücken Sie Enter, um das Spiel zu starten!"
)
READY_EN = "Are you ready to play Thermal Captcha? Press Enter to start the game!"

THANKS_DE = "Vielen Dank, dass Sie Thermal Captcha gespielt haben!"
THANKS_EN = "Thanks for playing Thermal Captcha"

FIRST_PLAYER_DE = "Sie sind die erste Person, die das Spiel spielt!"
FIRST_PLAYER_EN = "You are the first person to play the game!"


def bilingual_parts(de: str, en: str) -> BilingualBlock:
    return de, en


def bilingual(de: str, en: str) -> str:
    """Stack German above English with a separator marker."""
    return f"{de}\n{BILINGUAL_SEPARATOR_MARKER}\n{en}"


def blocks_to_text(blocks: list[BilingualBlock]) -> str:
    return "\n\n".join(bilingual(de, en) for de, en in blocks)


def score_summary_de(score: int) -> str:
    return f"Sie haben {score} von {TRIALS_PER_PERSON} richtig!"


def score_summary_en(score: int) -> str:
    return f"You got {score} out of {TRIALS_PER_PERSON} correct!"


def format_comparison_lines_de(score: int, above: int, same: int, below: int) -> list[str]:
    lines: list[str] = []
    if score < TRIALS_PER_PERSON:
        lines.append(f"{above} Personen haben {score + 1} oder mehr richtig")
    lines.append(f"{same} Personen haben dasselbe Ergebnis wie Sie")
    if score > 0:
        lines.append(f"{below} Personen haben {score - 1} oder weniger richtig")
    return lines


def format_comparison_lines_en(score: int, above: int, same: int, below: int) -> list[str]:
    lines: list[str] = []
    if score < TRIALS_PER_PERSON:
        lines.append(f"{above} people got {score + 1} or more correct")
    lines.append(f"{same} people got the same as you")
    if score > 0:
        lines.append(f"{below} people got {score - 1} or less")
    return lines


def format_comparison_bilingual(score: int, above: int, same: int, below: int) -> str:
    de = "\n".join(format_comparison_lines_de(score, above, same, below))
    en = "\n".join(format_comparison_lines_en(score, above, same, below))
    return bilingual(de, en)


def title_screen_parts() -> tuple[str, BilingualBlock]:
    return GAME_NAME, bilingual_parts(PRESS_ENTER_START_DE, PRESS_ENTER_START_EN)


def title_screen_text() -> tuple[str, str]:
    title, block = title_screen_parts()
    return title, bilingual(*block)


def instructions_screen_sections() -> TitledBilingualSection:
    de_body = f"{INSTRUCTIONS_BODY_DE}\n\n{PRESS_ENTER_CONTINUE_DE}"
    en_body = f"{INSTRUCTIONS_BODY_EN}\n\n{PRESS_ENTER_CONTINUE_EN}"
    return (INSTRUCTIONS_TITLE_DE, de_body), (INSTRUCTIONS_TITLE_EN, en_body)


def instructions_screen_parts() -> list[BilingualBlock]:
    (de_title, de_body), (en_title, en_body) = instructions_screen_sections()
    return [bilingual_parts(f"{de_title}\n\n{de_body}", f"{en_title}\n\n{en_body}")]


def instructions_screen_text() -> str:
    return blocks_to_text(instructions_screen_parts())


def ready_screen_parts() -> BilingualBlock:
    return bilingual_parts(READY_DE, READY_EN)


def round_progress_parts(trial: int, total: int = TRIALS_PER_PERSON) -> BilingualBlock:
    return f"Runde {trial} von {total}", f"Round {trial} of {total}"


def ready_screen_text() -> str:
    return bilingual(*ready_screen_parts())


def thanks_screen_parts() -> BilingualBlock:
    return bilingual_parts(THANKS_DE, THANKS_EN)


def thanks_screen_text() -> str:
    return bilingual(*thanks_screen_parts())


def first_player_results_sections(score: int) -> ResultsBilingualSection:
    de_body = f"{FIRST_PLAYER_DE}\n\n{PRESS_ENTER_CONTINUE_DE}"
    en_body = f"{FIRST_PLAYER_EN}\n\n{PRESS_ENTER_CONTINUE_EN}"
    return (score_summary_de(score), de_body), (score_summary_en(score), en_body)


def first_player_results_parts(score: int) -> BilingualBlock:
    (de_headline, de_body), (en_headline, en_body) = first_player_results_sections(score)
    return bilingual_parts(f"{de_headline}\n\n{de_body}", f"{en_headline}\n\n{en_body}")


def first_player_results_text(score: int) -> str:
    return bilingual(*first_player_results_parts(score))


def comparison_results_sections(
    score: int, above: int, same: int, below: int
) -> ResultsBilingualSection:
    de_body = "\n".join(format_comparison_lines_de(score, above, same, below))
    de_body = f"{de_body}\n\n{PRESS_ENTER_CONTINUE_DE}"
    en_body = "\n".join(format_comparison_lines_en(score, above, same, below))
    en_body = f"{en_body}\n\n{PRESS_ENTER_CONTINUE_EN}"
    return (score_summary_de(score), de_body), (score_summary_en(score), en_body)


def comparison_results_parts(score: int, above: int, same: int, below: int) -> BilingualBlock:
    (de_headline, de_body), (en_headline, en_body) = comparison_results_sections(
        score, above, same, below
    )
    return bilingual_parts(f"{de_headline}\n\n{de_body}", f"{en_headline}\n\n{en_body}")


def comparison_results_text(score: int, above: int, same: int, below: int) -> str:
    return bilingual(*comparison_results_parts(score, above, same, below))
