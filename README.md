# Codex Optimizer

A hook-backed Codex plugin that silently rewrites supported shell commands
through RTK, analyzes compaction candidates without injecting duplicate model
context, keeps responses concise, and avoids unnecessary implementation scope.

[中文文档 / Chinese documentation](docs/README.zh-CN.md)

## Automatic means automatic

No `$codex-optimizer` invocation is required for coding, debugging, testing,
refactoring, repository, or shell tasks. After the hooks are trusted, the
runtime path is:

```text
natural Bash command
  → PreToolUse → rtk rewrite → rewritten command
  → command execution
  → PostToolUse → silent local stage analysis + metrics
```

PreToolUse emits no hook message or model context. The normal executed-command
line is the evidence: it directly shows `rtk ...`. PostToolUse records smaller
candidates locally without emitting hook output:

```text
rtk git status
```

At session start the model receives only the three effective mode values; the
ten-stage list is not repeated into every conversation. Unsupported commands
and outputs that do not produce a smaller candidate remain silent.

Codex currently has no supported PostToolUse field that silently replaces an
arbitrary tool result. Returning `continue: false` performs replacement but
marks the hook as `(stopped)`. Codex Optimizer deliberately does not do that:
RTK performs real output reduction before Bash results reach Codex, while
PostToolUse preserves the original result and silently records candidate
metrics. It emits no `systemMessage`, `additionalContext`, or blocking result.
See the official
[Codex hooks protocol](https://learn.chatgpt.com/docs/hooks#posttooluse).

## Modes

All modes are enabled by default:

| Mode | Default | Effect |
| --- | --- | --- |
| Caveman | `full` | Removes filler, hedging, repetition, and pleasantries while preserving all technical content; temporarily favors clarity for safety and irreversible actions. |
| Ponytail | `full` | Chooses the smallest correct implementation; prefers standard library, platform features, and existing dependencies. |
| RTK | `on` | Uses a silent `PreToolUse` rewrite and token-neutral `PostToolUse` analysis. |

## Output stages

Stages silently record local metrics only when they produce a smaller
candidate. Candidates are never emitted or injected beside the original tool
result, so normal execution never becomes `(stopped)` and stage analysis adds
zero transcript or model context.

| Stage | Description |
| --- | --- |
| ANSI Stripping | Removes terminal color and formatting sequences. |
| Test Aggregation | Summarizes pass, fail, skip counts and preserves failure details. |
| Build Filtering | Removes routine build progress while retaining errors and warnings. |
| Git Compaction | Condenses `git status`, `git log`, and `git diff`. |
| Linter Aggregation | Groups diagnostics and reports error/warning totals. |
| Search Grouping | Groups `rg`/`grep` matches by file. |
| Source Code Filtering | Removes redundant comments/blank lines only when a large read already needs lossy compaction; userscript metadata is preserved. |
| Smart Truncation | Keeps representative head/tail context and reports omitted lines. |
| Anchor-Safe Read Compaction | Recognizes anchored read formats and keeps complete edit anchors. |
| Hard Truncation | Enforces the 12,000-character candidate ceiling. |

Safety invariants are tested: reads of 80 lines or fewer remain exact,
explicit offset/limit reads remain exact, skill files remain exact, and
recognizable `sudo`, publish, remote-write, and destructive commands never
reach RTK or receive automatic `permissionDecision: allow`.

## Install

Requirements: Codex CLI and an `rtk` binary in `PATH`.

```bash
git clone https://github.com/Lcryolite/codex-optimizer.git
cd codex-optimizer
codex plugin marketplace add .
codex plugin add codex-optimizer@codex-optimizer
```

Start a new Codex session, open `/hooks`, inspect the three plugin hooks, and
trust them. Codex requires this trust step because hooks execute local code.
The hook launcher resolves the newest valid installed cache at execution time,
so reinstalling an update does not leave already-running sessions pointing at
a deleted version directory.
The one-session automation escape hatch
`--dangerously-bypass-hook-trust` should be used only in an already isolated,
audited environment.

Then ask for normal coding work—no trigger phrase is needed. An explicit
`$codex-optimizer` can still force the skill outside its automatic scope.

## Verify activation and savings

The status command lists all effective modes, all ten stages, and cumulative
candidate reductions:

```bash
python3 plugins/codex-optimizer/scripts/codex_optimizer.py status
python3 plugins/codex-optimizer/scripts/codex_optimizer.py stats
```

Metrics are written under Codex's per-plugin data directory. Candidate
reductions are diagnostic opportunities, not claimed model-input savings. The
reproducible end-to-end benchmark below counts only actual model-visible text.

Persistent mode overrides are opt-in:

```bash
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py show
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py set caveman full
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py set rtk on
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py reset
```

## Reproducible token benchmark

The benchmark uses `tiktoken 0.14.0` with `o200k_base`. It counts the assistant
response, executed command, and RTK tool output. PreToolUse emits no message;
PostToolUse silently records local metrics and emits no hook output or model
`additionalContext`.
The user prompt, tool-call JSON framing, hidden reasoning, and once-per-session
mode context are excluded from the operation-only table and reported
separately below. This deterministic synthetic fixture makes byte-for-byte
runtime verification independent of compiler versions or timing.

### Before optimization

Assistant response:

```text
The test suite completed successfully. I ran the full Cargo test command and all twenty tests passed in one suite. The passing cases cover access-token validation, refresh-token rotation, cache expiry, and the complete set of user creation, lookup, update, and rejection paths. There were no failed, ignored, measured, or filtered tests, and the run finished in 0.03 seconds, so the repository is ready for the next step.
```

Command:

```bash
cargo test --manifest-path benchmarks/fixtures/rust-project/Cargo.toml
```

Tool output:

```text
   Compiling codex-optimizer-benchmark v0.1.0
    Finished `test` profile [unoptimized + debuginfo] target(s) in 1.24s
     Running unittests src/lib.rs (target/debug/deps/benchmark-0123456789abcdef)

running 20 tests
test auth::accepts_valid_access_token ... ok
test auth::refreshes_expired_access_token ... ok
test auth::rejects_expired_refresh_token ... ok
test auth::rejects_malformed_access_token ... ok
test auth::rejects_missing_signature ... ok
test auth::rejects_unknown_issuer ... ok
test auth::rejects_wrong_audience ... ok
test auth::rotates_refresh_token ... ok
test cache::evicts_expired_entries ... ok
test cache::keeps_recent_entries ... ok
test user::creates_user ... ok
test user::deletes_user ... ok
test user::finds_user_by_email ... ok
test user::finds_user_by_id ... ok
test user::lists_active_users ... ok
test user::rejects_duplicate_email ... ok
test user::rejects_empty_email ... ok
test user::rejects_unknown_user ... ok
test user::updates_display_name ... ok
test user::updates_password_hash ... ok

test result: ok. 20 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.03s
```

### After automatic RTK + silent PostToolUse + Caveman

Executed command:

```bash
rtk cargo test --manifest-path benchmarks/fixtures/rust-project/Cargo.toml
```

RTK first reduces the raw 1,123-character output to:

```text
cargo test: 20 passed (1 suite, 0.03s)
```

PostToolUse computes this candidate for local metrics without emitting it:

```text
Test Results:
  PASS: 20 passed
```

Caveman response:

```text
Tests pass: 20/20 in 1 suite; 0 failures.
```

Exact token accounting:

| Part | Before | After | Saved |
| --- | ---: | ---: | ---: |
| Assistant response | 87 | 16 | 71 |
| Command | 15 | 17 | -2 |
| Tool output | 307 | 16 | 291 |
| Model-context optimizer notices | 0 | 0 | 0 |
| **Total** | **409** | **49** | **360 (88.0%)** |

Tool-output path: **307 raw tokens → 16 RTK/model-visible tokens**.
PostToolUse's 9-token candidate is not emitted. The measured operation is
88.0% smaller. This fixture is evidence, not a universal promise; savings vary
with command, output, and response style.

Fixed activation context is also measured, rather than hidden:

| Activation component | Tokens |
| --- | ---: |
| Default `SKILL.md` | 475 |
| SessionStart mode state | 20 |
| **Total fixed context** | **495** |

The optional 247-token mode-settings reference is loaded only when the user
asks to change, explain, save, or reset a mode. Repeating the same synthetic
operation after one activation gives:

| Operations | Before | After including fixed context | Saved |
| ---: | ---: | ---: | ---: |
| 1 | 409 | 544 | -135 (-33.0%) |
| 2 | 818 | 593 | 225 (27.5%) |
| 5 | 2,045 | 740 | 1,305 (63.8%) |

This is transcript/context accounting, not a billing promise; provider prompt
caching and the number of model continuations affect billed input separately.

Reproduce both token counts and byte-for-byte runtime behavior:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install tiktoken==0.14.0
.venv/bin/python benchmarks/token_savings.py --verify-runtime
```

The fixture data is in
[`benchmarks/combined_rtk_caveman.json`](benchmarks/combined_rtk_caveman.json).
Six response-only cases remain in
[`benchmarks/token_savings.json`](benchmarks/token_savings.json): Caveman
`full` saves 253 of 403 tokens (62.8%) on that fixed corpus.

## Development validation

```bash
CODEX_SYSTEM_SKILLS="${CODEX_HOME:-$HOME/.codex}/skills/.system"
python3 "$CODEX_SYSTEM_SKILLS/plugin-creator/scripts/validate_plugin.py" \
  plugins/codex-optimizer
python3 "$CODEX_SYSTEM_SKILLS/skill-creator/scripts/quick_validate.py" \
  plugins/codex-optimizer/skills/codex-optimizer
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
.venv/bin/python benchmarks/token_savings.py --verify-runtime
```

## License and attribution

MIT. See [LICENSE](plugins/codex-optimizer/LICENSE) and
[NOTICE](plugins/codex-optimizer/NOTICE.md).
