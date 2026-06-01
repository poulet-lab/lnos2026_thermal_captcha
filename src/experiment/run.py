"""Thermal Captcha — operator entry point."""

from __future__ import annotations

import signal
import sys
import traceback

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from .config import load_settings
from .game import run_game
from .globals import TRIALS_PER_PERSON
from .rankings import person_scores, score_distribution, stimulus_trace_ranking
from .session_log import log_error, log_script_event
from .tcs_controller import ThermodeController

console = Console()
_thermode: ThermodeController | None = None


def _signal_handler(sig, frame) -> None:
    console.print("\n[bold red]Interrupt detected — closing thermode…[/bold red]")
    global _thermode
    if _thermode is not None:
        try:
            _thermode.halt()
            _thermode.close()
        except Exception:
            pass
    sys.exit(0)


def display_main_menu() -> str:
    console.rule("[bold cyan]THERMAL CAPTCHA — CONTROL PANEL")
    settings = load_settings()
    mode = "[yellow]MOCK TCS[/yellow]" if settings.mock_tcs else f"[green]TCS {settings.tcs_port}[/green]"
    console.print(f"Mode: {mode}\n")
    console.print("[purple]1.[/purple] Start game")
    console.print("[purple]2.[/purple] See stimulus-trace ranking")
    console.print("[purple]3.[/purple] See person ranking")
    console.print("[purple]0.[/purple] Exit")

    choice = Prompt.ask("[white]Enter your choice[/white] [purple](0-3)[/purple]", default="")
    mapping = {"1": "start_game", "2": "trace_ranking", "3": "person_ranking", "0": "exit"}
    return mapping.get(choice, "invalid")


def show_trace_ranking() -> None:
    ranking = stimulus_trace_ranking()
    table = Table(title="Stimulus trace ranking (correct identifications)")
    table.add_column("Stimulus", style="cyan")
    table.add_column("Correct count", justify="right")
    if not ranking:
        console.print("[yellow]No data yet.[/yellow]")
        return
    for name, count in ranking:
        table.add_row(name, str(count))
    console.print(table)


def show_person_ranking() -> None:
    dist = score_distribution()
    table = Table(title="Person score distribution")
    table.add_column("Score (out of 10)", justify="right")
    table.add_column("Number of people", justify="right")
    if not dist:
        console.print("[yellow]No data yet.[/yellow]")
        return
    for score in range(TRIALS_PER_PERSON, -1, -1):
        if score in dist:
            table.add_row(str(score), str(dist[score]))
    console.print(table)
    scores = person_scores()
    if scores:
        console.print(f"\n[dim]{len(scores)} people played so far.[/dim]")


def main() -> None:
    global _thermode
    log_script_event("start", "run")
    signal.signal(signal.SIGINT, _signal_handler)

    while True:
        choice = display_main_menu()
        if choice == "start_game":
            try:
                run_game(settings=load_settings())
            except KeyboardInterrupt:
                console.print("\n[yellow]Game interrupted.[/yellow]")
        elif choice == "trace_ranking":
            show_trace_ranking()
        elif choice == "person_ranking":
            show_person_ranking()
        elif choice == "exit":
            console.print("\n[bold green]Goodbye![/bold green]")
            break
        else:
            console.print("[red]Invalid choice. Enter 0, 1, 2, or 3.[/red]")

    log_script_event("end", "run")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log_error("run", str(sys.exc_info()[1]), traceback.format_exc())
        raise
