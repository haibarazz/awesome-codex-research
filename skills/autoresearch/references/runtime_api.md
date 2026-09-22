---
doc_id: autoresearch-runtime-api
doc_type: reference
title: AutoResearch Runtime API
status: stable
summary: 定义 LLM 与确定性 Runtime 的六个接口、请求边界、返回语义和 canonical 写入纪律。
read_when:
  - 初始化或检查 AutoResearch 项目时
  - 创建图节点、启动实验、收口实验或校验项目时
depends_on:
  - research-contract
  - research-graph-protocol
  - experiment-playbook
activation:
  level: PHASE
  phases:
    - BOOTSTRAP
    - LITERATURE_RESEARCH
    - CANDIDATE_DESIGN
    - EXPERIMENT_EXECUTION
    - RESULT_ROUTING
    - STAGE_REFLECTION
---

# AutoResearch Runtime API

## Contents

1. Boundary
2. Invocation
3. Six Commands
   - 3.1 Operation → API 映射
   - 3.2 `propose` action 语义
   - 3.3 Response Envelope
4. Minimal Examples
5. Deterministic Enforcement
6. Storage and Recovery

## 1. Boundary

LLM 负责数据理解、文献机制、假设、结果解释和路线选择；Runtime 负责 ID、字段、状态转换、数值门、预算、文件创建、原子替换和 HTML 渲染。

LLM 不得直接修改：

- `EXPERIMENT_GRAPH.json`
- `.autoresearch/runtime_state.json`
- `EXPERIMENT_GRAPH.html`
- Experiment Card 的 `## Runtime Record` 区
- Runtime 写入的 attempt 边界事件

所有 mutation 必须使用 `Proposal → Validate → Apply`。拒绝结果不是工具故障；LLM 应读取 `violations` 和 `allowed_next_actions`，修正科研提案后再次提交。

## 2. Invocation

```bash
python3 <skill>/scripts/autoresearch_runtime.py \
  --project-root <research-project> <command> [--request request.json]
```

Mutation 命令也可使用 `--request -` 从 stdin 读取 JSON。成功返回退出码 `0` 和 `accepted: true`；拒绝返回退出码 `2`、`accepted: false`、稳定错误码、违规项和允许的下一动作。

每个 mutation 都必须携带唯一 `request_id`，命名为
`<action-or-run>-<UTC YYYYMMDD>-<三位序号>`，例如
`create-candidate-20260719-001`。相同 ID 与相同 payload 会返回第一次结果；
相同 ID 与不同 payload 会被拒绝；修正 payload 后必须使用递增序号的新 ID。

## 3. Six Commands

| Command | 用途 | 是否写入 |
|---|---|---|
| `init` | 冻结 Brief/Benchmark 哈希、预算、主指标、`promotion_confirmation_policy` 和初始角色；初始化 Graph | 是 |
| `inspect` | 返回机器 Phase/trigger、角色（含 provisional 标记）、晋升 policy、预算、审计计数、Frontier、运行和节点摘要 | 否 |
| `propose` | 校验并应用图操作 | 是 |
| `start-run` | 分配 Experiment/Attempt ID，创建 Card 与 JSONL | 是 |
| `finish-run` | 收口结果、预算、角色、晋升门、日志和 Graph | 是 |
| `validate` | 检查全项目一致性并从 JSON 重建 HTML | 仅重建 HTML |

`propose` 的 `action` 只允许：

`CREATE_LITERATURE`、`CREATE_CANDIDATE`、`CREATE_REPAIR`、`CREATE_MERGE`、`SET_FRONTIER`、`HOLD_NODE`、`REOPEN_NODE`、`CLOSE_NODE`、`PROMOTE_RESEARCH_BASE`、`ASSIGN_REFERENCE_BASELINE`、`REGISTER_STAGE_SUMMARY`、`REGISTER_BASELINE_SEED_EVIDENCE`、`FINALIZE_RESEARCH`。

### 3.1 Operation → API 映射

判断动作只写入 `controller_handoff.graph_operations` 作为审计记录，不产生
Runtime mutation；落库动作必须伴随表中指定的 Runtime 调用。

