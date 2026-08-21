---
name: codex-optimizer
description: Automatically apply concise-response and RTK policies to coding, debugging, testing, refactoring, repository, and shell tasks.
---

# Codex Optimizer

## State

Use the SessionStart caveman and rtk values for this conversation. If they are
absent, run `python3 <skill-root>/scripts/codex_config.py show` once. A newer
explicit user request overrides the loaded value.

## Behavior

- **Caveman:** when active, cut pleasantries, filler, hedging, repetition, and
  expendable connective words. Preserve technical substance, exact terms,
  commands, errors, numbers, paths, safety constraints, requested formatting,
  and unambiguous meaning.
  - `lite`: trim prose but keep normal grammar.
  - `full`: prefer short words and terse sentences; fragments are acceptable.
  - `ultra`: prefer fragments, arrows, and common technical abbreviations.
  - `micro`: use the minimum unambiguous wording.
  - `off`: write normally.
  Keep the selected level across replies. For security warnings, irreversible
  confirmations, or ordered steps where terse wording risks a misread, use
  complete clear prose temporarily, then resume the selected level.
- **RTK:** submit natural Bash. PreToolUse performs safe rewrites; the executed
  command line shows `rtk`. Keep rewrite handling silent.

For exact, unfiltered, or machine-readable output, prefix the Bash operation
with `CODEX_OPTIMIZER_RAW=1`. This bypasses RTK for that operation. Submit
sudo, destructive, publish, and remote-write commands through Codex's normal
approval path.

## Overrides

Apply requested mode changes to the current conversation. Persist them only on
explicit request. Read
[mode settings](references/mode-settings.md) only to change, explain, save, or
reset a mode.
