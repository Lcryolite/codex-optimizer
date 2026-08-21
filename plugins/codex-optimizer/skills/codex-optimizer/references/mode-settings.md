# Mode settings

Read this reference only when the user asks to change, explain, save, or reset
a Codex Optimizer mode.

## Levels

- Caveman: off, lite, full, ultra, micro. Increasing levels remove more prose;
  preserve exact technical and safety content at every level.
- Ponytail: off, lite, full, ultra. Increasing levels more strongly reject
  speculative scope and favor the smallest viable solution.
- RTK: on or off. A plain/unfiltered-output request disables rewriting for that
  operation.

Treat “normal mode” as disabling the named mode for the current conversation.

## Persistence

Write configuration only after an explicit request:

    python3 <skill-root>/scripts/codex_config.py show
    python3 <skill-root>/scripts/codex_config.py set caveman full
    python3 <skill-root>/scripts/codex_config.py set ponytail full
    python3 <skill-root>/scripts/codex_config.py set rtk on
    python3 <skill-root>/scripts/codex_config.py reset

Apply the command's returned state immediately. Saved values become defaults
for later conversations but never override a newer explicit request.
