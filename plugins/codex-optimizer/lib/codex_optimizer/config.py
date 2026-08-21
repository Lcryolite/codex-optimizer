"""Persistent Codex Optimizer settings shared by hooks and the skill CLI."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


DEFAULTS = {"caveman": "full", "rtk": "on"}
LEVELS = {
    "caveman": {"off", "lite", "full", "ultra", "micro"},
    "rtk": {"off", "on"},
}


def config_path() -> Path:
    return Path.home() / ".codex" / "codex-optimizer.json"


def load() -> dict[str, str]:
    values = dict(DEFAULTS)
    try:
        raw = json.loads(config_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return values

    if not isinstance(raw, dict):
        return values
    for mode, allowed in LEVELS.items():
        value = raw.get(mode)
        if isinstance(value, str) and value in allowed:
            values[mode] = value
    return values


def save(values: dict[str, str]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="codex-optimizer.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(values, handle, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
