---
doc_id: dataset-profile-template
doc_type: template
title: Dataset Profile Template
status: stable
summary: 生成简短的数据侦察记录，区分 Observed Facts、Inferred Findings 和 Risks/Pending。
read_when:
  - Research Bootstrap 分析数据集时
depends_on:
  - research-contract
  - governance-and-autonomy
activation:
  level: ON_DEMAND
---

# Dataset Profile Template

## Responsibility

Before asking the user alignment questions, record only the dataset information that can materially affect the Research Brief, Benchmark, or experiment design. This is not a complete data dictionary or a long-term analysis report. Adapt the amount of detail to the dataset.

## Observed Facts

Record the important facts directly verified from the dataset, project code, or existing artifacts. Include evidence paths where they help another agent recheck the fact.

## Inferred Findings

Record only necessary interpretations, such as the likely task, target, field meaning, or split semantics. For each material inference, state its basis and confidence. Do not present an inference as an observed fact.

## Risks / Pending

Record unresolved issues that could change the Research Brief, Benchmark, or experiment design, such as unclear labels, missing splits, leakage, or ambiguous field semantics. Omit sections and details that are not relevant to the current dataset.
