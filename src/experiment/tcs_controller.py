"""TCS thermode control with mock mode for development."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from .globals import MOCK_TCS, TCS_MAXIMUM_TEMPERATURE, TCS_PORT
from .stimuli import StimulusDefinition
from .thermal_traces import ThermalRecorder, save_thermal_trace

if TYPE_CHECKING:
    from poulet_py import TCS

console = Console()


class ThermodeController:
    def __init__(self) -> None:
        self._device: TCS | None = None

    @property
    def is_mock(self) -> bool:
        return MOCK_TCS

    def open(self) -> None:
        if self.is_mock:
            return
        from poulet_py import TCS

        self._device = TCS(
            port=TCS_PORT,
            maximum_temperature=TCS_MAXIMUM_TEMPERATURE,
        )
        self._device.open()

    def close(self) -> None:
        if self._device is not None:
            try:
                self._device.close()
            finally:
                self._device = None

    def deliver(
        self,
        stimulus: StimulusDefinition,
        *,
        person: int,
        trial: int,
        environment: str,
        traces_dir: Path | None = None,
    ) -> None:
        if self.is_mock:
            time.sleep(stimulus.delivery_duration_s)
            return

        assert self._device is not None
        recorder = ThermalRecorder(self._device)
        recorder.start()
        try:
            tcs_stim = stimulus.to_tcs_stimulus()
            if tcs_stim is None:
                time.sleep(stimulus.delivery_duration_s)
            else:
                from poulet_py import TCSCommand

                self._device.execute_command(TCSCommand.HALT_STIMULATION)
                time.sleep(0.05)
                self._device.trigger(tcs_stim)
                deadline = time.monotonic() + stimulus.delivery_duration_s
                while time.monotonic() < deadline:
                    if not self._device.stimulus_running:
                        remaining = deadline - time.monotonic()
                        if remaining > 0:
                            time.sleep(remaining)
                        break
                    time.sleep(0.01)
        finally:
            rows = recorder.stop()
            if rows:
                try:
                    csv_path, png_path, plot_channels = save_thermal_trace(
                        rows,
                        stimulus,
                        person=person,
                        trial=trial,
                        environment=environment,
                        console=console,
                        output_dir=traces_dir,
                    )
                    console.print(f"[dim]  thermal trace: {csv_path}[/dim]")
                    console.print(
                        f"[dim]  thermal plot:  {png_path} "
                        f"(channels: {', '.join(plot_channels)})[/dim]"
                    )
                except Exception as exc:
                    console.print(
                        f"[yellow]Warning: failed to save thermal trace: {exc}[/yellow]"
                    )
            else:
                console.print("[yellow]Warning: no thermal samples recorded[/yellow]")

    def halt(self) -> None:
        if self._device is not None and not self.is_mock:
            from poulet_py import TCSCommand

            self._device.execute_command(TCSCommand.HALT_STIMULATION)

    def __enter__(self) -> ThermodeController:
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
