---
doc_id: stage-reflection
doc_type: prompt
title: Stage Reflection Prompt
status: stable
summary: 对冻结阶段证据执行第一性原理分析、对抗审查、受约束头脑风暴、交互假设审查与路线裁决。
read_when:
  - Stage Summary 触发时
  - 研究方向关闭、转向或 Research Base 晋升后
depends_on:
  - research-contract
  - research-records-protocol
  - research-graph-protocol
  - interaction-review-gate
activation:
  level: PHASE
  phases:
    - STAGE_REFLECTION
---

# Stage Reflection Prompt

本文件是 AutoResearch 生成阶段总结时必须读取的执行规范。它指导 AI 完成一次阶段科研反思、对抗审查、头脑风暴和路线裁决，并将最终结果写入 `logs/summaries/volume_NNN_summary.md`。
阶段总结不是实验日志的缩写版，也不是排行榜说明。实验事实已经由 Experiment Card、Research Experiment Log 和 Run Event Log 保存；本流程只回答这些事实意味着什么、当前解释可能错在哪里，以及下一阶段最值得消除的关键不确定性是什么。

## 目录
1. 核心任务与不可违反的边界
2. 输入与冻结证据包
3. 证据纪律
4. 完整执行流程
5. 独立角色提示词
6. 对抗辩论与综合裁决提示词
7. Stage Summary 固定六部分输出契约
8. 下一阶段候选生成契约
9. 路线决策规则
10. 完成前硬门
11. 禁止模式
12. 最小调用提示词

## 1. 核心任务与不可违反的边界
你正在主持一次阶段科研反思，而不是整理会议纪要。
你的任务是：
1. 从冻结证据中恢复本阶段真正成立和不成立的认识；
2. 从第一性原理解释结果为何发生，而不是用模型名称或涨跌分复述现象；
3. 主动建立当前解释的最强反方论证和竞争机制；
4. 将成功、失败、意外结果和预测错误转化为可迁移认识；
5. 围绕尚未解决的机制生成少量可证伪、可区分的下一阶段假设；
6. 对跨实验分支的组合设想执行正交性、全文文献证据和独立多 agent 审查；
7. 在 `DEEPEN / BROADEN / REPAIR / PIVOT / CONCLUDE` 中作出明确路线裁决。
必须遵守以下边界：
- 不得改写、覆盖或“清理”已经封存的实验日志。
- 不得按实验编号逐条复述本阶段发生了什么。
- 不得把指标相关性直接写成因果机制。
- 不得把 Technical Failure 解释为方法效果差。
- 不得把 Killed by Stop-loss 当作完整可比结果或底座晋升证据。
- 不得隐藏失败实验、相反证据、预测错误或审查分歧。
- 不得为了显得有反思而编造问题；没有致命缺陷时应明确写“当前未发现致命缺陷”。
- 不得为了显得有创新而生成随机模块、分支或 loss 堆叠。
- 不得因为 A、B 分别失败就断言 A+B 必然失败，也不得因此枚举所有失败分支的排列组合。
- 不得让一个平均分、多数票或当前最佳指标抵消证据有效性上的致命问题。
- 不得默认“继续改模型”总是优于保持现状、补证据或结束方向；`do nothing / keep current Research Base` 必须是合法选项。

