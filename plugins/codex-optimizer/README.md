# Codex Optimizer

[Chinese documentation](../../docs/README.zh-CN.md)

Codex-native plugin that automatically applies terse responses, YAGNI-first
implementation, and RTK shell guidance to coding tasks.

All three modes are enabled by default: Caveman `full`, Ponytail `full`, and
RTK `on` when available. The repository root README contains the reproducible
Caveman and combined RTK+Caveman token benchmark: [benchmark documentation](../../README.md#token-benchmark).

- **Caveman** — terse responses with `lite`, `full`, `ultra`, and `micro` levels.
- **Ponytail** — smallest correct diff with standard-library and existing-dependency preference.
- **RTK** — automatic `rtk` prefixes for supported shell commands and safe chain rewriting.

## Install locally

From the repository root (`codex-optimizer`), register the marketplace and install the plugin:

```bash
codex plugin marketplace add .
codex plugin add codex-optimizer@codex-optimizer
```

Then start a new Codex CLI session. The skill automatically applies to coding
tasks; `$codex-optimizer` is optional and can force it for another task.
Codex's plugin browser is also available with `/plugins`.

If local files change after installation, refresh the cachebuster and reinstall:

```bash
python3 /home/lknife/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py .
codex plugin add codex-optimizer@codex-optimizer
```

## Usage

Modes are automatic by default; override them only when needed:

```text
Use $codex-optimizer with caveman micro.
Use ponytail lite for this implementation.
Run this command with plain, unfiltered output.
Stop caveman; answer normally from here.
```

| Mode | Values | Purpose |
| --- | --- | --- |
| Caveman | `off`, `lite`, `full`, `ultra`, `micro` (default: `full`) | Compress explanations while preserving technical substance. |
| Ponytail | `off`, `lite`, `full`, `ultra` (default: `full`) | Prefer standard library, native features, existing dependencies, and the smallest viable change. |
| RTK | `on` (default), `off` | Prefix supported commands with `rtk`; leave unsupported commands unchanged. |

RTK requires the binary to be available:

```bash
rtk --version
```

## Optional helpers

The skill includes two dependency-free Python helpers:

```bash
python3 skills/codex-optimizer/scripts/rtk_rewrite.py 'git status && npm test'
python3 skills/codex-optimizer/scripts/codex_config.py show
python3 skills/codex-optimizer/scripts/codex_config.py set caveman full
python3 skills/codex-optimizer/scripts/codex_config.py set rtk on
python3 skills/codex-optimizer/scripts/codex_config.py reset
```

`rtk_rewrite.py` only prints an RTK rewrite (or the raw fallback). `codex_config.py`
stores explicit defaults in `~/.codex/codex-optimizer.json`; it does not execute
shell commands or change Codex configuration automatically.

## Layout

```text
.
├── .codex-plugin/plugin.json
├── skills/codex-optimizer/SKILL.md
├── skills/codex-optimizer/scripts/codex_config.py
├── skills/codex-optimizer/scripts/rtk_rewrite.py
├── LICENSE
└── README.md
```

## Validation

```bash
python3 /home/lknife/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
python3 /home/lknife/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/codex-optimizer
```

## License

MIT. See [LICENSE](LICENSE).