| Graph Operation | 类别 | Runtime 落点 |
|---|---|---|
| `GENERATE` | 判断 | 无；只存在于临时 GoT 工作区 |
| `REVIEW` | 判断 | 无；结论随随后建点动作落库 |
| `AGGREGATE` | 判断 | 无；结论写入研究日志或 Stage Summary |
| `BACKTRACK` | 判断 | 无；焦点变化体现在下一次 `SELECT` 或建点的 parent 选择 |
| `BRANCH` | 落库 | `propose CREATE_CANDIDATE` |
| `REFINE` | 落库 | `propose CREATE_REPAIR` |
| `MERGE` | 落库 | `propose CREATE_MERGE` |
| `HOLD` | 落库 | `propose HOLD_NODE` |
| `CLOSE` | 落库 | `propose CLOSE_NODE` |
| `SELECT` | 落库 | `start-run`；由它分配 ID、Attempt 并创建 Experiment Card |

### 3.2 `propose` action 语义

| Action | 唯一语义 |
|---|---|
| `CREATE_LITERATURE` | 写入一个包含 trigger、search_outcome 与 selected_papers 的完成态 Literature Node。 |
| `CREATE_CANDIDATE` | 从当前 Research Base 创建一个通过普通候选审查的 Research Node。 |
| `CREATE_REPAIR` | 从指定 Experimental Parent 创建一个通过 Paper Repair 规则的修复 Research Node。 |
| `CREATE_MERGE` | 在 Interaction Review Gate 通过后创建一个组合 Research Node 及其 MERGE 证据边。 |
| `SET_FRONTIER` | 整体替换 `active_frontier`；Runtime 校验节点资格、去重及数量不超过三个。 |
| `HOLD_NODE` | 将 Research Node 设为 HOLD，并登记理由与可核验的 release condition。 |
| `REOPEN_NODE` | 仅允许 `HOLD → OPEN`，且请求必须引用 release condition 已满足的证据路径；CLOSED 永不重开，旧方向复活必须新建节点并使用 SOURCE 边。 |
| `CLOSE_NODE` | 将非受保护 Research Node 设为稳定终局 CLOSED，并保留关闭理由与全部历史。 |
| `PROMOTE_RESEARCH_BASE` | 在 Runtime 通过 0.5 pp、seed、精简与分支替换门后授予 Research Base 角色并写入 role event。 |
| `ASSIGN_REFERENCE_BASELINE` | 将具有完整可比结果的节点登记为 Reference Baseline 并写入 role event。 |
| `REGISTER_STAGE_SUMMARY` | 在 Graph 顶层追加阶段检查点，并用必填的非负 `subagent_calls` 更新反思与调用审计计数。 |
| `REGISTER_BASELINE_SEED_EVIDENCE` | 登记 Promotion Confirmation 的额外 seed attempt 与指标证据，不新建 Research Node，也不进入 Frontier。 |
| `FINALIZE_RESEARCH` | 写入 `TARGET_REACHED` 或 `TARGET_NOT_REACHED` 终局；冻结后除 `validate` 外拒绝所有新 mutation。 |

### 3.3 Response Envelope

成功响应固定包含 `accepted: true`、`revision`、`result` 与
`allowed_next_actions`；拒绝响应固定包含 `accepted: false`、
`error_code`、结构化 `violations[{code,path,message}]` 与
`allowed_next_actions`。唯一 Schema 是
[`runtime_response.schema.json`](../assets/schemas/runtime_response.schema.json)。

`allowed_next_actions` 只使用 13 个 §3.2 action，以及 `inspect`、
`validate`。`init`、`start-run` 与 `finish-run` 是 Runtime 命令，不属于该
action 词表；修正方法由 violation 和 §5 错误码表说明，不得在该数组中发明临时建议词。

## 4. Minimal Examples

候选提案：