## 2. 输入与冻结证据包
开始反思前，先建立只读的 `Stage Evidence Pack`。至少读取：
- 阶段开始与结束时的 Benchmark 契约、版本及变更记录；
- 阶段开始与结束时的 Anchor Baseline、Research Base、Champion、Reference Baseline 和 Core Comparison Target；
- 本卷封存的 Research Experiment Log；
- 本阶段所有 FINISHED Experiment Card；
- 必要的 Run Event Log、trainer artifact 和评估产物链接；
- 每个实验的预登记假设、支持预测、证伪条件和实际结局；
- 本阶段的 Research Base 晋升、Champion 变化和 Benchmark 变更记录；
- Paper Repair Cycle 的 Experimental Parent、修复假设及双重比较结果；
- 与当前解释有关的论文机制卡、消融结论和文献检索结果；
- 当前 `EXPERIMENT_GRAPH.html` 中的 Primary Parent、Source / Merge Edge、开放分支、失败边界和 Active Frontier；
- 尚未解决的异常、冲突结果、失败 slice 和技术不确定性。
推荐调用变量：
```text
SKILL_ROOT                = <安装后的 AutoResearch skill 根目录；开发期可等于 PROJECT_ROOT>
PROJECT_ROOT              = <项目根目录>
STAGE_REFLECTION_PROMPT   = <本提示词的绝对路径>
RESEARCH_CONTRACT_SOURCE  = <Research Contract、Research Brief 与当前 Benchmark 的路径>
VOLUME_ID                 = <volume_NNN>
BENCHMARK_SOURCE          = <Benchmark 文件或章节>
MASTER_EXPERIMENT_LOG     = <EXPERIMENT_LOG.md>
SEALED_RESEARCH_LOG       = <logs/research/volume_NNN.md>
RUN_EVENT_ROOT            = <logs/runs/>
LITERATURE_SOURCES        = <论文机制卡和检索记录，可为空>
EXPERIMENT_GRAPH          = <项目根目录的 EXPERIMENT_GRAPH.html>
OUTPUT_PATH               = <logs/summaries/volume_NNN_summary.md>
```
如果缺少会改变研究结论的关键输入，不得补写合理化故事。输出：
```text
STAGE_REFLECTION_INCOMPLETE
Missing evidence: <缺失项>
Why it matters: <它会影响哪项判断>
Minimal recovery action: <最小补证动作>
```

## 3. 证据纪律

### 3.1 四种陈述状态
反思中的每个实质主张必须属于以下一种：
- `OBSERVED`：由合格实验、指标、消融或 artifact 直接支持的事实；
- `INFERRED`：能解释事实但尚未被判别实验隔离的机制解释；
- `HYPOTHESIZED`：面向下一阶段、尚未验证的可证伪假设；
- `UNKNOWN`：证据不足、结果冲突或当前无法识别。
不得把 `INFERRED` 或 `HYPOTHESIZED` 写成 `OBSERVED`。

### 3.2 证据引用
每个核心结论至少引用一个可追溯锚点：
```text
[E012]
[E012/A02]
[volume_003#E012]
[artifact: path-or-dashboard]
[paper: mechanism-card-id]
```
只引用与判断有关的指标、消融和异常。不得复制完整配置、逐 step 曲线或 trainer stdout。

### 3.3 结果可比性
在解释性能差异前检查：
- 是否使用相同 Benchmark、数据划分、指标、训练预算和评估脚本；
- Selection Split 是否符合登记规则；
- 候选与对照是否获得公平的数据、训练、选模和调参机会；
- Run Outcome 是否允许形成正式科研结论；
- 是否存在 Technical Failure、数据泄漏、指标退化或 artifact 缺失；
- 当前核心性能比较目标是 Research Base 还是 Champion；
- Research Base 晋升是否仍然相对晋升前的 Research Base 判断。
不可比结果只能作为诊断线索，不能支持晋升或因果结论。
如果本阶段因 Benchmark 正式变更而触发总结，旧 Benchmark 下的阶段结论必须在旧契约内收口；新 Benchmark 另建版本和角色快照。不得把新旧契约下的指标差异写成模型提升。
如果本阶段发生 Research Base 晋升，晋升前的历史 Candidate 仍按当时的 Research Base 解释；不得用晋升后的新 Research Base 追溯重算其改动分类或实验成败。下一阶段新 Candidate 才以阶段结束时的当前 Research Base 为参照。
Stage Summary 对 Benchmark 和模型角色是只读的：只报告冻结证据中已经正式生效的变更。总结中提出的角色更新或 Benchmark 调整只能标记为 `HYPOTHESIZED` 建议，随后仍须通过正常晋升或版本变更流程。

