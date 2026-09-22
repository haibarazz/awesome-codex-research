---
doc_id: research-records-protocol
doc_type: reference
title: Research Records Protocol
status: stable
summary: 定义 Experiment Card、研究日志、机器事件日志、Master Roadmap、分卷、artifact 和 Stage Summary 的记录与读取规则。
read_when:
  - 创建、更新或收口实验记录时
  - 读取当前研究进度与历史证据时
  - 触发 Stage Summary、封存日志卷或切换阶段时
depends_on:
  - research-contract
  - governance-and-autonomy
  - experiment-playbook
activation:
  level: ON_DEMAND
---

# Research Records Protocol

## Contents

1. Purpose and Required Inputs
2. Canonical Terms
3. Directory and Sources of Truth
4. Experiment Card Lifecycle
5. Research and Run Logs
6. Master Experiment Log and Roadmap
7. Stage Summary Triggers and Decision Flow
8. Required Writeback
9. Exceptions and Related Modules

## 1. Purpose

本模块规定研究事实、机器运行事件、阶段 Roadmap 和反思总结如何分层记录，使 AI 能先读取最小上下文，再按需下钻到完整证据。

## 2. Required Inputs

- 冻结的 Research Brief 与 Benchmark
- 当前 Master Experiment Log
- Experiment Card
- Run Event Log 与 trainer artifact
- Experiment Graph

## 3. Canonical Terms

| Term | 含义 |
|---|---|
| `Experiment Card` | 单次正式实验从预登记到收口的唯一事实记录 |
| `Research Experiment Log` | 面向研究者的精简 Markdown 实验记录 |
| `Run Event Log` | 面向自动化监控与故障恢复的 JSONL 事件流 |
| `Master Experiment Log` | 项目统一入口与阶段 Roadmap |
| `Stage Summary` | 基于冻结证据包完成的阶段反思与路线裁决 |
| `Stage Evidence Pack` | Stage Summary 使用的只读实验、日志和 artifact 集合 |

## 4. Directory and Source-of-Truth Layout

```text
EXPERIMENT_LOG.md
logs/
├── research/
│   ├── volume_001.md
│   └── volume_002.md
├── runs/
│   ├── E001/
│   │   ├── A01.jsonl
│   │   └── A02.jsonl
│   └── E002/
│       └── A01.jsonl
└── summaries/
    └── volume_001_summary.md
```

- Experiment Card 是单次实验事实源；
- `EXPERIMENT_LOG.md` 是项目级入口和 Roadmap；
- Research Experiment Log 保存精简科研判断；
- Run Event Log 保存机器事件；
- trainer stdout/stderr、TensorBoard、W&B 和 checkpoint 是被引用的 artifact，不复制进 Markdown。

## 5. Experiment Card Lifecycle

每次正式实验必须由 Runtime `start-run` 创建 Experiment Card。Card 只包含两个固定顶级区：

| 区域 | Owner | 内容 | 写入规则 |
|---|---|---|---|
| `## Runtime Record` | Runtime | 身份与 PLANNED 冻结事实、Attempt 生命周期和时间戳、命令与版本、预算、Run Outcome、指标、artifact 引用与 hash | 仅 `start-run` / `finish-run` 写入；内容 hash 必须与 runtime_state 一致 |
| `## Research Notes` | LLM | 预登记阐述、RUNNING 期工程修复、诊断线索、结果解释和决策 | 普通文件编辑只在末尾追加；Runtime 重写 Card 时原样保留 |

`start-run.preregistration` 必须提交 hypothesis、single_main_change、falsification_condition 和 classification；Runtime 与 Research Node 核对后写入 Runtime Record。Experiment 和 Attempt 状态依次使用 `PLANNED / RUNNING / FINISHED`，实际命令、配置、seed、代码与数据版本、启停时间、artifact 和预算也由 Runtime 记录。

不得先运行后补写 PLANNED 内容，也不得用训练后的新文档覆盖原始计划。

Runtime 在 `finish-run` 前及 `validate` 时校验 Runtime Record hash；任何人工改写都必须拒绝收口或报告违规。Research Notes 不参与该 hash，既有行不得删除或改写。Research Notes 保持精简，结果表只展开 Benchmark 的 1–3 个展示指标；全量 metrics、slice 结果和错误通过 artifact 链接引用。

失败实验使用同一结构，必须写清 Run Outcome、失败原因、假设是否关闭及下一步。

## 6. Research and Run Logs

