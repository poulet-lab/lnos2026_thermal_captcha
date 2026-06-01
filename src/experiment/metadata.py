"""Session metadata.json helpers."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any


def _deep_merge(base: dict, updates: dict) -> None:
    for key, value in updates.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _metadata_path(session_folder: Path | str) -> Path:
    return Path(session_folder) / "metadata.json"


def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".json", dir=str(path.parent))
    try:
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        shutil.move(tmp, path)
    except Exception:
        try:
            Path(tmp).unlink(missing_ok=True)
        except OSError:
            pass
        raise


def read_metadata(session_folder: Path | str) -> dict:
    path = _metadata_path(session_folder)
    if not path.exists():
        return {"raw": {}, "processed": {}, "analyzed": {}}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if (
        isinstance(data.get("raw"), dict)
        and isinstance(data.get("processed"), dict)
        and isinstance(data.get("analyzed"), dict)
    ):
        return {
            "raw": data["raw"],
            "processed": data["processed"],
            "analyzed": data["analyzed"],
        }
    if "raw" not in data and "processed" not in data and "analyzed" not in data:
        return {"raw": dict(data), "processed": {}, "analyzed": {}}
    return {
        "raw": data.get("raw") if isinstance(data.get("raw"), dict) else {},
        "processed": data.get("processed") if isinstance(data.get("processed"), dict) else {},
        "analyzed": data.get("analyzed") if isinstance(data.get("analyzed"), dict) else {},
    }


def update_raw(session_folder: Path | str, updates: dict[str, Any]) -> dict:
    path = _metadata_path(session_folder)
    metadata = read_metadata(session_folder)
    for key in ("raw", "processed", "analyzed"):
        metadata.setdefault(key, {})
    _deep_merge(metadata["raw"], updates)
    _write_json_atomic(path, metadata)
    return metadata
