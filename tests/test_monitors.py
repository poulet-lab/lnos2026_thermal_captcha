"""Tests for monitor detection."""

import sys

from src.experiment.monitors import (
    Monitor,
    choose_participant_monitor,
    get_monitor,
    get_participant_monitor,
    list_monitors,
    parse_xrandr_listmonitors,
    parse_xrandr_query,
)


def test_get_monitor_fallback():
    mon = get_monitor(99, fallback_offset=1920)
    assert mon.x == 1920
    assert mon.width == 1920


def test_choose_participant_monitor_prefers_non_primary():
    monitors = [
        Monitor(x=0, y=0, width=1920, height=1080, primary=True),
        Monitor(x=1920, y=0, width=1920, height=1080, primary=False),
    ]
    mon = choose_participant_monitor(monitors)
    assert mon == monitors[1]


def test_get_participant_monitor_uses_offset_without_non_primary(monkeypatch):
    monitors = [Monitor(x=0, y=0, width=1920, height=1080, primary=True)]
    monkeypatch.setattr("src.experiment.monitors.list_monitors", lambda: monitors)

    mon = get_participant_monitor(
        fallback_offset=1920,
        fallback_width=2048,
        fallback_height=1152,
    )

    assert mon.x == 1920
    assert mon.width == 2048
    assert mon.height == 1152
    assert mon.primary is False


def test_list_monitors_on_windows():
    if sys.platform != "win32":
        return
    monitors = list_monitors()
    assert len(monitors) >= 1
    assert all(m.width > 0 and m.height > 0 for m in monitors)


def test_parse_xrandr_listmonitors():
    text = """
Monitors: 2
 0: +*eDP-1 1920/344x1080/193+0+0  eDP-1
 1: +HDMI-1 1920/508x1080/286+1920+0  HDMI-1
""".strip()
    monitors = parse_xrandr_listmonitors(text)
    assert len(monitors) == 2
    assert monitors[0].width == 1920
    assert monitors[0].height == 1080
    assert monitors[0].x == 0
    assert monitors[0].primary is True
    assert monitors[1].x == 1920
    assert monitors[1].primary is False


def test_parse_xrandr_query():
    text = """
Screen 0: minimum 320 x 200, current 3840 x 1080 maximum 16384 x 16384
HDMI-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) *0
DP-1 connected 1920x1080+1920+0 (normal left inverted right x axis y axis) 0
DP-2 disconnected (normal left inverted right x axis y axis)
""".strip()
    monitors = parse_xrandr_query(text)
    assert len(monitors) == 2
    assert monitors[0].primary is True
    assert monitors[1].x == 1920


def test_list_monitors_on_linux_when_xrandr_available():
    if not sys.platform.startswith("linux"):
        return
    monitors = list_monitors()
    if not monitors:
        return
    assert all(m.width > 0 and m.height > 0 for m in monitors)
