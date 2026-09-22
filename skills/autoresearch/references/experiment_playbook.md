---
doc_id: experiment-playbook
doc_type: reference
title: Experiment Playbook
status: stable
summary: 定义正式实验的预登记、启动、监控、长短 epoch 停止、运行结局、技术重试和收口流程。
read_when:
  - 创建 Experiment Card 或启动正式训练前
  - 监控 epoch、执行 early stopping 或 stop-loss 时
  - 处理 Technical Failure、attempt 重试或实验收口时
depends_on:
  - research-contract
  - benchmark-and-model-roles
  - research-records-protocol
activation:
  level: PHASE
  phases:
    - EXPERIMENT_EXECUTION
    - RESULT_ROUTING
---

# Experiment Playbook

## Contents

1. Purpose and Required Inputs
2. Canonical Terms and Pre-run Hard Gates
3. Selection Split
4. Short-Epoch and Long-Epoch Regimes
5. Run Outcomes
6. Technical Smoke and Retry
7. Monitoring and Stop-loss
8. Experiment Closure and Required Writeback
9. Exceptions and Related Modules

## 1. Purpose

本模块把已冻结的 Benchmark 和 Candidate 转换为一次可比较、可停止、可恢复、可收口的正式实验。

## 2. Required Inputs

启动前必须取得：

- `RESEARCH_BRIEF.md`
- 当前 `BENCHMARK.md`
- 当前 Research Base 与比较锚点
- 已通过候选审查的 Research Node
- 处于 `PLANNED` 的 Experiment Card
- 剩余 Research Budget

## 3. Canonical Terms

| Term | 含义 |
|---|---|
| `Selection Split` | 用于 early stopping、checkpoint 选择和 go/no-go 判断的数据划分 |
| `Full Comparable Run` | 跑满固定预算或按预登记正常早停结束的正式训练 |
| `Fast-run Regime` | 一次完整可比训练含正常早停不超过 5 分钟 |
| `Slow-run Regime` | 一次完整可比训练含正常早停超过 5 分钟 |
| `Long-Epoch Regime` | 单个完整 epoch 预计超过 20 分钟 |
| `Short-Epoch Regime` | 单个完整 epoch 预计不超过 20 分钟 |
| `Technical Smoke` | 只验证工程路径、不产生科研结论的低成本 attempt |

## 4. Pre-run Hard Gates

正式训练前，AI 必须确认：

1. Benchmark 版本、数据划分、指标、训练预算和评估脚本均已冻结；
2. Primary Parent、Research Base 和 Core Comparison Target 明确；
3. Experiment Card 已登记假设、机制、唯一主要改动和证伪条件；
4. 五维分类、候选优先级和必要 Gate 已通过；
5. Selection Split、最大 epoch/step、early stopping、单次墙钟和 stop-loss 已预登记；
6. 代码、数据、配置、seed 和预期 artifact 可以追踪；
7. 剩余预算足以完成本次正式实验；
8. Technical Smoke 如有必要，已经验证数据、forward、loss、backward、指标和保存路径。

任何硬门缺失时不得启动正式训练。

## 5. Selection Split

项目存在 validation 时：

- validation 必须承担 early stopping、checkpoint 选择和 go/no-go；
- test 只用于最终正式评估。

项目只有 train/test 时：

- 允许 test-as-feedback；
- 必须在 Experiment Card 和日志中声明 test 已参与选择；
- 同一方向最多进行三次调参；
- 不得将该 test 结果声称为未参与选择的无偏泛化估计。

## 6. Short-Epoch Regime

单个 epoch 不超过 20 分钟时，除 NaN、Inf、OOM、梯度爆炸、代码错误等明确技术或数值故障外，原则上只在完整 epoch 结束后判断是否继续。

不得因为 batch/step loss 的短期噪声在 epoch 中途终止，也不得为节省少量时间临时改变已登记的 early stopping。

## 7. Long-Epoch Regime

单个 epoch 超过 20 分钟时，Benchmark 必须预登记：

- 最少完整运行 1 个还是 2 个 epoch；
- epoch 内允许监控的信号；
- 正常 patience；
- 最佳 checkpoint 恢复方式。

