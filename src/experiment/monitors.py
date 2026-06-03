"""Detect monitor geometry (Windows)."""

from __future__ import annotations

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


def list_monitors() -> list[Monitor]:
    if sys.platform == "win32":
        return _enum_monitors_windows()
    return []


def get_monitor(index: int, fallback_offset: int = 0) -> Monitor:
    """Return monitor by index (0 = leftmost). Falls back to offset-based guess."""
    monitors = list_monitors()
    if monitors and 0 <= index < len(monitors):
        return monitors[index]

    if fallback_offset > 0:
        return Monitor(x=fallback_offset, y=0, width=1920, height=1080, primary=False)

    return Monitor(x=0, y=0, width=1920, height=1080, primary=True)


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
        return ["No monitors detected (using fallback offset)."]
    lines = []
    for i, m in enumerate(monitors):
        primary = " primary" if m.primary else ""
        lines.append(f"  [{i}] {m.width}x{m.height} at ({m.x}, {m.y}){primary}")
    return lines
