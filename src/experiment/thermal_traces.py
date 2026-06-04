"""Record and save per-trial thermal traces."""

from __future__ import annotations

import csv
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rich.console import Console

from .globals import (
    BASELINE_TEMPERATURE,
    THERMAL_TRACES_DIR,
    THERMAL_TRACE_SAMPLING_HZ,
    TRACE_PLOT_Y_MAX,
    TRACE_PLOT_Y_MIN,
)
from .stimuli import Family

if TYPE_CHECKING:
    from poulet_py import TCS

    from .stimuli import StimulusDefinition

TRACE_CSV_COLUMNS = ("elapsed_time", "s0", "s1", "s2", "s3", "s4")
TEMPERATURE_CHANNELS = ("s0", "s1", "s2", "s3", "s4")
PLOT_CHANNEL_COUNT = 2


class ThermalRecorder:
    """Drain the TCS circular buffer so we keep up with ~100 Hz acquisition."""

    def __init__(
        self,
        device: TCS,
        sampling_hz: float = THERMAL_TRACE_SAMPLING_HZ,
    ) -> None:
        self._device = device
        self._poll_interval = 1.0 / sampling_hz
        self._active = False
        self._rows: list[dict[str, float]] = []
        self._thread: threading.Thread | None = None
        self._last_buffer_idx = 0
        self._t0_ns: int | None = None

    def start(self) -> None:
        self._rows = []
        self._t0_ns = None
        with self._device._sampling_cond:  # noqa: SLF001
            self._last_buffer_idx = self._device._buffer_idx  # noqa: SLF001
        self._active = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def stop(self) -> list[dict[str, float]]:
        self._active = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._drain_buffer()
        return self._rows

    def _append_sample(self, sample) -> None:
        ts = int(sample["timestamp"])
        if self._t0_ns is None:
            self._t0_ns = ts
        self._rows.append(
            {
                "elapsed_time": (ts - self._t0_ns) / 1e9,
                "s0": float(sample["s0"]),
                "s1": float(sample["s1"]),
                "s2": float(sample["s2"]),
                "s3": float(sample["s3"]),
                "s4": float(sample["s4"]),
            }
        )

    def _drain_buffer(self) -> None:
        device = self._device
        with device._sampling_cond:  # noqa: SLF001
            total = device._buffer_idx  # noqa: SLF001
            buffer = device._buffer  # noqa: SLF001
            buffer_size = device.buffer_size

        while self._last_buffer_idx < total:
            idx = self._last_buffer_idx % buffer_size
            self._append_sample(buffer[idx])
            self._last_buffer_idx += 1

    def _record_loop(self) -> None:
        while self._active:
            loop_start = time.monotonic()
            try:
                self._drain_buffer()
            except (RuntimeError, AttributeError):
                pass

            elapsed = time.monotonic() - loop_start
            sleep_time = max(0.0, self._poll_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)


def channel_stats(rows: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    stats: dict[str, dict[str, float]] = {}
    for channel in TEMPERATURE_CHANNELS:
        values = [row[channel] for row in rows]
        stats[channel] = {
            "start": values[0],
            "end": values[-1],
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
        }
    return stats


def pick_plot_channels(rows: list[dict[str, float]], count: int = PLOT_CHANNEL_COUNT) -> tuple[str, ...]:
    """Pick the channels with the largest temperature swing (usually s0 + s1)."""
    stats = channel_stats(rows)
    ranked = sorted(
        TEMPERATURE_CHANNELS,
        key=lambda channel: stats[channel]["range"],
        reverse=True,
    )
    return tuple(ranked[:count])


def print_trace_debug(
    rows: list[dict[str, float]],
    stimulus: StimulusDefinition,
    plot_channels: tuple[str, ...],
    *,
    console: Console | None = None,
) -> None:
    out = console or Console()
    stats = channel_stats(rows)
    duration = rows[-1]["elapsed_time"] - rows[0]["elapsed_time"]
    rate = len(rows) / duration if duration > 0 else 0.0
    plot_set = set(plot_channels)

    out.print(
        f"  [dim]thermal debug ({stimulus.name}): "
        f"{len(rows)} samples, {duration:.2f}s, {rate:.0f} Hz[/dim]"
    )
    for channel in TEMPERATURE_CHANNELS:
        s = stats[channel]
        marker = "[cyan]* plot[/cyan]" if channel in plot_set else ""
        out.print(
            f"    {channel}: {s['start']:.1f} -> {s['end']:.1f}C "
            f"(range {s['range']:.2f}C) {marker}"
        )


def trace_paths(
    environment: str,
    person: int,
    trial: int,
    stimulus_name: str,
    *,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / f"{stimulus_name}.csv", output_dir / f"{stimulus_name}.png"

    person_dir = THERMAL_TRACES_DIR / environment / f"person_{person}"
    person_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{environment}_p{person:02d}_t{trial:02d}_{stimulus_name}"
    return person_dir / f"{stem}.csv", person_dir / f"{stem}.png"


def save_thermal_trace_csv(rows: list[dict[str, float]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TRACE_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def save_thermal_trace_plot(
    rows: list[dict[str, float]],
    path: Path,
    stimulus: StimulusDefinition,
    *,
    person: int,
    trial: int,
    plot_channels: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    if not rows:
        return ()

    channels = plot_channels or pick_plot_channels(rows)
    elapsed = [r["elapsed_time"] for r in rows]

    _, ax = plt.subplots(figsize=(10, 6))
    for channel in channels:
        values = [r[channel] for r in rows]
        ax.plot(elapsed, values, label=channel, linewidth=2)
    ax.axhline(
        BASELINE_TEMPERATURE,
        color="gray",
        linestyle="--",
        alpha=0.7,
        label=f"Baseline ({BASELINE_TEMPERATURE}°C)",
    )

    if stimulus.family is not Family.FLAT:
        target = stimulus.target
        ax.axhline(
            target,
            color="red",
            linestyle="--",
            alpha=0.7,
            label=f"Target ({target:.1f}°C)",
        )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title(f"{stimulus.name} (p{person} t{trial})")
    ax.set_ylim(TRACE_PLOT_Y_MIN, TRACE_PLOT_Y_MAX)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return channels


def save_thermal_trace(
    rows: list[dict[str, float]],
    stimulus: StimulusDefinition,
    *,
    person: int,
    trial: int,
    environment: str,
    console: Console | None = None,
    output_dir: Path | None = None,
) -> tuple[Path, Path, tuple[str, ...]]:
    plot_channels = pick_plot_channels(rows)
    csv_path, png_path = trace_paths(
        environment,
        person,
        trial,
        stimulus.name,
        output_dir=output_dir,
    )
    save_thermal_trace_csv(rows, csv_path)
    save_thermal_trace_plot(
        rows,
        png_path,
        stimulus,
        person=person,
        trial=trial,
        plot_channels=plot_channels,
    )
    print_trace_debug(rows, stimulus, plot_channels, console=console)
    return csv_path, png_path, plot_channels
