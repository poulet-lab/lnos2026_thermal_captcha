"""Deliver all non-flat stimuli in isolation for TCS calibration."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from rich.console import Console

from .analyze_calibration import run_analysis
from .globals import AMPLITUDES, CALIBRATION_TRACES_DIR, current_environment
from .stimuli import STIMULUS_POOL, Family, StimulusDefinition
from .tcs_controller import ThermodeController

console = Console()

CALIBRATION_ENVIRONMENT = "calibration"
DEFAULT_SETTLE_DELAY_S = 5.0


@dataclass(frozen=True)
class TcsParams:
    surface: int
    baseline: float
    target: float
    rise_rate: float
    return_speed: float
    duration: int


def calibration_stimulus_order() -> list[StimulusDefinition]:
    """Pulse, then slow_up, then fast_up; by amplitude; positive before negative."""
    order: list[StimulusDefinition] = []
    for family in (Family.PULSE, Family.SLOW_UP_FAST_DOWN, Family.FAST_UP_SLOW_DOWN):
        for amplitude in AMPLITUDES:
            for direction in (1, -1):
                dir_label = "pos" if direction > 0 else "neg"
                name = f"{family.value}_{dir_label}_{int(amplitude)}"
                order.append(STIMULUS_POOL[name])
    return order


def _tcs_params(stimulus: StimulusDefinition) -> TcsParams | None:
    tcs = stimulus.to_tcs_stimulus()
    if tcs is None:
        return None
    return TcsParams(
        surface=tcs.surface,
        baseline=tcs.baseline,
        target=tcs.target,
        rise_rate=tcs.rise_rate,
        return_speed=tcs.return_speed,
        duration=tcs.duration,
    )


def run_calibration(
    output_dir: Path | None = None,
    settle_delay_s: float = DEFAULT_SETTLE_DELAY_S,
    thermode: ThermodeController | None = None,
) -> Path:
    if output_dir is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = CALIBRATION_TRACES_DIR / f"run_{stamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    environment = current_environment()
    console.print(f"\n[bold green]Stimulus calibration[/bold green] [dim]({environment})[/dim]")
    console.print(f"[dim]Output: {output_dir}[/dim]")
    console.print(f"[dim]Settle delay between stimuli: {settle_delay_s:.1f}s[/dim]\n")

    own_thermode = thermode is None
    thermode = thermode or ThermodeController()
    if own_thermode:
        thermode.open()

    manifest_rows: list[dict] = []
    stimuli = calibration_stimulus_order()

    try:
        for trial_idx, stimulus in enumerate(stimuli, start=1):
            console.print(f"[bold]Trial {trial_idx}/{len(stimuli)}: {stimulus.name}[/bold]")
            tcs = _tcs_params(stimulus)
            if tcs is not None:
                console.print(
                    f"[dim]  TCS target={tcs.target:.1f}C rise={tcs.rise_rate:.2f} "
                    f"return={tcs.return_speed:.2f} duration={tcs.duration}ms[/dim]"
                )

            if trial_idx > 1:
                thermode.halt()
                console.print(f"[dim]  settling {settle_delay_s:.1f}s...[/dim]")
                time.sleep(settle_delay_s)

            thermode.deliver(
                stimulus,
                person=0,
                trial=trial_idx,
                environment=CALIBRATION_ENVIRONMENT,
                traces_dir=output_dir,
            )

            csv_path = output_dir / f"{stimulus.name}.csv"
            png_path = output_dir / f"{stimulus.name}.png"
            manifest_rows.append(
                {
                    "trial": trial_idx,
                    "stimulus_name": stimulus.name,
                    "family": stimulus.family.value,
                    "amplitude": stimulus.amplitude,
                    "direction": stimulus.direction,
                    "target": stimulus.target,
                    "csv": str(csv_path),
                    "png": str(png_path),
                    "tcs": asdict(tcs) if tcs is not None else None,
                }
            )
            console.print()

        manifest = {
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "environment": environment,
            "settle_delay_s": settle_delay_s,
            "stimuli": manifest_rows,
        }
        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        console.print(f"[dim]Manifest: {manifest_path}[/dim]\n")

        run_analysis(output_dir, console=console)
        return output_dir
    finally:
        if own_thermode:
            thermode.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run isolated TCS stimulus calibration")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output folder (default: data/raw/thermal_traces/calibration/run_YYYYMMDD_HHMMSS)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_SETTLE_DELAY_S,
        help="Seconds to wait between stimuli (default: 5)",
    )
    args = parser.parse_args()
    run_calibration(output_dir=args.output, settle_delay_s=args.delay)


if __name__ == "__main__":
    main()
