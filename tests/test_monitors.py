"""Tests for monitor detection."""

import sys

from src.experiment.monitors import get_monitor, list_monitors


def test_get_monitor_fallback():
    mon = get_monitor(99, fallback_offset=1920)
    assert mon.x == 1920
    assert mon.width == 1920


def test_list_monitors_on_windows():
    if sys.platform != "win32":
        return
    monitors = list_monitors()
    assert len(monitors) >= 1
    assert all(m.width > 0 and m.height > 0 for m in monitors)