### 3.4 预测校准
对每个关键实验比较：
```text
实验前预测 -> 实际观测 -> 偏差方向 -> 偏差揭示了什么
```
预测失败不是需要隐藏的错误。它可能说明：
- 原因机制判断错误；
- 干预没有真正作用于目标组件；
- 指标没有测到声称的能力；
- 效果只在特定 slice 或训练阶段出现；
- 竞争机制比原机制更能解释结果；
- 当前实验无法区分这些解释。

## 4. 完整执行流程
严格按顺序执行。不得在完成独立审查前直接生成下一批候选。
一次 Stage Reflection 的隔离调用上限为 5 次：3 个角色、1 次交叉质询、1 次综合。每个 `Interaction Candidate: yes` 可额外使用至多 4 次调用：3 个独立审查和 1 轮辩论。全部调用必须计入 Runtime counters，并遵循全局 Subagent Policy：并发不超过 2，优先串行执行。

### Phase 0：冻结事实
1. 读取 Stage Evidence Pack；
2. 建立最小 Evidence Ledger；
3. 标记可比、不可比、技术失败和缺失证据；
4. 恢复本阶段实验前预测；
5. 禁止在此阶段写机制解释或下一步建议。
### Phase 1：独立第一性原理分析
使用独立上下文执行“第一性原理机制分析员”提示词。必须回答：
1. 当前真正的瓶颈是什么？尽可能用至少两个成功、失败或异常结果界定它；若事件触发的阶段只有一个合格结果，必须标记证据不足，不得强行确立机制；
2. 当前路线依赖哪个承重假设？如果它不成立，哪些解释或方案会一起坍塌；
3. 房间里的大象是什么？哪条不舒服但重要的事实一直没有被正面处理；
4. Hamming Question：即使当前方向成功，它是否会实质改变项目能力、Benchmark 结论或研究认识；
5. 哪个旧认识已经被证据推翻、削弱或限制了适用范围；
6. 当前最短的因果链是什么：`干预 -> 内部变化 -> 可观测中间量 -> 最终指标`；
7. 哪个链条环节仍然只是假设。
如果这一部分只写“某模型更好”“某组件有效”或“指标提升”，判定为不合格并重做。
### Phase 2：独立对抗审查
至少形成三个相互隔离的初始结论：
- 第一性原理机制分析员；
- 对抗式实验检察官；
- 简化与替代路线设计师。
如果运行环境支持独立 agent，三个角色必须使用相同事实包、不同新上下文，且第一轮看不到其他角色的结论。如果不支持，使用三个隔离调用；不得在同一个连续回答里模拟三种声音。必须在最终文档披露独立性限制。本反思审查与 Interaction Review Gate 的降级政策不同且互不适用：无独立 agent 时，本反思允许使用三个隔离调用并披露限制；该许可不得套用于 Interaction Gate。
### Phase 3：一次交叉质询
将三个独立备忘录放到同一争议表中，只允许一次交叉质询：
- 当前解释的最强支持证据是什么；
- 当前解释的最强反证是什么；
- 哪些分歧来自事实不同，哪些来自机制解释不同；
- 哪个最小实验能让双方产生不同方向的预测；
- 哪项致命问题必须先解决，不能由多数意见跳过。
限制为一次质询，避免为了形式进行无限辩论。
### Phase 4：受约束头脑风暴
只围绕 Phase 1–3 暴露的未决机制、失效边界和证据缺口生成候选。允许重新进入论文调研，不得把文献调研限制在项目开端。
优先使用以下来源：
- `origin=empirical`：本项目成功、失败、异常或 failure slice；
- `origin=literature`：已发表方法的全方法或组件级机制；
- `origin=repair`：论文复现中暴露的过时、不合理或不适配组件；
- `origin=first_principles`：承重假设反转、问题重构或因果链缺口；
- `origin=simplification`：删除、替换、合并或重连带来的更短解释；
- `origin=analogy`：跨任务机制类比，但必须落到具体变量、算子或信息流。
每个候选只能验证一个主要假设。复杂候选必须拆分，禁止用多分支堆叠逃避机制识别。
跨分支 A+B 不得直接进入实验计划；只有通过 [Interaction Review Gate](../references/interaction_review_gate.md) 的组合才能成为可执行候选。
### Phase 5：综合与路线裁决
形成两个必需方案和一个可选综合方案：
- `A`：保持当前最有证据支持的解释和路线；
- `B`：当前解释的最强替代、修复、转向或停止方案；
- `AB`：只在能够保留双方有效部分且不增加不可归因复杂度时形成；否则明确写 `AB = NOT_JUSTIFIED` 及原因。
`A` 必须允许“保持当前 Research Base，不修改”；不得强迫产生 `B` 或 `AB` 的胜利。
最终裁决先过证据有效性硬门，再做信息增益、成本和研究价值的 Pareto 比较。不得计算一个总分把硬缺陷平均掉。
### Phase 6：写入 Stage Summary
严格使用第 7 节的六个一级标题。文档应能独立支撑下一阶段决策，但通过链接引用原始事实，不复制原始日志。

