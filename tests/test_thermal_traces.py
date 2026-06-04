"""Tests for thermal trace recording and saving."""

from __future__ import annotations

import csv
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.experiment.stimuli import STIMULUS_POOL
from src.experiment.thermal_traces import (
    TRACE_CSV_COLUMNS,
    ThermalRecorder,
    channel_stats,
    pick_plot_channels,
    save_thermal_trace,
    save_thermal_trace_csv,
    save_thermal_trace_plot,
    trace_paths,
)
from src.experiment.tcs_controller import ThermodeController


def _sample_rows(n: int = 5) -> list[dict[str, float]]:
    return [
        {
            "elapsed_time": i * 0.05,
            "s0": 32.0,
            "s1": 32.0 + i * 0.1,
            "s2": 32.0 + i * 0.05,
            "s3": 32.0,
            "s4": 32.0,
        }
        for i in range(n)
    ]


def test_trace_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.experiment.thermal_traces.THERMAL_TRACES_DIR",
        tmp_path / "thermal_traces",
    )
    csv_path, png_path = trace_paths("lnos", 1, 2, "flat")
    assert csv_path == tmp_path / "thermal_traces" / "lnos" / "person_1" / "lnos_p01_t02_flat.csv"
    assert png_path == tmp_path / "thermal_traces" / "lnos" / "person_1" / "lnos_p01_t02_flat.png"
    assert csv_path.parent.is_dir()


def test_save_csv_and_plot(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.experiment.thermal_traces.THERMAL_TRACES_DIR",
        tmp_path / "thermal_traces",
    )
    rows = _sample_rows()
    stimulus = STIMULUS_POOL["pulse_pos_5"]
    csv_path, png_path, plot_channels = save_thermal_trace(
        rows,
        stimulus,
        person=1,
        trial=1,
        environment="lnos",
    )
    assert plot_channels == ("s1", "s2")

    assert csv_path.exists()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == list(TRACE_CSV_COLUMNS)
        saved = list(reader)
    assert len(saved) == len(rows)
    assert float(saved[0]["s1"]) == pytest.approx(32.0)

    assert png_path.exists()
    assert png_path.stat().st_size > 0


def test_save_thermal_trace_csv(tmp_path):
    path = tmp_path / "trace.csv"
    save_thermal_trace_csv(_sample_rows(3), path)
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3


def test_pick_plot_channels_uses_largest_ranges():
    rows = [
        {"elapsed_time": 0.0, "s0": 32.0, "s1": 32.0, "s2": 31.9, "s3": 31.9, "s4": 31.9},
        {"elapsed_time": 1.0, "s0": 42.0, "s1": 41.0, "s2": 32.0, "s3": 32.0, "s4": 32.0},
    ]
    assert pick_plot_channels(rows) == ("s0", "s1")


def test_channel_stats():
    rows = _sample_rows(3)
    stats = channel_stats(rows)
    assert stats["s1"]["range"] == pytest.approx(0.2)
    assert stats["s0"]["range"] == pytest.approx(0.0)


def test_save_thermal_trace_plot_skips_empty(tmp_path):
    stimulus = STIMULUS_POOL["flat"]
    path = tmp_path / "trace.png"
    save_thermal_trace_plot([], path, stimulus, person=1, trial=1)
    assert not path.exists()


def test_save_thermal_trace_plot_returns_channels(tmp_path):
    stimulus = STIMULUS_POOL["pulse_pos_5"]
    path = tmp_path / "trace.png"
    channels = save_thermal_trace_plot(_sample_rows(), path, stimulus, person=1, trial=1)
    assert channels == ("s1", "s2")
    assert path.exists()


