#!/usr/bin/env python3
"""Preview a safe RTK rewrite without executing the command."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "lib"))

from codex_optimizer.rewrite import (  # noqa: E402
    contains_approval_sensitive_mutation,
    contains_sudo,
    requests_raw_output,
    rewrite_with_rtk,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", help="one shell command; read stdin when omitted")
    args = parser.parse_args()
    command = args.command if args.command is not None else sys.stdin.read().rstrip("\n")
    if not command:
        parser.error("provide a command or pipe one on stdin")
    if requests_raw_output(command):
        print(command)
        return 0
    try:
        blocked = contains_sudo(command)
    except ValueError:
        print("rtk_rewrite: unbalanced quotes; command left unchanged", file=sys.stderr)
        print(command)
        return 0
    if blocked:
        print("rtk_rewrite: refusing sudo command; use an approved elevation flow", file=sys.stderr)
        return 3
    if contains_approval_sensitive_mutation(command):
        print("rtk_rewrite: refusing approval-sensitive mutation; use Codex's normal approval flow", file=sys.stderr)
        return 3
    print(rewrite_with_rtk(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
