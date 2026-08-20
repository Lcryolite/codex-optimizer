#!/usr/bin/env python3
"""Manage persistent Codex Optimizer defaults."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "lib"))

from codex_optimizer.config import DEFAULTS, LEVELS, config_path, load, save  # noqa: E402


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
