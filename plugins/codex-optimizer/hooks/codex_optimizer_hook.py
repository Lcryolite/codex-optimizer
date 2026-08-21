#!/usr/bin/env python3
"""Codex hook entry point for automatic RTK rewrite and output compaction."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any


PLUGIN_ROOT = Path(os.environ.get("PLUGIN_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(PLUGIN_ROOT / "lib"))

from codex_optimizer.compact import compact_tool_output  # noqa: E402
from codex_optimizer.config import load  # noqa: E402
from codex_optimizer.metrics import record  # noqa: E402
from codex_optimizer.rewrite import safe_rewrite  # noqa: E402


def _payload() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def _emit(value: dict[str, Any] | None) -> None:
    if value:
        json.dump(value, sys.stdout, separators=(",", ":"))
        sys.stdout.write("\n")


def _tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("tool_input", payload.get("input", {}))
    return value if isinstance(value, dict) else {}


def _extract_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        pieces = [_extract_text(item) for item in value]
        text = "\n".join(piece for piece in pieces if piece)
        return text or None
    if not isinstance(value, dict):
        return None
    for key in ("output", "stdout", "text"):
        text = value.get(key)
        if isinstance(text, str) and text:
            return text
    content = value.get("content")
    if content is not None:
        text = _extract_text(content)
        if text:
            return text
    stdout = _extract_text(value.get("stdout"))
    stderr = _extract_text(value.get("stderr"))
    combined = "\n".join(part for part in (stdout, stderr) if part)
    return combined or None


def session_start() -> dict[str, Any]:
    modes = load()
    context = (
        f"codex-optimizer: caveman={modes['caveman']}; "
        f"rtk={modes['rtk']}."
    )
    return {
        "systemMessage": "[codex-optimizer] active",
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        },
    }


def pre_tool_use(payload: dict[str, Any]) -> dict[str, Any] | None:
    if str(payload.get("tool_name", "")).lower() != "bash":
        return None
    modes = load()
    if modes["rtk"] != "on":
        return None
    tool_input = _tool_input(payload)
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return None
    rewritten = safe_rewrite(command)
    if rewritten == command:
        return None
    updated = dict(tool_input)
    updated["command"] = rewritten
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": updated,
        },
    }


def post_tool_use(payload: dict[str, Any]) -> dict[str, Any] | None:
    if load()["rtk"] != "on":
        return None
    output = _extract_text(payload.get("tool_response", payload.get("tool_result")))
    if not output:
        return None
    tool_name = str(payload.get("tool_name", ""))
    result = compact_tool_output(tool_name, _tool_input(payload), output)
    if not result.changed:
        return None
    try:
        record(result.original_chars, result.compacted_chars, result.stages)
    except (OSError, TypeError, ValueError):
        pass
    return None


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    action = sys.argv[1]
    payload = _payload()
    if action == "session-start":
        _emit(session_start())
    elif action == "pre-tool-use":
        _emit(pre_tool_use(payload))
    elif action == "post-tool-use":
        _emit(post_tool_use(payload))
    else:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
