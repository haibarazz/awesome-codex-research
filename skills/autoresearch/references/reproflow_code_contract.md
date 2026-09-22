---
doc_id: reproflow-code-contract
doc_type: reference
title: ReproFlow Codebase Bootstrap and Bridge Contract
status: stable
summary: 定义 AutoResearch 如何检查现有代码、仅在无代码时安全引入 ReproFlow，并把实验节点映射到可复现运行。
read_when:
  - 首次进入一个 AutoResearch 工作目录并检查代码时
  - 无可运行代码，需要引入默认 ReproFlow 底座时
  - 在 ReproFlow 中实现 Candidate 或启动正式实验时
depends_on:
  - research-contract
  - governance-and-autonomy
  - experiment-playbook
  - autoresearch-runtime-api
activation:
  level: PHASE
  phases:
    - BOOTSTRAP
    - EXPERIMENT_EXECUTION
    - RESULT_ROUTING
---

# ReproFlow Codebase Bootstrap and Bridge Contract

## 1. Boundary

AutoResearch 是研究控制层；ReproFlow 是缺少现有代码时的默认实验执行底座。代码初始化发生在 Graph Runtime 初始化之前，不创建 Research Node、Experiment 或科研结论。

每个新工作目录先运行：

```bash
python3 <skill>/scripts/bootstrap_codebase.py \
  --project-root <project> inspect
```

只能根据返回的 `codebase_status` 路由：

- `REPROFLOW_PRESENT`：接管现有 ReproFlow；
- `EXISTING_CODE`：保留现有架构，禁止克隆或覆盖，使用 Codebase Profile 模板建立接口映射；
- `NO_CODE`：自动执行 ReproFlow bootstrap，不再请求用户确认。

目录含有数据、论文、Skill、文档、日志或研究 artifact，不等于存在可运行代码。

## 2. Safe Bootstrap

`NO_CODE` 时运行：

```bash
python3 <skill>/scripts/bootstrap_codebase.py \
  --project-root <project> bootstrap
```

默认来源为 `https://github.com/haibarazz/ReproFlow.git` 的 `main`，但每次必须记录实际解析到的 commit SHA。

Bootstrap 必须：

1. 不覆盖任何已有代码或控制文件；
2. 保留已有数据文件、README 与许可证；
3. 在空目录中直接 clone；在已有 Git 仓库或仅含非代码文件的目录中导入工作树而不制造嵌套 `.git`；
4. 根目录存在不可安全合并的非代码冲突时，自动尝试 `codebase/`；
5. 生成 `.autoresearch/codebase_bootstrap.json` 与 `CODEBASE_PROFILE.md`；
6. 以 ReproFlow 指纹和 `validate` 结果确认落盘成功。

Bootstrap 只建立本地代码底座；不得向 ReproFlow 上游 push、创建 PR 或写入远端，除非用户另行明确授权。

Clone、网络或权限故障属于外部基础设施问题。只允许按 Governance 完成一次 Recovery Cycle，不得用手工复制绕过冲突或来源记录。

## 3. ReproFlow Authority

ReproFlow 存在后，先读取 `<code_root>/AGENTS.md`。只有修改对应扩展点时，才进一步读取：

- `<code_root>/docs/architecture.md`
- `<code_root>/docs/ai_reproduction_guide.md`
- 当前任务匹配的 `<code_root>/.claude/skills/*/SKILL.md`

不得把这些项目内规则复制进 AutoResearch Contract。ReproFlow 负责数据 adapter、模型、trainer、metric、配置和运行入口的代码组织；本文件只定义两套系统之间的桥。

## 4. Code Change Contract

在 ReproFlow 中实现 Candidate 时：

- 禁止创建绕过 `main.py`、配置组和统一 evaluator 的独立训练脚本；
- 数据 schema 放在 `configs/data/`，模型配置放在 `configs/model/`，指标放在 `configs/metrics/`；
- 只有 batch 形态改变时新增 data adapter，只有 loss、objective 或训练循环契约改变时新增 trainer；
- 论文专用实现先放在 `paper_methods/<method>/`，通用后再提升到共享模块；
- 不得在模型代码中硬编码数据列、label、seed、指标、路径或 Benchmark 预算；
- 一个 Candidate 只实现一个预登记的主要改动，禁止借代码整理偷带额外科研改动。

Benchmark 冻结后，其数据划分、Selection Split、指标、evaluator、seed 协议和训练预算均不可由 Candidate 修改。

## 5. Experiment Bridge

每个正式 Attempt 必须把 Runtime 身份传入 ReproFlow：

```text
tracking.experiment_id = <Experiment ID>
tracking.run_id        = <Attempt ID>
```

正式运行必须启用：

```text
tracking.enabled=true
artifacts.save_metrics_json=true
artifacts.save_manifest=true
```

并在 `start-run.artifact_refs` 中预登记：

- resolved config snapshot；
- machine-readable metrics JSON；
- artifact manifest；
- history 或 trainer log；

另外必须记录：

- best checkpoint（如任务产生）；
- 当前代码 commit；若工作树有改动，再附完整 diff；
- 数据版本与 Benchmark ID。

`start-run` 必须发生在训练命令之前。成功的正式 attempt 只有在四个 typed
artifact 均存在、身份一致且可解析后才允许 `finish-run`；Runtime 从
`metrics_json.best_entry` 读取冻结指标并记录 hash。LLM 不得根据终端滚动输出
填写或改写正式指标。

上述身份、命令、版本、预算、artifact 引用、正式指标及 hash 只写入
Experiment Card 的 `## Runtime Record`；Runtime 校验该区 hash。运行中的工程
修复、诊断与科研解释只允许追加到 `## Research Notes`，Runtime 更新 Card 时
必须原样保留该区。

## 6. Verification Gate

引入或接管 ReproFlow 后依次执行：

1. `bootstrap_codebase.py ... validate`；
2. 为用户数据建立或核验 `configs/data/<dataset>.yaml`；
3. 运行 `python scripts/doctor.py ...`；
4. 运行一次不产生科研结论的最小 one-epoch Technical Smoke；
5. 更新 `CODEBASE_PROFILE.md` 的 Verification；
6. 只有上述步骤通过后，才建立 Anchor Baseline 和启动正式实验。

Doctor 或 Smoke 暴露的普通配置、依赖或代码问题由 AI 在授权内修复。只有命中 Research Contract 已批准的三类暂停原因，才可进入 `HUMAN_REVIEW_REQUIRED`。
