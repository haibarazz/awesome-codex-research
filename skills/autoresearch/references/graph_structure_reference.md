---
doc_id: graph-structure-reference
doc_type: reference
title: Graph Structure Reference
status: stable
summary: Experiment Graph Schema 的人读结构说明，覆盖快照、节点、缺值、引用、指标和边对象。
read_when:
  - 构造 Runtime 请求出错或 violations 指向结构问题时
depends_on:
  - research-graph-protocol
  - candidate-priority-rules
activation:
  level: ON_DEMAND
---

# Graph Structure Reference

本文是 Schema 的人读版；Schema 与 Runtime 才是强制源。正常路径不需要读本文——提交请求并处理 violations 即可。

## 1. Benchmark Snapshot

`EXPERIMENT_GRAPH.json` 顶层维护不可变 `benchmarks` 数组，供 HTML 解释不同 Benchmark 版本下的历史节点：

```json
{
  "benchmarks": [
    {
      "benchmark_id": "benchmark-v1",
      "benchmark_ref": "BENCHMARK.md",
      "display_metrics": [
        {
          "metric_id": "auc",
          "label": "AUC",
          "role": "PRIMARY",
          "direction": "MAXIMIZE",
          "unit": "RATIO",
          "precision": 4
        }
      ]
    }
  ]
}
```

快照只保存 `benchmark_id`、`benchmark_ref`、1–3 个 `display_metrics`，以及每项的 `metric_id`、`label`、`role`、`direction`、`unit`、`precision`。每个版本只登记一次；被节点引用后不可修改。指标定义变化必须创建新版本，跨版本不得计算直接 delta。

## 2. Permanent IDs and Time

- Research Node：`RN-XXXX`；Literature Node：`LN-XXXX`；Experiment：`EXXX`。
- 三套 ID 独立、单调递增、永久不可复用，不编码论文、方法、状态、优先级或模型角色。
- Candidate 建点时取得 RN；正式执行后只关联 Experiment ID，不更换 RN。
- 节点保存不可变 `created_at`；Graph 顶层保存事务完成后的 `updated_at`。
- 机器时间统一使用 ISO 8601 UTC。详细 attempt 与角色时间属于 Card、JSONL 和 role event。
- `SINGLE_RUN_JUSTIFIED` 的 Research Base 晋升 role event 额外保存 `single_seed_provisional: true`；其他角色事件可省略该字段。
- 机器字段与枚举使用英文规范值；中文只用于人类展示。

## 3. Research Node Shape

Research Node 采用薄节点：核心单值字段保持扁平，只有 `classification`、`metric_summary` 与 `refs` 使用固定嵌套对象。不得增加 `identity`、`lineage`、`research_intent`、`execution_state` 或 `evidence` 包装层。

```json
{
  "node_id": "RN-0012",
  "node_type": "RESEARCH",
  "created_at": "2026-07-16T18:30:00Z",
  "title": "Replace LSTM with BiLSTM",
  "benchmark_id": "benchmark-v1",
  "research_base_id": "RN-0004",
  "comparison_target_id": "RN-0007",
  "experiment_id": null,
  "hypothesis": "...",
  "mechanism": "...",
  "single_main_change": "...",
  "falsification_condition": "...",
  "branch_status": "OPEN",
  "branch_reason": null,
  "release_condition": null,
  "run_outcome": "NOT_RUN",
  "hypothesis_verdict": "UNTESTED",
  "candidate_priority": "GOLD",
  "priority_reason": "...",
  "classification": {},
  "metric_summary": [],
  "refs": {}
}
```

Research Node 不保存 `primary_parent_id`；唯一 Primary Parent 来自传入 `PRIMARY_PARENT` 边。`research_base_id` 与 `comparison_target_id` 是建点时冻结的比较锚点。

### 3.1 Fixed `refs` Keys

每个 Research Node 的固定 refs 键只定义为：

```json
{
  "refs": {
    "experiment_card": null,
    "research_log": null,
    "run_directory": null,
    "paper_mechanism_cards": [],
    "interaction_review_pack": null
  }
}
```

- `experiment_card` 由 `start-run` 创建并登记。
- `research_log` 在形成科研判断后登记。
- `run_directory` 指向 `logs/runs/EXXX/`。
- `paper_mechanism_cards` 保存直接支撑节点的机制卡。
- `interaction_review_pack` 只允许 MERGE 节点填写。

不得用通用 `artifacts` 数组替代固定 refs，也不得复制被引用文档正文。Stage Summary 只在 Graph 顶层 `stage_summaries` 登记。

### 3.2 Null and Missing-Value Rules

