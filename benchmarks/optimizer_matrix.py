#!/usr/bin/env python3
"""Measure RTK, Caveman, Ponytail, and their combination on one fixed task."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys


BENCHMARKS = Path(__file__).resolve().parent
REPO_ROOT = BENCHMARKS.parent
sys.path.insert(0, str(BENCHMARKS))

from token_savings import count, load_encoder, load_ponytail_context, verify_runtime  # noqa: E402


PARTS = ("implementation", "assistant", "command", "tool_output")
ARMS = {
    "baseline": (False, False, False),
    "rtk": (True, False, False),
    "caveman": (False, True, False),
    "ponytail": (False, False, True),
    "combined": (True, True, True),
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def arm_texts(
    matrix: dict[str, object], transcript: dict[str, object], arm: str
) -> dict[str, str]:
    rtk, caveman, ponytail = ARMS[arm]
    before = transcript["before"]
    after = transcript["after"]
    return {
        "implementation": matrix[
            "ponytail_implementation" if ponytail else "baseline_implementation"
        ],
        "assistant": after["assistant"] if caveman else before["assistant"],
        "command": after["command"] if rtk else before["command"],
        "tool_output": after["tool_output"] if rtk else before["tool_output"],
    }


def activation_tokens(encoder, transcript: dict[str, object]) -> dict[str, int]:
    optimizer_skill = (
        REPO_ROOT
        / "plugins"
        / "codex-optimizer"
        / "skills"
        / "codex-optimizer"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    ponytail_skill = (
        REPO_ROOT / "plugins" / "ponytail" / "skills" / "ponytail" / "SKILL.md"
    ).read_text(encoding="utf-8")
    ponytail_context = load_ponytail_context(REPO_ROOT)
    optimizer_skill_tokens = count(encoder, optimizer_skill)
    ponytail_tokens = count(encoder, ponytail_skill) + count(encoder, ponytail_context)

    def optimizer_context(caveman: str, rtk: str) -> int:
        return count(encoder, f"codex-optimizer: caveman={caveman}; rtk={rtk}.")

    return {
        "baseline": 0,
        "rtk": optimizer_skill_tokens + optimizer_context("off", "on"),
        "caveman": optimizer_skill_tokens + optimizer_context("full", "off"),
        "ponytail": ponytail_tokens,
        "combined": (
            optimizer_skill_tokens
            + optimizer_context("full", "on")
            + ponytail_tokens
        ),
    }


def measure(encoder, matrix: dict[str, object], transcript: dict[str, object]):
    activation = activation_tokens(encoder, transcript)
    rows = {}
    for arm in ARMS:
        texts = arm_texts(matrix, transcript, arm)
        parts = {part: count(encoder, texts[part]) for part in PARTS}
        operation = sum(parts.values())
        rows[arm] = {
            "parts": parts,
            "operation": operation,
            "activation": activation[arm],
            "first_session": operation + activation[arm],
        }
    return rows


def verify_implementations(matrix: dict[str, object]) -> None:
    for key in ("baseline_implementation", "ponytail_implementation"):
        namespace: dict[str, object] = {}
        exec(matrix[key], namespace)
        resolve_port = namespace["resolve_port"]
        for value, expected in matrix["contract_cases"]:
            actual = resolve_port(value)
            if actual != expected:
                raise SystemExit(
                    f"{key} failed: resolve_port({value!r}) = {actual!r}, expected {expected!r}"
                )
        for value in matrix["invalid_cases"]:
            try:
                resolve_port(value)
            except ValueError:
                continue
            raise SystemExit(f"{key} failed to preserve ValueError for {value!r}")


def print_report(rows: dict[str, dict[str, object]]) -> None:
    baseline = rows["baseline"]["operation"]
    print("\noptimizer isolation matrix (tokens)")
    print("arm        impl  reply  command  output  operation  saved    activation  first-session")
    print("---------  ----  -----  -------  ------  ---------  -------  ----------  -------------")
    for arm, row in rows.items():
        parts = row["parts"]
        saved = baseline - row["operation"]
        percentage = saved / baseline * 100
        print(
            f"{arm:9}  {parts['implementation']:4d}  {parts['assistant']:5d}  "
            f"{parts['command']:7d}  {parts['tool_output']:6d}  "
            f"{row['operation']:9d}  {saved:4d} ({percentage:5.1f}%)  "
            f"{row['activation']:10d}  {row['first_session']:13d}"
        )
    print("break-even repetitions (same fixed task, activation paid once)")
    for arm in ARMS:
        if arm == "baseline":
            continue
        per_operation_saved = baseline - rows[arm]["operation"]
        break_even = math.floor(rows[arm]["activation"] / per_operation_saved) + 1
        print(f"  {arm:9}: {break_even}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encoding", default="o200k_base")
    parser.add_argument(
        "--matrix", type=Path, default=BENCHMARKS / "optimizer_matrix.json"
    )
    parser.add_argument(
        "--transcript",
        type=Path,
        default=BENCHMARKS / "combined_rtk_caveman.json",
    )
    parser.add_argument("--verify-runtime", action="store_true")
    args = parser.parse_args()

    matrix = load_json(args.matrix)
    transcript = load_json(args.transcript)
    encoder = load_encoder(args.encoding)
    print(f"encoding: {args.encoding}")
    print(f"fixture: {matrix['id']}")
    print_report(measure(encoder, matrix, transcript))
    if args.verify_runtime:
        verify_implementations(matrix)
        print("implementation equivalence: PASS")
        verify_runtime(args.transcript)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