```json
{
  "request_id": "create-candidate-20260717-001",
  "action": "CREATE_CANDIDATE",
  "parent_node_id": "RN-0012",
  "research_base_id": "RN-0012",
  "comparison_target_id": "RN-0015",
  "title": "Replace the loss reweighting component",
  "hypothesis": "The replacement improves AUC by more than the frozen threshold.",
  "mechanism": "It reduces gradient dominance by frequent examples.",
  "single_main_change": "Replace only the loss reweighting rule.",
  "falsification_condition": "AUC improvement does not exceed the frozen threshold.",
  "classification": {
    "evidence_class": "N",
    "change_scope": "COMPONENT",
    "research_layer": "L3",
    "intervention_locus": "LOSS",
    "change_operator": "REPLACE"
  },
  "candidate_priority": "GOLD",
  "priority_reason": "Single replace operation with direct mechanism evidence.",
  "source_node_ids": ["LN-0004"],
  "source_reason": "The Literature Node provides the transfer mechanism.",
  "evidence_refs": ["literature/mechanisms/paper-a.md"],
  "refs": {
    "paper_mechanism_cards": ["literature/mechanisms/paper-a.md"]
  }
}
```

启动 attempt：

```json
{
  "request_id": "run-20260717-001",
  "node_id": "RN-0016",
  "run_kind": "FULL",
  "seed": 42,
  "preregistration": {
    "hypothesis": "The replacement improves AUC by more than the frozen threshold.",
    "single_main_change": "Replace only the loss reweighting rule.",
    "falsification_condition": "AUC improvement does not exceed the frozen threshold.",
    "classification": {
      "evidence_class": "N",
      "change_scope": "COMPONENT",
      "research_layer": "L3",
      "intervention_locus": "LOSS",
      "change_operator": "REPLACE"
    }
  },
  "command": "python train.py --config configs/E017.json",
  "code_version": "git:abc123",
  "data_version": "dataset-v3",
  "planned_max_seconds": 1800,
  "planned_max_cost": 0,
  "config_ref": "configs/E017.json",
  "artifact_refs": {
    "resolved_config": "artifacts/E017/A01/resolved_config.yaml",
    "metrics_json": "artifacts/E017/A01/metrics.json",
    "artifact_manifest": "artifacts/E017/A01/artifacts_manifest.json",
    "trainer_log": "artifacts/E017/A01/trainer.log"
  },
  "expected_artifacts": ["artifacts/E017/A01/best.pt"]
}
```

收口 attempt：

```json
{
  "request_id": "finish-run-20260717-001",
  "experiment_id": "E017",
  "attempt_id": "A01",
  "run_outcome": "NORMAL_EARLY_STOP",
  "hypothesis_verdict": "SUPPORTED",
  "duration_seconds": 428,
  "cost": 0,
  "hard_constraints_passed": true,
  "stop_reason": "Frozen early-stopping rule fired.",
  "checkpoint_ref": "artifacts/E017/best.pt",
  "interpretation": "The observed direction matches the preregistered mechanism.",
  "decision": "Evaluate Research Base promotion."
}
```

`start-run.preregistration` 的四项事实必须与目标 Research Node 完全一致；
Runtime 将其冻结到 Experiment Card 的 `## Runtime Record`。

正式运行的 `metrics` 不由 LLM 填写。Runtime 从预登记的 `metrics_json`
读取 Benchmark display metrics；如果请求为了交叉检查而同时提交 `metrics`，
其数值必须与 artifact 完全一致，否则整个 `finish-run` 在科研状态写入前被拒绝。

以下三个响应由测试固定时钟后真实生成，并由 Response Schema 校验。

PROVENANCE:
`PATH=/opt/miniconda3/bin:$PATH python3 -m pytest -q scripts/tests/test_autoresearch_runtime.py -k 'runtime_response_schema_validates_real_responses or documented_runtime_examples_match_real_outputs'`

Inspect：

