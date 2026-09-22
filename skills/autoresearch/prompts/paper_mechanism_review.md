---
doc_id: paper-mechanism-review
doc_type: prompt
title: Paper Mechanism Review Prompt
status: stable
summary: 基于真实论文全文恢复机制、判断迁移粒度、建立 R/A/N Delta Ledger 并生成目标项目复现候选。
read_when:
  - 入选论文完成 PDF 下载和全文核验后
  - 设计全方法、组件级或协议级复现时
depends_on:
  - research-contract
  - paper-reproduction-and-innovation
  - benchmark-and-model-roles
activation:
  level: PHASE
  phases:
    - LITERATURE_RESEARCH
    - CANDIDATE_DESIGN
---

# Paper Mechanism Review Prompt

当 AutoResearch 需要深读一篇论文、判断它能否迁移到目标项目，并生成忠实复现或有限修复候选时，使用本 Prompt。

每次调用只处理一篇论文。目标不是总结论文，而是恢复论文真正改变了什么、为什么可能有效，以及如何在当前 Research Base 上形成可证伪实验。

## 目录

- [核心边界](#核心边界)
- [必须读取](#必须读取)
- [1. 核验论文与全文](#1-核验论文与全文)
- [2. 恢复 Mechanism Fingerprint](#2-恢复-mechanism-fingerprint)
- [3. 用连续段落解释论文方法](#3-用连续段落解释论文方法)
- [4. 选择迁移粒度](#4-选择迁移粒度)
- [5. 建立项目接口映射](#5-建立项目接口映射)
- [6. 建立 Delta Ledger 并分类 R / A / N](#6-建立-delta-ledger-并分类-r--a--n)
- [7. 执行机制保持测试](#7-执行机制保持测试)
- [8. 生成忠实复现候选](#8-生成忠实复现候选)
- [9. 处理完整复现效果不佳](#9-处理完整复现效果不佳)
- [10. Paper Repair Cycle](#10-paper-repair-cycle)
- [11. 从论文复现继续创新](#11-从论文复现继续创新)
- [12. 输出 Paper Mechanism Card](#12-输出-paper-mechanism-card)
- [普通候选审查](#普通候选审查)
- [完成条件](#完成条件)

## 核心边界

- 论文方法在目标项目自身数据集与 Benchmark 上复现；除非用户明确要求，不需要先复现论文原始数据集或原始 Benchmark。
- 项目价值、Candidate 比较和 Research Base 晋升始终相对当前 Research Base 判断。
- 全方法、组件级或协议级复现都可以是忠实 R/A；复现粒度不决定创新性。
- R 与 A 不属于创新。任何主动改变原论文机制、目标、自由度、算子、信息流或更新规则的修改，都先标记为 N candidate。
- 一篇论文复现有效后，后续仍可继续调研其他论文，对不同组件进行复现和创新；不得把整条研究绑定在单篇论文上。
- 论文完整方法效果不好时，不立即放弃；先判断是否存在局部有效组件，再决定是否进入最多三个核心假设的 Paper Repair Cycle。

## 必须读取

开始前读取：

- `../references/research_contract.md`；
- `../references/benchmark_and_model_roles.md`；
- `../references/paper_reproduction_and_innovation.md`；
- `../templates/paper_mechanism_card.md`；
- 当前项目的 Research Brief、Dataset Profile 和 Benchmark；
- 当前 Research Base、Champion、Anchor Baseline 及其有效结果；
- 与当前研究方向有关的 Experiment Log、Stage Summary 和已有 Literature Survey；
- 目标论文的可读全文与正式来源。

如果涉及 N candidate，再读取：

- `../references/candidate_priority_rules.md`；

普通 N candidate 由当前主 AI 在同一次 Controller 调用中完成 REVIEW；不要启动独立审查 agent 或生成独立 Review 文档。只有跨分支 MERGE 使用 Interaction Review Gate。

项目冻结的 Research Brief、Benchmark 和对应权威模块优先于论文来源和本 Prompt。

## 1. 核验论文与全文

优先使用论文官方页面、正式 proceedings、官方 OpenReview、作者正式版本或可信预印本。

至少记录：

- 标题、作者、年份与 venue；
- 正式接收或版本证据；
- 主来源 URL 与 PDF 来源；
- 当前读取的版本；
- 本地全文路径或可复查来源；
- 全文是否可读。

缺少可读全文时，不得把摘要或博客当作已深读证据。输出：

```text
PAPER_REVIEW_INCOMPLETE
Missing source: <缺失内容>
Why it matters: <会影响哪项机制判断>
Minimal recovery action: <如何补全>
```

## 2. 恢复 Mechanism Fingerprint

不得从论文标题、模块名称或摘要直接推断创新点。必须从正文恢复以下机制：

- `Problem`：论文真正解决的技术瓶颈；
- `Original Baseline`：论文从什么标准方法出发；
- `Intervention Locus`：改动位于数据、特征、骨干、组件、分支、loss、优化或推理中的哪里；
- `State and Signal`：输入状态、新增信号与监督来源；
- `Operator`：新增、替换或改变了什么算子、参数化或更新规则；
- `Objective / Constraint`：目标函数、正则、约束或优化几何；
- `Training Flow`：训练过程发生了什么变化；
- `Inference Flow`：推理过程发生了什么变化；
- `Claimed Mechanism`：作者认为它为什么改善目标；
- `Dependencies`：需要的数据、标签、模型、代码、算力和前置假设；
- `Limits`：未验证、失败或明确不适用的范围。

至少建立五处正文证据锚点，覆盖：

1. 方法定义；
2. 核心公式、算法或伪代码；
3. 关键主实验；
4. 机制消融；
5. 限制、失败或未验证范围。

每项实质判断必须能回到页码、公式、算法、图或表。无法从论文证据确认时标记 `UNKNOWN`，不得补写合理化故事。

## 3. 用连续段落解释论文方法

在字段提取后，用一段连续中文说明：

- 原始方法的完整流程；
- 创新发生的具体位置；
- 新增或改变的信息流；
- 训练与推理的变化；
- 与 Original Baseline 的本质差异；
- 哪些实验和消融支持作者的机制主张。

不得只罗列模块名称或写“加入某组件后效果更好”。

## 4. 选择迁移粒度

根据论文机制与目标项目的真实对应关系，选择一种迁移粒度。

### 全方法复现

当目标任务、输入输出、监督形式和论文问题基本同构，论文完整流程可以在目标项目上实现时使用。

全方法 R/A 复现不受“全方法 N candidate 必须拆解”的限制，因为它不是创新候选。

### 组件级复现

当论文创新只作用于某个局部组件，或者当前项目已有稳定 Research Base 时，优先把对应组件替换成论文方法，其余部分保持不变。

这是 AutoResearch 最常见的论文复现方式。

### 协议级复现

当论文核心是训练课程、采样策略、优化流程、推理协议或数据构造时，只迁移该协议。必须证明没有偷偷改变冻结的 Benchmark。

### No-Go

当论文关键监督、数据、状态或机制假设在目标项目中不存在，并且无法进行功能等价映射时，标记 `No-Go`。不得为了凑论文数量强行类比或生成不可执行实验。

## 5. 建立项目接口映射

明确写出：

```text
论文变量或模块  ->  当前 Research Base 中的变量或模块
原输入信号      ->  目标项目中真实可获得的对应信号
原更新规则      ->  当前训练循环中的具体位置
原目标函数      ->  目标项目中的公式、伪代码或实现入口
原对照组        ->  当前项目中的公平对照
原机制预测      ->  目标指标、slice 或交互上的方向性预测
```

映射必须落到功能位置和代码接口，不能停留在名称相似。

例如论文修改 attention，就说明替换当前 Research Base 的哪个 attention、保留哪些输入输出、不变配置是什么；不能只写“在本项目加入该 attention”。

## 6. 建立 Delta Ledger 并分类 R / A / N

逐项比较论文操作和目标项目实现：

| 原论文操作 | 目标项目操作 | 仅为兼容所必需？ | 是否改变机制、目标或自由度？ | 分类依据 |
|---|---|---:|---:|---|

分类规则：

- `R`：保持原论文算法和实现逻辑，只把数据、标签实例或任务样本换成目标项目；
- `A`：只做兼容目标代码所必需、功能等价的接口适配；
- `N candidate`：任何非兼容性必需的主动修改，或改变函数映射、目标、信号、算子、信息流、更新规则与可学习自由度；
- `No-Go`：无法保持机制或无法建立公平实验。

不得通过重新命名把 N 写成 A，也不得把 R/A 写成创新。

## 7. 执行机制保持测试

复现候选进入实验队列前，回答：

1. 去掉论文特有机制后，是否能够退化回当前 Research Base 或其明确对应组件？
2. 论文依赖的信息流、监督信号或优化压力在目标项目中是否真实存在？
3. 哪些变化只是数据实例替换，哪些是必要接口适配，哪些已经改变原机制？
4. 哪个结果会支持论文机制，而不只是说明模型偶然涨分？
5. 哪个结果会证伪“该机制能够迁移到当前项目”的假设？
6. 论文方法与当前 Research Base 是否获得相同数据、训练预算、调参机会和评估脚本？

输出 `Transfer Fidelity = high | medium | low`。

- `high`：机制、功能位置、信号和目标均被保留；
- `medium`：存在必要适配，但核心机制仍可辨认和检验；
- `low`：机制已明显变形、关键依赖缺失或无法公平比较。

`low` 不得进入优先执行队列，应修正映射或标记 No-Go。

## 8. 生成忠实复现候选

为可迁移论文生成一个主要复现候选。它只验证一个核心问题：

> 把这篇论文的机制忠实放到当前 Research Base 的对应功能位置后，它在目标项目自身 Benchmark 上是否仍然有效？

候选必须明确：

- 当前 Research Base；
- 复现粒度：全方法、组件级或协议级；
- Evidence Class：R 或 A；
- 唯一主要改动；
- 固定不变项；
- 必要适配项；
- 机制支持预测；
- 竞争解释；
- 明确证伪条件；
- 最小判别实验；
- 需要观察的 Primary Metric、机制指标、slice 和效率指标；
- 预期依赖、成本和 artifact。

R/A 复现不使用 Gold、Silver、Hold 或 Reject 候选优先级。它们按论文相关性、机制价值、Transfer Fidelity、信息增益和成本进行执行排序。

## 9. 处理完整复现效果不佳

论文完整方法在目标项目上效果不佳时，不立即关闭整篇论文。

首先判断：

- 是机制整体不适用，还是某个组件不适配；
- 哪些组件可能产生正贡献，哪些组件可能抵消收益；
- 是否存在过时组件、不合理假设或目标项目特有冲突；
- 哪个最小组件实验能够区分这些解释。

允许通过受控消融、组件恢复或组件级复现判断局部价值。每次只检验一个主要组件或机制，不得一次替换多个部分后声称找到了原因。

如果已有忠实 R/A 结果与机制证据支持修复，可以进入 Paper Repair Cycle。

## 10. Paper Repair Cycle

一次 Paper Repair Cycle 最多提出三个核心修复假设。

每个修复必须：

- 由论文机制、消融、失败 slice 或新近论文证据支持；
- 只修复一个过时、不合理或不适配的主要组件；
- 以忠实 R/A 模型或上一个受控修复版本作为 Experimental Parent；
- 将局部改动分类为 N candidate；
- 相对 Experimental Parent 判断修复是否有效；
- 相对当前 Research Base 判断整个方向是否具有项目价值；
- 通过 Candidate Adversarial Review 后才能开跑。

修复模型即使显著优于 Experimental Parent，只要没有达到相对当前 Research Base 的常规晋升条件，就不得更新 Research Base。

三个核心修复假设都失败后，关闭本次 Paper Repair Cycle，但保留论文机制卡、失败证据和仍可能独立有效的组件结论。

## 11. 从论文复现继续创新

论文复现取得提升后，后续研究不必只围绕该论文继续。

AI 可以：

- 在已验证论文组件之上继续调研其他论文；
- 对不同组件分别复现不同论文方法；
- 使用结果暴露的残余失败生成 results-grounded N candidate；
- 替换过时组件、修改 loss、优化、推理或其他局部机制；
- 在保持当前 Research Base 的前提下比较多条研究路线。

但每个新实验仍然只验证一个主要假设，并且必须以当前 Research Base 作为项目价值与晋升参照。

普通模块堆叠、随意新增分支、把多篇论文直接串联成综合模型，不构成创新。

## 12. 输出 Paper Mechanism Card

为每篇论文生成独立的 Paper Mechanism Card，至少包含：

1. 来源、版本与全文验证；
2. Mechanism Fingerprint；
3. 正文证据锚点；
4. 关键结果、消融与限制；
5. 连续的论文方法说明；
6. 项目接口映射；
7. Delta Ledger；
8. 迁移粒度与 R/A/N/No-Go 分类；
9. Transfer Fidelity；
10. 机制支持预测、竞争解释和证伪条件；
11. 主要忠实复现候选；
12. 已有结果与 Paper Repair 候选，如适用；
13. 与 Literature Survey、Experiment Card 和日志的引用。

同时更新项目 Literature Survey 中该论文的状态、机制家族、迁移结论和下一步。

## 13. 完成硬门

只有全部通过后，才能把论文移交给实验规划：

- [ ] 使用了可读全文，而不是摘要或二手解读；
- [ ] 至少有五处正文证据锚点；
- [ ] 已恢复真实机制，而不是复述论文名称；
- [ ] 已明确全方法、组件级、协议级或 No-Go；
- [ ] 已映射到当前 Research Base 的真实功能位置；
- [ ] Delta Ledger 完整，R/A/N 没有偷换；
- [ ] Transfer Fidelity 不是 low；
- [ ] 只有一个主要复现假设；
- [ ] 支持预测、竞争解释和证伪条件均明确；
- [ ] 数据、训练预算和评估口径符合当前 Benchmark；
- [ ] R/A 未被描述为创新；
- [ ] N 类修复已经移交 Candidate Adversarial Review；
- [ ] Paper Mechanism Card 与 Literature Survey 已更新。

## 禁止模式

- 只阅读标题、摘要或博客就声称深读论文；
- 用论文名称代替机制说明；
- 因为任务名称相似就假设方法可以迁移；
- 为了完整复现而同时改变当前 Research Base 的多个无关组件；
- 把必要接口适配写成创新；
- 把组件堆叠、换名称、普通 loss 或新增 gate 自动写成创新；
- 论文完整方法效果不好就直接放弃所有组件；
- 只和失败的 Experimental Parent 比较，不和当前 Research Base 比较；
- 复现成功后停止调研其他论文；
- 根据 test 结果反复发明修复候选。
