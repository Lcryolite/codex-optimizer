# Codex Optimizer 中文文档

[English README](../README.md)

Codex Optimizer 是一个基于真实 Codex hooks 的自动优化插件：由 RTK 静默改写受支持的
shell 命令，在不注入重复模型上下文的前提下分析压缩候选，并减少回复冗余。本仓库还通过
Git submodule 固定并发布完整的上游 Ponytail 插件。

## “自动”是运行时自动

编码、调试、测试、重构、仓库和 shell 任务都不需要手动输入
`$codex-optimizer`。信任 hooks 后，执行链为：

```text
自然 Bash 命令
  → PreToolUse → rtk rewrite → 改写后的命令
  → 执行命令
  → PostToolUse → 静默本地阶段分析 + 指标
```

PreToolUse 不再输出 hook 消息或模型上下文，正常的命令执行行会直接显示 `rtk ...`，这已经
是充分证据。PostToolUse 仅在本地记录更小候选，不输出 hook 消息：

```text
rtk git status
```

会话启动时只向模型注入两个有效模式值，不再重复十个阶段名称。不支持的命令或不能产生
更小候选的输出保持静默。

Codex 目前没有“静默替换任意 PostToolUse 结果”的受支持字段。返回
`continue: false` 虽能替换结果，但会把 hook 标记为 `(stopped)`。本插件明确不再这样做：
RTK 在 Bash 输出进入 Codex 前完成真实缩减；PostToolUse 保留原始结果、记录候选指标，但
不输出 `systemMessage`、`additionalContext` 或阻断结果。
详见官方 [Codex hooks 协议](https://learn.chatgpt.com/docs/hooks#posttooluse)。

## 默认模式

| 模式 | 默认值 | 作用 |
| --- | --- | --- |
| Caveman | `full` | 删除客套、模糊措辞、重复和填充语，保留全部技术内容；安全与不可逆操作临时优先清晰表达。 |
| RTK | `on` | 通过静默 `PreToolUse` 改写和零模型上下文的 `PostToolUse` 分析运行。 |

Ponytail 不再作为 Codex Optimizer 内部的不完整模式存在。本 marketplace 发布未经复制的
上游插件，因此会安装其完整 skill 与生命周期 hooks；配置和版本也由上游独立维护。

## 全部输出阶段

只有产生更小候选的阶段才会静默记录本地指标。候选不会输出，也不会与原始工具结果一起
注入模型，因此分析增加零 transcript 和模型上下文，正常执行也不会变成 `(stopped)`。

| 阶段 | 说明 |
| --- | --- |
| ANSI Stripping | 删除终端颜色和格式控制码。 |
| Test Aggregation | 汇总通过、失败、跳过数量，并保留失败细节。 |
| Build Filtering | 删除常规构建进度，保留错误和警告。 |
| Git Compaction | 压缩 `git status`、`git log`、`git diff`。 |
| Linter Aggregation | 汇总诊断和错误/警告数量。 |
| Search Grouping | 按文件分组 `rg`/`grep` 结果。 |
| Source Code Filtering | 仅在大型读取本来就需要有损压缩时删除冗余注释和空行；保留 userscript 元数据。 |
| Smart Truncation | 保留有代表性的首尾上下文，并报告省略行数。 |
| Anchor-Safe Read Compaction | 识别带锚点的读取格式，保留完整编辑锚点。 |
| Hard Truncation | 对候选结果强制执行 12,000 字符上限。 |

测试锁定了安全边界：不超过 80 行的读取保持原样，显式 offset/limit 读取保持原样，skill
文件保持原样；任何可识别的 `sudo`、发布、远程写入和破坏性命令都不会交给 RTK，也不会
获得自动 `permissionDecision: allow`。

某次 Bash 操作需要精确、未过滤或机器可读输出时，可只绕过这一次 RTK：

```bash
CODEX_OPTIMIZER_RAW=1 rg --json needle src
```

hook 不会改写该操作；此前缀保留在实际 shell 命令中，不会修改持久化 RTK 设置。

## 安装

需要 Codex CLI，并确保 `rtk` 和 `node` 都在 `PATH` 中。Codex Optimizer 使用 RTK，
上游 Ponytail 生命周期 hooks 使用 Node.js：

```bash
git clone --recurse-submodules https://github.com/Lcryolite/codex-optimizer.git
cd codex-optimizer
codex plugin marketplace add .
codex plugin add codex-optimizer@codex-optimizer
codex plugin add ponytail@codex-optimizer
```

已有 checkout 先初始化子模块：

```bash
git submodule update --init --recursive
```

新开 Codex 会话，执行 `/hooks`，检查并信任两个插件的 hooks。Codex 要求这一步，是因为 hook
会运行本地代码。hook 启动器会在执行时解析最新的有效安装缓存，因此重新安装更新后，已在
运行的会话不会继续指向被删除的旧版本目录。`--dangerously-bypass-hook-trust` 仅适用于已
经隔离并审计过的单次自动化环境。

之后直接提出正常编码任务即可，不需要触发词。`$codex-optimizer` 仍可用于自动范围之外的
任务。

## 更新 Ponytail

仓库固定到一个经过审查的上游 commit。更新时只移动 submodule gitlink：

```bash
git submodule update --remote plugins/ponytail
git diff --submodule=log -- plugins/ponytail
git add plugins/ponytail
```

随后验证两个插件并提交。Ponytail 源码没有复制进 Codex Optimizer，因此更新可通过普通
Git 历史审计和回退。

## 检查是否启动及实际节省

```bash
python3 plugins/codex-optimizer/scripts/codex_optimizer.py status
python3 plugins/codex-optimizer/scripts/codex_optimizer.py stats
```

`status` 会列出有效模式、十个阶段和累计候选缩减量。候选缩减是诊断指标，不冒充实际模型
输入节省；下面的可复现端到端基准只统计真实模型可见文本。

持久化覆盖只在用户明确要求时写入：

```bash
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py show
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py set caveman full
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py set rtk on
python3 plugins/codex-optimizer/skills/codex-optimizer/scripts/codex_config.py reset
```

## 可复现 Token 基准

基准使用 `tiktoken 0.14.0` 和 `o200k_base`，统计 assistant 回复、实际执行命令和 RTK 工具
输出。PreToolUse 不输出消息；PostToolUse 静默记录本地指标，不输出 hook 消息或模型
`additionalContext`。用户 prompt、tool-call JSON
外壳、隐藏推理和每会话一次的模式上下文不计入单次操作表，而是在下方单独报告。fixture
为确定性合成数据，因此字节级校验不依赖编译器版本或实际耗时。

### 基线 + 四个优化测试臂

固定隔离 fixture 规定每个优化器只能改变自己负责的产物：RTK 改变命令/工具输出，Caveman
只改变回复文字，Ponytail 只改变实现。表中包括基线、三个单项测试臂和三者合并测试臂。
两个实现必须通过相同的有效及无效输入契约；真实 RTK hook 与输出 fixture 进行字节级运行
验证。

| 测试臂 | 实现 | 回复 | 命令 | 输出 | 操作本体 | 节省 | 激活成本 | 首次会话 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 基线 | 243 | 87 | 15 | 307 | 652 | — | 0 | 652 |
| 仅 RTK | 243 | 87 | 17 | 16 | 363 | 289（44.3%） | 414 | 777 |
| 仅 Caveman | 243 | 16 | 15 | 307 | 581 | 71（10.9%） | 414 | 995 |
| 仅 Ponytail | 40 | 87 | 15 | 307 | 449 | 203（31.1%） | 2,874 | 3,323 |
| 三者合并 | 40 | 16 | 17 | 16 | 89 | 563（86.3%） | 3,288 | 3,377 |

四个优化测试臂都减少了本 fixture 的操作文本；计入完整激活上下文后，首次会话都没有节省。
假定以后每次仍有同样的操作差值、激活只支付一次，则 RTK 第 2 次回本，Caveman 第 6 次，
Ponytail 第 15 次，合并第 6 次。真实任务的节省不会恒定。

Caveman 与 Ponytail 是模型指令，不是确定性转换器；它们的输出在计数前固定。因此数据只
证明这些具体产物，不代表平均模型遵循率或生产环境收益。完整方法与命令见
[benchmark 环境](../benchmarks/README.md)。
各臂完全相同的用户任务、tool-call 外壳、隐藏推理和全局 skill catalog 均不计入；这些部分
在本次产物比较中相消。

### 压缩前

Assistant 回复：

```text
The test suite completed successfully. I ran the full Cargo test command and all twenty tests passed in one suite. The passing cases cover access-token validation, refresh-token rotation, cache expiry, and the complete set of user creation, lookup, update, and rejection paths. There were no failed, ignored, measured, or filtered tests, and the run finished in 0.03 seconds, so the repository is ready for the next step.
```

命令：

```bash
cargo test --manifest-path benchmarks/fixtures/rust-project/Cargo.toml
```

工具输出：

```text
   Compiling codex-optimizer-benchmark v0.1.0
    Finished `test` profile [unoptimized + debuginfo] target(s) in 1.24s
     Running unittests src/lib.rs (target/debug/deps/benchmark-0123456789abcdef)

running 20 tests
test auth::accepts_valid_access_token ... ok
test auth::refreshes_expired_access_token ... ok
test auth::rejects_expired_refresh_token ... ok
test auth::rejects_malformed_access_token ... ok
test auth::rejects_missing_signature ... ok
test auth::rejects_unknown_issuer ... ok
test auth::rejects_wrong_audience ... ok
test auth::rotates_refresh_token ... ok
test cache::evicts_expired_entries ... ok
test cache::keeps_recent_entries ... ok
test user::creates_user ... ok
test user::deletes_user ... ok
test user::finds_user_by_email ... ok
test user::finds_user_by_id ... ok
test user::lists_active_users ... ok
test user::rejects_duplicate_email ... ok
test user::rejects_empty_email ... ok
test user::rejects_unknown_user ... ok
test user::updates_display_name ... ok
test user::updates_password_hash ... ok

test result: ok. 20 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.03s
```

### 自动 RTK + 静默 PostToolUse + Caveman 后

实际执行命令：

```bash
rtk cargo test --manifest-path benchmarks/fixtures/rust-project/Cargo.toml
```

RTK 先把原始 1,123 字符输出缩减为：

```text
cargo test: 20 passed (1 suite, 0.03s)
```

PostToolUse 会计算以下候选用于本地指标，但不会输出它：

```text
Test Results:
  PASS: 20 passed
```

Caveman 回复：

```text
Tests pass: 20/20 in 1 suite; 0 failures.
```

精确 token 统计：

| 部分 | 压缩前 | 压缩后 | 节省 |
| --- | ---: | ---: | ---: |
| Assistant 回复 | 87 | 16 | 71 |
| 命令 | 15 | 17 | -2 |
| 工具输出 | 307 | 16 | 291 |
| 模型上下文中的优化器提示 | 0 | 0 | 0 |
| **总计** | **409** | **49** | **360（88.0%）** |

工具输出路径为：**307 原始 tokens → 16 RTK/模型可见 tokens**。PostToolUse 的
9-token 候选不会输出。本次实测操作减少 88.0%；这是固定 fixture 的
证据，不是对所有任务的保证。

固定激活上下文也明确计入：

| 激活组成 | Tokens |
| --- | ---: |
| Codex Optimizer `SKILL.md` | 399 |
| Codex Optimizer SessionStart 状态 | 15 |
| 上游 Ponytail `SKILL.md` | 1,610 |
| 上游 Ponytail `full` SessionStart 规则 | 1,264 |
| **两个已安装插件合计** | **3,288** |

218-token 的可选模式设置 reference 仅在用户要求修改、解释、保存或重置 Codex Optimizer
模式时加载。Ponytail SessionStart 一行通过带 `PLUGIN_DATA` 实际执行固定版本的上游 hook
得出，因此 Codex 输出不含仅面向 Claude 的 statusline 提示。两个插件激活后重复执行同一
fixture：

| 操作次数 | 压缩前 | 含固定上下文的压缩后 | 节省 |
| ---: | ---: | ---: | ---: |
| 1 | 409 | 3,337 | -2,928（-715.9%） |
| 2 | 818 | 3,386 | -2,568（-313.9%） |
| 5 | 2,045 | 3,533 | -1,488（-72.8%） |
| 10 | 4,090 | 3,778 | 312（7.6%） |

这是 transcript/上下文核算，不是账单承诺；provider prompt caching 和模型 continuation
次数会另外影响实际计费输入。

复现 token 和字节级运行结果：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install tiktoken==0.14.0
.venv/bin/python benchmarks/token_savings.py --verify-runtime
.venv/bin/python benchmarks/optimizer_matrix.py --verify-runtime
```

完整数据：
[`benchmarks/combined_rtk_caveman.json`](../benchmarks/combined_rtk_caveman.json)。
另有 6 组只测回复的固定样本：Caveman `full` 在 403 tokens 中节省 253 tokens
（62.8%）。

## 开发校验

```bash
CODEX_SYSTEM_SKILLS="${CODEX_HOME:-$HOME/.codex}/skills/.system"
python3 "$CODEX_SYSTEM_SKILLS/plugin-creator/scripts/validate_plugin.py" \
  plugins/codex-optimizer
python3 "$CODEX_SYSTEM_SKILLS/skill-creator/scripts/quick_validate.py" \
  plugins/codex-optimizer/skills/codex-optimizer
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
.venv/bin/python benchmarks/token_savings.py --verify-runtime
.venv/bin/python benchmarks/optimizer_matrix.py --verify-runtime
```

## 许可证与致谢

MIT，详见 [LICENSE](../plugins/codex-optimizer/LICENSE) 和
[NOTICE](../plugins/codex-optimizer/NOTICE.md)。Ponytail 作为独立 MIT 子模块发布，详见其
[许可证](../plugins/ponytail/LICENSE)。
