---
name: codex-optimizer
description: Use when the user explicitly asks for Codex Optimizer behavior, terse responses, YAGNI-first implementation, or RTK-wrapped shell commands; do not activate for ordinary coding tasks without that request.
---

# Codex Optimizer for Codex

This skill has three independent modes. Keep them independent:

- Caveman controls how the response is written.
- Ponytail controls how much code is built.
- RTK controls how supported shell commands are selected and written.

This skill is instruction-driven. It does not silently intercept every shell
tool call. When RTK is enabled, write the `rtk` prefix explicitly in the
command you ask Codex to run.

## Mode selection

Activate only the mode and level the user requested. If the user says only
“use Codex Optimizer”, use saved defaults when they explicitly ask for them;
otherwise leave all modes unchanged and ask for no extra setup.

Level mappings:

- `caveman`: `off`, `lite`, `full`, `ultra`, `micro`.
- `ponytail`: `off`, `lite`, `full`, `ultra`.
- `rtk`: `off` or `on`.

Treat “stop”, “quit”, and “normal mode” as a request to disable the named
mode. A level change applies to the current conversation. Do not write a
persistent configuration file unless the user explicitly asks to save the
setting.

## Caveman mode

When active, preserve all technical substance while removing verbal waste.

- `lite`: professional, tight, no filler; keep normal sentences.
- `full`: remove most articles and hedging; fragments are acceptable.
- `ultra`: abbreviate common terms (`DB`, `auth`, `config`, `req`,
  `res`, `fn`, `impl`) and use arrows for causality.
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

## RTK mode

Before using RTK in a conversation, check that the binary exists with
`rtk --version`. If it is missing, do not invent an RTK invocation: use the
plain command and mention the one-time fallback.

For supported commands, prefix every top-level segment:

```text
rtk git status
rtk git add . && rtk git commit -m "message"
rtk npm test
```

Supported command families:

`git`, `gh`, `ls`, `tree`, `grep`, `cat`, `head`, `tail`,
`tsc`, `lint`, `eslint`, `prettier`, `next`, `cargo`, `rustc`,
`vitest`, `playwright`, `jest`, `test`, `pnpm`, `npm`, `npx`,
`yarn`, `bun`, `docker`, `kubectl`, `aws`, `psql`, `wc`,
`prisma`, and `dotnet`.

Do not double-prefix a command already beginning with `rtk`. Do not rewrite
operators or text inside quotes. If a chain is unbalanced or too complex to
reason about safely, leave it unchanged. The bundled `rtk_rewrite.py` helper
prints a rewritten command without executing it; use it for complex chains
instead of reimplementing the parser in prose.

Never send a `sudo` segment through this helper or direct RTK execution. Stop
and use the host's approved elevated-operation flow, or ask the user to run it
manually. When full, unfiltered output is needed for diagnosis or an exact
machine-readable result, use the plain command even when RTK is enabled.

## Optional persistent defaults

The bundled `codex_config.py` helper stores only this plugin's defaults at
`~/.codex/codex-optimizer.json`. Use it only after the user asks to save,
show, or reset defaults:

```text
python3 <skill-root>/scripts/codex_config.py show
python3 <skill-root>/scripts/codex_config.py set caveman full
python3 <skill-root>/scripts/codex_config.py set rtk on
python3 <skill-root>/scripts/codex_config.py reset
```

The effective defaults are Caveman off, Ponytail off, and RTK on when the
`rtk` binary is available. A saved value does not override a new explicit
user request for the current conversation.