<!-- RUNTIME_RESPONSE_EXAMPLE:inspect:START -->
```json
{
  "accepted": true,
  "allowed_next_actions": [
    "inspect",
    "validate"
  ],
  "result": {
    "active_frontier": [
      {
        "node_id": "RN-0002",
        "priority": "GOLD",
        "title": "Replace the data weighting component"
      }
    ],
    "active_run": null,
    "audit_counters": {
      "stage_reflections": 0,
      "subagent_calls": 0
    },
    "benchmark_id": "benchmark-v1",
    "budget": {
      "consumed": {
        "attempts_started": 0,
        "cost": 0.0,
        "experiments_started": 0,
        "run_seconds": 0.0
      },
      "limits": {
        "cost_unit": "GPU_HOURS",
        "max_cost": 100.0,
        "max_experiments": 8,
        "max_run_seconds": 10000.0
      },
      "new_experiment_limit_reached": false,
      "terminal": false,
      "time_or_cost_exhausted": false
    },
    "command": "inspect",
    "controller_status": "CONTINUE",
    "current_phase": "CANDIDATE_DESIGN",
    "last_trigger": "CANDIDATES_READY",
    "node_counts": {
      "literature": 0,
      "research": 2
    },
    "primary_metric": {
      "branch_replacement_tolerance": 0.001,
      "direction": "MAXIMIZE",
      "fast_run_seconds": 300.0,
      "metric_id": "auc",
      "promotion_threshold": 0.005,
      "simplification_tolerance": 0.005,
      "target": 0.9
    },
    "project_id": "runtime-test",
    "promotion_confirmation_policy": {
      "mode": "SINGLE_RUN_JUSTIFIED",
      "single_run_justification": "A full run exceeds the Benchmark's frozen five-minute single-run qualification threshold.",
      "single_run_threshold": {
        "resource": "DURATION_SECONDS",
        "value": 300.0
      }
    },
    "reference_baseline_ids": [],
    "roles": {
      "anchor_baseline": {
        "node_id": "RN-0001",
        "primary_value": 0.8,
        "title": "Stable baseline"
      },
      "champion": {
        "node_id": "RN-0001",
        "primary_value": 0.8,
        "title": "Stable baseline"
      },
      "research_base": {
        "node_id": "RN-0001",
        "primary_value": 0.8,
        "single_seed_provisional": false,
        "title": "Stable baseline"
      }
    },
    "validation": {
      "valid": true,
      "violations": []
    }
  },
  "revision": 3
}
```
<!-- RUNTIME_RESPONSE_EXAMPLE:inspect:END -->

被拒的 `propose SET_FRONTIER`：

<!-- RUNTIME_RESPONSE_EXAMPLE:rejected_propose:START -->
```json
{
  "accepted": false,
  "allowed_next_actions": [],
  "controller_status": "CONTINUE",
  "error_code": "INVALID_FRONTIER",
  "violations": [
    {
      "code": "INVALID_FRONTIER",
      "message": "Active Frontier requires at most three distinct Research Nodes",
      "path": "$"
    }
  ]
}
```
<!-- RUNTIME_RESPONSE_EXAMPLE:rejected_propose:END -->

成功的 `finish-run`：

<!-- RUNTIME_RESPONSE_EXAMPLE:finish_run:START -->
```json
{
  "accepted": true,
  "allowed_next_actions": [
    "PROMOTE_RESEARCH_BASE",
    "ASSIGN_REFERENCE_BASELINE",
    "inspect"
  ],
  "result": {
    "artifacts_written": [
      "experiments/E001.md",
      "logs/research/volume_001.md",
      "logs/runs/E001/A01.jsonl"
    ],
    "attempt_id": "A01",
    "budget": {
      "consumed": {
        "attempts_started": 1,
        "cost": 1.0,
        "experiments_started": 1,
        "run_seconds": 301.0
      },
      "limits": {
        "cost_unit": "GPU_HOURS",
        "max_cost": 100.0,
        "max_experiments": 8,
        "max_run_seconds": 10000.0
      },
      "new_experiment_limit_reached": false,
      "terminal": false,
      "time_or_cost_exhausted": false
    },
    "budget_overruns": [],
    "command": "finish-run",
    "controller_status": "CONTINUE",
    "experiment_id": "E001",
    "hypothesis_verdict": "SUPPORTED",
    "node_id": "RN-0002",
    "promotion_gate": {
      "allowed_next_actions": [],
      "reason": "Justified single run passed provisionally",
      "status": "ELIGIBLE"
    },
    "role_events": [
      {
        "benchmark_id": "benchmark-v1",
        "created_at": "2026-07-19T00:00:00Z",
        "event_type": "REPLACED",
        "evidence_ref": "experiments/E001.md",
        "node_id": "RN-0002",
        "previous_node_id": "RN-0001",
        "reason": "Reconciled the best valid primary metric after result writeback",
        "role": "CHAMPION"
      }
    ],
    "run_outcome": "NORMAL_EARLY_STOP"
  },
  "revision": 8
}
```
<!-- RUNTIME_RESPONSE_EXAMPLE:finish_run:END -->