def test_recorder_drains_buffer():
    dtype = [("timestamp", "uint64"), *((f"s{i}", "float64") for i in range(5))]
    buffer = np.array(
        [
            (100, 32.0, 32.1, 31.9, 31.9, 31.9),
            (200, 32.5, 32.6, 31.9, 31.9, 31.9),
            (300, 33.0, 33.1, 31.9, 31.9, 31.9),
        ],
        dtype=dtype,
    )

    device = MagicMock()
    device.buffer_size = len(buffer)
    device._buffer = buffer
    device._buffer_idx = 3
    device._sampling_cond = threading.Condition()

    recorder = ThermalRecorder(device)
    recorder._last_buffer_idx = 0
    recorder._drain_buffer()

    assert len(recorder._rows) == 3
    assert recorder._rows[0]["s0"] == pytest.approx(32.0)
    assert recorder._rows[1]["s0"] == pytest.approx(32.5)
    assert recorder._rows[2]["s0"] == pytest.approx(33.0)
    assert recorder._rows[0]["elapsed_time"] == pytest.approx(0.0)
    assert recorder._rows[2]["elapsed_time"] == pytest.approx(200e-9)


def test_deliver_mock_skips_traces(tmp_path, monkeypatch):
    monkeypatch.setattr("src.experiment.tcs_controller.MOCK_TCS", True)
    monkeypatch.setattr(
        "src.experiment.thermal_traces.THERMAL_TRACES_DIR",
        tmp_path / "thermal_traces",
    )
    controller = ThermodeController()
    controller.deliver(
        STIMULUS_POOL["flat"],
        person=1,
        trial=1,
        environment="mock_tcs",
    )
    assert not (tmp_path / "thermal_traces").exists()


def test_deliver_saves_traces(tmp_path, monkeypatch):
    monkeypatch.setattr("src.experiment.tcs_controller.MOCK_TCS", False)
    monkeypatch.setattr(
        "src.experiment.thermal_traces.THERMAL_TRACES_DIR",
        tmp_path / "thermal_traces",
    )

    device = MagicMock()
    device.stimulus_running = False
    device.buffer_size = 1

    sample = np.array(
        (1_000_000_000, 32.0, 32.1, 31.9, 31.9, 31.9),
        dtype=[("timestamp", "uint64"), *((f"s{i}", "float64") for i in range(5))],
    )
    device._buffer = np.array([sample])
    device._buffer_idx = 1
    device._sampling_cond = threading.Condition()

    controller = ThermodeController()
    controller._device = device

    with patch("src.experiment.tcs_controller.ThermalRecorder") as recorder_cls:
        recorder_cls.return_value.stop.return_value = _sample_rows(10)
        with patch("src.experiment.tcs_controller.time.sleep"):
            controller.deliver(
                STIMULUS_POOL["flat"],
                person=2,
                trial=3,
                environment="troubleshooting",
            )

    csv_path = (
        tmp_path
        / "thermal_traces"
        / "troubleshooting"
        / "person_2"
        / "troubleshooting_p02_t03_flat.csv"
    )
    png_path = csv_path.with_suffix(".png")
    assert csv_path.exists()
    assert png_path.exists()


def test_deliver_save_failure_does_not_raise(monkeypatch):
    monkeypatch.setattr("src.experiment.tcs_controller.MOCK_TCS", False)

    device = MagicMock()
    device.stimulus_running = False
    device.buffer_size = 1
    sample = np.array(
        (1_000_000_000, 32.0, 32.1, 31.9, 31.9, 31.9),
        dtype=[("timestamp", "uint64"), *((f"s{i}", "float64") for i in range(5))],
    )
    device._buffer = np.array([sample])
    device._buffer_idx = 1
    device._sampling_cond = threading.Condition()

    controller = ThermodeController()
    controller._device = device

    with patch("src.experiment.tcs_controller.ThermalRecorder") as recorder_cls:
        recorder_cls.return_value.stop.return_value = _sample_rows(3)
        with patch("src.experiment.tcs_controller.time.sleep"):
            with patch(
                "src.experiment.tcs_controller.save_thermal_trace",
                side_effect=OSError("disk full"),
            ):
                controller.deliver(
                    STIMULUS_POOL["flat"],
                    person=1,
                    trial=1,
                    environment="lnos",
                )