长 epoch 以 Selection Split 的完整 epoch 指标作为主要泛化信号。training loss 继续下降、但 Selection Split 从最佳 epoch 明显下降，视为过拟合倾向。

默认规则：

- 完成预登记的最少完整 epoch 后；
- 若一个完整 epoch 未改善，使用 `patience = 1` 停止；
- 保存并恢复最佳 Selection Split checkpoint；
- 若下一 epoch 已在评估返回前启动，确认过拟合趋势后允许中途停止。

Benchmark 可以冻结不同 patience，但 Candidate 与对照必须使用同一口径。

## 8. Run Outcomes

每次正式训练必须归入：

| Run Outcome | 判定 | 科研用途 |
|---|---|---|
| `COMPLETED` | 跑满 Benchmark 固定预算 | 完整可比结果 |
| `NORMAL_EARLY_STOP` | 严格按预登记正常早停结束 | 完整可比结果 |
| `STOP_LOSS` | 触发预登记止损线 | 失败筛选证据，不可晋升 |
| `TECHNICAL_FAILURE` | OOM、断连、代码错误、artifact 损坏等 | 不得解释为方法效果 |

不得用临时缩短 epoch、减少训练数据或降低评估频率的短跑替代 Full Comparable Run。

## 9. Technical Smoke and Retry

Technical Smoke：

- 使用正式 Experiment ID；
- 使用独立 attempt；
- 明确标记为 smoke；
- 只验证工程正确性；
- 指标不得进入正式结果表、模型角色判断或底座晋升。

Technical Failure 后：

1. 保存错误证据和最后有效 artifact；
2. 保留原 Experiment ID；
3. 修复工程问题；
4. 使用新的 attempt 编号重试；
5. 在 Experiment Card 和 Run Event Log 中记录修复与重试关系。

若故障属于外部基础设施且有限恢复后仍无可用路径，按 [Governance and Autonomy](governance_and_autonomy.md) 进入 `HUMAN_REVIEW_REQUIRED`。

## 10. Monitoring and Stop-loss

训练期间：

- step/batch、资源和 heartbeat 写入 Run Event Log；
- 影响科研判断的 epoch 指标和停止原因写入 Experiment Card；
- stop-loss 只能使用预登记阈值；
- 技术故障可以随时终止；
- 正常效果判断遵循对应长短 epoch 规则；
- 终止时保存最佳 checkpoint、最后有效状态和完整原因。

训练 loss 单独下降不构成继续训练理由；Selection Split 改善、预登记预算和过拟合证据共同决定是否继续。

## 11. Experiment Closure

实验结束后依次执行：

1. 确认 Run Outcome；
2. 校验 checkpoint、metrics、配置、代码与数据版本；
3. 计算与 Research Base、Champion 和必要 Experimental Parent 的可比结果；
4. 对照预登记假设给出科研判定；
5. 更新 Experiment Card 至 `FINISHED`；
6. 更新研究日志和实验图；
7. 交由 [Benchmark and Model Roles](benchmark_and_model_roles.md) 判断 Champion、Reference Baseline 或 Research Base 资格；
8. 交由 Research Graph Controller 决定扩展、修复、Hold、关闭或回溯。

## 12. Required Writeback

- Experiment Card
- `logs/runs/EXXX/AYY.jsonl`
- Research Experiment Log
- trainer、checkpoint 和 metrics artifact 路径
- Experiment Graph 中的 `run_outcome`、`hypothesis_verdict` 和结果摘要

## 13. Exceptions and Recovery

Benchmark 口径冲突时停止正式实验，并按 [Benchmark and Model Roles](benchmark_and_model_roles.md) 处理版本化。原始运行事实与研究叙事冲突时，以可验证的 Run Event Log 和 artifact 为准。

## 14. Related Modules

- [Research Contract](research_contract.md)
- [Benchmark and Model Roles](benchmark_and_model_roles.md)
- [Research Records Protocol](research_records_protocol.md)
- [Research Graph Protocol](research_graph_protocol.md)
