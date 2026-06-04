"""Thermal Captcha — operator entry point."""

from __future__ import annotations

import signal
import sys
import traceback

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from .difficulty import Difficulty, difficulty_label
from .display import ParticipantDisplay
from .game import run_game
from .globals import MOCK_TCS, TCS_PORT, TRIALS_PER_PERSON, current_environment
from .rankings import person_scores, score_distribution, stimulus_trace_ranking
from .session_log import log_error, log_script_event
from .tcs_controller import ThermodeController

console = Console()
_thermode: ThermodeController | None = None
_display: ParticipantDisplay | None = None

EXIT_REMINDER = (
    "If there aren't any errors and you want to start the game again, please close "
    "the window and click on the Desktop icon again. If there are errors, please take "
    "a picture or copy them and save them so we can resolve them later."
)


def show_exit_reminder() -> None:
    console.print()
    console.print(
        Panel(
            f"[bold yellow]{EXIT_REMINDER}[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
    )
    console.print()


def _signal_handler(sig, frame) -> None:
    console.print("\n[bold red]Interrupt detected — closing thermode…[/bold red]")
    global _thermode, _display
    if _thermode is not None:
        try:
            _thermode.halt()
            _thermode.close()
        except Exception:
            pass
    if _display is not None:
        try:
            _display.stop()
        except Exception:
            pass
    sys.exit(0)


def prompt_difficulty() -> Difficulty | None:
    console.print("\n[bold]Level of difficulty:[/bold]")
    console.print("[purple]1.[/purple] Easy    (±5, ±10 °C)")
    console.print("[purple]2.[/purple] Medium  (±3, ±6 °C)")
    console.print("[purple]3.[/purple] Hard    (±1, ±2 °C)")
    choice = Prompt.ask("[white]Enter your choice[/white] [purple](1-3)[/purple]", default="")
    mapping = {
        "1": Difficulty.EASY,
        "2": Difficulty.MEDIUM,
        "3": Difficulty.HARD,
    }
    return mapping.get(choice)


def display_main_menu() -> str:
    console.rule("[bold cyan]THERMAL CAPTCHA — CONTROL PANEL")
    mode = "[yellow]MOCK TCS[/yellow]" if MOCK_TCS else f"[green]TCS {TCS_PORT}[/green]"
    console.print(f"Mode: {mode}  |  Environment: [cyan]{current_environment()}[/cyan]\n")
    console.print("[purple]1.[/purple] Start game")
    console.print("[purple]2.[/purple] See stimulus-trace ranking")
    console.print("[purple]3.[/purple] See person ranking")
    console.print("[purple]0.[/purple] Exit")

    choice = Prompt.ask("[white]Enter your choice[/white] [purple](0-3)[/purple]", default="")
    mapping = {"1": "start_game", "2": "trace_ranking", "3": "person_ranking", "0": "exit"}
    return mapping.get(choice, "invalid")


def show_trace_ranking() -> None:
    environment = current_environment()
    ranking = stimulus_trace_ranking(environment=environment)
    table = Table(title=f"Stimulus trace ranking — {environment}")
    table.add_column("Stimulus", style="cyan")
    table.add_column("Correct count", justify="right")
    if not ranking:
        console.print("[yellow]No data yet.[/yellow]")
        return
    for name, count in ranking:
        table.add_row(name, str(count))
    console.print(table)


def show_person_ranking() -> None:
    environment = current_environment()
    dist = score_distribution(environment=environment)
    table = Table(title=f"Person score distribution — {environment}")
    table.add_column("Score (out of 10)", justify="right")
    table.add_column("Number of people", justify="right")
    if not dist:
        console.print("[yellow]No data yet.[/yellow]")
        return
    for score in range(TRIALS_PER_PERSON, -1, -1):
        if score in dist:
            table.add_row(str(score), str(dist[score]))
    console.print(table)
    scores = person_scores(environment=environment)
    if scores:
        console.print(f"\n[dim]{len(scores)} people played in {environment} so far.[/dim]")


def _close_display() -> None:
    global _display
    if _display is not None:
        try:
            _display.stop()
        except Exception:
            pass
        _display = None


def main() -> None:
    global _thermode, _display
    log_script_event("start", "run")
    signal.signal(signal.SIGINT, _signal_handler)

    try:
        while True:
            choice = display_main_menu()
            if choice == "start_game":
                try:
                    difficulty = prompt_difficulty()
                    if difficulty is None:
                        console.print("[red]Invalid choice. Enter 1, 2, or 3.[/red]")
                        continue
                    console.print(f"[dim]Selected: {difficulty_label(difficulty)}[/dim]")
                    if _display is None:
                        _display = ParticipantDisplay()
                        _display.start()
                    run_game(display=_display, difficulty=difficulty)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Game interrupted.[/yellow]")
            elif choice == "trace_ranking":
                show_trace_ranking()
            elif choice == "person_ranking":
                show_person_ranking()
            elif choice == "exit":
                show_exit_reminder()
                console.print("[bold green]Goodbye![/bold green]")
                break
            else:
                console.print("[red]Invalid choice. Enter 0, 1, 2, or 3.[/red]")
    finally:
        _close_display()

    log_script_event("end", "run")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log_error("run", str(sys.exc_info()[1]), traceback.format_exc())
        raise
