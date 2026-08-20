#!/usr/bin/env python3
"""Preview an RTK rewrite without executing the command."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys


OPERATORS = {"&&", "||", ";", "|"}


def split_chain(command: str) -> list[str] | None:
    """Split top-level shell operators while preserving every character."""

    parts: list[str] = []
    buffer: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0

    while index < len(command):
        char = command[index]
        next_char = command[index + 1] if index + 1 < len(command) else ""

        if escaped:
            buffer.append(char)
            escaped = False
            index += 1
            continue

        if char == "\\":
            buffer.append(char)
            escaped = True
            index += 1
            continue

        if quote is not None:
            buffer.append(char)
            if char == quote:
                quote = None
            index += 1
            continue

        if char in {"'", '"'}:
            quote = char
            buffer.append(char)
            index += 1
            continue

        if (char, next_char) in {("&", "&"), ("|", "|")}:
            parts.append("".join(buffer))
            parts.append(char + next_char)
            buffer = []
            index += 2
            continue

        if char in {";", "|"}:
            parts.append("".join(buffer))
            parts.append(char)
            buffer = []
            index += 1
            continue

        buffer.append(char)
        index += 1

    if quote is not None:
        return None
    parts.append("".join(buffer))
    return parts


def sudo_segments(parts: list[str]) -> list[str]:
    return [
        part.strip()
        for part in parts
        if part.strip() not in OPERATORS
        and part.strip().startswith("sudo")
        and (part.strip() == "sudo" or part.strip()[4].isspace())
    ]


def rewrite_with_rtk(command: str) -> str:
    """Delegate parsing and rewrite policy to the installed RTK binary."""

    executable = shutil.which("rtk")
    if executable is None:
        return command

    try:
        result = subprocess.run(
            [executable, "rewrite", command],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return command

    rewritten = result.stdout.rstrip("\n")
    return rewritten if rewritten else command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", help="one shell command; read stdin when omitted")
    args = parser.parse_args()
    command = args.command if args.command is not None else sys.stdin.read().rstrip("\n")
    if not command:
        parser.error("provide a command or pipe one on stdin")

    parts = split_chain(command)
    if parts is None:
        print("rtk_rewrite: unbalanced quotes; command left unchanged", file=sys.stderr)
        print(command)
        return 0

    blocked = sudo_segments(parts)
    if blocked:
        print("rtk_rewrite: refusing sudo command; use an approved elevation flow", file=sys.stderr)
        for segment in blocked:
            print(f"  {segment}", file=sys.stderr)
        return 3

    print(rewrite_with_rtk(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