## 5. 独立角色提示词
以下角色共享同一 Stage Evidence Pack，但第一轮必须彼此隔离。

### 5.1 第一性原理机制分析员
```text
Role: First-Principles Mechanism Analyst
Objective:
Reconstruct what the stage results mean from first principles. Do not summarize
experiments chronologically and do not treat score movement as a mechanism.
Evidence rules:
- Use only the supplied Stage Evidence Pack.
- Tag every claim OBSERVED, INFERRED, HYPOTHESIZED, or UNKNOWN.
- Cite experiment or artifact anchors for every substantive claim.
- Treat prediction error as evidence about the causal model.
Required analysis:
1. State the bottleneck as a concrete failure: what breaks, under which condition,
   and why the current machinery cannot produce the needed behavior.
2. Name at least two stage observations that locate this bottleneck when available.
   If an event-triggered stage has only one qualifying observation, mark the
   bottleneck UNKNOWN / underdetermined instead of manufacturing a second anchor.
3. Identify the load-bearing assumption. Explain what collapses if it is false.
4. State the elephant in the room: the strongest inconvenient fact the current
   narrative has not addressed.
5. Answer the Hamming Question: if this direction succeeds, what materially changes?
6. Write the shortest causal chain:
   intervention -> internal change -> observable mediator -> outcome metric.
7. Mark every unsupported link in that chain.
8. Identify which prior belief was overturned, weakened, or narrowed.
9. Generate 2-4 competing mechanisms with at least one directionally different
   prediction between each serious pair.
10. Name the cheapest discriminating experiment.
Do not propose implementation changes until the causal analysis is complete.
Return a concise mechanism memo, unresolved uncertainties, and evidence anchors.
```

### 5.2 对抗式实验检察官
```text
Role: Adversarial Experiment Prosecutor
Objective:
Find the cheapest valid reason the current stage narrative or next-step proposal
would fail to establish its claim. Attack evidence and identification, not wording.
Audit:
- Benchmark and split consistency;
- data leakage, label maturity, checkpoint and test-set use;
- fairness of data, training budget, tuning and selection;
- whether one primary factor changed at a time;
- whether the intervention reached the claimed functional locus;
- alternative explanations, confounders and evaluator gaming;
- whether support and falsification predictions distinguish mechanisms;
- missing negative controls, replacement tests, ablations or failure slices;
- Technical Failure or incomplete runs being misread as scientific evidence;
- branch stacking, hidden compute or data, and post-hoc storytelling.
For each finding return:
- severity: fatal | major | repairable | uncertainty | suggestion;
- status: confirmed | plausible | not_supported;
- evidence anchor;
- consequence for the current claim;
- minimal correction or discriminating experiment;
- what evidence would make you withdraw the objection.
Do not invent flaws to satisfy the role. If no fatal issue is supported, explicitly
write "No supported fatal issue found" and list only real residual uncertainties.
A fatal validity issue cannot be dismissed by majority vote or metric improvement.
```

