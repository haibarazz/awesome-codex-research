---
doc_id: paper-innovation-prompt-patterns
doc_type: reference
title: Paper Innovation Prompt Patterns
status: stable
summary: 汇总问题卡、正交变换、竞争机制、反事实、Pareto 和主张证据审计等论文创新提示模式。
read_when:
  - 论文复现后需要生成机制明确的后续创新候选时
depends_on:
  - research-contract
  - paper-reproduction-and-innovation
activation:
  level: ON_DEMAND
---

# 创新提示词模式

本文件记录从本地整理的 GitHub Skill 语料中提炼出的提示词机制。它们是生成候选的算子，不是创新的充分条件。使用时必须把抽象类比落到 LLM/深度学习的具体变量、算子、目标函数或训练流程。

## 目录

- [来源范围](#来源范围)
- [1. 问题卡先于算法名](#1-问题卡先于算法名)
- [2. 正交变换算子](#2-正交变换算子)
- [3. 竞争机制而非单一故事](#3-竞争机制而非单一故事)
- [4. 文献通道与错误通道分离](#4-文献通道与错误通道分离)
- [5. 困难样本驱动精炼](#5-困难样本驱动精炼)
- [6. 假设树与洞见回传](#6-假设树与洞见回传)
- [7. 实质性分歧委员会](#7-实质性分歧委员会)
- [8. 反事实和失效分支](#8-反事实和失效分支)
- [9. 多目标硬门与 Pareto 排序](#9-多目标硬门与-pareto-排序)
- [10. 主张-证据审计](#10-主张-证据审计)
- [不采用的模式](#不采用的模式)

## 来源范围

全库发现约 417 个 `SKILL.md` 路径；关键词扫描后，由主流程和两个独立审查任务深读 20 余个高相关 skill。核心来源：

- `sources/claude-scholar/skills/research-ideation/SKILL.md`
- `sources/scientific-agent-skills/skills/scientific-brainstorming/SKILL.md`
- `sources/scientific-agent-skills/skills/hypothesis-generation/SKILL.md`
- `sources/scientific-agent-skills/skills/hypogenic/SKILL.md`
- `sources/scientific-agent-skills/skills/consciousness-council/SKILL.md`
- `sources/scientific-agent-skills/skills/scientific-critical-thinking/SKILL.md`
- `sources/scientific-agent-skills/skills/experimental-design/SKILL.md`
- `sources/scientific-agent-skills/skills/arbor/SKILL.md`
- `sources/scientific-agent-skills/skills/what-if-oracle/SKILL.md`
- `sources/scientific-agent-skills/skills/peer-review/SKILL.md`
- `sources/claude-scholar/skills/paper-self-review/SKILL.md`
- `sources/openjudge/skills/eval_pipeline/01-eval-design/SKILL.md`
- `sources/openjudge/skills/eval_pipeline/07-redteam/SKILL.md`
- `sources/nature-paper-skills/skills/research/paper-analyzer/SKILL.md`
- `sources/nature-paper-skills/skills/review/paper-reviewer/SKILL.md`

## 1. 问题卡先于算法名

来源：`research-ideation`。

要求候选先写：真实问题、假设、已有证据、缺失证据、支持条件、证伪条件和最小下一步。它能阻止模型直接生成“XX-LoRA”“XX-Agent”名称，再倒推故事。

只在候选收敛阶段强制；发散阶段过早使用会压制探索。

## 2. 正交变换算子

来源：`scientific-brainstorming` 及其 `brainstorming_methods.md`。

可用算子：

- Substitute：替换状态、算子、监督或更新规则；
- Combine：组合互补机制，但必须产生新性质；
- Adapt：从其他任务迁移机制而非术语；
- Modify：改变粒度、尺度、时间或层级；
- Eliminate：删除冗余假设或监督；
- Reverse：反转信息流、因果顺序或教师/学生关系；
- TRIZ contradiction：寻找性能、效率、稳定性、个性化之间的结构性矛盾；
- Morphological analysis：在状态、算子、监督、目标、推理五个轴上系统组合。

每个类比都要写成：

```text
源机制 -> LLM/深度学习变量 -> 可执行改动 -> 可区分预测
```

只产生修辞类比而没有变量映射的候选直接删除。

## 3. 竞争机制而非单一故事

来源：`hypothesis-generation`。

为同一失败生成 3–5 个机制解释，例如：数据不足、状态表示错误、优化冲突、推理时资源不足、评价错配。每对候选至少有一个方向不同的预测，否则属于同义重复。

默认只承诺方向、排序和交互；没有 pilot 或先验时禁止编造精确增益数值。

## 4. 文献通道与错误通道分离

来源：`hypogenic` 的 HypoRefine/Union 思路。

分别生成：

- `origin=literature`：已有论文机制；
- `origin=empirical`：项目日志、错误样本和消融揭示的机制；
- `origin=analogy`：跨任务类比。

合并时保留来源和证据等级。不能把文献事实、项目观察和模型猜测混写成同一类证据。

## 5. 困难样本驱动精炼

来源：`hypogenic` 与 `arbor`。

用冻结开发集的 failure slice 替换或细化弱候选；记录父候选、反例、修改原因和被淘汰路径。失败是后续候选必须满足的负约束，不是可以删除的噪声。

不得根据 test 结果反复发明候选。

## 6. 假设树与洞见回传

来源：`arbor`。

将候选组织为：方向节点 -> 具体干预 -> 实验证据 -> 可复用洞见。执行者只测试一个固定假设，不能在结果不好时偷偷换问题。实验结束后把叶节点观察抽象成父节点约束。

适用于后续迭代实验，不要求初次调研就建立复杂树工具。

## 7. 实质性分歧委员会

来源：`consciousness-council`。

独立角色必须持有不同目标：机制忠实、近邻碰撞、实验可证伪。第一轮隔离结论，第二轮才允许互相反驳。多个角色重复同一意见不算多样性。

## 8. 反事实和失效分支

来源：`what-if-oracle`、OpenJudge eval/red-team skills。

固定改变的变量、幅度、时间和初始状态，检查：最好、最可能、最坏、分布漂移、反共识和二阶后果。概率只能来自数据或明确标记为主观先验。

为每个方法建立“机制 x 失效类型”矩阵，至少覆盖 near-miss、confounder、distribution shift 和 evaluator gaming。

## 9. 多目标硬门与 Pareto 排序

来源：`hypothesis-generation` 的质量标准。

先检查可测试性、可证伪性和机制差异三个硬门；通过后才比较解释力、范围、近邻一致性、可行性和新颖性。不要把所有维度压成一个总分，让高语言新颖度抵消不可执行性。

## 10. 主张-证据审计

来源：`scientific-critical-thinking`、`paper-self-review`。

对每个创新主张输出：

```text
Claim:
Verdict: keep | weaken | revise | remove
Evidence:
Missing evidence:
Closest collision:
Allowed wording:
Forbidden wording:
```

探索候选可标记为 `speculative` 保留；但不能进入论文主线或被写成已证实结论。

## 不采用的模式

- 无证据的固定“黄金比例”或伪精确权重；
- 为了形式完整强制生成图片、长篇 LaTeX 或 50 篇引用；
- 自由角色扮演但没有真实目标冲突；
- 让同一模型同时生成对抗样本和判定成功；
- 只按平均分或单次最佳 checkpoint 排名；
- 把 SCAMPER/TRIZ 本身写成算法贡献。
