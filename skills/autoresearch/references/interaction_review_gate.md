---
doc_id: interaction-review-gate
doc_type: reference
title: Interaction Review Gate
status: stable
summary: 审查跨分支 A+B 候选的机制正交性、全文文献证据、独立投票和最小可归因实验。
read_when:
  - Candidate Design 中出现跨分支 MERGE 候选时
  - Stage Reflection 提出 Interaction Candidate 时
depends_on:
  - research-contract
  - research-graph-protocol
  - candidate-priority-rules
activation:
  level: PHASE
  phases:
    - CANDIDATE_DESIGN
    - STAGE_REFLECTION
---

# Interaction Review Gate（跨分支交互审查门）

本节适用于把实验谱系图中两个不同分支的机制组合为一个新候选，例如 A+B。它既适用于 A、B 单独无效的情况，也适用于其中一个或两个已有正向结果的情况。

A+B 允许同时包含两个已有改动，但只能检验一个主要假设：

```text
Interaction Hypothesis:
A 与 B 在预先指定的机制、中介量或失败边界上存在正向交互，
联合效果不能由 A、B 各自独立效果充分解释。
```

除 A 与 B 外不得再附带第三个主要改动。不得把“也许一起会更好”作为交互假设。

## Step 1：从谱系图筛选正交组合

只检查 Phase 1–3 暴露出的互补分支，不对全部历史节点做两两排列组合。

首先确认：

- A、B 能在同一当前 Research Base、同一 Benchmark 和同一评估口径下表达；
- Base、A、B 已有同一 Benchmark 下的 Full Comparable Run；
- A、B 作用于不同瓶颈、信息路径或因果链环节；
- A、B 具有不同的可观测中介量或方向预测；
- A、B 不提供高度重复的功能，不只是两个相似分支或重复扩容；
- 二者结构兼容，不会因一个机制存在而使另一个机制失去定义。

正交性只能标记为：

```text
ORTHOGONAL      = 机制非冗余、预测可区分且结构兼容，可以继续
PARTIAL/UNKNOWN = 证据不足或存在实质重叠，必须 Hold 或先补证
NOT_ORTHOGONAL  = 主要机制重复或无法区分，Reject
```

只有 `ORTHOGONAL` 可以进入下一步。文件位置不同、组件名称不同或来自不同论文，不构成正交证据。

## Step 2：真实全文文献证据门

AI 必须围绕 A、B 的互补机制执行聚焦检索，真实下载并核验论文 PDF，阅读支持判断的正文、方法、消融或实验部分。标题、摘要、搜索摘要和二手解读不得作为通过证据。

证据至少满足一条：

1. `Direct support`：至少一篇全文论文直接报告、分析或消融了等价机制的联合使用；
2. `Triangulated support`：至少两篇相互独立的全文论文分别支持 A、B 的非重叠机制，并且 Stage Reflection 能写出可证伪的互补因果桥梁。

每条证据必须记录论文版本、PDF 路径、页码或章节、图表/实验锚点和它具体支持的主张。找不到合格证据时，A+B 只能保持 Hold；不得为了保留候选降低证据标准。

## Step 3：冻结 Interaction Review Pack

在调用 subagent 前生成同一份只读输入包：

```text
Interaction Candidate ID:
Current Research Base:
Benchmark version:
A node / result / mechanism / mediator:
B node / result / mechanism / mediator:
Base-A-B comparability check:
Orthogonality claim:
Predicted interaction and causal bridge:
Competing explanation:
Full-text literature evidence anchors:
Minimal A+B implementation:
No-third-change confirmation:
Success and falsification conditions:
Expected information gain:
Cost and remaining budget:
Structural and branch-inflation risk:
Primary Parent:
Source / Merge edges:
```

如果 Base、A、B 缺少任一合格可比结果，A+B 必须保持 Hold，只能先登记缺失对照的证据恢复动作。如果 A、B 来自不同历史 Research Base，必须先把机制重新表达到同一个当前 Research Base，并恢复公平证据；不得直接跨不可比底座拼接。

## Step 4：三个 subagent 独立初审

必须调用三个真实、彼此隔离的 subagent；不得在同一个连续回答中模拟三个角色。三个 subagent 接收相同的 Interaction Review Pack，第一轮看不到其他审查者结论。

本 Gate 与 Stage Reflection 三角色审查的降级政策不同且互不适用：无法获得三个真实 subagent 时不得用隔离调用替代，候选一律 Hold。

`Orthogonality Auditor`：

```text
判断 A 与 B 是否真正作用于不同机制、信息路径或因果链环节。
寻找功能重复、共享中介、伪正交、结构冲突和重复扩容。
不要评价新颖性，只评价正交性与兼容性。
```

`Literature Evidence Reviewer`：

```text
核查全文证据是否真正支持 A+B 的联合机制。
区分直接证据、可接受的机制三角验证和表面类比。
检查证据锚点、适用边界、相反结果和论文之间是否独立。
```

`Experimental Design Reviewer`：

```text
判断 A+B 是否是最小、公平、可归因且预算合理的判别实验。
检查 Base/A/B 对照是否足够、是否偷带第三个改动、成功条件是否预登记，
以及更简单的替换、删除或单组件实验能否回答同一问题。
```

每个 subagent 必须使用以下结构返回：

```text
Decision: PASS | HOLD | REJECT
Hard veto: none | orthogonality | literature | comparability | attribution | budget | branch-inflation
Strongest supporting evidence:
Strongest counterevidence:
Unresolved uncertainty:
What would change the decision:
Confidence: low | medium | high
```

## Step 5：一次辩论、修订投票与主 AI 核验

三个独立初审完成后，只进行一次有限交叉质询。每个 subagent 可以针对另外两份备忘录指出一项关键错误或缺失证据，然后提交最终 `PASS / HOLD / REJECT`。禁止无限辩论或为了形成多数而改变角色标准。

A+B 取得进入实验计划的必要资格，当且仅当：

- 三个 subagent 均完成独立初审和最终投票；
- 最终至少两个 subagent 投 `PASS`；
- 主 AI 核验后不存在已确认的 Hard veto。

多数票不能覆盖已确认的非正交、无合格全文证据、不可公平比较、无法归因、预算越界或明显分支膨胀。单个审查者提出但尚未证实的 Hard veto 必须使候选暂时 Hold，直到主 AI 用证据解决；不得直接按 2:1 忽略。运行环境无法调用三个独立 subagent 时，A+B 保持 Hold，不得开跑。

主 AI 必须在 Stage Summary 中显式记录 reviewer 是否 3/3 完成、初始与最终投票、未解决 Hard veto、已确认 Hard veto 和最终 `Interaction Gate decision`。只有 `Gate decision = PASS` 的组合可以进入 Active Frontier。

## Step 6：进入候选与谱系图

通过审查后：

- A+B 的 Primary Parent 是共同的当前 Research Base；
- A、B 通过 Source / Merge Edge 作为机制来源；
- `Single main change` 写为“仅组合 A 与 B，以检验预登记的 Interaction Hypothesis”；
- 不得同时增加额外分支、loss、数据处理或训练协议改动；
- 在实验前预登记交互成功标准、竞争解释和失败后的回溯位置。

若指标适合定义加性交互，应预登记 interaction contrast；若不适合，必须预登记 A+B 相对 Base、A、B 的方向预测和最小差异阈值。不得看到 A+B 结果后再选择最有利的协同定义。

Stage Summary 的第五部分必须简要列出被认真考虑的跨分支组合、正交性结论、文献证据门和三方最终投票。未通过者说明 Hold/Reject 原因，不写入 Active Frontier。