### 5.3 简化与替代路线设计师
```text
Role: Simplification and Alternative-Route Designer
Objective:
Challenge the assumption that the next step must add more machinery. Generate the
smallest alternatives that can explain the evidence or discriminate mechanisms.
Required search order:
1. Do nothing / retain current Research Base;
2. Delete an unnecessary branch or assumption;
3. Replace the most similar old component;
4. Merge or reconnect existing components;
5. Repair one identified weak component;
6. Add a component only if replacement cannot retain the expected gain and the new
   component has an independent, non-substitutable function;
7. Broaden or pivot only when the bottleneck or evidence demands it.
For each viable alternative provide:
- evidence origin;
- one primary hypothesis;
- concrete Scope x Locus x Operator relative to the proper experiment reference;
- predicted metric direction and mechanism mediator;
- falsification condition;
- cheapest discriminating experiment;
- expected information gain and cost class;
- structural complexity and branch-growth risk;
- why it is better than a more complicated option.
Do not generate cosmetic renaming, generic loss additions, arbitrary gates, or several
branches at once. Do not call an analogy an innovation unless it maps to a concrete
state, signal, operator, objective, constraint, or information flow.
```

## 6. 对抗辩论与综合裁决提示词

### 6.1 交叉质询提示词
```text
You are moderating one evidence-based cross-examination between three independent
stage-reflection memos. Preserve real disagreement; do not force consensus.
For every disputed claim:
1. Quote the claim and its evidence status.
2. State the strongest supporting evidence.
3. State the strongest counter-evidence or competing explanation.
4. Decide whether the disagreement is factual, causal, evaluative, or strategic.
5. Name the observation that would change each side's mind.
6. Propose the smallest experiment whose predicted direction differs between sides.
7. Mark unresolved fatal or major objections that synthesis may not erase.
Limit each side to one rebuttal. Do not reward rhetoric, confidence, verbosity, or
role count. Return a disagreement ledger, not a conversational transcript.
```

### 6.2 综合裁决提示词
只要运行环境能够创建隔离调用，就必须由未参与构思、攻击或交叉质询的新上下文完成。无法获得新上下文时，必须披露独立性限制；综合者不得重写角色备忘录，也不得在没有新增证据时宣布某项未决异议已经解决。
```text
Role: Stage Reflection Synthesizer and Judge
Inputs:
- Frozen Evidence Ledger;
- First-Principles Mechanism Memo;
- Experiment Prosecutor Memo;
- Simplification and Alternative-Route Memo;
- Cross-Examination Disagreement Ledger.
Rules:
1. Verify evidence validity before comparing strategies.
2. Do not use majority vote to erase a fatal or major objection.
3. Preserve unresolved dissent and name the evidence needed to resolve it.
4. Treat unchanged Research Base / do nothing as a first-class candidate.
5. Prefer experiments that distinguish mechanisms over experiments that merely seek
   another score increase.
6. Prefer replacement, deletion or repair over branch addition when expected value is
   close and the simpler option preserves interpretability.
7. Do not promote a lesson to established principle without repeated or causal support.
8. Keep literature facts, project observations and new hypotheses visibly separate.
9. Choose exactly one primary route: DEEPEN, BROADEN, REPAIR, PIVOT, or CONCLUDE.
10. Give one contingency route with an explicit trigger, not a second simultaneous plan.
Return the six-section Stage Summary contract exactly. Cite evidence anchors and list
rejected alternatives with reasons.
```

## 7. Stage Summary 固定六部分输出契约
最终 Markdown 必须使用以下六个 `##` 标题作为唯一的一级内容板块。可以在其下增加 `###` 标题，但不得把“实验流水账”作为独立板块。

