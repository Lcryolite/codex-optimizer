---
name: codex-optimizer
description: Automatically use for coding, debugging, testing, refactoring, repository, and shell tasks to apply all Codex Optimizer modes by default—Caveman, Ponytail, and RTK—without requiring the user to name the skill. Do not activate for non-coding questions unless the user asks.
---

# Codex Optimizer for Codex

This skill automatically loads for coding work. The user does not need to type
`$codex-optimizer` or name any mode. An explicit `$codex-optimizer` still
forces the skill when the user wants it for a task outside the normal coding
scope.

## Automatic defaults

- Apply Caveman `full` by default: concise explanations that preserve all
  technical substance.
- Apply Ponytail `full` by default: smallest correct implementation with no
  speculative scope.
- Apply RTK command and output optimization by default for shell work when the
  `rtk` binary is available.
- Respect an explicit level change for the current conversation.
- If the user says `plain command`, `unfiltered output`, `disable RTK`, or
  equivalent, use the raw command for the current task or operation.
- If `rtk` is unavailable, run the raw command and mention the one-time
  fallback only when it affects the result. Do not repeatedly probe a missing
  binary in the same task.

This is instruction-driven rather than a process-level hook. Codex writes an
optimized command before running it; it does not silently intercept an already
constructed shell call. The Pi extension itself is not loaded into Codex. The
installed `rtk` CLI is the execution source for command rewriting and output
compaction.

## Mode selection

All three modes are automatic whenever this skill is active:

- `caveman`: defaults to `full`; levels are `off`, `lite`, `full`, `ultra`,
  `micro`.
- `ponytail`: defaults to `full`; levels are `off`, `lite`, `full`, `ultra`.
- `rtk`: defaults to automatic `on`; `off` is a temporary opt-out.

Do not wait for the user to mention a mode. Treat an explicit `rtk off`,
`disable RTK`, `caveman off`, `ponytail off`, `normal mode`, or raw-output
request as a temporary opt-out. Saved values are respected until the user
changes them.

Treat “stop”, “quit”, and “normal mode” as a request to disable the named
mode. A level change applies to the current conversation. Do not write a
persistent configuration file unless the user explicitly asks to save the
setting.

## Caveman mode

When active, preserve all technical substance while removing verbal waste.

- `lite`: professional, tight, no filler; keep normal sentences.
- `full`: remove most articles and hedging; fragments are acceptable.
- `ultra`: abbreviate common terms (`DB`, `auth`, `config`, `req`, `res`, `fn`,
  `impl`) and use arrows for causality.
- `micro`: use the shortest clear explanation that still preserves the answer.

Drop pleasantries, filler, and unsupported hedging. Keep exact code blocks,
error text, commands, identifiers, numbers, and technical terms unchanged.
Use the pattern “thing → action → reason → next step” when it fits.

Temporarily return to normal clarity for security warnings, destructive or
irreversible actions, confirmations, or a confused user. Caveman changes
explanations only; never compress code, quoted errors, safety constraints, or
the user's requested output format.

## Ponytail mode

When active, implement the smallest correct solution and question unnecessary
scope without blocking the requested work. Before adding code, stop at the
first rung that solves the need:

1. Does this need to exist at all? Skip speculative work.
2. Can the standard library do it?
3. Can a native platform feature do it?
4. Does an already-installed dependency cover it?
5. Can it be one line?
6. Otherwise write the minimum code that works.

Avoid unrequested abstractions, factories with one implementation, speculative
configuration, scaffolding for later, and new dependencies for a few lines of
code. Prefer deletion and boring code. In `lite`, name the lazier alternative
and let the user choose. In `full`, enforce the ladder. In `ultra`, challenge
the requirement and choose the smallest viable implementation in the same
response.

Never remove input validation at trust boundaries, error handling that avoids
data loss, security, accessibility, or anything explicitly requested. For
non-trivial logic, leave one runnable check behind; trivial one-liners need no
test. When the user did not request an explanation, put code first and keep
the follow-up to at most three short lines.

## Automatic RTK behavior

When preparing a shell command:

1. Resolve `rtk` once when command optimization is needed. A missing binary is
   a normal fallback, not a reason to invent an invocation.
2. Prefer the installed RTK wrapper that matches the command, such as
   `rtk test`, `rtk git`, `rtk grep`, `rtk rg`, `rtk lint`, `rtk npm`, or
   `rtk cargo`. Use `rtk --help` when the appropriate wrapper is unclear.
3. For a compound command, use `rtk rewrite "<raw command>"` as the source of
   truth for shell parsing, supported commands, bypasses, and partial rewrites.
   Use a non-empty rewrite result; if it produces no safe rewrite, keep the
   raw command or split the operation into clear commands.
4. Do not double-prefix a command already beginning with `rtk`. Preserve
   operators and quoted text unless the installed rewriter changes them.
5. Use plain commands when the user needs complete unfiltered output for
   diagnosis, exact machine-readable data, security review, or a verbatim
   artifact.

The bundled `rtk_rewrite.py` helper previews a rewrite without executing the
command. It delegates to `rtk rewrite` when available and leaves the raw
command unchanged when the binary is missing.

Never send a `sudo` segment through the rewriter or direct RTK execution. Stop
and use the host's approved elevated-operation flow, or ask the user to run it
manually.

## Optional persistent defaults

The bundled `codex_config.py` helper stores this plugin's defaults at
`~/.codex/codex-optimizer.json`. Use it only after the user asks to save,
show, or reset defaults:

```text
python3 <skill-root>/scripts/codex_config.py show
python3 <skill-root>/scripts/codex_config.py set caveman full
python3 <skill-root>/scripts/codex_config.py set rtk on
python3 <skill-root>/scripts/codex_config.py reset
```

The defaults are Caveman full, Ponytail full, and RTK on. A saved value does not
override a new explicit user request for the current conversation.
