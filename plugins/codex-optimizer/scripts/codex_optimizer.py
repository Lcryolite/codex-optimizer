#!/usr/bin/env python3
"""Inspect Codex Optimizer runtime state and measured savings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "lib"))

from codex_optimizer.compact import ALL_STAGES  # noqa: E402
from codex_optimizer.config import load  # noqa: E402
from codex_optimizer.metrics import load_metrics, reset_metrics  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "stats", "reset-stats"), nargs="?", default="status")
    args = parser.parse_args()
    if args.action == "reset-stats":
        reset_metrics()
    if args.action == "stats":
        print(json.dumps(load_metrics(), indent=2, sort_keys=True))
        return 0
    value = {
        "active": True,
        "modes": load(),
        "stages": list(ALL_STAGES),
        "metrics": load_metrics(),
    }
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
