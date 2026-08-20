#!/usr/bin/env python3
"""Manage explicit persistent defaults for the Codex Optimizer skill."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path


DEFAULTS = {"caveman": "full", "rtk": "on", "ponytail": "full"}
LEVELS = {
    "caveman": {"off", "lite", "full", "ultra", "micro"},
    "rtk": {"off", "on"},
    "ponytail": {"off", "lite", "full", "ultra"},
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
    fd, temporary = tempfile.mkstemp(prefix="codex-optimizer.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(values, handle, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("show", help="print effective defaults")
    subparsers.add_parser("path", help="print the config path")
    set_parser = subparsers.add_parser("set", help="persist one mode value")
    set_parser.add_argument("mode", choices=sorted(LEVELS))
    set_parser.add_argument("value")
    subparsers.add_parser("reset", help="restore package defaults")
    args = parser.parse_args()

    if args.action == "path":
        print(config_path())
        return 0

    if args.action == "show":
        print(json.dumps(load(), indent=2))
        return 0

    if args.action == "reset":
        save(DEFAULTS)
        print(json.dumps(DEFAULTS, indent=2))
        return 0

    allowed = LEVELS[args.mode]
    if args.value not in allowed:
        parser.error(f"{args.mode} value must be one of: {', '.join(sorted(allowed))}")
    values = load()
    values[args.mode] = args.value
    save(values)
    print(json.dumps(values, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
