# Mode settings

Read this reference only when the user asks to change, explain, save, or reset
a Codex Optimizer mode.

## Levels

- Caveman: off, lite, full, ultra, micro. Increasing levels remove more prose;
  preserve exact technical and safety content at every level.
- RTK: on or off. Prefix a plain, exact, or machine-readable Bash operation
  with `CODEX_OPTIMIZER_RAW=1` to bypass rewriting for that operation.

Treat “normal mode” as disabling the named mode for the current conversation.

## Persistence

Write configuration only after an explicit request:

    python3 <skill-root>/scripts/codex_config.py show
    python3 <skill-root>/scripts/codex_config.py set caveman full
    python3 <skill-root>/scripts/codex_config.py set rtk on
    python3 <skill-root>/scripts/codex_config.py reset

Apply the command's returned state immediately. Saved values become defaults
for later conversations but never override a newer explicit request.
