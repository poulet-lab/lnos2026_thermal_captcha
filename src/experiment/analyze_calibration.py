"""Analyze thermal calibration or troubleshooting trace folders."""

from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .globals import BASELINE_TEMPERATURE
from .stimuli import STIMULUS_POOL, Family, StimulusDefinition

OK_SCORE = 0.8
WEAK_SCORE = 0.3
MIN_SAMPLES = 50

REPORT_FILES = {"calibration_report.csv", "manifest.json", "calibration_summary.txt"}


@dataclass(frozen=True)
class TraceMetrics:
    stimulus_name: str
    family: str
    amplitude: float
    direction: int
    target_temp: float
    n_samples: int
    duration_s: float
    sample_rate_hz: float
    primary_channel: str
    peak_temp: float
    peak_error: float
    range_c: float
    expected_amplitude: float
    score: float
    status: str
    csv_path: str


def stimulus_name_from_csv(path: Path) -> str | None:
    stem = path.stem
    if stem in STIMULUS_POOL:
        return stem
    match = re.search(r"_t\d+_(.+)$", stem)
    if match and match.group(1) in STIMULUS_POOL:
        return match.group(1)
    return None


def _primary_channel(rows: list[dict[str, float]]) -> str:
    channels = ("s0", "s1", "s2", "s3", "s4")
    best = channels[0]
    best_range = -1.0
    for channel in channels:
        values = [float(row[channel]) for row in rows]
        channel_range = max(values) - min(values)
        if channel_range > best_range:
            best_range = channel_range
            best = channel
    return best


def _peak_for_stimulus(rows: list[dict[str, float]], channel: str, stimulus: StimulusDefinition) -> float:
    values = [float(row[channel]) for row in rows]
    if stimulus.direction >= 0:
        return max(values)
    return min(values)


def _status_for(score: float, n_samples: int) -> str:
    if n_samples < MIN_SAMPLES:
        return "sparse_sampling"
    if score >= OK_SCORE:
        return "ok"
    if score >= WEAK_SCORE:
        return "weak"
    return "failed"


def analyze_trace_csv(path: Path, stimulus: StimulusDefinition | None = None) -> TraceMetrics | None:
    stimulus_name = stimulus_name_from_csv(path)
    if stimulus_name is None:
        return None
    if stimulus is None:
        stimulus = STIMULUS_POOL[stimulus_name]

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None

    channel = _primary_channel(rows)
    duration_s = float(rows[-1]["elapsed_time"]) - float(rows[0]["elapsed_time"])
    sample_rate = len(rows) / duration_s if duration_s > 0 else 0.0
    values = [float(row[channel]) for row in rows]
    peak_temp = _peak_for_stimulus(rows, channel, stimulus)
    range_c = max(values) - min(values)
    expected = stimulus.amplitude if stimulus.family is not Family.FLAT else 0.0
    score = range_c / expected if expected > 0 else (1.0 if range_c < 0.5 else 0.0)

    return TraceMetrics(
        stimulus_name=stimulus_name,
        family=stimulus.family.value,
        amplitude=stimulus.amplitude,
        direction=stimulus.direction,
        target_temp=stimulus.target,
        n_samples=len(rows),
        duration_s=duration_s,
        sample_rate_hz=sample_rate,
        primary_channel=channel,
        peak_temp=peak_temp,
        peak_error=abs(peak_temp - stimulus.target),
        range_c=range_c,
        expected_amplitude=expected,
        score=score,
        status=_status_for(score, len(rows)),
        csv_path=str(path),
    )


def analyze_folder(folder: Path) -> list[TraceMetrics]:
    metrics: list[TraceMetrics] = []
    for csv_path in sorted(folder.glob("*.csv")):
        if csv_path.name in REPORT_FILES:
            continue
        result = analyze_trace_csv(csv_path)
        if result is not None:
            metrics.append(result)
    return metrics


def save_report(metrics: list[TraceMetrics], folder: Path) -> Path:
    report_path = folder / "calibration_report.csv"
    fieldnames = list(asdict(metrics[0]).keys()) if metrics else []
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        if not metrics:
            return report_path
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics:
            writer.writerow(asdict(row))
    return report_path


def save_summary_text(metrics: list[TraceMetrics], folder: Path) -> Path:
    summary_path = folder / "calibration_summary.txt"
    lines = [
        "Thermal calibration summary",
        f"Baseline reference: {BASELINE_TEMPERATURE}C",
        "",
    ]
    for row in metrics:
        lines.append(
            f"{row.stimulus_name:35} {row.status:16} "
            f"range={row.range_c:5.1f}C target={row.target_temp:5.1f}C "
            f"peak={row.peak_temp:5.1f}C n={row.n_samples:4d}"
        )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path


def print_summary_table(metrics: list[TraceMetrics], console: Console | None = None) -> None:
    out = console or Console()
    if not metrics:
        out.print("[yellow]No trace CSV files found to analyze.[/yellow]")
        return

    table = Table(title="Calibration analysis")
    table.add_column("Stimulus")
    table.add_column("Family")
    table.add_column("Status")
    table.add_column("Range", justify="right")
    table.add_column("Target", justify="right")
    table.add_column("Peak", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("N", justify="right")

    current_family = None
    for row in metrics:
        if row.family != current_family:
            if current_family is not None:
                table.add_section()
            current_family = row.family
        table.add_row(
            row.stimulus_name,
            row.family,
            row.status,
            f"{row.range_c:.1f}",
            f"{row.target_temp:.1f}",
            f"{row.peak_temp:.1f}",
            f"{row.score:.2f}",
            str(row.n_samples),
        )

    out.print()
    out.print(table)
    out.print()


def run_analysis(folder: Path, console: Console | None = None) -> list[TraceMetrics]:
    out = console or Console()
    folder = folder.resolve()
    metrics = analyze_folder(folder)
    if not metrics:
        out.print(f"[yellow]No analyzable traces in {folder}[/yellow]")
        return metrics

    report_path = save_report(metrics, folder)
    summary_path = save_summary_text(metrics, folder)
    print_summary_table(metrics, console=out)
    out.print(f"[dim]Report: {report_path}[/dim]")
    out.print(f"[dim]Summary: {summary_path}[/dim]")
    return metrics


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Analyze thermal calibration trace folder")
    parser.add_argument("folder", type=Path, help="Folder containing trace CSV files")
    args = parser.parse_args()
    run_analysis(args.folder)


if __name__ == "__main__":
    main()
