---
doc_id: research-contract
doc_type: contract
title: AutoResearch Research Contract
status: stable
summary: AutoResearch 的最高级研究原则、文档权威关系和渐进式模块路由。
read_when: [每次启动或恢复 AutoResearch 时首先读取, 不确定某条规则归属或模块读取顺序时]
depends_on: []
activation: {level: ALWAYS, phases: []}
---

# AutoResearch Research Contract

## 1. Purpose

本文件是 AutoResearch 的轻量总契约和文档注册表，只保存跨模块最高级原则、权威关系和读取路由。它覆盖调研选题、论文方法复现、候选生成、实验执行、失败修复、研究反思和路线切换，不覆盖论文正文写作。

## 2. Authority and Reading Order

规则优先级为：已版本化的 Research Brief、Benchmark 与授权边界 → 本 Contract 的跨模块不变量 → 对应领域的唯一权威 Reference → Prompt → Template → Workflow HTML。

同一规则只能由一个 Reference 完整定义。其他文件只提供短摘要和链接，不复制整段规范。发现冲突时不得静默选择或合并，必须定位权威模块；若冲突会改变冻结契约，则按 Governance 处理。

## 3. Core Invariants

1. 首次运行先检查可运行代码；只有确认无代码时才安全引入 ReproFlow，随后生成 Codebase Profile、分析数据集、完成 3–5 个高价值问题并冻结 Research Brief。
2. Brief 冻结后，AI 在授权和预算内无人值守运行，常规实验决策不再请求用户批准。
3. 研究级终止只有 `TARGET_REACHED` 与 `TARGET_NOT_REACHED`；`HUMAN_REVIEW_REQUIRED` 只是受限暂停。
4. Benchmark 的数据划分、指标、训练预算、评估脚本和硬约束不得随 Candidate 改变。
5. Anchor Baseline、Research Base、Champion、Reference Baseline 与 Experimental Parent 是不同角色。
6. 每个正式实验只验证一个主要假设，并遵循“假设 → 预登记 → 修改 → 运行 → 判断 → 保留/回滚/修复”。
7. 论文方法在目标项目自己的数据和 Benchmark 上复现；R/A 不是创新，N 只能称为候选创新。
8. 替换、删除和可归因组件改动优先于无约束新增分支；Research Base 晋升必须满足专门规则。
9. Technical Failure 不得解释为方法无效；失败实验和原始运行事实必须保留。
10. `EXPERIMENT_GRAPH.json` 是实验图唯一科研事实源；LLM 只能通过 Runtime 提案修改，HTML 只能从 JSON 重建。
11. Stage Summary 是图级检查点和阶段决议，不是实验节点。
12. 所有研究持续到目标达到或预算耗尽；无候选、无涨点和论文路线失败必须在剩余预算内自动恢复或转向。
13. 数据、论文、Skill、文档或日志不等于可运行代码；已有代码不得被 ReproFlow clone 覆盖或强制迁移。

## 4. Authoritative Reference Registry

| Module | 何时读取 | 核心规则 | 主要写回 |
|---|---|---|---|
| [Governance and Autonomy](governance_and_autonomy.md) | 启动、预算、暂停、终止 | Brief 冻结；无人值守授权；两种终止状态；三类人工暂停 | Dataset Profile、Research Brief、预算与终止状态 |
| [ReproFlow Codebase Contract](reproflow_code_contract.md) | 首次检查代码、无代码 bootstrap、实现或运行 ReproFlow Candidate | 仅在无代码时引入；不覆盖；代码组织；Experiment-to-run bridge；doctor/smoke gate | Codebase Profile、bootstrap provenance、结构化运行 artifact |
| [Benchmark and Model Roles](benchmark_and_model_roles.md) | 建立对照、比较结果、晋升底座 | Benchmark 固定；模型角色分离；0.5 pp 晋升；seed、精简与新增分支门 | Benchmark、角色事件、晋升证据 |
| [Paper Reproduction and Innovation](paper_reproduction_and_innovation.md) | 文献检索、论文复现、Paper Repair | 真实 PDF；目标数据复现；R/A/N；组件迁移；最多三个修复假设 | Literature Survey、Mechanism Card、复现候选 |
| [Candidate Priority Rules](candidate_priority_rules.md) | 审查 N candidate | 五维分类；结构默认等级；Gold/Silver/Hold/Reject/Invalid；伪创新硬门 | 候选优先级与理由 |
| [Experiment Playbook](experiment_playbook.md) | 启动、监控、停止和收口训练 | 预登记；Selection Split；长短 epoch；Run Outcome；技术重试 | Experiment Card、Run Event Log、运行 artifact |
| [Research Records Protocol](research_records_protocol.md) | 写日志、读进度、阶段总结 | Card 生命周期；双日志；Master Roadmap；分卷；Stage Summary | 实验日志、Roadmap、Stage Summary |
| [Research Graph Protocol](research_graph_protocol.md) | 图决策点和下一实验选择 | 节点/边科研语义；Active Frontier；Graph Operations；结果路由与选择器 | Experiment Graph JSON/HTML |
| [Interaction Review Gate](interaction_review_gate.md) | 跨分支 MERGE 候选设计或阶段反思 | 机制正交性；真实全文证据；独立审查与投票；最小可归因交互实验 | Interaction Review Pack、Gate decision |
| [Graph Structure Reference](graph_structure_reference.md) | Runtime violations 指向图结构问题时按需读取 | Schema 的人读字段、ID、null、refs、metric_summary 与边对象说明 | 不直接写回 |
| [Runtime API](runtime_api.md) | 初始化、图变更、实验启动/收口、全项目校验 | 六个接口；Proposal→Validate→Apply；确定性状态、数值门与原子写入 | Graph、Card、JSONL、Runtime State、HTML |

