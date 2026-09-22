---
doc_id: governance-and-autonomy
doc_type: reference
title: Governance and Autonomy
status: stable
summary: 定义 AutoResearch 启动对齐、Research Brief 冻结、预算边界、无人值守授权、人工暂停与研究终止状态。
read_when:
  - 初始化一项 AutoResearch 任务时
  - 冻结或变更 Research Brief 与研究预算时
  - 判断是否需要人工介入或结束整条研究时
depends_on:
  - research-contract
activation:
  level: PHASE
  phases:
    - BOOTSTRAP
    - RESULT_ROUTING
    - TERMINATION
    - HUMAN_REVIEW
---

# Governance and Autonomy

## Contents

1. Purpose and Required Inputs
2. Canonical Terms
3. Research Bootstrap and Brief Freeze
4. Autonomous Execution Boundary
5. Terminal and Human Review States
6. Required Writeback
7. Exceptions and Related Modules

## 1. Purpose

本模块管理 AutoResearch 从启动对齐到最终终止的研究级治理。它规定用户何时完成最后一次常规授权、AI 获得多大自主权、预算如何冻结，以及哪些事件允许进入 `HUMAN_REVIEW_REQUIRED`。

## 2. Required Inputs

启动时读取或生成：

- 用户提供的数据集、项目代码和已有结果；
- [ReproFlow Codebase Contract](reproflow_code_contract.md) 与 [Codebase Profile Template](../templates/codebase_profile.md)；
- [Dataset Profile Template](../templates/dataset_profile.md)；
- [Research Brief Template](../templates/research_brief.md)；
- [Benchmark Contract Template](../templates/benchmark_contract.md)；
- 用户明确提供的目标、资源和权限边界。

## 3. Canonical Terms

| Term | 含义 |
|---|---|
| `Research Brief` | 用户最终确认的研究目标、完成条件、预算和授权契约 |
| `Research Budget Envelope` | `wall_clock_hours`、`gpu_hours`、带币种的 `monetary_cost`、`formal_experiment_count` 中至少一个硬上限 |
| `TARGET_REACHED` | 冻结的 Primary Metric 达标且全部 Hard Constraints 通过 |
| `TARGET_NOT_REACHED` | 任一预登记预算硬上限耗尽时仍未达到目标 |
| `HUMAN_REVIEW_REQUIRED` | 仅处理根本有效性、外部阻塞或用户主动变更的临时暂停状态 |
| `Recovery Cycle` | 外部阻塞进入人工暂停前的一次有限诊断与恢复过程 |

## 4. Research Bootstrap and Brief Freeze

首次自主运行必须依次执行：

1. AI 检查当前目录是否存在可运行代码；已有代码则保留，无代码则按 ReproFlow Contract 自动安全 bootstrap；
2. 生成或核验 `CODEBASE_PROFILE.md`，记录代码根、来源、入口与预检；
3. AI 读取数据集、代码和已有 artifact，完成基础分析；
4. 生成 `DATASET_PROFILE.md`；
5. 用户完整描述研究需求与目标；
6. AI 只提出 3–5 个会改变目标、Benchmark、预算或完成标准的高价值问题；
7. 生成 `RESEARCH_BRIEF.md` 草案；
8. 用户明确最终确认后，将 Brief 从 `DRAFT` 冻结为 `FROZEN`。

能够从数据、代码和既有结果中查明的事实不得询问用户。最终确认前，代码库写入只允许安全 Codebase Bootstrap；研究控制层可以生成 `DATASET_PROFILE.md` 和 `RESEARCH_BRIEF.md` 草案，但不得启动会形成科研结论的实验。

`DATASET_PROFILE.md` 使用三层证据：

- `Observed Facts`：直接从文件、代码或 artifact 确认的事实；
- `Inferred Findings`：AI 推断，必须记录依据与置信度；
- `Risks / Pending`：尚未解决且可能影响 Brief、Benchmark 或实验设计的问题。

Dataset Profile 保持简短和自适应，不要求完整数据字典。它不得决定性能目标、研究方向或 Benchmark 裁决。

Research Brief 正文固定为：

1. `Research Goal`
2. `Success Criteria`
3. `Budget and Autonomy`
4. `Final Confirmation`

Brief 至少冻结：

