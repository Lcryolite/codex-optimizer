"""Concurrency-safe metrics for potential output-compaction candidates."""

from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import tempfile
from typing import Any


def _data_dir() -> Path:
    configured = os.environ.get("PLUGIN_DATA")
    if configured:
        return Path(configured)
    return Path.home() / ".codex" / "codex-optimizer-data"


def _empty() -> dict[str, Any]:
    return {
        "events": 0,
        "source_chars": 0,
        "candidate_chars": 0,
        "candidate_reduction_chars": 0,
        "estimated_candidate_reduction_tokens": 0,
        "stages": {},
    }


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return _empty()
    if not isinstance(value, dict):
        return _empty()
    normalized = _empty()
    legacy_keys = {
        "candidate_chars": "compact_context_chars",
        "candidate_reduction_chars": "context_delta_chars",
        "estimated_candidate_reduction_tokens": "estimated_context_delta_tokens",
    }
    for key in (
        "events",
        "source_chars",
        "candidate_chars",
        "candidate_reduction_chars",
        "estimated_candidate_reduction_tokens",
    ):
        raw = value.get(key)
        legacy_key = legacy_keys.get(key)
        if raw is None and legacy_key is not None:
            raw = value.get(legacy_key)
        if isinstance(raw, int) and raw >= 0:
            normalized[key] = raw
    stages = value.get("stages")
    if isinstance(stages, dict):
        normalized["stages"] = {
            str(stage): count
            for stage, count in stages.items()
            if isinstance(count, int) and count >= 0
        }
    return normalized


def _write(path: Path, value: dict[str, Any]) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix="metrics.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def record(original_chars: int, compacted_chars: int, stages: tuple[str, ...]) -> None:
    directory = _data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "metrics.json"
    lock_path = directory / "metrics.lock"
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        value = _read(path)
        saved = max(0, original_chars - compacted_chars)
        value["events"] = int(value.get("events", 0)) + 1
        value["source_chars"] = int(value.get("source_chars", 0)) + original_chars
        value["candidate_chars"] = int(value.get("candidate_chars", 0)) + compacted_chars
        value["candidate_reduction_chars"] = (
            int(value.get("candidate_reduction_chars", 0)) + saved
        )
        value["estimated_candidate_reduction_tokens"] = round(
            int(value["candidate_reduction_chars"]) / 4
        )
        stage_counts = value.setdefault("stages", {})
        if not isinstance(stage_counts, dict):
            stage_counts = {}
            value["stages"] = stage_counts
        for stage in stages:
            stage_counts[stage] = int(stage_counts.get(stage, 0)) + 1
        _write(path, value)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def load_metrics() -> dict[str, Any]:
    return _read(_data_dir() / "metrics.json")


def reset_metrics() -> None:
    directory = _data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    _write(directory / "metrics.json", _empty())
