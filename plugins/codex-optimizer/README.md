# Codex Optimizer

[Full English documentation](../../README.md) ·
[中文文档](../../docs/README.zh-CN.md)

Hook-backed Codex plugin with three automatic modes:

- Caveman `full`: terse responses with exact technical content and clarity
  exceptions for safety or irreversible actions.
- Ponytail `full`: smallest correct implementation.
- RTK `on`: silent `PreToolUse` command rewriting plus token-neutral
  and silent `PostToolUse` stage analysis.

## Install

From the repository root:

```bash
codex plugin marketplace add .
codex plugin add codex-optimizer@codex-optimizer
```

Start a new session, use `/hooks` to inspect and trust the plugin hooks, then
submit normal coding work. No `$codex-optimizer` trigger is required.
The launcher resolves the newest valid installed cache at execution time, so
updates do not strand already-running sessions on deleted version paths.

## Verify

```bash
python3 scripts/codex_optimizer.py status
python3 scripts/codex_optimizer.py stats
```

The runtime implements all ten stages: ANSI Stripping, Test
Aggregation, Build Filtering, Git Compaction, Linter Aggregation, Search
Grouping, Source Code Filtering, Smart Truncation, Anchor-Safe Read
Compaction, and Hard Truncation. Stage metrics are recorded locally without
hook output.

The root README includes the full pre-compression transcript, actual RTK
rewrite/output, and a byte-for-byte reproducible token benchmark. Measured
combined result: **409 → 49 tokens (88.0% operation-only)**; output-stage
analysis emits no transcript or model context. See the root README for current
activation-cost accounting.

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE.md).