- 研究领域、任务和已有 Baseline 状态；
- 唯一一个 Primary Metric 及其 Performance Target；
- 零个或多个 Hard Constraints；
- 至少一个 Research Budget Envelope 维度；
- 允许和禁止的行动；
- Dataset Profile 与 Benchmark 的路径。

Secondary Metrics 可以用于解释、选择和报告，但除非预先升级为 Hard Constraint，否则不得单独阻止 `TARGET_REACHED`。

## 5. Autonomous Execution Boundary

Brief 冻结后，只要行动仍处于授权目标、Benchmark、预算、权限和资源边界内，AI 必须自动完成：

- 文献调研与方法复现；
- 候选生成、审查和实验运行；
- 失败诊断、有限修复、回滚和路线切换；
- Research Base 晋升与 Champion 更新；
- Stage Summary、实验图和日志维护。

中间实验、论文选择、失败修复、Stage Summary、底座晋升和路线切换均不得再次请求常规批准。AI 不得静默移动 Performance Target、增加预算或扩大权限。

预算使用四个单位明确的字段，至少一个为正数：

- `wall_clock_hours`：自然流逝的小时数；
- `gpu_hours`：GPU-hours；
- `monetary_cost`：金额与 ISO 4217 币种，二者必须同时登记；
- `formal_experiment_count`：正式 Experiment 数量。

同时登记多个维度时，每个都是独立硬上限，任何一个先耗尽即进入预算终止判断。

文献检索、PDF 下载、Stage Reflection、候选审查和 subagent 调用产生的 token/API 开销默认不计入 GPU 或货币预算；只有用户在 Brief 中显式设置 `llm_cost_counted: true` 时，才计入已登记币种的 monetary budget。无论是否计入 LLM 成本，`wall_clock_hours` 始终按自然时间流逝。Runtime 的 `audit_counters` 记录 Stage Reflection 与 subagent 调用次数，仅供审计，不自动折算成本。

## 6. Terminal and Human Review States

研究级主动终止只有：

- `TARGET_REACHED`；
- `TARGET_NOT_REACHED`。

单次实验失败、连续无涨点、论文复现失败、Paper Repair 失败、当前无候选、普通技术失败或路线切换都不是终止理由。剩余预算内必须继续诊断、恢复、调研或转向。

`HUMAN_REVIEW_REQUIRED` 仅允许由三类事件触发：

1. 数据或评测有效性根本失效，例如泄漏、错误划分、标签/样本语义错误、数据损坏或评估脚本错误；
2. 外部基础设施或访问阻塞在 Recovery Cycle 后仍无法恢复，且没有已授权替代路径；
3. 用户明确要求暂停，或实质性修改冻结的目标、Benchmark、预算或权限。

未标准化、普通缺失、类别不平衡、常规清洗和可修复工程问题由 AI 自行处理，不触发人工暂停。

外部阻塞的 Recovery Cycle 必须：

1. 保存日志、checkpoint 和错误证据；
2. 诊断原因；
3. 尝试一次安全重连、重启或恢复；
4. 在已有授权内尝试一个替代运行路径。

正式进入人工暂停后停止新实验并冻结研究状态。人工等待时长不计入墙钟预算；已经发生或暂停期间继续产生的 GPU、服务和存储消耗仍计入预算。用户裁决后从剩余额度恢复；若暂停前预算已经耗尽，直接进入 `TARGET_NOT_REACHED`。

## 7. Required Writeback

- `CODEBASE_PROFILE.md`
- `DATASET_PROFILE.md`
- `RESEARCH_BRIEF.md`
- `BENCHMARK.md`
- 预算使用状态
- 人工暂停问题、受影响证据和恢复条件
- 最终研究总结与最佳可复现 artifact

Brief 的生命周期为 `DRAFT → FROZEN → SUPERSEDED`。正式变更必须创建新版本并保留旧版本。

## 8. Exceptions and Recovery

Benchmark 根本有效性问题的具体版本化与锚点重跑规则见 [Benchmark and Model Roles](benchmark_and_model_roles.md)。训练技术失败的 attempt 恢复见 [Experiment Playbook](experiment_playbook.md)。

## 9. Related Modules

- [Research Contract](research_contract.md)
- [ReproFlow Codebase Contract](reproflow_code_contract.md)
- [Research Bootstrap Prompt](../prompts/research_bootstrap.md)
- [Benchmark and Model Roles](benchmark_and_model_roles.md)
- [Research Records Protocol](research_records_protocol.md)
