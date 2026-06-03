"""TCS thermode control with mock mode for development."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from .globals import MOCK_TCS, TCS_MAXIMUM_TEMPERATURE, TCS_PORT
from .stimuli import StimulusDefinition

if TYPE_CHECKING:
    from poulet_py import TCS


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

    def deliver(self, stimulus: StimulusDefinition) -> None:
        if self.is_mock:
            time.sleep(stimulus.delivery_duration_s)
            return

        assert self._device is not None
        tcs_stim = stimulus.to_tcs_stimulus()
        if tcs_stim is None:
            time.sleep(stimulus.delivery_duration_s)
            return

        self._device.trigger(tcs_stim)
        deadline = time.monotonic() + stimulus.delivery_duration_s
        while time.monotonic() < deadline:
            if not self._device.stimulus_running:
                remaining = deadline - time.monotonic()
                if remaining > 0:
                    time.sleep(remaining)
                break
            time.sleep(0.01)

    def halt(self) -> None:
        if self._device is not None and not self.is_mock:
            from poulet_py import TCSCommand

            self._device.execute_command(TCSCommand.HALT_STIMULATION)

    def __enter__(self) -> ThermodeController:
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
