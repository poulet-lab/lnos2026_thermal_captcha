"""Load configuration from environment."""

import os
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    return value in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    tcs_port: str
    tcs_maximum_temperature: float
    mock_tcs: bool
    second_monitor_offset: int


def load_settings() -> Settings:
    load_dotenv(find_dotenv(usecwd=True))
    return Settings(
        tcs_port=os.getenv("TCS_PORT", "COM3"),
        tcs_maximum_temperature=float(os.getenv("TCS_MAXIMUM_TEMPERATURE", "45")),
        mock_tcs=_env_bool("MOCK_TCS", default=True),
        second_monitor_offset=int(os.getenv("SECOND_MONITOR_OFFSET", "1920")),
    )