Research Experiment Log 只在正式 attempt 收口并形成科研判断，或角色/路线发生重要变化时更新。PLANNED、RUNNING、heartbeat 和普通工程状态只写 Experiment Card 与 Run Event Log，避免研究日志重复机器过程。

Research Experiment Log 只保存会影响科研判断的假设、唯一主要改动、正式结果、归因、决策和证据路径。

Run Event Log 使用一行一个带时间戳事件的 JSONL，记录：

- attempt 启停与 heartbeat；
- epoch、评估与 checkpoint；
- 资源状态、warning 和 error；
- 重试、工程修复和终止；
- trainer 原始日志与监控 artifact 路径。

技术重试、不同 seed 和晋升确认使用新的 attempt 编号 `AYY`，不覆盖旧 JSONL。

## 7. Master Experiment Log and Roadmap

`EXPERIMENT_LOG.md` 固定只包含：

1. 研究目标：核心问题、Benchmark、最终完成标准；
2. 阶段 Roadmap：阶段目标、退出条件、状态和日志入口；
3. 当前位置：当前阶段、阶段性一句话认识、下一个里程碑和最近 Stage Summary。

它不复制模型角色全集、Active Frontier、逐实验摘要、完整 Experiment Card 或 artifact 清单。

Roadmap 阶段由 AI 按研究语义自适应划分，可以围绕研究方向、创新家族、论文复现与 Paper Repair、Research Base 演进或 Benchmark 版本组织。Roadmap 阶段与日志 volume 不要求一一对应。

读取顺序固定为：

1. `EXPERIMENT_LOG.md`
2. 当前 `logs/research/volume_NNN.md`
3. 最近 `logs/summaries/volume_NNN_summary.md`
4. 需要核查运行事实时，读取 `logs/runs/EXXX/AYY.jsonl`
5. 只有具体诊断需要时，读取 trainer artifact

## 8. Stage Summary Triggers

出现任一事件时，生成 Stage Summary 并开启新卷：

- 累计完成 10 个正式实验；
- Research Base 正式晋升；
- Benchmark 正式变更；
- 当前研究方向关闭或切换；
- 一次 Paper Repair Cycle 结束。

Champion 单独更新不触发 Stage Summary。

Stage Summary 生成后：

- 所覆盖的 Research Experiment Log volume 封存只读；
- 新卷承接实验编号、关键结论、当前角色和下一批候选；
- 实验编号不重置；
- 在 Experiment Graph 顶层 `stage_summaries` 中登记图级检查点。

## 9. Stage Summary Decision Flow

执行 [Stage Reflection Prompt](../prompts/stage_reflection.md)，先构建只读 Stage Evidence Pack，再固定回答：

1. 我们到底知道了什么；
2. 这些结果为什么发生；
3. 我们可能错在哪里；
4. 留下了什么可迁移认识；
5. 下一阶段有哪些真正可判别的方向；
6. 研究路线现在应当怎么走。

机制解释必须从第一性原理出发，区分 `OBSERVED`、`INFERRED`、`HYPOTHESIZED` 和 `UNKNOWN`，并引用 Experiment ID、attempt、artifact 或 Paper Mechanism Card。

头脑风暴只能发生在事实冻结、机制分析和对抗审查之后。每个候选只验证一个主要假设，并给出竞争解释、失败条件和最小判别实验。

Stage Summary 必须从以下路线选择一个主路线，并给出一个带触发条件的备用路线：

- `DEEPEN`
- `BROADEN`
- `REPAIR`
- `PIVOT`
- `CONCLUDE`

## 10. Required Writeback

- 通过 Runtime 更新 Experiment Card 的 Runtime Record；LLM 只追加 Research Notes
- 通过 Runtime 追加 Research Experiment Log
- 通过 Runtime 写入 attempt 启停边界；trainer 追加同一 JSONL 的监控事件
- 更新 Master Experiment Log
- 生成并封存 Stage Summary
- 更新 Experiment Graph 的 Stage Summary 检查点和相关节点引用

## 11. Exceptions and Recovery

原始事实与总结冲突时，以 Experiment Card、Run Event Log 和可验证 artifact 为准，不得为保持叙事一致而改写原始记录。技术故障的运行处理见 [Experiment Playbook](experiment_playbook.md)。

## 12. Related Modules

- [Research Contract](research_contract.md)
- [Experiment Playbook](experiment_playbook.md)
- [Research Graph Protocol](research_graph_protocol.md)
- [AutoResearch Runtime API](runtime_api.md)
- [Stage Reflection Prompt](../prompts/stage_reflection.md)
