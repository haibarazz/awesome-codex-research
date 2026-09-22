---
doc_id: research-brief-template
doc_type: template
title: Research Brief Template
status: stable
summary: 生成用户最终确认的研究任务书，冻结目标、成功条件、预算、自主权与最终授权。
read_when:
  - Research Bootstrap 创建或版本化 Research Brief 时
depends_on:
  - research-contract
  - governance-and-autonomy
activation:
  level: ON_DEMAND
---

# Research Brief Template

## Responsibility

Create the concise, final launch contract between the user and the autonomous research agent. It must make the research objective, completion condition, resource boundary, and authorization boundary unambiguous before experiments begin.

Adapt the wording and level of detail to the project. Do not expand this document into a dataset report, experiment roadmap, literature plan, or running log.

**Dataset Profile:** `<path>`

**Benchmark:** `<path or PENDING>`

## 1. Research Goal

State the domain, task, target scenario, and final objective at the level needed to guide autonomous research. Do not preselect papers, candidate methods, or novelty claims.

## 2. Success Criteria

Record the current Baseline status, exactly one Primary Metric, a machine-decidable Performance Target, and any Hard Constraints required for `TARGET_REACHED`.

If the completion condition is still ambiguous, keep the Brief in `DRAFT`.

## 3. Budget and Autonomy

Record at least one hard research-budget limit and the actions the AI is allowed or forbidden to perform. After the Brief is frozen, the AI must operate independently inside these boundaries without requesting per-experiment approval.

Use this unit-explicit envelope; at least one of the four limit values must be non-null and positive:

```yaml
budget_envelope:
  wall_clock_hours: <number or null>
  gpu_hours: <number or null>
  monetary_cost:
    amount: <number or null>
    currency: <ISO 4217 code or null>
  formal_experiment_count: <positive integer or null>
  llm_cost_counted: false
```

`monetary_cost.amount` and `currency` must either both be set or both be null. Literature search, PDF download, reflection, and review token/API costs are excluded by default; set `llm_cost_counted: true` only when the user explicitly places them inside the monetary envelope. Wall-clock time always follows natural elapsed time.

In the allowed-actions record, keep `literature_paper_count_preference: 3-4` unless the user states another preference during Bootstrap. Once the Brief is frozen, literature quantity and search parameters are autonomous and require no further confirmation.

## 4. Final Confirmation

Record the Brief state as `DRAFT`, `FROZEN`, or `SUPERSEDED`.

`FROZEN` requires one explicit final confirmation from the user. Once frozen, the research continues until `TARGET_REACHED` or `TARGET_NOT_REACHED`, except for the narrowly defined temporary `HUMAN_REVIEW_REQUIRED` gates in the Research Contract.