## 5. Deterministic Enforcement

Runtime 拒绝以下操作：冻结 Brief/Benchmark 被修改、跨 Benchmark 比较、过期 Research Base、Frontier 超过三个、非单一主要改动、N candidate 超过结构优先级上限、非法状态转换、并发启动两个 attempt、路径逃逸项目根、预算耗尽后继续运行，以及不满足 seed、精简累计或新增分支替换门的底座晋升。

`init` 必须显式提交 Benchmark 冻结的 `promotion_confirmation_policy`。`TWO_SEEDS` 要求首次正式结果外再补两个不同 seed；`ONE_CONFIRM_SEED` 要求再补一个；二者都要求各 seed 方向一致且平均提升超过冻结晋升线。`SINGLE_RUN_JUSTIFIED` 仅在首个完整 attempt 的时长或成本严格超过冻结门槛时可晋升，并把 `single_seed_provisional: true` 写入 Research Base role event；`inspect.roles.research_base` 返回该标记。

`finish-run` 根据 artifact 指标自动判定 Champion、Core Comparison Target，并为
Champion 变化写入 role event；`PROMOTE_RESEARCH_BASE` 与
`ASSIGN_REFERENCE_BASELINE` 仍保持提案制，因为二者需要结构稳定性或长期比较
价值判断。

`start-run` 必须预登记 `planned_max_seconds` 与 `planned_max_cost`，且二者不得超过剩余硬预算。`planned_max_cost` 的单位只来自 Brief 冻结后写入 `budget.limits.cost_unit` 的 `GPU_HOURS` 或 ISO 4217 币种；值大于 0 而没有单位时 Runtime 拒绝启动。Attempt、Card 和 JSONL 都记录同一派生单位。`finish-run` 始终如实记录实际消耗；实际值超过预登记上限时写入 `budget_overruns`，该 attempt 自动失去 Hard-Constraint-valid 资格，不得触发目标、Champion 或 Research Base。

机器状态转换固定为：

- `init → BOOTSTRAP / BOOTSTRAP_FROZEN`；
- `start-run → EXPERIMENT_EXECUTION / EXPERIMENT_STARTED`；
- `finish-run → RESULT_ROUTING / EXPERIMENT_FINISHED`；
- `REGISTER_STAGE_SUMMARY` 在 Stage Reflection 完成并登记后回到 `RESULT_ROUTING / STAGE_SUMMARY_COMPLETED`；
- `FINALIZE_RESEARCH → TERMINATION / RESEARCH_FINALIZED`。

`inspect` 返回 `current_phase`、`last_trigger` 和 `active_run`，它们是崩溃恢复的唯一入口。Runtime 的 `audit_counters.stage_reflections` 与 `audit_counters.subagent_calls` 只记录调用次数；LLM token/API 成本默认不折算进 GPU-hours 预算或带币种的 monetary budget，除非 Brief 显式纳入。

Runtime 对每张 Experiment Card 的 `## Runtime Record` 保存内容 hash；
`finish-run` 与 `validate` 发现该区被改写时拒绝收口或报告违规。
`## Research Notes` 不参与 hash，Runtime 更新 Card 时保留其全部既有内容。

