---
doc_id: codebase-profile-template
doc_type: template
title: Codebase Profile Template
status: stable
summary: 记录现有或自动引入代码库的根目录、来源、稳定入口、项目契约、AutoResearch 映射和技术预检状态。
read_when:
  - 接管已有代码库时
  - 自动引入 ReproFlow 后核验或更新代码接口时
depends_on:
  - research-contract
  - reproflow-code-contract
activation:
  level: ON_DEMAND
---

# Codebase Profile Template

在项目根目录生成 `CODEBASE_PROFILE.md`。只记录 AutoResearch 运行和恢复所需的代码事实，不复制项目 README 或完整架构文档。

## Source

- Framework / project:
- Code root:
- Status: `EXISTING_CODE | REPROFLOW_PRESENT`
- Bootstrap mode: `NOT_APPLICABLE | DIRECT_CLONE | TEMPLATE_IMPORT | ADOPT_EXISTING`
- Repository:
- Requested ref:
- Resolved commit:

## Stable Entrypoints

- Project contract:
- Environment / dependency entry:
- Dataset onboarding or validation:
- Training:
- Evaluation:
- Baseline:
- Smoke test:

## Contract Mapping

说明现有代码分别如何承载：

- data schema 与 frozen split；
- model、component、branch 与 loss；
- trainer / optimizer；
- evaluator 与 1–3 个展示指标；
- config snapshot；
- `tracking.experiment_id` / `tracking.run_id` 与 Runtime Experiment ID / Attempt ID；
- metrics、manifest、checkpoint、log 与代码版本。

正式运行还必须说明 resolved config、metrics JSON、artifact manifest 与 trainer
log 如何映射到 Runtime `artifact_refs`；指标以 Runtime 读取到的 artifact 为准。

如果现有代码缺少某个接口，记录最小 adapter 方案；不得借接入过程重写项目架构。

## Frozen Surfaces

列出 Benchmark 冻结后 Candidate 不得修改的文件或配置，包括数据划分、指标、evaluator、seed 协议和训练预算。

## Verification

- Codebase fingerprint:
- Dependency check:
- Dataset doctor / equivalent:
- Technical Smoke:
- Remaining engineering risks:
