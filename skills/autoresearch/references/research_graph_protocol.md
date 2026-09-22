---
doc_id: research-graph-protocol
doc_type: reference
title: Research Graph Protocol
status: stable
summary: 定义实验图的科研语义、稳定状态、边、Graph Operations、结果路由与下一实验选择。
read_when:
  - 生成、选择、修复、关闭、回溯或合并研究方向时
  - 正式实验完成并需要路由下一行动时
depends_on:
  - research-contract
  - candidate-priority-rules
  - research-records-protocol
activation:
  level: PHASE
  phases:
    - BOOTSTRAP
    - LITERATURE_RESEARCH
    - CANDIDATE_DESIGN
    - RESULT_ROUTING
    - STAGE_REFLECTION
---

# Research Graph Protocol

## 1. Purpose and Authority

Research Graph Controller 在科研决策点维护实验谱系、Active Frontier 与唯一下一实验，持续到目标达成或预算耗尽。`EXPERIMENT_GRAPH.json` 是唯一图事实源，HTML 只由 Runtime 派生；图保存可审计对象与决策，不保存逐字思维，也不替代 Brief、Benchmark、Card、日志或 Stage Summary。

本文只定义科研判断。字段、ID、null、refs、metric_summary 与边对象形状见按需的 [Graph Structure Reference](graph_structure_reference.md)；Schema 与 Runtime 才是结构强制源。五维分类与优先级的唯一人读定义在 [Candidate Priority Rules](candidate_priority_rules.md)。

## 2. Nodes, Checkpoints, and Roles

- `LITERATURE` 表示一次已完成的聚焦检索与机制方向来源，不能成为模型代码的 Primary Parent。
- `RESEARCH` 是通过硬门的 Candidate 及其后续实验结果的永久身份；执行后继续更新同一 RN，不另建 Experiment Node。
- 未通过硬门的想法只存在于临时 GoT；失败、Hold、关闭、回溯和角色变化均不得改换既有 RN。
- Stage Summary 是顶层 `stage_summaries` 引用的子图检查点，不是节点或边；新候选仍须重新过硬门。
- Anchor Baseline、Research Base、Champion、Reference Baseline 是可审计角色，不是节点种类。当前角色由 `role_states` 表示，历史变化只追加 `role_events`。
- Active Frontier 是顶层最多三个通过硬门、`NOT_RUN` 且 `UNTESTED` 的候选集合；OPEN 只表示分支可扩展，不自动进入 Frontier。

## 3. Stable Research States

| Field | Value | 科研语义 |
|---|---|---|
| `branch_status` | `OPEN` | 方向仍允许产生后继候选 |
|  | `HOLD` | 等待明确补证、依赖或重审条件，不因时间自动恢复 |
|  | `CLOSED` | 停止沿此节点探索并永久保留历史；新证据须新建节点 |
| `run_outcome` | `NOT_RUN` | 尚无正式实验 |
|  | `COMPLETED` | 跑满 Benchmark 固定预算 |
|  | `NORMAL_EARLY_STOP` | 按预登记早停结束，仍是完整可比结果 |
|  | `STOP_LOSS` | 失败筛选结果，不能晋升 Research Base |
|  | `TECHNICAL_FAILURE` | 工程失败，不得解释为方法效果 |
| `hypothesis_verdict` | `UNTESTED` | 尚无有效正式检验 |
|  | `SUPPORTED` | 达到预登记方向、阈值与判别条件 |
|  | `NOT_SUPPORTED` | 未满足假设，不等于证明反向机制 |
|  | `INCONCLUSIVE` | 有效结果仍不能区分竞争解释 |
|  | `NOT_EVALUABLE` | 技术失败或结果不公平、不可比较 |

`STOP_LOSS` 默认只支持筛选层面的 NOT_SUPPORTED；`TECHNICAL_FAILURE` 对应 NOT_EVALUABLE。Attempt 过程属于 Card/JSONL，不复制瞬时 SELECTED/RUNNING 状态进图。

## 4. Literature Node Judgment

一个 Literature Node 表示围绕一个明确问题完成的聚焦调研，不表示单篇论文或论文目录。目标下载、核验并筛选 3–4 篇全文；合格论文不足三篇时保留实际数量并记录缺口，不得降标凑数。逐篇证据留在 Mechanism Card；LN 只保留问题、共同机制、入选引用与方向。

LN 完成后才写图，结论为 `DIRECTIONS_FOUND` 或 `NO_DIRECTION`；网络、下载、服务器故障或未完成检索不属于 NO_DIRECTION。科研判断变化必须新建 LN，旧节点只允许修正 DOI、标题、路径等事实元数据。

`NO_DIRECTION` 不终止也不人工暂停，依次：① Frontier 有候选则继续；② 扩到相邻任务、功能等价机制或更抽象理论再检索；③ 瓶颈明确则生成有最近邻全文证据的第一性原理 N candidate；④ 回溯并切换 Locus/Layer，必要时 Stage Summary→PIVOT。同一瓶颈无新证据时最多连续三个 NO_DIRECTION（直接、相邻、抽象）；之后必须生成、回溯或转向。

## 5. Edge Semantics