`FULL`、`PROMOTION_CONFIRMATION` 和 `RETRY` 必须在 `start-run` 中预登记四个
typed artifact：resolved config、metrics JSON、artifact manifest 和 trainer log。
成功收口前 Runtime 会检查文件存在、JSON 可解析、Experiment/Attempt 身份一致、
指标完整且 artifact hash 未在收口后变化。[Experiment Playbook §9](experiment_playbook.md#9-technical-smoke-and-retry) 是 `SMOKE` 语义唯一权威；Runtime 仅按其允许省略四类正式 artifact，并阻止科研状态更新。

`finish-run` 只接受：

- `COMPLETED` / `NORMAL_EARLY_STOP` 配合完整 1–3 指标；
- `STOP_LOSS` 配合 `NOT_SUPPORTED`；
- `TECHNICAL_FAILURE` 配合 `NOT_EVALUABLE`；

### 5.1 Stable Error Codes

下表是 Runtime 的完整稳定错误码词表。AI 先读结构化 violation，再按本表修正；
修正 mutation 后使用符合 §2 规范的新 `request_id`。

<!-- STABLE_ERROR_CODES:START -->
| Error code | 触发条件 | AI 应对 |
|---|---|---|
| `ALREADY_INITIALIZED` | 已存在 canonical 项目时再次 `init` | 改用 `inspect` 或 `validate`。 |
| `ARTIFACT_ID_MISMATCH` | artifact 内 Experiment/Attempt 身份与请求不一致 | 重新生成身份正确的 artifact，再用新 ID 收口。 |
| `ARTIFACT_LINK_MISMATCH` | manifest 中的 artifact 链接与预登记路径不一致 | 修正 manifest 与冻结路径后重试。 |
| `ARTIFACT_METRICS_MISMATCH` | 请求内 metrics 与 metrics JSON 不一致 | 删除手填指标或改用 artifact 权威值。 |
| `BENCHMARK_MISMATCH` | 节点、父节点或对照跨 Benchmark | 回到当前 Benchmark 重新建点。 |
| `BRANCH_ADDITION_GATE` | ADD 未满足替换实验或独立功能门 | 先做替换候选或保留为非底座角色。 |
| `BUDGET_AVAILABLE` | 预算尚可用却请求失败终止 | 继续选择实验，不得提前终止。 |
| `BUDGET_EXHAUSTED` | 时间或成本预算耗尽后仍启动运行 | `inspect` 后提交 `FINALIZE_RESEARCH`。 |
| `CANDIDATE_REJECTED` | 五维组合的结构默认是 REJECT/INVALID | 拆分或重新分类候选。 |
| `CANONICAL_INCONSISTENCY` | Graph、State 或 artifact 事实不一致 | 运行 `validate`，恢复一致后再继续。 |
| `EXPERIMENT_BUDGET_EXHAUSTED` | 新 Experiment 数量达到上限 | 完成已有 attempt 或终止研究。 |
| `FORMAL_ARTIFACTS_REQUIRED` | 正式 run 未预登记四类 typed artifact | 补齐四个引用后重新 `start-run`。 |
| `FORMAL_ARTIFACT_MISSING` | 正式收口时预登记 artifact 不存在 | 产出缺失文件后重新 `finish-run`。 |
| `FRONTIER_GATE_FAILED` | Frontier 节点不满足开放、当前底座或未运行条件 | 修正/暂缓节点后重设 Frontier。 |
| `FROZEN_CONTRACT_CHANGED` | Brief 或 Benchmark hash 改变 | 进入人工审查，不得自动覆盖。 |
| `HUMAN_REVIEW_REQUIRED` | 当前状态已冻结为人工审查 | 停止 mutation，仅检查并等待用户处理。 |
| `IDEMPOTENCY_CONFLICT` | 同一 request_id 被不同 payload 复用 | 为修正后的 payload 分配新 ID。 |
| `IMMUTABLE_SEED_EVIDENCE` | 同一节点/seed 的证据被改写 | 保留原证据；新增合法 seed 或人工审查。 |
| `INSUFFICIENT_COST_BUDGET` | 计划成本超过剩余额度 | 选择更低成本计划或终止。 |
| `INSUFFICIENT_TIME_BUDGET` | 计划时长超过剩余时间 | 缩短合规计划或终止。 |
| `INTERACTION_GATE_FAILED` | MERGE 未满足三审、票数或 hard veto 规则 | 保持 HOLD，补足审查证据。 |
| `INVALID_ARTIFACT_REFS` | artifact_refs 键、路径或类型不合法 | 按四类 typed artifact 契约修正。 |
| `INVALID_BENCHMARK` | Benchmark 快照字段或展示指标不合法 | 修正冻结 Benchmark 后重新初始化。 |
| `INVALID_BUDGET` | Budget 字段、数值、至少一项限制或 cost unit 不合法 | 按 Brief 的单位明确预算 envelope。 |
| `INVALID_CANDIDATE` | Candidate 结构违反单假设或 MERGE 边界 | 拆分候选并重新提交。 |
| `INVALID_CLASSIFICATION` | 五维值或组合不在 canonical 矩阵 | 使用矩阵中的合法组合。 |
| `INVALID_FORMAL_ARTIFACT` | JSON、manifest 或 metrics artifact 无法解析 | 重新生成合规 artifact。 |
| `INVALID_FRONTIER` | Frontier 重复、含非 Research Node 或超过三个 | 提交至多三个合格且不同的节点。 |
| `INVALID_INITIAL_MODEL` | 初始模型字段、指标或 seed 证据不合法 | 修正单个初始模型。 |
| `INVALID_INITIAL_MODELS` | 初始化时没有任何模型 | 至少登记一个初始模型。 |
| `INVALID_INITIAL_ROLES` | Anchor、Research Base 或 Champion 非唯一 | 为三种必需角色各指定唯一 holder。 |
| `INVALID_LITERATURE_NODE` | 文献节点结果与 selected_papers 不一致 | 修正搜索结果和全文记录。 |
| `INVALID_LITERATURE_TRIGGER` | 文献检索 trigger 不在规范枚举 | 使用已定义 trigger。 |
| `INVALID_MERGE` | MERGE 分类、来源或共同底座不合法 | 按 Interaction Gate 重建组合候选。 |
| `INVALID_METRICS` | 指标缺失、非数值或不属于 Benchmark | 只提交冻结的 1–3 个展示指标。 |
| `INVALID_NODE_TYPE` | 操作收到错误节点类型 | 改用对应 Research/Literature Node。 |
| `INVALID_PDF_ARTIFACT` | 文献 PDF 缺失或文件头无效 | 下载真实 PDF 后重新登记。 |
| `INVALID_PRIMARY_METRIC` | 主指标与 Benchmark 定义或阈值不合法 | 修正初始化主指标契约。 |
| `INVALID_PRIMARY_PARENT` | Candidate 未使用规定的当前底座/父节点 | 使用当前 Research Base 或合法 Repair parent。 |
| `INVALID_PRIORITY` | Candidate priority 缺失或不合法 | 使用 GOLD、SILVER 或 HOLD。 |
| `INVALID_PROMOTION_CONFIRMATION` | seed 确认 attempt 不满足身份或时序 | 使用同一 RN/Experiment 的新 seed。 |
| `INVALID_REFS` | 节点证据引用与 action 类型不匹配 | 修正 refs 并保留真实文件。 |
| `INVALID_REPLACEMENT` | ADD 的替换对照不是有效 REPLACE 结果 | 创建并完成合法替换实验。 |
| `INVALID_REQUEST` | 字段类型、必填值或数值范围不合法 | 按 violation.path 修正请求。 |
| `INVALID_REQUEST_ID` | request_id 字符或长度非法 | 按 §2 命名规范生成新 ID。 |
| `INVALID_REQUEST_JSON` | CLI 请求不是可解析 JSON object | 修正 JSON 文件或 stdin。 |
| `INVALID_RETRY` | 非技术失败节点发起 RETRY | 创建科研候选或仅对技术失败重试。 |
| `INVALID_ROLE_ASSIGNMENT` | 角色授予对象或证据不合格 | 选择完成且可比的节点。 |
| `INVALID_SIMPLIFICATION_CAMPAIGN` | 精简 campaign 字段或删除集合不合法 | 一次登记完整删除集合。 |
| `INVALID_STAGE_ROUTE` | Stage Summary 路线不在固定枚举 | 使用 DEEPEN/BROADEN/REPAIR/PIVOT/CONCLUDE。 |
| `INVALID_TRANSITION` | 节点、run 或角色状态转换非法 | `inspect` 当前状态后选择合法 action。 |
| `INVALID_VERDICT` | Run Outcome 与假设判定不匹配 | 按 Playbook 组合修正。 |
| `MISSING_EVIDENCE` | REOPEN、角色或科研操作缺少证据引用 | 先生成并引用可核验 artifact。 |
| `MISSING_REQUEST` | mutation CLI 未提供 `--request` | 传入 JSON 文件或 stdin。 |
| `NODE_NOT_SELECTED` | FULL/SMOKE 节点不在 Active Frontier | 先 `SET_FRONTIER`。 |
| `NO_ACTIVE_RUN` | 没有 active attempt 却调用 `finish-run` | `inspect` 后启动或恢复正确 run。 |
| `PAPER_REPAIR_LIMIT` | Paper Repair 超过三个核心修复假设 | 关闭该路线或回到新文献方向。 |
| `PREREGISTRATION_MISMATCH` | start-run 四项冻结事实与 Research Node 不同 | 恢复原预登记事实。 |
| `PRIORITY_UPGRADE_FORBIDDEN` | 请求优先级高于结构上限 | 使用矩阵给出的上限。 |
| `PROMOTION_GATE_FAILED` | 指标、seed、结构或专项晋升门未通过 | 按 gate 结果补证或仅保留比较角色。 |
| `PROPOSAL_REJECTED` | mutation 后全项目不变量校验失败 | `inspect` 并修正提案，不得手改 canonical 文件。 |
| `PROTECTED_ROLE_NODE` | 尝试关闭 Anchor/Base/Champion | 保留角色节点，改走其他分支。 |
| `REPLACEMENT_EVIDENCE_PENDING` | ADD 替换对照仍缺 seed 或底座证据 | 完成指定确认后再晋升。 |
| `REPLACEMENT_REQUIRED` | 替换方案有效且接近 ADD 方案 | 强制优先晋升替换方案。 |
| `RESEARCH_TERMINATED` | 两种终止态后继续 mutation | 只读检查并结束。 |
| `RUN_ALREADY_ACTIVE` | 已有 active attempt 时再次 start-run | 完成当前 `finish-run`。 |
| `RUN_ID_MISMATCH` | finish-run 的 Experiment/Attempt 与 active run 不同 | 使用 `inspect` 返回的 active ID。 |
| `RUNTIME_ERROR` | CLI 文件系统或项目加载失败 | 修复路径/文件后运行 `validate`。 |
| `SIMPLIFICATION_ANCHOR_MISMATCH` | 精简 campaign 未对当前 anchor 比较 | 合并全部删除并使用冻结 anchor。 |
| `SIMPLIFICATION_CAMPAIGN_INCOMPLETE` | 分支删除未作为一次完整 campaign | 完成组合删除实验后再判断。 |
| `STALE_RESEARCH_BASE` | Candidate 相对旧 Research Base 创建 | 基于当前底座重建候选。 |
| `UNKNOWN_BENCHMARK` | 请求引用未登记 Benchmark | 使用 active Benchmark。 |
| `UNKNOWN_COMMAND` | CLI command 不在六接口 | 使用 §3 的六个命令。 |
| `UNKNOWN_NODE` | 请求引用不存在的 LN/RN | 从 `inspect`/Graph 取得真实 ID。 |
| `VALIDATION_FAILED` | `validate` 发现一个或多个一致性违规 | 按 violations 修复后重复 `validate`。 |
<!-- STABLE_ERROR_CODES:END -->

## 6. Storage and Recovery

- Graph 与 Runtime State 使用同一 `revision`，跨进程调用由项目锁串行化。
- 专业 artifact 和 Runtime State 先写，派生 HTML 随后写，canonical Graph 最后原子替换。
- `validate` 检查 revision、ID、DAG、边、角色、Frontier、Experiment/Attempt、冻结哈希与 JSON Schema；一致后从 Graph 重建 HTML。
- `.autoresearch/runtime_state.json` 只保存机器 Phase/trigger、预算、审计计数器、幂等记录和 attempt 执行事实，不建立第二套科研图。

Schema 位于 `assets/schemas/`。字段或状态变化必须先升级 Schema 与 Runtime，再升级本文和 Graph Protocol；LLM 不得在请求中发明枚举。
