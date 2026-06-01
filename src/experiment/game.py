"""Game session logic."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from rich.console import Console
from rich.prompt import Prompt

from .config import Settings, load_settings
from .display import ParticipantDisplay
from .globals import CHOICE_COUNT, TRIALS_PER_PERSON
from .rankings import score_comparison
from .responses import append_trial, next_person_number
from .stimuli import STIMULUS_NAMES, STIMULUS_POOL, StimulusDefinition
from .tcs_controller import ThermodeController

if TYPE_CHECKING:
    pass

console = Console()


def sample_trial_stimuli(n: int = TRIALS_PER_PERSON) -> list[StimulusDefinition]:
    names = random.sample(list(STIMULUS_NAMES), k=min(n, len(STIMULUS_NAMES)))
    if len(names) < n:
        names.extend(random.choices(list(STIMULUS_NAMES), k=n - len(names)))
    return [STIMULUS_POOL[name] for name in names]


def sample_choice_options(correct_name: str) -> list[str]:
    pool = [n for n in STIMULUS_NAMES if n != correct_name]
    distractors = random.sample(pool, k=CHOICE_COUNT - 1)
    options = [correct_name, *distractors]
    random.shuffle(options)
    return options


def run_game(
    display: ParticipantDisplay | None = None,
    thermode: ThermodeController | None = None,
    settings: Settings | None = None,
) -> int:
    settings = settings or load_settings()
    person = next_person_number()
    console.print(f"\n[bold green]Starting game for Person {person}[/bold green]")

    own_display = display is None
    own_thermode = thermode is None
    display = display or ParticipantDisplay(settings=settings)
    thermode = thermode or ThermodeController(settings=settings)

    if own_display:
        display.start()
    if own_thermode:
        thermode.open()

    score = 0
    try:
        display.show_title()
        Prompt.ask("\n[white]Press Enter when ready to start[/white]", default="")
        display.show_instructions()
        Prompt.ask("\n[white]Press Enter after reading instructions[/white]", default="")

        trials = sample_trial_stimuli()
        for trial_idx, stimulus in enumerate(trials, start=1):
            console.print(f"[dim]Trial {trial_idx}/{TRIALS_PER_PERSON}: {stimulus.name}[/dim]")
            display.show_attention(on=True)
            thermode.deliver(stimulus)
            display.show_attention(on=False)

            options = sample_choice_options(stimulus.name)
            chosen = display.show_choices(options)
            correct = chosen == stimulus.name
            if correct:
                score += 1
            append_trial(person, trial_idx, stimulus.name, chosen, correct)
            console.print(
                f"  chosen={chosen} [{'green' if correct else 'red'}]"
                f"{'✓' if correct else '✗'}[/]"
            )

        above, same, below = score_comparison(score)
        display.show_results(score, above, same, below)
        console.print(
            f"\n[bold]Person {person} finished: {score}/{TRIALS_PER_PERSON} correct[/bold]"
        )
        Prompt.ask("\n[white]Press Enter to return to menu[/white]", default="")
        return person
    finally:
        if own_thermode:
            thermode.close()
        if own_display:
            display.stop()
