"""Detect monitor geometry (Windows and Linux/X11)."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Monitor:
    x: int
    y: int
    width: int
    height: int
    primary: bool


def _enum_monitors_windows() -> list[Monitor]:
    import ctypes
    from ctypes import wintypes

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD),
        ]

    monitors: list[Monitor] = []
    MONITORINFOF_PRIMARY = 1

    def callback(hmonitor, _hdc, _rect, _data):
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if not ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            return True
        rect = info.rcMonitor
        monitors.append(
            Monitor(
                x=rect.left,
                y=rect.top,
                width=rect.right - rect.left,
                height=rect.bottom - rect.top,
                primary=bool(info.dwFlags & MONITORINFOF_PRIMARY),
            )
        )
        return True

    cb_type = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(RECT),
        ctypes.c_double,
    )
    ctypes.windll.user32.EnumDisplayMonitors(None, None, cb_type(callback), 0)
    monitors.sort(key=lambda m: (m.x, m.y))
    return monitors


_GEOMETRY_RE = re.compile(r"(\d+)(?:/\d+)?x(\d+)(?:/\d+)?\+(-?\d+)\+(-?\d+)")


def parse_xrandr_listmonitors(text: str) -> list[Monitor]:
    """Parse `xrandr --listmonitors` output."""
    monitors: list[Monitor] = []
    for line in text.splitlines():
        match = _GEOMETRY_RE.search(line)
        if not match:
            continue
        width, height, x, y = (int(value) for value in match.groups())
        flags = line.split(":", 1)[1] if ":" in line else line
        primary = "*" in flags
        monitors.append(
            Monitor(x=x, y=y, width=width, height=height, primary=primary)
        )
    monitors.sort(key=lambda m: (m.x, m.y))
    return monitors


def parse_xrandr_query(text: str) -> list[Monitor]:
    """Parse `xrandr --query` connected-output lines."""
    monitors: list[Monitor] = []
    for line in text.splitlines():
        if " connected" not in line:
            continue
        match = _GEOMETRY_RE.search(line)
        if not match:
            continue
        width, height, x, y = (int(value) for value in match.groups())
        primary = " primary" in line
        monitors.append(
            Monitor(x=x, y=y, width=width, height=height, primary=primary)
        )
    monitors.sort(key=lambda m: (m.x, m.y))
    return monitors


def _run_xrandr(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["xrandr", *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _enum_monitors_linux() -> list[Monitor]:
    listmonitors = _run_xrandr("--listmonitors")
    if listmonitors:
        monitors = parse_xrandr_listmonitors(listmonitors)
        if monitors:
            return monitors

    query = _run_xrandr("--query")
    if query:
        return parse_xrandr_query(query)
    return []


def list_monitors() -> list[Monitor]:
    if sys.platform == "win32":
        return _enum_monitors_windows()
    if sys.platform.startswith("linux"):
        return _enum_monitors_linux()
    return []


def get_monitor(
    index: int,
    fallback_offset: int = 0,
    fallback_width: int = 1920,
    fallback_height: int = 1080,
) -> Monitor:
    """Return monitor by index (0 = leftmost). Falls back to offset-based guess."""
    monitors = list_monitors()
    if monitors and 0 <= index < len(monitors):
        return monitors[index]

    if fallback_offset > 0:
        return Monitor(
            x=fallback_offset,
            y=0,
            width=fallback_width,
            height=fallback_height,
            primary=False,
        )

    return Monitor(
        x=0,
        y=0,
        width=fallback_width,
        height=fallback_height,
        primary=True,
    )


def choose_participant_monitor(monitors: list[Monitor]) -> Monitor | None:
    """Return the first detected monitor that is not marked primary."""
    for monitor in monitors:
        if not monitor.primary:
            return monitor
    return None


def get_participant_monitor(
    fallback_offset: int = 0,
    fallback_width: int = 1920,
    fallback_height: int = 1080,
) -> Monitor:
    """Return the participant display monitor, preferring a non-primary screen."""
    monitors = list_monitors()
    monitor = choose_participant_monitor(monitors)
    if monitor is not None:
        return monitor

    if fallback_offset > 0:
        return Monitor(
            x=fallback_offset,
            y=0,
            width=fallback_width,
            height=fallback_height,
            primary=False,
        )

    if monitors:
        return monitors[0]

    return Monitor(
        x=0,
        y=0,
        width=fallback_width,
        height=fallback_height,
        primary=True,
    )


def force_window_to_monitor(hwnd: int, monitor: Monitor) -> None:
    """Force a window HWND onto a monitor rect (Windows only)."""
    if sys.platform != "win32":
        return
    import ctypes

    SWP_NOZORDER = 0x0004
    SWP_SHOWWINDOW = 0x0040
    ctypes.windll.user32.SetWindowPos(
        hwnd,
        0,
        monitor.x,
        monitor.y,
        monitor.width,
        monitor.height,
        SWP_NOZORDER | SWP_SHOWWINDOW,
    )


def format_monitors_for_log() -> list[str]:
    """Return human-readable lines describing detected monitors."""
    monitors = list_monitors()
    if not monitors:
        hint = "install xrandr" if sys.platform.startswith("linux") else "check display drivers"
        return [f"No monitors detected (using fallback offset; {hint})."]
    lines = []
    for i, m in enumerate(monitors):
        primary = " primary" if m.primary else ""
        lines.append(f"  [{i}] {m.width}x{m.height} at ({m.x}, {m.y}){primary}")
    return lines
