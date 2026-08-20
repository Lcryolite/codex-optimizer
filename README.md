# Codex Optimizer

A hook-backed Codex plugin that automatically rewrites supported shell
commands through RTK, adds compact tool context, keeps responses concise, and
avoids unnecessary implementation scope.

[中文文档 / Chinese documentation](docs/README.zh-CN.md)

## Automatic means automatic

No `$codex-optimizer` invocation is required for coding, debugging, testing,
refactoring, repository, or shell tasks. After the hooks are trusted, the
runtime path is:

```text
natural Bash command
  → PreToolUse → rtk rewrite → rewritten command
  → command execution
  → PostToolUse → deterministic compact context → model-visible continuation
```

The plugin is automatic but not invisible. It emits evidence only when data
changes:

```text
[codex-optimizer] RTK rewrite: git status → rtk git status
[codex-optimizer] Context stages: Git Compaction; compact view 4,742 → 900 chars; original result preserved.
```

At session start it also reports that the hooks are active and lists every
enabled stage. Unsupported commands and outputs that do not benefit from
compaction remain unchanged and produce no false stage notice.

Codex currently has no supported PostToolUse field that silently replaces an
arbitrary tool result. Returning `continue: false` performs replacement but
marks the hook as `(stopped)`. Codex Optimizer deliberately does not do that:
RTK performs real output reduction before Bash results reach Codex, while
PostToolUse preserves the original result and adds a compact context view. See
the official [Codex hooks protocol](https://learn.chatgpt.com/docs/hooks#posttooluse).

## Modes

All modes are enabled by default:

| Mode | Default | Effect |
| --- | --- | --- |
| Caveman | `full` | Removes response filler while preserving code, exact errors, safety constraints, and requested formats. |
| Ponytail | `full` | Chooses the smallest correct implementation; prefers standard library, platform features, and existing dependencies. |
| RTK | `on` | Uses a real `PreToolUse` rewrite and `PostToolUse` output pipeline. |

## Output stages

A stage is shown only when it transforms the compact context view. The original
tool result is preserved so normal execution never becomes `(stopped)`.

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
| Hard Truncation | Enforces the compact-context 12,000-character ceiling. |

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
compact-context deltas:

```bash
python3 plugins/codex-optimizer/scripts/codex_optimizer.py status
python3 plugins/codex-optimizer/scripts/codex_optimizer.py stats
```

Metrics are written under Codex's per-plugin data directory. They describe
compact-context size differences, not guaranteed model-input savings. The
reproducible end-to-end benchmark below uses an actual tokenizer.

Persistent mode overrides are opt-in:

```bash
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py show
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py set caveman full
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py set rtk on
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py reset
```

## Reproducible token benchmark

The benchmark uses `tiktoken 0.14.0` with `o200k_base`. It counts all
model-visible text for the measured operation: assistant response, command,
RTK tool output, PostToolUse compact context, rewrite/stage notices, and context
header. It excludes the user prompt, tool-call JSON framing, hidden reasoning,
and the once-per-session activation notice. This is a deterministic synthetic
fixture so byte-for-byte runtime verification does not depend on compiler
versions or timing.

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

### After automatic RTK + PostToolUse + Caveman

Visible optimizer evidence:

```text
[codex-optimizer] RTK rewrite: cargo test --manifest-path benchmarks/fixtures/rust-project/Cargo.toml → rtk cargo test --manifest-path benchmarks/fixtures/rust-project/Cargo.toml
[codex-optimizer] Context stages: Test Aggregation; compact view 39 → 31 chars; original result preserved.
[codex-optimizer compact context; original tool result preserved]
Context stages: Test Aggregation
Compact view: 39 → 31 chars (8 fewer, 21%)
```

Executed command:

```bash
rtk cargo test --manifest-path benchmarks/fixtures/rust-project/Cargo.toml
```

RTK first reduces the raw 1,123-character output to:

```text
cargo test: 20 passed (1 suite, 0.03s)
```

PostToolUse keeps that RTK result and adds this compact context:

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
| Tool output + compact context | 307 | 25 | 282 |
| Optimizer notices | 0 | 106 | -106 |
| **Total** | **409** | **164** | **245 (59.9%)** |

Tool-output path: **307 raw tokens → 16 RTK tokens**, plus **9 tokens of
PostToolUse compact context**. Including preserved RTK output and every visible
notice makes the end-to-end result 59.9% smaller. This measured fixture is
evidence, not a universal promise; savings vary with command, output, and
response style.

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
python3 /home/lknife/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/codex-optimizer
python3 /home/lknife/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/codex-optimizer/skills/codex-optimizer
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
.venv/bin/python benchmarks/token_savings.py --verify-runtime
```

## License and attribution

MIT. See [LICENSE](plugins/codex-optimizer/LICENSE) and
[NOTICE](plugins/codex-optimizer/NOTICE.md).
