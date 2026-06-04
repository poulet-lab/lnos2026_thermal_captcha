"""Game session logic."""

from __future__ import annotations

import random

from rich.console import Console
from rich.panel import Panel

from .difficulty import Difficulty, allowed_amplitudes, stimulus_names_for_difficulty
from .display import ParticipantDisplay
from .globals import (
    CHOICE_COUNT,
    SECOND_MONITOR_HEIGHT,
    SECOND_MONITOR_INDEX,
    SECOND_MONITOR_OFFSET,
    SECOND_MONITOR_WIDTH,
    TRIALS_PER_PERSON,
    current_environment,
)
from .monitors import format_monitors_for_log, get_monitor
from .rankings import is_first_player, score_comparison
from .responses import append_trial, next_person_number
from .stimuli import STIMULUS_POOL, StimulusDefinition
from .tcs_controller import ThermodeController

console = Console()


def sample_trial_stimuli(
    difficulty: Difficulty,
    n: int = TRIALS_PER_PERSON,
) -> list[StimulusDefinition]:
    pool = list(stimulus_names_for_difficulty(difficulty))
    names = random.sample(pool, k=min(n, len(pool)))
    if len(names) < n:
        names.extend(random.choices(pool, k=n - len(names)))
    return [STIMULUS_POOL[name] for name in names]


def sample_choice_options(correct_name: str, difficulty: Difficulty) -> list[str]:
    pool = [n for n in stimulus_names_for_difficulty(difficulty) if n != correct_name]
    distractors = random.sample(pool, k=CHOICE_COUNT - 1)
    options = [correct_name, *distractors]
    random.shuffle(options)
    return options


def run_game(
    difficulty: Difficulty,
    display: ParticipantDisplay | None = None,
    thermode: ThermodeController | None = None,
) -> int:
    person = next_person_number()
    environment = current_environment()
    amp_text = ", ".join(str(a) for a in allowed_amplitudes(difficulty))
    console.print(
        f"\n[bold green]Starting game for Person {person}[/bold green] "
        f"[dim]({environment}, difficulty={difficulty.value}, amplitudes: {amp_text})[/dim]"
    )
    console.print("[dim]Detected monitors:[/dim]")
    for line in format_monitors_for_log():
        console.print(f"[dim]{line}[/dim]")
    target = get_monitor(
        SECOND_MONITOR_INDEX,
        SECOND_MONITOR_OFFSET,
        fallback_width=SECOND_MONITOR_WIDTH,
        fallback_height=SECOND_MONITOR_HEIGHT,
    )
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

        trials = sample_trial_stimuli(difficulty)
        for trial_idx, stimulus in enumerate(trials, start=1):
            console.print(f"[dim]Trial {trial_idx}/{TRIALS_PER_PERSON}: {stimulus.name}[/dim]")
            display.show_round_progress(trial_idx)
            display.show_attention(on=True)
            thermode.deliver(
                stimulus,
                person=person,
                trial=trial_idx,
                environment=environment,
            )
            display.show_attention(on=False)

            options = sample_choice_options(stimulus.name, difficulty)
            chosen = display.show_choices(options)
            display.show_round_progress(trial_idx)
            correct = chosen == stimulus.name
            if correct:
                score += 1
            append_trial(
                person,
                trial_idx,
                stimulus.name,
                chosen,
                correct,
                environment=environment,
                difficulty=difficulty.value,
            )
            console.print(
                f"  chosen={chosen} [{'green' if correct else 'red'}]"
                f"{'✓' if correct else '✗'}[/]"
            )

        first = is_first_player(
            exclude_person=person,
            environment=environment,
            difficulty=difficulty,
        )
        if first:
            display.show_results(score, is_first_player=True)
        else:
            above, same, below = score_comparison(
                score,
                exclude_person=person,
                environment=environment,
                difficulty=difficulty,
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
