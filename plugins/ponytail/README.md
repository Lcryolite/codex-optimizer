# Ponytail — on-demand Codex wrapper

[Project documentation](../../README.md) ·
[Upstream Ponytail](https://github.com/DietrichGebert/ponytail)

This wrapper exposes every upstream Ponytail skill through an exact mirror in
`skills`. The authoritative source remains the pinned `upstream` Git
submodule; Codex packaging omits directory symlinks, so a regular directory is
required in the installable plugin.

For the default `full` mode, SessionStart and SubagentStart update local mode
state without emitting model context. Codex's skill router loads Ponytail for
coding tasks and skips it for non-coding tasks. `off`, `lite`, and `ultra`
emit only a compact state instruction. The upstream UserPromptSubmit mode
tracker remains available for explicit mode commands.

No upstream rule is modified. After moving the submodule commit at `upstream`,
run `python3 scripts/sync_upstream_skills.py`; contract tests compare every
mirrored byte with upstream.
