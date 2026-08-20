# Codex Optimizer

将一套面向编码代理的效率工作流封装为可安装的 Codex 插件。插件提供一个
`codex-optimizer` skill，包含三个相互独立的模式：

- **Caveman**：减少解释性文本和 token，支持 `lite`、`full`、`ultra`、`micro`。
- **Ponytail**：YAGNI 优先，优先标准库、平台能力和已有依赖，保持最小正确改动。
- **RTK**：对支持的 shell 命令显式使用 `rtk` 前缀，并提供安全的链式命令改写 helper。

## 运行方式

Codex skill 通过指令生效，不会静默拦截所有 shell 调用：

- 用 `$codex-optimizer` 或自然语言显式启用 skill。
- Caveman 和 Ponytail 通过 skill 指令生效。
- RTK 前缀由 Codex 在生成命令时显式写出。
- `rtk_rewrite.py` 只输出改写结果，不执行命令。
- `sudo` 命令会被 helper 拒绝，必须走宿主环境批准的提权流程。

## 安装

需要 Codex CLI。首次安装：

```bash
git clone https://github.com/Lcryolite/codex-optimizer.git
cd codex-optimizer
codex plugin marketplace add .
codex plugin add codex-optimizer@codex-optimizer
```

安装后重新开启 Codex CLI 会话，然后运行 `/plugins` 检查插件，或在任务中显式调用：

```text
Use $codex-optimizer with caveman full.
Use ponytail lite for this implementation.
Enable RTK for supported shell commands.
```

## 模式与级别

| 模式 | 可选值 | 作用 |
| --- | --- | --- |
| Caveman | `off` / `lite` / `full` / `ultra` / `micro` | 压缩解释，保留代码、错误和技术细节。 |
| Ponytail | `off` / `lite` / `full` / `ultra` | 先检查需求、标准库、平台能力和已有依赖，再写最少代码。 |
| RTK | `off` / `on` | 对支持的命令使用 `rtk`；不支持的命令保持原样。 |

Caveman 只影响解释文本，不压缩代码、错误消息、安全边界或用户要求的格式。
Ponytail 不会删除信任边界校验、错误处理、安全性、无障碍要求或明确需求。

## Token 基准

仓库包含 6 组固定测试数据：[`benchmarks/token_savings.json`](benchmarks/token_savings.json)。
每组数据提供同一个编码任务的普通版、`lite`、`full`、`ultra` 和 `micro` 回复，脚本使用
`tiktoken` 的 `o200k_base` 编码统计回复 token 数：

```bash
python3 -m pip install tiktoken
python3 benchmarks/token_savings.py
```

当前固定样本结果（6 组共 403 个基准 token）：

| Caveman 级别 | 压缩后 token | 节省 token | 节省比例 |
| --- | ---: | ---: | ---: |
| `lite` | 246 | 157 | 39.0% |
| `full` | 150 | 253 | 62.8% |
| `ultra` | 131 | 272 | 67.5% |
| `micro` | 117 | 286 | 71.0% |

这些数字只统计回复文本，不包含 prompt、代码、错误原文和 shell/tool 输出；它们是可复现的
样本基准，不是每次任务的固定承诺。实际节省量取决于语言、任务复杂度、是否需要完整解释和
用户要求的输出格式。Ponytail 的收益主要体现在减少无必要实现，RTK 的收益主要取决于命令
输出压缩；两者没有混入上表的 Caveman 回复统计。

## RTK

启用前先确认 RTK 可执行：

```bash
rtk --version
```

示例：

```bash
rtk git status
rtk npm test
```

复杂链式命令可以使用不执行命令的 helper：

```bash
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/rtk_rewrite.py \
  'git status && npm test'
```

## 持久化默认值

只有用户明确要求保存时才写入 `~/.codex/codex-optimizer.json`：

```bash
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py show
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py set caveman full
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py set rtk on
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py reset
```

## 目录结构

```text
.
├── .agents/plugins/marketplace.json
├── benchmarks/token_savings.json
├── benchmarks/token_savings.py
├── plugins/codex-optimizer/
│   ├── .codex-plugin/plugin.json
│   ├── skills/codex-optimizer/SKILL.md
│   ├── skills/codex-optimizer/scripts/codex_config.py
│   ├── skills/codex-optimizer/scripts/rtk_rewrite.py
│   ├── LICENSE
│   └── README.md
└── README.md
```

## 校验

```bash
python3 /home/lknife/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/codex-optimizer
python3 /home/lknife/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/codex-optimizer/skills/codex-optimizer
python3 benchmarks/token_savings.py
```

## License

MIT，详见 [LICENSE](plugins/codex-optimizer/LICENSE)。