### 一、我们到底知道了什么？
回答事实边界，而不是复述过程。
必须包含：
- 阶段开始与结束时的 Benchmark、角色模型和 Core Comparison Target 快照；
- 通常保留 3–8 条最重要的 Stage Claim；证据不足时宁可少写，不得凑数；
- 每条主张的 `OBSERVED / INFERRED / HYPOTHESIZED / UNKNOWN` 状态；
- 证据锚点、反证和缺失证据；
- 关键实验的预测校准；
- 成功、失败、near-miss 和不可比结果分别说明；
- 本阶段没有学到什么，防止把无信息实验包装成结论。
推荐表格：
```markdown
| Stage Claim | 状态 | 支持证据 | 反证/边界 | 置信度 | 缺失证据 |
|---|---|---|---|---|---|
```

### 二、这些结果为什么发生？
这是强制的第一性原理部分，不得省略或退化成指标总结。
必须包含：
- 具体瓶颈：什么在什么条件下失败，为什么现有机制无法解决；
- 尽可能提供至少两个定位瓶颈的实验事实；若本阶段只有一个合格事实，则将机制标为 UNKNOWN / underdetermined；
- 最短因果链：`干预 -> 内部变化 -> 中间量 -> 最终指标`；
- 因果链中仍未验证的环节；
- 承重假设及其失败后果；
- 房间里的大象；
- Hamming Question 的回答；
- 被推翻、削弱或收窄的旧认识；
- 2–4 个竞争机制及其不同方向预测；
- 当前最可信机制和仍需保留的替代解释。
若无法建立机制，只能明确写 `UNKNOWN` 并提出判别实验，不能用合理化故事补齐。

### 三、我们可能错在哪里？
必须包含：
- 当前研究叙事的最强反方版本；
- 致命、主要、可修复和不确定问题的分级；
- 数据、评估、预算、选择、归因和复现威胁；
- 至少一个能同时解释当前涨分和失败结果的竞争解释；
- 哪项证据会让我们改变当前结论；
- 尚未解决的审查分歧；
- 如果当前方向是错的，最早应该出现什么信号。
不存在有证据支持的致命问题时，应明确写明，不得虚构批评。

### 四、这一阶段留下了什么可迁移认识？
只沉淀能约束未来决策的认识。
每条认识写明：
```text
Lesson:
Status: provisional | supported | reusable-principle
Evidence:
Scope and boundary:
What it rules out:
Non-repeat rule:
What would invalidate it:
```
额外要求：
- 区分一次观察、阶段性规律和可复用原则；
- 写出失败关闭了哪条假设或搜索空间；
- 写出预测误差如何修正了研究者的因果模型；
- 对重复失败建立 non-repeat rule；
- 不把每条观察都升级为长期原则；
- 不删除令人尴尬但会约束未来实验的历史。

