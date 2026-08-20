#!/usr/bin/env python3
"""Measure the checked-in response fixtures with a tiktoken encoding."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


LEVELS = ("lite", "full", "ultra", "micro")


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
        help="fixture JSON path",
    )
    args = parser.parse_args()

    encoder = load_encoder(args.encoding)
    cases = json.loads(args.data.read_text(encoding="utf-8"))
    totals = {level: [0, 0] for level in LEVELS}

    print(f"encoding: {args.encoding}")
    print("case                    base   lite   full  ultra  micro")
    print("----------------------  -----  -----  -----  -----  -----")
    for case in cases:
        counts = {
            "base": len(encoder.encode(case["baseline"])),
            **{level: len(encoder.encode(case[level])) for level in LEVELS},
        }
        print(
            f"{case['id'][:22]:22}  "
            + "  ".join(f"{counts[key]:5d}" for key in ("base", *LEVELS))
        )
        for level in LEVELS:
            totals[level][0] += counts["base"]
            totals[level][1] += counts[level]

    print("\naggregate")
    for level in LEVELS:
        base, compact = totals[level]
        saved = base - compact
        percentage = saved / base * 100 if base else 0
        print(f"{level:>5}: {base} -> {compact} tokens; saved {saved} ({percentage:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
