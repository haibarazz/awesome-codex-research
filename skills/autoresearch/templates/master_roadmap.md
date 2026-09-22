---
doc_id: master-roadmap-template
doc_type: template
title: Master Experiment Log and Roadmap Template
status: stable
summary: 生成项目 EXPERIMENT_LOG.md，只保存研究目标、阶段 Roadmap 和当前位置。
read_when:
  - 初始化或更新项目 Master Experiment Log 时
depends_on:
  - research-contract
  - research-records-protocol
activation:
  level: ON_DEMAND
---

# Master Experiment Log / Roadmap Template

## 目录

- [职责](#职责)
- [1. 研究目标](#1-研究目标)
- [2. 阶段 Roadmap](#2-阶段-roadmap)
- [3. 当前位置](#3-当前位置)
- [4. 实验册索引](#4-实验册索引)
- [5. 当前角色快照](#5-当前角色快照)
- [6. 最近阶段决议](#6-最近阶段决议)
- [7. 恢复入口](#7-恢复入口)

## 职责

在项目根目录生成并持续维护 `EXPERIMENT_LOG.md`，作为整条 AutoResearch 研究主线的统一入口。

它本质上是一份紧凑的研究 Roadmap 和渐进式日志索引，只帮助 AI 快速回答：

1. 这项研究最终要完成什么；
2. 当前研究被划分成哪些阶段；
3. 现在走到哪里，下一步应该读取什么。

**Research Brief：** `<path>`

**Current Benchmark：** `<path and version>`

## 1. 研究目标

用最短内容记录：

- 核心研究问题或任务；
- 当前 Benchmark 版本；
- Primary Metric 与最终完成标准；
- 指向 Research Brief 的链接。

这里只保存长期稳定的任务方向，不记录候选方法、论文清单或临时实验想法。

## 2. 阶段 Roadmap

由 AI 根据项目实际研究结构划分阶段，不使用跨项目固定阶段表。

阶段可以按照以下任一具有研究意义的方式组织：

- 研究方向或机制问题；
- 创新类型或方法家族；
- 论文复现与 Paper Repair 主线；
- Research Base 演进；
- Benchmark 版本；
- 其他能够解释研究依赖关系的结构。

每个阶段只需简洁记录：

- 阶段名称与目标；
- 进入条件；
- 退出条件；
- 当前状态；
- 对应的 Research Experiment Log volume；
- 对应的 Stage Summary；
- 必要时记录主路线和备用路线。

一个 Roadmap 阶段可以关联多个日志 volume；一个日志 volume 只记录当时所属阶段。日志开新卷不自动意味着 Roadmap 进入新阶段。

Roadmap 具体阶段由 AI 自主创建、合并、关闭或重排，但不得改写已经封存的历史阶段和证据链接。

## 3. 当前位置

始终保持这一部分最新，并限制为快速恢复研究所需的最少信息：

- 当前阶段；
- 当前状态，例如 ACTIVE、HUMAN_REVIEW_REQUIRED、TARGET_REACHED 或 TARGET_NOT_REACHED；
- 当前阶段的一句话认识；
- 下一个研究里程碑；
- 当前 Research Experiment Log；
- 最近一次 Stage Summary；
- 当前 Benchmark 版本；
- 必要时记录恢复研究所需的唯一入口。

这一部分不是实时仪表盘，不展开活跃 Candidate 队列、逐实验进度、详细阻塞原因或资源监控。

## 更新时机

只在以下事件发生时更新 `EXPERIMENT_LOG.md`：

- 首次建立研究 Roadmap；
- 进入、关闭、合并或切换 Roadmap 阶段；
- 新日志 volume 开启；
- Stage Summary 完成并形成路线裁决；
- Research Base 晋升导致研究方向发生实质变化；
- Benchmark 正式切换版本；
- 进入或恢复 `HUMAN_REVIEW_REQUIRED`；
- 进入 `TARGET_REACHED` 或 `TARGET_NOT_REACHED`。

普通实验启动、heartbeat、每个 epoch 结束或单个 Candidate 分数变化，不更新 Master Experiment Log。

## 渐进式读取顺序

AI 恢复研究时按以下顺序读取：

1. `EXPERIMENT_LOG.md`：确定研究目标、当前阶段和下一步入口；
2. 当前阶段对应的 `logs/research/volume_NNN.md`：恢复实验假设、结果和决策；
3. 最近的 `logs/summaries/volume_NNN_summary.md`：恢复阶段认识与路线裁决；
4. 只有需要核查运行事实或技术故障时，才读取 `logs/runs/EXXX/AYY.jsonl` 和 trainer artifact。

不得为了恢复上下文而默认加载全部历史 Run Event Log。

## 禁止写入

Master Experiment Log 不固定保存：

- Anchor Baseline、Research Base、Champion 和 Reference Baseline 的完整列表；
- 活跃 Candidate 队列；
- 逐实验一行摘要；
- 完整 Experiment Card；
- checkpoint、命令、配置或 artifact 清单；
- trainer stdout / stderr；
- heartbeat、逐 step 或逐 batch 指标；
- 可以从 Research Experiment Log、Stage Summary 或 Run Event Log 查到的重复内容。

如果 `EXPERIMENT_LOG.md` 已经大到无法快速判断“当前在哪、下一步读什么”，说明内容职责发生了膨胀，应把细节下沉到对应分卷日志。