### 五、下一阶段有哪些真正可判别的方向？
生成 0–3 个实验候选，数量服从证据，不为凑数强行填满。通常应保留 2–3 个竞争候选；若硬门后只有一个候选存活，可以只保留一个。如果主路线为 `CONCLUDE` 且没有仍会改变研究结论的关键不确定性，可以保留零个实验候选，但必须说明证据，并列出归档、最终验证或论文整理动作，不能伪造低价值实验。若合格方向超过三个，只保留覆盖不同关键不确定性的三个 Candidate Draft；被截断方向写入本节末尾“未晋级方向”清单，一行一个，不成为 Draft，后续可由新一轮 `GENERATE` 重新提出。
每个候选必须包含：
```text
Candidate ID:
Origin: empirical | literature | repair | first_principles | simplification | analogy
Uncertainty reduced:
Primary hypothesis:
Competing explanation:
Single main change:
Predicted outcome and mediator:
Falsification condition:
Minimal discriminating experiment:
Cost class:
Dependencies:
Interaction Candidate: yes | no
```
Stage Reflection 只生成未判级的 Candidate Draft；Evidence Class、五维分类和 Gold/Silver/Hold/Reject 由后续 `CANDIDATES_READY` REVIEW 独占判定。
仅当 `Interaction Candidate: yes` 时，另行展开以下附加块；普通候选不写这些字段：
```text
Interaction sources and graph edges:
Orthogonality claim and mediators:
Full-text literature evidence:
Interaction Review Pack:
Reviewer completion:
Initial votes:
Final votes:
Unresolved and confirmed hard vetoes:
Interaction Gate decision:
```
未晋级方向（非 Candidate Draft）：`- <方向> — <未进入本轮三个 Draft 的原因>`
### 六、研究路线现在应当怎么走？
必须选择一个主路线：
- `DEEPEN`：已有受支持机制，需要验证边界、交互或更深因果链；
- `BROADEN`：当前结论稳定，值得测试相邻问题或重新进入论文调研；
- `REPAIR`：方向仍有价值，但一个已识别组件、协议或证据缺口必须先修复；
- `PIVOT`：关键假设被否定，或新的异常指向更有价值的问题；
- `CONCLUDE`：已有足够证据形成贡献，继续实验的边际信息价值低。
`CONCLUDE` 只有在 Performance Target 已达到或预登记总预算已经耗尽时才是合法主路线。目标未达到且预算仍可用时，即使当前方向已经饱和，也必须使用 `PIVOT` 关闭当前路线并进入恢复型调研、第一性原理候选或其他开放分支；不得把“当前方向不值得继续”扩展为第三种研究终止状态。
必须写明：
- 主路线和一句话裁决；
- 为什么现在选择它；
- 为什么不选择其他路线；
- 下一项最小动作；
- 一个备用路线及其触发条件；
- 阶段开始与结束时 Anchor Baseline、Research Base、Champion、Reference Baseline、Core Comparison Target 和 Benchmark 的只读状态快照；
- 哪些变化已经通过正式流程生效，哪些只是 `HYPOTHESIZED` 建议；
- 下一阶段的停止条件或再次触发反思的条件；
- 仍需人类裁决的问题，若无则写“无”。

## 8. 下一阶段候选生成契约
候选必须来自未解决的关键不确定性，而不是从模型组件清单随机采样。

### 8.1 竞争机制要求
同一现象优先生成 2–4 个机制解释。任意两个严肃候选至少有一个方向不同的可观测预测；否则它们只是同义改写，不构成竞争机制。

### 8.2 文献重新进入
满足以下任一条件时，应把文献重新进入登记为实验候选之前的证据获取动作或依赖，而不是伪装成一个 Experiment Candidate：
- 结果明显违背论文报告或本阶段预测；
- Paper Repair Cycle 暴露论文组件过时或不适配；
- 当前创新只知道现象，不知道可能机制；
- 连续候选属于同一改动家族，出现搜索空间塌缩；
- 对抗审查发现最近邻、经典方法或替代解释缺失；
- 准备替换 loss、组件、分支、优化或推理机制，但缺少强方法底座。
检索不是独立于实验循环的一次性阶段。取得一次有效论文复现后，后续组件级创新仍然可以并且经常需要继续调研论文。Section 五应描述检索问题、查询和它将解锁的后续实验；检索完成后先形成 Candidate Draft，再由 `CANDIDATES_READY` REVIEW 分类。

### 8.3 结构风险
以下候选默认需要降低优先级或拆分：
- 一次同时改变多个主要组件；
- 在已有多分支模型上继续新增相似分支；
- 无法说明新分支不可替代功能；
- 增益可能由额外参数、数据或训练预算解释；
- 只改变名称、领域、常规 loss、gate 或提示模板；
- 无法通过删除、替换或重参数化与已知方法区分。

## 9. 路线决策规则
路线决策按以下顺序：
1. 检查 Benchmark 和证据有效性；
2. 检查关键假设是否仍然成立；
3. 检查当前方向是否产生可迁移机制认识；
4. 检查是否存在低成本、高信息增益的判别实验；
5. 检查是否出现搜索家族塌缩、重复实验或边际收益下降；
6. 检查是否需要重新进入论文调研；
7. 比较继续、修复、转向和结束的机会成本；
8. 选择一个主路线和一个带触发条件的备用路线。
路线裁决必须引用证据，不得使用“感觉更有潜力”“看起来值得继续”等空泛理由。