## 5. Prompt Registry

| Prompt | 何时读取 | 核心流程 |
|---|---|---|
| [Research Bootstrap](../prompts/research_bootstrap.md) | 首次启动或重建 Brief | 数据侦察 → 3–5 个问题 → 冻结 Research Brief |
| [Research Graph Controller](../prompts/research_graph_controller.md) | 五类科研决策点 | 状态校验 → 图操作 → 结果路由 → 唯一下一行动 |
| [Paper Mechanism Review](../prompts/paper_mechanism_review.md) | 论文全文核验后 | 恢复机制、判断迁移层级、生成可执行复现 |
| [Candidate Adversarial Review](../prompts/candidate_adversarial_review.md) | 普通候选需要固定自审格式时 | 主 AI 一次 REVIEW，不生成独立 Review 文档 |
| [Stage Reflection](../prompts/stage_reflection.md) | Stage Summary 触发时 | 冻结证据 → 第一性原理 → 对抗审查 → 路线裁决 |

## 6. Template Registry

| Template | 生成文档 | 核心内容 |
|---|---|---|
| [Dataset Profile](../templates/dataset_profile.md) | `DATASET_PROFILE.md` | Observed、Inferred、Risks/Pending |
| [Codebase Profile](../templates/codebase_profile.md) | `CODEBASE_PROFILE.md` | 代码根、来源、入口、契约映射与技术预检 |
| [Research Brief](../templates/research_brief.md) | `RESEARCH_BRIEF.md` | Goal、Success、Budget/Autonomy、Confirmation |
| [Benchmark Contract](../templates/benchmark_contract.md) | `BENCHMARK.md` | 数据划分、指标、训练评估、停止、版本 |
| [Master Roadmap](../templates/master_roadmap.md) | `EXPERIMENT_LOG.md` | 研究目标、阶段 Roadmap、当前位置 |
| [Experiment Card](../templates/experiment_card.md) | 单次实验卡 | 假设、改动、结果、决策 |
| [Research Experiment Log](../templates/research_experiment_log.md) | `logs/research/volume_NNN.md` | 精简科研判断 |
| [Run Event Log Schema](../templates/run_event_log_schema.md) | `logs/runs/EXXX/AYY.jsonl` | 机器事件与恢复证据 |
| [Literature Survey](../templates/literature_survey.md) | 文献调研记录 | 查询、筛选、全文核验、方向总结 |
| [Paper Mechanism Card](../templates/paper_mechanism_card.md) | 单篇机制卡 | 全文证据、机制、迁移判断 |

## 7. Paper-Reproduction Supporting References

| Reference | 何时读取 | 核心内容 |
|---|---|---|
| [Experiment Ranking Rubric](paper_reproduction/experiment_ranking_rubric.md) | 论文候选需要更细审查时 | 证据、机制、可证伪性和成本的对抗审查 |
| [Paper Transfer Template](paper_reproduction/paper_transfer_template.md) | 需要完整论文迁移交付时 | 原机制、目标位置、R/A/N 映射与实验设计 |
| [Prompt Patterns](paper_reproduction/prompt_patterns.md) | 构造论文创新提示时 | 忠实复现、组件替换和伪创新审查模式 |

## 8. Progressive Disclosure

第一方 Markdown 的 YAML 使用三级激活：

| Level | 读取规则 |
|---|---|
| `ALWAYS` | Skill 触发或恢复时始终读取；当前只允许本 Contract |
| `PHASE` | 仅当当前 Phase 位于 `activation.phases`，且 `read_when` 与当前动作匹配时读取 |
| `ON_DEMAND` | 只有生成、更新或核验对应 artifact，或命中 `read_when` 时读取 |

标准 Phase 为 `BOOTSTRAP`、`LITERATURE_RESEARCH`、`CANDIDATE_DESIGN`、`EXPERIMENT_EXECUTION`、`RESULT_ROUTING`、`STAGE_REFLECTION`、`TERMINATION` 与 `HUMAN_REVIEW`。Controller 每次只激活一个当前 Phase；`activation.phases` 只表示文件在该阶段可用，不表示必须读取。不得为了“完整了解项目”加载全部 References、Prompts、Templates、日志或 trainer artifact。

## 9. Document Conventions

第一方 Markdown 的 YAML 描述 `doc_id`、`doc_type`、`title`、`status`、`summary`、`read_when`、`depends_on` 和 `activation`；`activation` 只含 `level` 与 `phases`。`SKILL.md` 只保留标准的 `name` 与 `description`。

机器字段和枚举使用英文；用户文档采用“英文枚举（中文解释）”，Prompts 默认中文。中英文 Workflow 必须保持结构、链接、规则含义和成熟度同步；它们只负责导航，不是权威规则源。

第一方文档正文语言保持各文件现状，不强制统一；本规则只约束后续新改动，同一文件内标题语言必须与正文语言一致，不要求回溯重写已有文件。
