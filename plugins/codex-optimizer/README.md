# Codex Optimizer

Codex-native plugin for terse responses, YAGNI-first implementation, and
optional RTK shell guidance. It contains one skill with three independent modes:

- **Caveman** — terse responses with `lite`, `full`, `ultra`, and `micro` levels.
- **Ponytail** — smallest correct diff with standard-library and existing-dependency preference.
- **RTK** — explicit `rtk` prefixes for supported shell commands and safe chain rewriting.

## Install locally

From the repository root (`codex-optimizer`), register the marketplace and install the plugin:

```bash
codex plugin marketplace add .
codex plugin add codex-optimizer@codex-optimizer
```

Then start a new Codex CLI session and invoke the skill with `$codex-optimizer`,
or describe the requested mode in your task. Codex's plugin browser is also
available with `/plugins`.

If local files change after installation, refresh the cachebuster and reinstall:

```bash
python3 /home/lknife/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py .
codex plugin add codex-optimizer@codex-optimizer
```

## Usage

Modes are independent:

```text
Use $codex-optimizer with caveman full.
Use ponytail lite for this implementation.
Enable RTK and use it for supported shell commands.
Stop caveman; answer normally from here.
```

| Mode | Values | Purpose |
| --- | --- | --- |
| Caveman | `off`, `lite`, `full`, `ultra`, `micro` | Compress explanations while preserving technical substance. |
| Ponytail | `off`, `lite`, `full`, `ultra` | Prefer standard library, native features, existing dependencies, and the smallest viable change. |
| RTK | `off`, `on` | Prefix supported commands with `rtk`; leave unsupported commands unchanged. |

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

`rtk_rewrite.py` only prints a transformed command. `codex_config.py` stores
explicit defaults in `~/.codex/codex-optimizer.json`; it does not execute shell
commands or change Codex configuration automatically.

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
