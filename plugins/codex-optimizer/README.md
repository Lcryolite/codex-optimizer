# Codex Optimizer

[Full English documentation](../../README.md) ·
[中文文档](../../docs/README.zh-CN.md)

Hook-backed Codex plugin with three automatic modes:

- Caveman `full`: concise, technically complete responses.
- Ponytail `full`: smallest correct implementation.
- RTK `on`: real `PreToolUse` command rewriting plus non-stopping
  `PostToolUse` compact context with visible stage notices.

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

The runtime implements and reports all ten stages: ANSI Stripping, Test
Aggregation, Build Filtering, Git Compaction, Linter Aggregation, Search
Grouping, Source Code Filtering, Smart Truncation, Anchor-Safe Read
Compaction, and Hard Truncation.

The root README includes the full pre-compression transcript, the actual RTK
rewrite/output, all visible overhead, and a byte-for-byte reproducible token
benchmark. Measured combined result: **409 → 164 tokens (59.9% saved)**,
including preserved RTK output and every visible notice.

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE.md).
