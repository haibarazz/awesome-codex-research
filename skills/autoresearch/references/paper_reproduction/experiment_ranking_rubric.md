---
doc_id: paper-experiment-ranking-rubric
doc_type: reference
title: Paper Experiment Ranking Rubric
status: stable
summary: 对论文迁移候选执行忠实度、近邻证据、可证伪性、成本和实验有效性的细粒度对抗审查。
read_when:
  - 论文产生多个实验候选且需要细粒度排序时
depends_on:
  - research-contract
  - paper-reproduction-and-innovation
  - candidate-priority-rules
activation:
  level: ON_DEMAND
---

# 实验对抗审查与排序

## 目录

1. 原则与事实包
2. Fidelity review
3. Prior-art review
4. Experiment validity review
5. 硬门
6. Pareto 排序
7. 实验决策与原创性状态
8. 汇总要求

## 原则

先过硬门，再排序。不要把不可执行、不可证伪或明显碰撞已有工作的方案，用一个较高“创意分”救回来。

普通论文候选由当前主 AI 在同一次 `REVIEW` 中依次使用三种审查视角，不启动独立 agent、投票或人工审批，也不生成独立 Review 文档。三种视角是固定检查维度，不是三个 Graph Operation。

## 事实包

REVIEW 只使用：

- Innovation Brief；
- 论文 Mechanism Fingerprint 和证据锚点；
- 项目接口映射；
- 实验卡；
- 最近邻证据账本；
- 可用预算和数据限制。

## Lens 1：Fidelity review

```text
Role: method-transfer fidelity reviewer.
Objective: determine whether the experiment preserves the source paper's actual
mechanism when moved into the target LLM/deep-learning project.

Check:
1. Is the intervention placed at the same functional locus?
2. Are the source state, signal, operator, objective and constraint preserved?
3. Which changes are unavoidable interface adaptation?
4. Does removing the paper-specific mechanism recover the target baseline?
5. Would the proposed result test the mechanism or only benchmark performance?

Return:
- fidelity: high | medium | low
- faithful parts
- distorted or missing parts
- minimum correction
- R/A/N classification
- experiment_recommendation: Go | Conditional Go | Hold | No-Go
```

`low` 不得进入优先执行队列。

## Lens 2：Prior-art review

先建立 `Neighbor Evidence Ledger`。每个最近邻必须记录：检索式、检索日期、数据库、论文标题、主来源 URL、版本、访问状态、本地全文路径、方法页/公式/算法锚点、与候选的逐元素比较、碰撞或排除理由、未解决不确定性。最接近的 3–5 篇若缺少可读主来源全文，不得完成 method novelty 判定。

```text
Role: hostile prior-art referee.
Objective: try to collapse the claimed novelty into the closest existing method.

Answer explicitly:
1. Is this pseudo-innovation? Why?
2. Is there technical innovation? Where exactly?
3. After deleting names and domain language, what mathematical or algorithmic
   operation remains?
4. Is it only a new task, feature, loss term, gate, module stack or tuning rule?
5. What are the 3-5 closest methods, and what survives an element-wise comparison?
6. Can the proposal be reparameterized, simplified or ablated back to a known method?
7. What experiment would most quickly falsify the novelty claim?

Return:
- pseudo_innovation: yes | likely | unclear | no
- technical_novelty: none | implementation | task | empirical | method
- closest_collision
- surviving_difference
- missing_search
- novelty_status: not_claimed | candidate | unclear | supported_by_current_search | pseudo_innovation
- experiment_recommendation: Go | Conditional Go | Hold | No-Go
```

未完成可审计的最近邻搜索或缺少证据账本时，结构分类仍为 N candidate，`novelty_status=unclear`；是否执行实验另行判断。

## Lens 3：Experiment validity review

```text
Role: experiment prosecutor.
Objective: find the cheapest reason this experiment would fail to establish its claim.

Audit:
- data split, patient/user/time leakage and label maturity;
- whether baseline and proposed method receive equal data, tokens, steps and tuning;
- seed count, checkpoint selection and test-set use;
- whether one primary factor is changed at a time;
- strong baseline, negative control and sufficient ablation;
- metric/task alignment, calibration and failure slices;
- whether support and falsification predictions distinguish alternatives;
- compute estimate and a minimal smoke test;
- reproducible configs, logs and artifacts.

Return:
- fatal flaws
- repairable flaws
- missing controls
- minimal discriminating experiment
- expected information gain
- cost class
- experiment_recommendation: Go | Conditional Go | Hold | No-Go
```

## 硬门

| Gate | 通过条件 | 失败处理 |
|---|---|---|
| G1 证据 | 有全文、方法证据和版本口径 | 替换论文或补全文 |
| G2 忠实 | fidelity 非 low | 重写映射 |
| G3 可测试 | 有可观察结果和最小实验 | Hold |
| G4 可证伪 | 有明确失败条件 | Hold |
| G5 可区分 | 预测能区分竞争解释 | 增加判别实验 |
| G6 公平 | 数据、预算、调参和选模公平 | No-Go 直到修复 |
| G7 近邻 | N 类候选排查最近 3–5 个方法 | 分类保持 N candidate；novelty_status=unclear |

## 排序方式

通过硬门后进行 Pareto 排序，不计算单一加权总分：

- **信息增益**：一次实验能关闭多少关键不确定性；
- **机制价值**：能否验证新的状态、信号、约束或优化解释；
- **执行成本**：数据准备、训练、评估和人工审计成本；
- **依赖深度**：是否需要前置标签、模型或系统；
- **论文价值**：成功和失败是否都能形成清晰结论；
- **风险**：泄漏、不可识别、评估投机和实现不稳定。

默认优先顺序：

1. 低成本、能直接证伪整条路线的实验；
2. 能区分两个主要机制解释的实验；
3. 忠实复现的强基线；
4. 依赖已验证前提的新扩展；
5. 高成本且多个组件同时变化的完整系统。

## 实验决策与原创性状态

`experiment_decision` 只回答是否值得执行：

- **Go**：实验设计硬门通过，可立即进入预注册 smoke；
- **Conditional Go**：存在明确、可修复的实验前置条件；
- **Hold**：当前实验无法提供足够信息或关键证据尚缺；
- **No-Go**：关键假设不成立、不可公平比较或成本明显失衡。

`novelty_status` 单独回答原创性证据：

- **not_claimed**：R/A，不提出原创性主张；
- **candidate**：结构上属于 N candidate，但近邻审查或证据尚未完成；
- **unclear**：已有碰撞或独立性/证据不足，当前无法判断；
- **supported_by_current_search**：在当前可审计检索范围内保留了技术差异，不表示绝对首创；
- **pseudo_innovation**：差异可坍缩为已有方法、常规适配或命名包装。

`experiment_decision=Go` 与 `novelty_status` 可独立组合；例如一个 N candidate 可以值得跑实验，但原创性仍为 unclear。

## 汇总要求

最终排序必须保留三种视角发现的冲突，任何 Hard Gate 缺陷都不能被综合措辞抹掉。对每个入围项写清：

```text
为什么现在做：
它减少的关键不确定性：
最快证伪方式：
成功后允许主张什么：
失败后关闭或修改什么：
为什么排在下一项之前：
```
