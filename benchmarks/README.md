# Optimizer benchmark environment

[Main documentation](../README.md) ·
[中文说明](../docs/README.zh-CN.md)

This environment measures a baseline, three isolated optimizers, and their
combination on one fixed synthetic task:

| Arm | Changed artifact |
| --- | --- |
| Baseline | None |
| RTK | Executed command and tool output |
| Caveman | Assistant prose only |
| Ponytail | Implementation only |
| Combined | All three changes |

Both implementations are executed against the same valid and invalid inputs.
The RTK arm runs the real Codex hook rewrite and deterministic Cargo-style
fixture. Component-isolation tests reject an arm that changes an artifact it
does not own.

Run:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install tiktoken==0.14.0
.venv/bin/python benchmarks/optimizer_matrix.py --verify-runtime
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_optimizer_matrix -v
```

The runner reports operation-only tokens, activation tokens, first-session
totals, and the repeated-operation break-even point. Counts use `o200k_base`;
the benchmark subprocess forces `PONYTAIL_DEFAULT_MODE=full` so user settings
cannot change the fixture.

The repository's Ponytail wrapper keeps that default SessionStart hook silent.
Its full upstream skill is counted only in coding arms; the marginal Ponytail
rules cost for non-coding arms is zero. Global skill-catalog metadata remains
outside the comparison.

## Interpretation limits

- RTK is an executable transformation and receives byte-for-byte runtime
  verification.
- Caveman and Ponytail are model instructions, not deterministic text/code
  transformers. Their fixture outputs are fixed before counting.
- Results prove the size of these exact artifacts. They do not estimate an
  average production session, model compliance, billing, prompt caching, or
  hidden reasoning tokens.
- The identical user task, tool-call framing, hidden reasoning, and global
  skill catalog are omitted from every arm because they cancel in the artifact
  comparison.
- Repetition break-even assumes the same per-operation savings while paying
  activation once. Real tasks vary.

Fixture sources:

- [`optimizer_matrix.json`](optimizer_matrix.json): task, two implementations,
  and shared behavior contract.
- [`combined_rtk_caveman.json`](combined_rtk_caveman.json): baseline/RTK command,
  output, and baseline/Caveman response.