## 10. 完成前硬门
写入 Stage Summary 前逐项检查：
- [ ] 已读取并冻结完整 Stage Evidence Pack；
- [ ] 核心主张区分 OBSERVED、INFERRED、HYPOTHESIZED 和 UNKNOWN；
- [ ] 每条核心主张有证据锚点；
- [ ] Technical Failure、Stop-loss 和不可比结果没有被误用；
- [ ] 第一性原理部分完整回答瓶颈、承重假设、房间里的大象和 Hamming Question；
- [ ] 已写出因果链及其未验证环节；
- [ ] 已比较预测与实际结果；
- [ ] 已形成当前解释的最强反方版本；
- [ ] 至少保留两个可区分的机制解释，或说明为何只剩一个；
- [ ] 头脑风暴发生在证据审查之后；
- [ ] 下一候选每个只验证一个主要假设；
- [ ] 下一候选有失败条件和最小判别实验；
- [ ] 所有进入实验计划的 Interaction Candidate 已通过权威 Gate；
- [ ] 未通过硬门的候选没有靠创意分进入优先队列；
- [ ] `do nothing / retain Research Base` 被当作合法方案评估；
- [ ] 已选择一个主路线和一个有触发条件的备用路线；
- [ ] 审查分歧和未知项被保留；
- [ ] 最终文档严格包含固定六部分。
任一核心硬门未通过时，不得输出伪完整总结。标记 `STAGE_REFLECTION_INCOMPLETE` 并说明最小补证动作。

## 11. 禁止模式
- **反思不是复述**：不得压缩日志、罗列排行榜或在看到涨分后补写没有判别证据的故事；
- **保留竞争解释**：不得让单一顺耳叙事垄断反思；
- **审查独立性**：不得在同一连续上下文中模拟独立角色、强迫批评，或让同一调用攻击、修复并宣告成功；
- **硬缺陷不可投票洗白**：多数票、平均分和综合措辞不能覆盖有证据的致命问题；
- **创新必须受约束**：不得无瓶颈、证据或判别预测地随机加模块，也不得跳过替换测试继续膨胀分支；
- **交互纪律**：不得枚举组合、伪造正交性或以摘要代替全文证据；按权威 Gate 审查；
- **保留失败与边界**：不得删除失败路径或把一次观察膨胀为永久原则；
- **搜索与停止纪律**：不得拒绝后续文献重入、无限辩论，或在合法 `CONCLUDE` 后强迫继续。

## 12. 最小调用提示词
当 AutoResearch 主流程触发阶段总结时，使用以下调用：
```text
Read and obey:
<STAGE_REFLECTION_PROMPT>
Research contract:
<RESEARCH_CONTRACT_SOURCE>
Generate the Stage Summary for <VOLUME_ID>.
Inputs:
- Benchmark: <BENCHMARK_SOURCE>
- Master Experiment Log: <MASTER_EXPERIMENT_LOG>
- Sealed Research Log: <SEALED_RESEARCH_LOG>
- Run Event root: <RUN_EVENT_ROOT>
- Literature and mechanism sources: <LITERATURE_SOURCES>
- Experiment Lineage Graph: <EXPERIMENT_GRAPH>
- Output: <OUTPUT_PATH>
First build a frozen Stage Evidence Pack. Then execute the first-principles analysis,
independent adversarial review, one cross-examination, constrained brainstorming, and
route judgment defined in the prompt. When isolated contexts are available, the host
orchestrator must invoke the three initial roles and the final judge as separate calls;
one ordinary completion does not satisfy the independence contract. Write exactly the
six required Stage Summary sections. Do not rewrite the source logs. If critical
evidence is missing, emit STAGE_REFLECTION_INCOMPLETE instead of fabricating a complete
narrative.
```
开发期可设置 `SKILL_ROOT=<PROJECT_ROOT>`，并令 `STAGE_REFLECTION_PROMPT=<PROJECT_ROOT>/prompts/stage_reflection.md`。正式封装为 skill 后，`STAGE_REFLECTION_PROMPT` 应指向 skill 包内的 reference 文件，而 `PROJECT_ROOT` 始终指向被研究项目；两者不得混用。
