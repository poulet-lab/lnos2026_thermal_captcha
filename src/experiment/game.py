"""Game session logic."""

from __future__ import annotations

import random

from rich.console import Console
from rich.panel import Panel

from .display import ParticipantDisplay
from .globals import (
    CHOICE_COUNT,
    SECOND_MONITOR_INDEX,
    SECOND_MONITOR_OFFSET,
    TRIALS_PER_PERSON,
    current_environment,
)
from .monitors import format_monitors_for_log, get_monitor
from .rankings import is_first_player, score_comparison
from .responses import append_trial, next_person_number
from .stimuli import STIMULUS_NAMES, STIMULUS_POOL, StimulusDefinition
from .tcs_controller import ThermodeController

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
) -> int:
    person = next_person_number()
    environment = current_environment()
    console.print(f"\n[bold green]Starting game for Person {person}[/bold green] [dim]({environment})[/dim]")
    console.print("[dim]Detected monitors:[/dim]")
    for line in format_monitors_for_log():
        console.print(f"[dim]{line}[/dim]")
    target = get_monitor(SECOND_MONITOR_INDEX, SECOND_MONITOR_OFFSET)
    console.print(
        f"[dim]Using monitor [{SECOND_MONITOR_INDEX}]: "
        f"{target.width}x{target.height} at ({target.x}, {target.y})[/dim]"
    )
    console.print()
    console.print(
        Panel(
            "[bold yellow]Click once on the other screen to show the screen of the Thermal Captcha game[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
    )
    console.print()

    own_display = display is None
    own_thermode = thermode is None
    display = display or ParticipantDisplay()
    thermode = thermode or ThermodeController()

    if own_display:
        display.start()
    if own_thermode:
        thermode.open()

    score = 0
    try:
        display.show_title()
        display.wait_for_enter()
        display.show_instructions()
        display.wait_for_enter()
        display.show_ready()
        display.wait_for_enter()

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
            append_trial(person, trial_idx, stimulus.name, chosen, correct, environment=environment)
            console.print(
                f"  chosen={chosen} [{'green' if correct else 'red'}]"
                f"{'✓' if correct else '✗'}[/]"
            )

        first = is_first_player(exclude_person=person, environment=environment)
        if first:
            display.show_results(score, is_first_player=True)
        else:
            above, same, below = score_comparison(
                score, exclude_person=person, environment=environment
            )
            display.show_results(
                score,
                is_first_player=False,
                above=above,
                same=same,
                below=below,
            )
        console.print(
            f"\n[bold]Person {person} finished: {score}/{TRIALS_PER_PERSON} correct[/bold]"
        )
        display.wait_for_enter()
        display.show_thanks()
        display.wait_for_enter()
        return person
    finally:
        if own_thermode:
            thermode.close()
        if own_display:
            display.stop()
