---
name: codex-optimizer
description: Automatically optimize coding and shell tasks with concise responses, minimal implementations, and RTK command rewriting. Use for coding, debugging, testing, refactoring, or repository work; skip unrelated questions.
---

# Codex Optimizer

## State

Use the SessionStart caveman, ponytail, and rtk values for this conversation.
If absent, run python3 <skill-root>/scripts/codex_config.py show once. Defaults:
caveman=full, ponytail=full, rtk=on. Explicit user requests override them.

## Behavior

- **Caveman:** when active, cut pleasantries, filler, hedging, repetition, and
  expendable connective words. Preserve all technical substance, exact terms,
  commands, code blocks, errors, numbers, paths, safety constraints, and the
  user's requested format. Compression must not introduce ambiguity.
  - `lite`: trim prose but keep normal grammar.
  - `full`: prefer short words and terse sentences; fragments are acceptable.
  - `ultra`: prefer fragments, arrows, and common technical abbreviations.
  - `micro`: use the minimum unambiguous wording.
  - `off`: write normally.
  Keep the selected level across replies. For security warnings, irreversible
  confirmations, or ordered steps where terse wording risks a misread, use
  complete clear prose temporarily, then resume the selected level.
- **Ponytail:** choose the smallest correct solution. Prefer no change,
  standard library, platform features, and existing dependencies. Retain
  necessary validation, error handling, security, and accessibility.
- **RTK:** submit natural Bash. PreToolUse performs safe rewrites; the executed
  command line shows rtk. Do not manually prefix or explain rewrites.

Use raw commands for requested exact/unfiltered output and machine-readable
diagnostics. Leave sudo, destructive, publish, and remote-write commands in
Codex's normal approval path.

PostToolUse runs all output stages for UI metrics, adds no model context, and
never stops tool processing.

## Overrides

Apply changes immediately; persist only on explicit request. Read
[mode settings](references/mode-settings.md) only to change, explain, save, or
reset a mode.
