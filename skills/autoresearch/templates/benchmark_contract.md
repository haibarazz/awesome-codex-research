---
doc_id: benchmark-contract-template
doc_type: template
title: Benchmark Contract Template
status: stable
summary: 生成项目 BENCHMARK.md，冻结数据划分、指标、训练评估、seed、停止规则、比较锚点与版本。
read_when:
  - 新建或版本化项目 Benchmark 时
depends_on:
  - research-contract
  - benchmark-and-model-roles
  - experiment-playbook
activation:
  level: ON_DEMAND
---

# Benchmark Contract Template

## 目录

- [职责](#职责)
- [1. 数据与划分](#1-数据与划分)
- [2. 指标与评估](#2-指标与评估)
- [3. 完整可比训练协议](#3-完整可比训练协议)
- [4. Seed 协议](#4-seed-协议)
- [5. 比较锚点与可复现 Artifact](#5-比较锚点与可复现-artifact)
- [6. 冻结硬门](#6-冻结硬门)
- [7. Benchmark 变更](#7-benchmark-变更)
- [签署](#签署)

## 职责

在正式实验开始前生成项目级 `BENCHMARK.md`，冻结一条研究主线中所有模型共同遵守的数据、训练、选择、评估与比较协议，并使每个结果都能在相同评测契约下公平比较。

AI 可以根据项目特点调整文档详略，但下列比较边界必须明确且可执行。

**Research Brief：** `<path>`

**Dataset Profile：** `<path>`

**Benchmark ID / Version：** `<stable identifier>`

## 1. 数据与划分

记录本版本实际使用的数据来源、版本或 fingerprint，以及 train、validation、test 等划分的可复现路径或生成方式。

明确：

- 样本、实体、分组或时间边界；
- 防止跨 split 重复、同实体泄漏、未来信息泄漏和标签泄漏的规则；
- Selection Split；
- 最终评估使用的 split；
- 数据预处理管线中必须对所有对照保持一致的部分。

项目存在 validation 时，Selection Split 必须使用 validation，test 只用于最终评估。只有项目确实没有 validation 时，才允许 test-as-feedback，并必须明确声明 test 已经参与 early stopping、checkpoint 选择或 go/no-go 判断。

普通标准化、清洗、缺失值处理和常规预处理由 AI 自主完成，不构成 HUMAN_REVIEW_REQUIRED。只有数据或评测有效性发生根本问题时才触发人工审查。

## 2. 指标与评估

引用 Research Brief 中唯一的 Primary Metric 和 Performance Target，并冻结：

- Primary Metric 的计算方向、聚合方式和判定精度；
- Secondary Metrics；
- Hard Constraints 的测量方法；
- 评估脚本、命令、配置和版本；
- checkpoint 选择与最终结果报告规则；
- 并列结果、缺失指标和无效输出的处理方式。

百分比型主指标沿用 Research Contract 中的百分点阈值。非百分比型主指标必须在本 Benchmark 中登记以下等价阈值：

- Research Base 性能晋升阈值；
- Simplification Trade-off 容忍线；
- Research Base 与 Champion 切换 Core Comparison Target 的差距阈值。

候选模型与所有对照必须使用同一评估脚本和口径。

## 3. 完整可比训练协议

冻结一次 Full Comparable Run 的共同协议，包括：

- 最大 epoch 或 step；
- 单次最大墙钟时间；
- 正常 early stopping 规则；
- Selection Split、patience、min-delta 和最佳 checkpoint 恢复规则；
- 预登记 Stop-loss 条件；
- 允许变化与禁止变化的训练配置边界；
- 必须保存的 checkpoint、metrics 和 artifact。

如果单个 epoch 预计不超过二十分钟，使用 Short-Epoch Regime，原则上只在完整 epoch 边界判断是否继续。

如果单个 epoch 预计超过二十分钟，使用 Long-Epoch Regime，并明确：

- 首先必须完整运行一个还是两个 epoch；
- 后续允许使用的 epoch 内监控信号；
- Selection Split 指标恶化时的停止规则；
- training loss 继续下降但 Selection Split 已恶化时，不得以 training loss 为理由继续过拟合。

Completed 与严格按照本 Benchmark 正常 early stopping 的 Normal Early Stop 都属于 Full Comparable Run。Killed by Stop-loss 只能作为失败筛选证据，Technical Failure 不得解释为方法效果。

### Budget Unit Mapping

从冻结的 Research Brief 原样引用 `wall_clock_hours`、`gpu_hours`、`monetary_cost.amount + currency` 与 `formal_experiment_count`；至少一项必须为正数。Runtime 的 `max_run_seconds` 由适用的小时预算换算，`max_experiments` 对应 `formal_experiment_count`，`max_cost` 的 `cost_unit` 必须明确为 `GPU_HOURS` 或 Brief 中登记的 ISO 4217 币种。没有冻结 `cost_unit` 时，`planned_max_cost` 必须为 0。

## 4. Seed 协议

登记普通探索实验使用的固定 seed。

必须填写以下冻结字段：

- `promotion_confirmation_policy`：只能是 `TWO_SEEDS`、`ONE_CONFIRM_SEED` 或 `SINGLE_RUN_JUSTIFIED`；
- Anchor Baseline 或当前 Research Base 在对应 seed 下的比较结果或 artifact；
- seed 结果的聚合与晋升判定方式。

三种 policy 的含义固定为：

- `TWO_SEEDS`：快跑默认；首次达标后追加两个不同 seed 的完整可比 attempt，三个 seed 均须方向一致，平均提升仍超过晋升线。
- `ONE_CONFIRM_SEED`：慢跑默认；首次达标后追加一个不同 seed 的完整可比 attempt，两个 seed 均须方向一致，平均提升仍超过晋升线。
- `SINGLE_RUN_JUSTIFIED`：仅当单次完整训练超过本 Benchmark 冻结的成本门槛时使用；必须同时登记 `single_run_threshold.resource`（`DURATION_SECONDS` 或 `COST`）、正数 `single_run_threshold.value` 与书面 `single_run_justification`。晋升后标记为 provisional。

非 `SINGLE_RUN_JUSTIFIED` policy 的 threshold 与 justification 必须为空。对应 seed 的 Research Base 结果缺失时，必须先用真实 artifact 通过 `REGISTER_BASELINE_SEED_EVIDENCE` 登记。

不得为所有普通探索实验重复运行多个 seed，也不得为候选和对照临时选择不同 seed。

## 5. 比较锚点与可复现 Artifact

在首个 Candidate 开跑前，完成并保存：

- Anchor Baseline 的模型定义、配置、代码版本、结果和 artifact；
- 初始 Research Base；如果没有其他稳定底座，初始 Research Base 可以等于 Anchor Baseline；
- 评估脚本和数据划分的可复现入口；
- 训练与评估环境、依赖版本和关键运行命令；
- Benchmark、模型结果和日志之间的引用路径。

Research Base 与 Champion 会在研究过程中变化，其最新状态由实验日志和 Stage Summary 维护，不反复改写冻结的 Benchmark。

## 6. 冻结硬门

正式实验开始前必须确认：

- 数据版本和 split 可以复现；
- Selection Split 与最终评估 split 已明确；
- Primary Metric、Secondary Metrics 和 Hard Constraints 可以由固定脚本计算；
- Full Comparable Run、early stopping 和 Stop-loss 规则已经登记；
- seed 协议已经登记；
- Anchor Baseline 已经完成，或其缺失已经作为当前 Benchmark 初始化任务被明确阻止在 Candidate 之前完成；
- Research Brief 的目标、预算和授权边界与本 Benchmark 不冲突。

任何一项仍会改变实验可比性时，不得启动正式 Candidate。

## 7. Benchmark 变更

普通 Candidate 表现不佳、论文复现失败或暂时没有涨点，不能成为修改 Benchmark 的理由。

如果发现数据泄漏、错误划分、标签或样本语义错误、数据损坏、评估脚本错误等有效性问题：

1. 停止启动新的正式实验；
2. 进入 `HUMAN_REVIEW_REQUIRED`；
3. 保留当前 Benchmark、日志、结果和 artifact；
4. 用户确认需要修正后，建立新的 Benchmark 版本，不覆盖旧版本；
5. 禁止跨 Benchmark 版本直接比较结果；
6. 在新版本下重新运行 Anchor Baseline、当前 Research Base，以及与 Research Base 不同的 Champion；
7. 重新建立比较锚点后，才允许继续新的 Candidate。

每次正式 Benchmark 变更都必须触发 Stage Summary，并在 Master Experiment Log 中记录版本切换及其原因。
