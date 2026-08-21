# Codex Optimizer

[Full English documentation](../../README.md) ·
[中文文档](../../docs/README.zh-CN.md)

Hook-backed Codex plugin with three automatic modes:

- Caveman `full`: concise, technically complete responses.
- Ponytail `full`: smallest correct implementation.
- RTK `on`: silent `PreToolUse` command rewriting plus token-neutral
  `PostToolUse` stage analysis.

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

The root README includes the full pre-compression transcript, actual RTK
rewrite/output, UI-versus-model-context accounting, and a byte-for-byte
reproducible token benchmark. Measured combined result: **409 → 49 tokens
(88.0% operation-only)**; output-stage analysis adds no model context. Including
the 343-token one-time activation context, the first fixture is **409 → 392
(4.2% saved)** and repeated operations amortize that fixed context.

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE.md).
