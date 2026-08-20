# Codex Optimizer 中文文档

[English README](../README.md)

这是一个会自动加载的 Codex 插件：对编码、调试、测试、重构和仓库任务自动减少无效解释、
保持实现最小化，并使用 RTK 压缩命令输出。

## 功能

- **Caveman**：压缩回复中的冗余文本，但保留代码、错误、安全边界和用户要求的格式。
- **Ponytail**：优先标准库、平台能力和已有依赖，只实现最小正确改动。
- **RTK**：自动对支持的 shell 命令使用 `rtk`，并使用 RTK 提供的紧凑输出。

三个模式默认全部开启：Caveman `full`、Ponytail `full`、RTK `on`。

## 安装

```bash
git clone https://github.com/Lcryolite/codex-optimizer.git
cd codex-optimizer
codex plugin marketplace add .
codex plugin add codex-optimizer@codex-optimizer
```

安装后重新开启 Codex 会话即可，不需要输入触发词。以下命令只是可选覆盖：

```text
Use $codex-optimizer with caveman micro.
Use ponytail lite for this implementation.
Run this command with plain, unfiltered output.
```

## Token 基准

仓库包含两类可复现测试：

1. 6 组只测试回复文本的 Caveman 样本。
2. 1 组同时启用 Caveman 和 RTK 的端到端 transcript。

统计使用 `tiktoken` 的 `o200k_base` 编码，分别计算 assistant 文本、命令文本和工具输出。
不统计用户 prompt、tool-call JSON 外壳、transcript 之外的代码和隐藏推理。

运行方式：

```bash
python3 -m pip install tiktoken
python3 benchmarks/token_savings.py --verify-runtime
```

运行时校验需要 `rtk` 在 `PATH` 中。脚本会实际执行普通命令和 RTK 命令，并逐字比较输出。

### 只测试回复文本

6 组固定编码任务的基准回复共 403 tokens：

| Caveman 级别 | 压缩后 | 节省 | 比例 |
| --- | ---: | ---: | ---: |
| `lite` | 246 | 157 | 39.0% |
| `full` | 150 | 253 | 62.8% |
| `ultra` | 131 | 272 | 67.5% |
| `micro` | 117 | 286 | 71.0% |

原始数据：[benchmarks/token_savings.json](../benchmarks/token_savings.json)。

### Caveman + RTK 同时启用

场景：运行一个包含 4 个测试、分属 2 个 test suite 的成功测试集，然后报告结果。
该 fixture 使用 RTK `0.45.0` 捕获，并由 `--verify-runtime` 校验。

压缩前：

Assistant 回复：

```text
The test suite completed successfully. I ran the standard test command and all four tests passed across two test suites. The passing cases cover refreshing an expired token, rejecting a malformed token, returning the current user, and rejecting an unknown user. There were no failures or snapshot changes, so the repository is ready for the next step.
```

命令：

```bash
bash benchmarks/fixtures/passing_suite.sh
```

工具输出：

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

同时启用两个模式后：

Assistant 回复：

```text
Tests pass: 4/4 in 2 suites; no failures.
```

命令：

```bash
rtk test bash benchmarks/fixtures/passing_suite.sh
```

工具输出：

```text
OUTPUT (last 5 lines):
  Test Suites: 2 passed, 2 total
  Tests:       4 passed, 4 total
  Snapshots:   0 total
  Time:        1.248 s
  Ran all test suites.
```

精确 token 统计：

| 部分 | 压缩前 | 压缩后 | 变化 |
| --- | ---: | ---: | ---: |
| Assistant 回复 | 65 | 15 | -50 |
| 命令 | 8 | 11 | +3 |
| 工具输出 | 118 | 56 | -62 |
| **总计** | **191** | **82** | **-109（57.1%）** |

这是固定 fixture 的实测结果，不是所有任务的保证。RTK 会增加命令 token，节省主要来自工具
输出过滤；实际结果会随语言、任务复杂度、测试输出、解释要求和 RTK 版本变化。

完整数据：[benchmarks/combined_rtk_caveman.json](../benchmarks/combined_rtk_caveman.json)。

## RTK 安全辅助工具

```bash
rtk --version
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/rtk_rewrite.py \
  'git status && npm test'
```

`rtk_rewrite.py` 只打印改写结果，不执行命令；它保留引号内容，不改写不支持的命令，并拒绝
包含 `sudo` 的命令链。

## 持久化默认值

只有用户明确要求保存时才写入 `~/.codex/codex-optimizer.json`：

```bash
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py show
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py set caveman full
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py set rtk on
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py reset
```

## 校验

```bash
python3 /home/lknife/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/codex-optimizer
python3 /home/lknife/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/codex-optimizer/skills/codex-optimizer
python3 benchmarks/token_savings.py --verify-runtime
```

## License

MIT，详见 [plugins/codex-optimizer/LICENSE](../plugins/codex-optimizer/LICENSE)。
