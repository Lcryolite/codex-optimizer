# Codex Optimizer

A hook-backed Codex plugin that silently rewrites supported shell commands
through RTK, analyzes compaction candidates without injecting duplicate model
context, and keeps responses concise. This repository also distributes the
upstream Ponytail plugin as a pinned Git submodule.

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

At session start the model receives only the two effective mode values; the
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

Codex Optimizer enables these modes by default:

| Mode | Default | Effect |
| --- | --- | --- |
| Caveman | `full` | Removes filler, hedging, repetition, and pleasantries while preserving all technical content; temporarily favors clarity for safety and irreversible actions. |
| RTK | `on` | Uses a silent `PreToolUse` rewrite and token-neutral `PostToolUse` analysis. |

Ponytail is the unmodified upstream plugin, not a partial mode reimplemented
inside Codex Optimizer. Installing it from this marketplace provides its
complete skills and lifecycle hooks. Its configuration and releases remain
independent.

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

For an exact, unfiltered, or machine-readable Bash operation, bypass RTK once
with a normal shell environment prefix:

```bash
CODEX_OPTIMIZER_RAW=1 rg --json needle src
```

The hook emits no rewrite for that operation. The prefix remains part of the
executed shell command and does not change the persistent RTK setting.

## Install

Requirements: Codex CLI plus `rtk` and `node` binaries in `PATH`. Codex
Optimizer uses RTK; the upstream Ponytail lifecycle hooks use Node.js.

```bash
git clone --recurse-submodules https://github.com/Lcryolite/codex-optimizer.git
cd codex-optimizer
codex plugin marketplace add .
codex plugin add codex-optimizer@codex-optimizer
codex plugin add ponytail@codex-optimizer
```

For an existing checkout, initialize the submodule first:

```bash
git submodule update --init --recursive
```

Start a new Codex session, open `/hooks`, inspect both plugins' hooks, and
trust them. Codex requires this trust step because hooks execute local code.
The hook launcher resolves the newest valid installed cache at execution time,
so reinstalling an update does not leave already-running sessions pointing at
a deleted version directory.
The one-session automation escape hatch
`--dangerously-bypass-hook-trust` should be used only in an already isolated,
audited environment.

Then ask for normal coding work—no trigger phrase is needed. An explicit
`$codex-optimizer` can still force the skill outside its automatic scope.

## Updating Ponytail

The repository pins Ponytail to a reviewed upstream commit. To update that
pin, fetch the latest configured upstream branch, validate both plugins, and
commit the resulting gitlink change:

```bash
git submodule update --remote plugins/ponytail
git diff --submodule=log -- plugins/ponytail
git add plugins/ponytail
```

No Ponytail source is copied into Codex Optimizer, so upstream updates stay
auditable and reversible through normal Git history.

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

### Baseline + four optimization arms

The fixed isolation fixture applies each optimizer only to its owned artifact:
RTK changes command/output, Caveman changes prose, and Ponytail changes
implementation. The table contains a baseline, three single-optimizer arms,
and the full combination. Both implementations pass the same valid/invalid
input contract; the real RTK hook and output fixture receive byte-for-byte
runtime verification.

| Arm | Implementation | Reply | Command | Output | Operation | Saved | Activation | First session |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 243 | 87 | 15 | 307 | 652 | — | 0 | 652 |
| RTK only | 243 | 87 | 17 | 16 | 363 | 289 (44.3%) | 414 | 777 |
| Caveman only | 243 | 16 | 15 | 307 | 581 | 71 (10.9%) | 414 | 995 |
| Ponytail only | 40 | 87 | 15 | 307 | 449 | 203 (31.1%) | 2,874 | 3,323 |
| Combined | 40 | 16 | 17 | 16 | 89 | 563 (86.3%) | 3,288 | 3,377 |

Every optimizer reduces this fixture's operation text. None saves tokens on
the first session after its full activation context is included. If the same
per-operation difference repeats while activation is paid once, RTK breaks
even at operation 2, Caveman at 6, Ponytail at 15, and the combined arm at 6.
Real tasks do not have constant savings.

Caveman and Ponytail are model instructions rather than deterministic
transformers. Their outputs were fixed before counting, so this demonstrates
these artifacts—not average model compliance or production savings. Full
methodology and commands: [benchmark environment](benchmarks/README.md).
The identical user task, tool-call framing, hidden reasoning, and global skill
catalog are excluded from every arm; they cancel in this artifact comparison.

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
| Codex Optimizer `SKILL.md` | 399 |
| Codex Optimizer SessionStart state | 15 |
| Upstream Ponytail `SKILL.md` | 1,610 |
| Upstream Ponytail `full` SessionStart rules | 1,264 |
| **Both installed plugins** | **3,288** |

The optional 218-token mode-settings reference is loaded only when the user
asks to change, explain, save, or reset a Codex Optimizer mode. The Ponytail
SessionStart row is measured by executing the pinned upstream hook with
`PLUGIN_DATA`, so Codex-specific output excludes its Claude-only statusline
nudge. Repeating the same synthetic operation after both plugins activate
gives:

| Operations | Before | After including fixed context | Saved |
| ---: | ---: | ---: | ---: |
| 1 | 409 | 3,337 | -2,928 (-715.9%) |
| 2 | 818 | 3,386 | -2,568 (-313.9%) |
| 5 | 2,045 | 3,533 | -1,488 (-72.8%) |
| 10 | 4,090 | 3,778 | 312 (7.6%) |

This is transcript/context accounting, not a billing promise; provider prompt
caching and the number of model continuations affect billed input separately.

Reproduce both token counts and byte-for-byte runtime behavior:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install tiktoken==0.14.0
.venv/bin/python benchmarks/token_savings.py --verify-runtime
.venv/bin/python benchmarks/optimizer_matrix.py --verify-runtime
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
.venv/bin/python benchmarks/optimizer_matrix.py --verify-runtime
```

## License and attribution

MIT. See [LICENSE](plugins/codex-optimizer/LICENSE) and
[NOTICE](plugins/codex-optimizer/NOTICE.md). Ponytail is distributed as an
independent MIT-licensed submodule; see its
[license](plugins/ponytail/LICENSE).