固定键不得因阶段或节点类别而省略。单值缺失使用 `null`，多值缺失使用 `[]`，未运行状态使用 `NOT_RUN` 与 `UNTESTED`。

- 根节点的 hypothesis、mechanism、single_main_change、falsification_condition、classification 为 `null`。
- R/A 节点的 candidate_priority 与 priority_reason 为 `null`。
- OPEN 不保存 branch_reason/release_condition；HOLD 两者均有值；CLOSED 只有 branch_reason。
- 未进入实验时 experiment_id 为 `null`；refs 的未生成路径按单值 `null`、多值 `[]` 表达。
- 无有效指标时 metric_summary 仍保留冻结指标项，各 value 为 `null`。

节点后续只更新值，不改变键集合。

### 3.3 Research Intent and Classification

除根节点外，hypothesis、mechanism、single_main_change、falsification_condition 都必须是独立、简短且可执行的字段；缺少任一项不得进入 Active Frontier。

五维分类枚举、R/A/N 与 Gold/Silver/Hold/Reject/Invalid 的唯一人读定义在 [Candidate Priority Rules](candidate_priority_rules.md)。本结构篇只要求非根节点保存合法 `classification`；N 节点同时保存 candidate_priority 与 priority_reason，R/A 节点对应字段为 `null`。

REJECT/INVALID Draft 不成为持久化 RN；`structural_default_priority` 可由矩阵计算，不在节点重复保存。正式执行后，开跑前的 candidate_priority 与 priority_reason 继续冻结，不得按结果倒改。

### 3.4 `metric_summary` Shape

每个 Benchmark 冻结同一组 1–3 个 display metrics；Primary 必须排第一，其余只能是已登记 Secondary 或 Hard Constraint。metric_summary 只保存原始值：

```json
{
  "metric_summary": [
    {"metric_id": "auc", "value": 0.8123},
    {"metric_id": "f1", "value": 0.7461},
    {"metric_id": "latency_ms", "value": null}
  ]
}
```

每项只能含 `metric_id` 和 `value`，数组数量、ID、顺序与 Benchmark 一致。value 只允许原始数值、布尔值或 `null`；单位、方向、精度、最佳 epoch、seed、置信区间和 slice 结果由 Benchmark、Card 或 artifact 保存。Graph 不持久化可由原始值和冻结锚点计算的 delta。

节点不得复制完整训练参数、step/batch/epoch 日志、完整论文分析、长篇结论或内部思维；它只保存渐进式引用。

## 4. Literature Node Shape

Literature Node 只在一次聚焦检索与全文核验完成后写入：

- `node_id`、固定 `node_type=LITERATURE`、`created_at`、`title`；
- `trigger`、`research_question`、`search_scope`；
- `search_outcome`、`outcome_reason`、`direction_summary`；
- `selected_papers`，每项仅含 `title`、`pdf_ref`、`mechanism_card_ref`；
- `literature_survey_ref`。

`DIRECTIONS_FOUND` 要求 direction_summary 和 1–4 篇论文；少于三篇须记录证据缺口。`NO_DIRECTION` 的 direction_summary 为 `null`，selected_papers 可为 0–4 项。

trigger 固定包含 `type`、`source_node_ids`、`source_ref`、`reason`。type 使用 `BOOTSTRAP | BOTTLENECK | BRANCH_CLOSED | FRONTIER_EMPTY | BASE_PROMOTION | STAGE_PIVOT | INTERACTION_REVIEW | NO_DIRECTION_RECOVERY`。完整查询、候选池、DOI、hash 与逐篇证据留在 Literature Survey 和 Mechanism Card。

BOOTSTRAP 可无来源节点；INTERACTION_REVIEW 通常引用两个 RN；NO_DIRECTION_RECOVERY 必须引用上一 NO_DIRECTION LN；其他 trigger 必须引用触发节点、文档或二者之一。

## 5. Edge Object

每条边只保存：

- `from_node_id`
- `to_node_id`
- `edge_type`
- `reason`
- `evidence_ref`

`(from_node_id, to_node_id, edge_type)` 是唯一键，不设 edge_id 或时间字段。PRIMARY_PARENT 的 reason/evidence 可为 `null`；DIRECTION 与 SOURCE 要有 reason；MERGE 的 reason 与指向 Interaction Review Pack 的 evidence_ref 均必填。边与目标节点同时冻结；只允许修正可验证的元数据错误。

## 6. Enforcement

字段、枚举、ID、null、DAG、边和引用由 `assets/schemas/experiment_graph.schema.json` 与 Runtime 强制执行。请求被拒时以 `error_code`、`violations` 和 `allowed_next_actions` 为准，不得手工修改 canonical Graph。