`PRIMARY_PARENT` 表示实际代码/模型继承；每个非根 RN 只能有一条。`DIRECTION` 表示 LN 产生或直接支持 RN。`SOURCE` 只表示旧结果、诊断或机制启发，不表示继承或组合。`MERGE` 只表示通过 Interaction Review Gate 的真实 A+B；目标仍以共同 Research Base 为唯一 Primary Parent。四类边均从旧到新并保持 DAG；回溯、关闭、角色、晋升与 Frontier 选择不是边。

## 6. Graph Operations

判断动作只写入 handoff；落库动作必须使用 [Runtime API §3.1](runtime_api.md#31-operation--api-映射)。

| Operation | 类别 | 效果与 Runtime 落点 |
|---|---|---|
| `GENERATE` | 判断 | 在临时 GoT 产生 Draft，不落库 |
| `REVIEW` | 判断 | 执行硬门、分类与必要 Pareto 比较 |
| `AGGREGATE` | 判断 | 聚合同一机制证据，写日志或 Summary |
| `BACKTRACK` | 判断 | 焦点退回最近仍有开放方向的祖先/替代分支 |
| `BRANCH` | 落库 | 新普通 RN；`propose CREATE_CANDIDATE` |
| `REFINE` | 落库 | 新 Paper Repair RN；`propose CREATE_REPAIR` |
| `MERGE` | 落库 | Gate 通过的组合 RN；`propose CREATE_MERGE` |
| `HOLD` | 落库 | 暂缓并登记理由/解除条件；`propose HOLD_NODE` |
| `CLOSE` | 落库 | 关闭并保留历史；`propose CLOSE_NODE` |
| `SELECT` | 落库 | 选唯一实验；随后 `start-run` 创建 Experiment/Attempt/Card |

`PRUNE` 不是操作：可恢复路线用 HOLD，无价值路线用 CLOSE。SELECT 本身不写文件或瞬时节点状态。

### 6.1 Candidate Review and Persistence

顺序固定为 GENERATE→REVIEW→BRANCH/REFINE/MERGE/HOLD。普通 REVIEW 由当前主 AI 在同一次调用完成：检查 Benchmark、公平预算、泄漏、单一改动、机制/证据、五维分类与结构上限；保存优先级、理由和下一操作即可。REJECT/INVALID 不建点；MERGE 才使用三个独立 reviewer，普通候选不增设 agent、投票、Markdown Pack 或人工审批。

### 6.2 Experiment Completion Router

正式实验后依次：①验证 Run Outcome、Benchmark、Selection Split 与 artifact；②有效达标则 TARGET_REACHED；③未达标且硬预算耗尽则 TARGET_NOT_REACHED；④否则处理三类人工暂停或技术恢复；⑤更新 Champion/Reference Baseline 并执行 Research Base 晋升门；⑥按 verdict 深入、修复、Hold、关闭、回溯或调研；⑦命中 Stage Summary 时先移交并结束调用；⑧否则刷新 Frontier；⑨SELECT 唯一下一实验。

- SUPPORTED 且晋升：以新底座重审开放方向；旧候选若仍有价值须相对新底座新建 RN，并以 SOURCE 引旧 RN。
- 论文候选是动态方向池而非顺序任务清单；底座变化后必须重审独立价值、可比性和信息增益。
- SUPPORTED 但不晋升：可保留 Champion/Reference Baseline，后续仍从当前 Research Base 生长。
- NOT_SUPPORTED 只有存在具体可证伪局部机制时才 REFINE；论文路线最多三个核心 Repair；否则 CLOSE+BACKTRACK。
- INCONCLUSIVE 有低成本判别实验则生成一个候选，否则 HOLD；NOT_EVALUABLE 只按技术/有效性问题处理。
- Frontier 为空时启动恢复型检索或第一性原理生成；成功路线只有提出新可证伪机制才继续深入。

Stage Summary 只按 Research Records Protocol 的正式触发点执行，不因每次实验完成自动生成。

### 6.3 Literature Triggers

Recovery Search 用于 Frontier 为空、分支关闭或连续无方向；Question-driven Search 可在 Frontier 非空时响应新底座瓶颈、组件/loss 缺口、Paper Repair、竞争解释或 Interaction 证据需求。每次必须登记会影响具体候选、组件、假设或路线的 Research Question；禁止无决策问题的泛检索。新旧方向统一 REVIEW，且不得批量启动实验。

### 6.4 Unique Next Experiment Selector

1. 决策债务优先：晋升 seed、ADD 替换实验、Benchmark 变更重跑、INCONCLUSIVE 最小判别实验；Promotion Confirmation 沿用 RN/Experiment，只加 attempt，不进 Frontier、不重复 SELECT。
2. 无债务时 GOLD 优先于 SILVER；HOLD 不在 Frontier。
3. 同级按字典序比较：目标差距潜力→机制证据→信息增益→简洁/归因→正式实验成本，禁止加权总分。
4. 仍平局则按进入 Frontier 时间、再按 RN ID 升序。
5. 每轮只 SELECT 一个；完成后重新 Router、刷新 Frontier，禁止预排队。

## 7. Runtime Enforcement

Graph mutation 只经 `Proposal → Validate → Apply`。结构错误读取按需 [Graph Structure Reference](graph_structure_reference.md)；科研判断仍以本文为准。
