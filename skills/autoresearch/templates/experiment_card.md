---
doc_id: experiment-card-template
doc_type: template
title: Experiment Card Template
status: stable
summary: 定义单次实验从 PLANNED、RUNNING 到 FINISHED 的事实记录，最终保持假设、改动、结果、决策四部分。
read_when:
  - 创建或更新正式实验卡时
depends_on:
  - research-contract
  - experiment-playbook
  - research-records-protocol
activation:
  level: ON_DEMAND
---

# Experiment Card Template

一个 Research Node 始终复用同一个 Experiment Card，技术重试与晋升确认只增加 Attempt。Card 只有两个顶级区：Runtime 独占 `## Runtime Record`，LLM 只在 `## Research Notes` 末尾追加。

| 字段 | 唯一 owner | 写入方式 |
|---|---|---|
| experiment_id、research_node_id、benchmark_id、research_base_id、comparison_target_id、Card status、created_at | Runtime | `start-run` |
| hypothesis、single_main_change、falsification_condition、classification | Runtime | `start-run` 从请求冻结并与 Research Node 核对 |
| mechanism | Runtime | `start-run` 从 Research Node 冻结 |
| attempt_id、kind、seed、lifecycle status、started_at、finished_at | Runtime | `start-run` / `finish-run` |
| command、config_ref、code_version、data_version、artifact_refs、checkpoint_ref | Runtime | `start-run` / `finish-run` |
| planned/actual budget、Brief 派生的 cost_unit、run_outcome、hypothesis_verdict、metrics、artifact_sha256 | Runtime | `start-run` / `finish-run` 从请求或 artifact 写入 |
| 预登记阐述、工程修复注记、诊断线索、结果解释、下一步决策 | LLM | 仅在 `## Research Notes` 末尾追加 |

```markdown
# Experiment E017

## Runtime Record

### Identity

- experiment_id: E017
- research_node_id: RN-0016
- benchmark_id: benchmark-v1
- research_base_id: RN-0004
- comparison_target_id: RN-0009
- status: PLANNED | RUNNING | FINISHED
- created_at: <ISO-8601>

### Frozen Preregistration

- hypothesis: <frozen hypothesis>
- single_main_change: <frozen change>
- falsification_condition: <frozen observable failure condition>
- classification: <frozen five-dimensional classification>
- mechanism: <frozen mechanism and mediator prediction>

### Attempts

| Attempt | Kind | Seed | Status | Started | Finished | Outcome | Metrics | Planned / actual budget with unit |
|---|---|---:|---|---|---|---|---|---|

### Attempt Runtime Details

- A01: <command, config/code/data versions, artifact refs and hashes>

### Result

- Run outcome: `<canonical value>`
- Hypothesis verdict: `<canonical value>`
- Metrics: <1–3 Benchmark display metrics>

## Research Notes

<!-- Append-only: add dated rationale, engineering notes, interpretation, and decisions below. -->
```

Runtime 保存并校验 `## Runtime Record` 内容 hash；LLM 不得编辑该区。`## Research Notes` 不参与 Runtime hash，既有行不得删除或改写。step/batch、错误堆栈、资源心跳和 trainer 输出不复制进正文；通过 `logs/runs/EXXX/AYY.jsonl` 与外部 artifact 引用。
