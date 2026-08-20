#!/usr/bin/env python3
"""Measure response fixtures and the combined RTK/Caveman transcript."""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
import shlex
import subprocess


LEVELS = ("lite", "full", "ultra", "micro")
TRANSCRIPT_PARTS = ("assistant", "command", "tool_output")


def load_encoder(name: str):
    try:
        import tiktoken
    except ImportError as exc:
        raise SystemExit(
            "tiktoken is required for this benchmark; install it with "
            "python3 -m pip install tiktoken"
        ) from exc
    try:
        return tiktoken.get_encoding(name)
    except ValueError as exc:
        raise SystemExit(f"unknown tiktoken encoding: {name}") from exc


def count(encoder, text: str) -> int:
    return len(encoder.encode(text))


def print_response_benchmark(encoder, data_path: Path) -> None:
    cases = json.loads(data_path.read_text(encoding="utf-8"))
    totals = {level: [0, 0] for level in LEVELS}

    print("response fixtures")
    print("case                    base   lite   full  ultra  micro")
    print("----------------------  -----  -----  -----  -----  -----")
    for case in cases:
        counts = {
            "base": count(encoder, case["baseline"]),
            **{level: count(encoder, case[level]) for level in LEVELS},
        }
        print(
            f"{case['id'][:22]:22}  "
            + "  ".join(f"{counts[key]:5d}" for key in ("base", *LEVELS))
        )
        for level in LEVELS:
            totals[level][0] += counts["base"]
            totals[level][1] += counts[level]

    print("\nresponse aggregate")
    for level in LEVELS:
        base, compact = totals[level]
        saved = base - compact
        percentage = saved / base * 100 if base else 0
        print(f"{level:>5}: {base} -> {compact} tokens; saved {saved} ({percentage:.1f}%)")


def print_combined_benchmark(encoder, data_path: Path) -> None:
    transcript = json.loads(data_path.read_text(encoding="utf-8"))
    before = {
        part: count(encoder, transcript["before"][part]) for part in TRANSCRIPT_PARTS
    }
    after = {
        part: count(encoder, transcript["after"][part]) for part in TRANSCRIPT_PARTS
    }
    before_total = sum(before.values())
    after_total = sum(after.values())
    saved = before_total - after_total
    percentage = saved / before_total * 100 if before_total else 0

    print("\ncombined RTK + Caveman transcript")
    print(f"captured RTK version: {transcript['rtk_version_captured']}")
    print("part                  before  after  saved")
    print("--------------------  ------  -----  -----")
    for part in TRANSCRIPT_PARTS:
        print(f"{part:20}  {before[part]:6d}  {after[part]:5d}  {before[part] - after[part]:5d}")
    print(
        f"total                 {before_total:6d}  {after_total:5d}  "
        f"{saved:5d} ({percentage:.1f}%)"
    )


def verify_runtime(data_path: Path) -> None:
    transcript = json.loads(data_path.read_text(encoding="utf-8"))
    repo_root = Path(__file__).resolve().parents[1]
    for phase in ("before", "after"):
        command = shlex.split(transcript[phase]["command"])
        result = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        actual = result.stdout
        expected = transcript[phase]["tool_output"]
        if result.returncode != 0 or result.stderr or actual != expected:
            print(f"runtime verification failed for {phase}: {' '.join(command)}")
            if result.returncode != 0:
                print(f"exit code: {result.returncode}")
            if result.stderr:
                print(f"stderr: {result.stderr!r}")
            print(
                "".join(
                    difflib.unified_diff(
                        expected.splitlines(keepends=True),
                        actual.splitlines(keepends=True),
                        fromfile="fixture",
                        tofile="runtime",
                    )
                )
            )
            raise SystemExit(1)
    print("runtime verification: PASS (baseline and RTK commands match fixtures)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--encoding",
        default="o200k_base",
        help="tiktoken encoding (default: o200k_base)",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).with_name("token_savings.json"),
        help="response fixture JSON path",
    )
    parser.add_argument(
        "--combined",
        type=Path,
        default=Path(__file__).with_name("combined_rtk_caveman.json"),
        help="combined transcript JSON path",
    )
    parser.add_argument(
        "--verify-runtime",
        action="store_true",
        help="run the baseline and RTK fixture commands and compare their output",
    )
    args = parser.parse_args()

    encoder = load_encoder(args.encoding)
    print(f"encoding: {args.encoding}")
    print_response_benchmark(encoder, args.data)
    print_combined_benchmark(encoder, args.combined)
    if args.verify_runtime:
        verify_runtime(args.combined)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
