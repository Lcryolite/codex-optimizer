# Codex Optimizer

Codex plugin for concise responses, minimal implementations, and optional RTK
command guidance.

[中文文档 / Chinese documentation](docs/README.zh-CN.md)

## Features

- **Caveman**: reduce response overhead while preserving code, errors, safety boundaries, and requested formats.
- **Ponytail**: choose the smallest correct implementation, preferring the standard library, native platform features, and existing dependencies.
- **RTK**: write supported shell commands with explicit `rtk` wrappers and use compact command output where RTK provides it.

The modes are independent. You can enable Caveman without Ponytail, Ponytail
without RTK, or all three together.

## Runtime model

This is an instruction-driven Codex skill:

- Activate it with `$codex-optimizer` or a natural-language request.
- Caveman and Ponytail affect how Codex responds and implements the task.
- RTK wrappers are written explicitly; the plugin does not silently intercept every shell call.
- `rtk_rewrite.py` prints a rewritten command and never executes it.
- The helper refuses `sudo` segments so elevation remains an explicit, approved operation.

## Install

Requires Codex CLI. From a checkout of this repository:

```bash
git clone https://github.com/Lcryolite/codex-optimizer.git
cd codex-optimizer
codex plugin marketplace add .
codex plugin add codex-optimizer@codex-optimizer
```

Start a new Codex session after installation, then use the skill explicitly:

```text
Use $codex-optimizer with caveman full.
Use ponytail lite for this implementation.
Enable RTK for supported shell commands.
```

## Modes

| Mode | Values | Effect |
| --- | --- | --- |
| Caveman | `off`, `lite`, `full`, `ultra`, `micro` | Compress explanations without compressing code, exact errors, safety constraints, or requested formats. |
| Ponytail | `off`, `lite`, `full`, `ultra` | Avoid speculative abstractions and dependencies; keep the smallest viable change. |
| RTK | `off`, `on` | Prefix supported commands with `rtk`; leave unsupported commands unchanged. |

## Token benchmark

The repository contains two reproducible measurements:

1. Six response-only fixtures for the Caveman levels.
2. One end-to-end transcript where Caveman and RTK are enabled together.

The benchmark uses `tiktoken` with `o200k_base` and counts assistant text,
command text, and tool output separately. It does not count the user prompt,
tool-call JSON framing, code payloads outside the transcript, or hidden model
reasoning.

Install the optional benchmark dependency and run both the token count and the
runtime fixture verification:

```bash
python3 -m pip install tiktoken
python3 benchmarks/token_savings.py --verify-runtime
```

The runtime verification requires `rtk` in `PATH`. It executes the checked-in
fixture and compares both the plain and RTK outputs byte-for-byte with the
captured transcript.

### Response-only results

Six fixed coding-response fixtures contain 403 baseline tokens in total:

| Caveman level | Compressed tokens | Saved tokens | Saved |
| --- | ---: | ---: | ---: |
| `lite` | 246 | 157 | 39.0% |
| `full` | 150 | 253 | 62.8% |
| `ultra` | 131 | 272 | 67.5% |
| `micro` | 117 | 286 | 71.0% |

Fixture data: [`benchmarks/token_savings.json`](benchmarks/token_savings.json).

### Combined RTK + Caveman scenario

This fixed scenario runs a passing four-test suite in two suites and reports
the result. The fixture was captured with RTK `0.45.0` and is verified by the
command above.

Before compression:

Assistant response:

```text
The test suite completed successfully. I ran the standard test command and all four tests passed across two test suites. The passing cases cover refreshing an expired token, rejecting a malformed token, returning the current user, and rejecting an unknown user. There were no failures or snapshot changes, so the repository is ready for the next step.
```

Command:

```bash
bash benchmarks/fixtures/passing_suite.sh
```

Tool output:

```text
> codex-optimizer-demo@1.0.0 test
> jest --runInBand

PASS src/auth.test.ts
  ✓ refreshes an expired token (8 ms)
  ✓ rejects a malformed token (2 ms)
PASS src/user.test.ts
  ✓ returns the current user (3 ms)
  ✓ rejects an unknown user (1 ms)

Test Suites: 2 passed, 2 total
Tests:       4 passed, 4 total
Snapshots:   0 total
Time:        1.248 s
Ran all test suites.
```

After enabling both modes:

Assistant response:

```text
Tests pass: 4/4 in 2 suites; no failures.
```

Command:

```bash
rtk test bash benchmarks/fixtures/passing_suite.sh
```

Tool output:

```text
OUTPUT (last 5 lines):
  Test Suites: 2 passed, 2 total
  Tests:       4 passed, 4 total
  Snapshots:   0 total
  Time:        1.248 s
  Ran all test suites.
```

Token accounting for the exact transcript:

| Part | Before | After | Difference |
| --- | ---: | ---: | ---: |
| Assistant response | 65 | 15 | -50 |
| Command | 8 | 11 | +3 |
| Tool output | 118 | 56 | -62 |
| **Total** | **191** | **82** | **-109 (57.1%)** |

This is a measured fixture, not a universal promise. RTK adds command tokens;
the gain comes from its output filter. Real savings vary with language, task
complexity, test-runner output, requested explanation detail, and the installed
RTK version. The complete fixture is
[`benchmarks/combined_rtk_caveman.json`](benchmarks/combined_rtk_caveman.json),
and the raw passing command is
[`benchmarks/fixtures/passing_suite.sh`](benchmarks/fixtures/passing_suite.sh).

## RTK

Check the binary before enabling RTK:

```bash
rtk --version
```

For a safe command-chain preview without execution:

```bash
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/rtk_rewrite.py \
  'git status && npm test'
```

The rewrite helper preserves quoted text, leaves unsupported commands alone,
and refuses `sudo` segments.

## Persistent defaults

Only save defaults when explicitly requested:

```bash
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py show
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py set caveman full
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py set rtk on
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py reset
```

The config file is `~/.codex/codex-optimizer.json`.

## Layout

```text
.
├── .agents/plugins/marketplace.json
├── benchmarks/
│   ├── combined_rtk_caveman.json
│   ├── fixtures/passing_suite.sh
│   ├── token_savings.json
│   └── token_savings.py
├── docs/README.zh-CN.md
├── plugins/codex-optimizer/
│   ├── .codex-plugin/plugin.json
│   ├── skills/codex-optimizer/SKILL.md
│   ├── skills/codex-optimizer/scripts/codex_config.py
│   ├── skills/codex-optimizer/scripts/rtk_rewrite.py
│   ├── LICENSE
│   └── README.md
└── README.md
```

## Validation

```bash
python3 /home/lknife/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/codex-optimizer
python3 /home/lknife/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/codex-optimizer/skills/codex-optimizer
python3 benchmarks/token_savings.py --verify-runtime
```

## License

MIT. See [plugins/codex-optimizer/LICENSE](plugins/codex-optimizer/LICENSE).
