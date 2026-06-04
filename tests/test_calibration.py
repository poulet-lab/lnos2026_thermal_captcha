"""Tests for calibration analysis and stimulus ordering."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.experiment.analyze_calibration import (
    analyze_folder,
    analyze_trace_csv,
    run_analysis,
    stimulus_name_from_csv,
)
from src.experiment.globals import TRACE_PLOT_Y_MAX, TRACE_PLOT_Y_MIN
from src.experiment.stimuli import STIMULUS_POOL, Family
from src.experiment.stimulus_calibration import calibration_stimulus_order
from src.experiment.thermal_traces import save_thermal_trace_plot


def test_calibration_stimulus_order():
    order = calibration_stimulus_order()
    assert len(order) == 36
    assert order[0].name == "pulse_pos_1"
    assert order[1].name == "pulse_neg_1"
    assert order[12].family is Family.SLOW_UP_FAST_DOWN
    assert order[12].name == "slow_up_fast_down_pos_1"
    assert order[24].family is Family.FAST_UP_SLOW_DOWN
    assert order[24].name == "fast_up_slow_down_pos_1"


def test_stimulus_name_from_csv():
    assert stimulus_name_from_csv(Path("pulse_pos_5.csv")) == "pulse_pos_5"
    assert (
        stimulus_name_from_csv(Path("troubleshooting_p03_t01_pulse_pos_5.csv"))
        == "pulse_pos_5"
    )


def _write_trace_csv(path: Path, temps: list[float]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["elapsed_time", "s0", "s1", "s2", "s3", "s4"],
        )
        writer.writeheader()
        for i, temp in enumerate(temps):
            writer.writerow(
                {
                    "elapsed_time": i * 0.01,
                    "s0": temp,
                    "s1": temp,
                    "s2": 32.0,
                    "s3": 32.0,
                    "s4": 32.0,
                }
            )


def test_analyze_calibration_report(tmp_path):
    good = tmp_path / "pulse_pos_5.csv"
    _write_trace_csv(good, [32.0 + i * (5.0 / 99) for i in range(100)])

    weak = tmp_path / "slow_up_fast_down_pos_5.csv"
    _write_trace_csv(weak, [32.0 + i * (1.0 / 19) for i in range(20)])

    failed = tmp_path / "slow_up_fast_down_neg_10.csv"
    _write_trace_csv(failed, [32.0] * 100)

    metrics = analyze_folder(tmp_path)
    by_name = {row.stimulus_name: row for row in metrics}

    assert by_name["pulse_pos_5"].status == "ok"
    assert by_name["slow_up_fast_down_pos_5"].status == "sparse_sampling"
    assert by_name["slow_up_fast_down_neg_10"].status == "failed"

    run_analysis(tmp_path)
    assert (tmp_path / "calibration_report.csv").exists()
    assert (tmp_path / "calibration_summary.txt").exists()


def test_analyze_trace_csv_peak_direction():
    path = Path("pulse_neg_5.csv")
    rows = []
    for i in range(100):
        rows.append(
            {
                "elapsed_time": i * 0.01,
                "s0": 32.0 - i * (5.0 / 99),
                "s1": 32.0 - i * (5.0 / 99),
                "s2": 32.0,
                "s3": 32.0,
                "s4": 32.0,
            }
        )

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / path.name
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        metrics = analyze_trace_csv(csv_path)
        assert metrics is not None
        assert metrics.peak_temp == pytest.approx(27.0, abs=0.2)


def test_save_thermal_trace_plot_ylim(tmp_path):
    rows = [
        {
            "elapsed_time": i * 0.05,
            "s0": 32.0 + i,
            "s1": 32.0 + i * 0.5,
            "s2": 32.0,
            "s3": 32.0,
            "s4": 32.0,
        }
        for i in range(5)
    ]
    png_path = tmp_path / "trace.png"

    from unittest.mock import MagicMock, patch

    mock_ax = MagicMock()
    with patch("src.experiment.thermal_traces.plt.subplots", return_value=(MagicMock(), mock_ax)):
        with patch("src.experiment.thermal_traces.plt.savefig"):
            with patch("src.experiment.thermal_traces.plt.close"):
                save_thermal_trace_plot(
                    rows,
                    png_path,
                    STIMULUS_POOL["pulse_pos_5"],
                    person=0,
                    trial=1,
                )

    mock_ax.set_ylim.assert_called_once_with(TRACE_PLOT_Y_MIN, TRACE_PLOT_Y_MAX)
