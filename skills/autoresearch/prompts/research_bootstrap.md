---
doc_id: research-bootstrap
doc_type: prompt
title: Research Bootstrap Prompt
status: stable
summary: 检查或安全初始化代码库，读取数据与项目状态，生成 Codebase/Dataset Profile，提出 3–5 个高价值问题并冻结 Research Brief。
read_when:
  - 首次启动 AutoResearch 时
  - Research Brief 缺失或需要正式重建时
depends_on:
  - research-contract
  - governance-and-autonomy
activation:
  level: PHASE
  phases:
    - BOOTSTRAP
---

# Research Bootstrap Prompt

当 AutoResearch 项目首次启动、启动状态不完整，或者中断后的项目需要恢复时，使用本 Prompt。

## 目录

- [核心目标](#核心目标)
- [必须读取](#必须读取)
- [0. 检查并准备代码库](#0-检查并准备代码库)
- [1. 恢复既有状态](#1-恢复既有状态)
- [2. 先检查，后提问](#2-先检查后提问)
- [3. 生成 Dataset Profile](#3-生成-dataset-profile)
- [4. 建立 Research Brief 草案](#4-建立-research-brief-草案)
- [5. 提出 3–5 个高价值问题](#5-提出-35-个高价值问题)
- [6. 修订并请求最终确认](#6-修订并请求最终确认)
- [7. 冻结并移交](#7-冻结并移交)
- [输出契约](#输出契约)

## 核心目标

先建立可运行且可追溯的代码底座，再把用户提供的数据集和研究意图转化为三个项目级文档：

1. 记录代码根、来源、入口与预检的 `CODEBASE_PROFILE.md`；
2. 简洁、具有证据依据的 `DATASET_PROFILE.md`；
3. 经过用户确认并冻结的 `RESEARCH_BRIEF.md`。

Bootstrap 是自动化研究开始前唯一强制进行的人机目标对齐阶段。在本阶段不得启动论文驱动的创新探索或正式实验。

## 必须读取

开始执行前，读取：

- `../references/research_contract.md`；
- `../references/governance_and_autonomy.md`；
- `../references/reproflow_code_contract.md`；
- `../templates/codebase_profile.md`；
- `../templates/dataset_profile.md`；
- `../templates/research_brief.md`；
- 项目中已经存在的 `DATASET_PROFILE.md`、`RESEARCH_BRIEF.md`、Benchmark、Roadmap 和实验日志。

当本 Prompt、已有项目文档与治理模块冲突时，先按 Research Contract 定位权威规则；冻结契约需要变更时执行正式版本化。

## 0. 检查并准备代码库

在读取数据和向用户提问前，调用 `scripts/bootstrap_codebase.py ... inspect`，不得仅凭目录是否非空判断已有代码。

- `REPROFLOW_PRESENT`：读取现有 Profile，或通过 bootstrap 命令接管并补齐 provenance；
- `EXISTING_CODE`：禁止引入 ReproFlow，使用 Codebase Profile 模板记录现有架构和最小 adapter；
- `NO_CODE`：自动调用 bootstrap 命令引入默认 ReproFlow，不再请求用户选择代码框架。

Bootstrap 只允许创建代码底座、provenance 和 Codebase Profile，不得安装未授权依赖、修改用户数据、创建实验节点或形成性能结论。完成后运行 `validate`；数据配置、doctor 和 one-epoch Technical Smoke 按 ReproFlow Contract 在正式 Baseline 前完成。

## 1. 恢复既有状态

首先判断当前是新项目还是恢复中的旧项目。

- 如果不存在 Research Brief，初始化 Bootstrap。
- 如果存在 `DRAFT` Brief，保留已经确认的内容，只继续解决真正影响研究的缺口。
- 如果存在 `FROZEN` Brief，且用户没有改变研究目标，不得重复进行对齐提问。先调用 AutoResearch Runtime `inspect`，按机器返回的 `current_phase`、`last_trigger`、`active_run` 和剩余预算恢复；不要从文件存在性或旧 handoff 猜测继续点。
- 如果用户要求实质性修改已经冻结的目标，创建一个新的 `DRAFT` 版本。不得直接修改原有 FROZEN Brief；替代版本获得确认前，也不得把旧版本标记为 `SUPERSEDED`。

不得丢弃已有证据，也不得静默重启研究历史。

## 2. 先检查，后提问

向用户提问前，先读取用户提供的数据集、项目代码、配置、已有结果和可用文档。

检查深度只需足以识别：

- 当前可能是什么数据和任务；
- 可能的标签、目标、输入、实体、分组或时间轴；
- 已有的数据划分或评估线索；
- 已有 Baseline 结果，如存在；
- 明显的数据质量、访问、泄漏或可比性风险；
- 哪些关键决策无法从项目证据中自行恢复。

除已授权的安全 Codebase Bootstrap 外，这里只允许只读检查和低成本技术预检。不得根据启动检查宣称模型性能、方法有效性或创新性。

## 3. 生成 Dataset Profile

使用 Dataset Profile 模板，在项目中生成或更新 `DATASET_PROFILE.md`。

内容必须简洁，并根据当前数据集随机应变。只记录会实质影响 Research Brief、Benchmark 或实验设计的信息。

必须区分：

- `Observed Facts`：直接核验的事实；必要时附上证据路径；
- `Inferred Findings`：必要推断，并写明依据和置信度；
- `Risks / Pending`：可能改变研究决策的未解决问题。

不得把 Dataset Profile 写成完整数据字典或长期数据分析报告。

## 4. 建立 Research Brief 草案

向用户追问前，先从用户初始描述、Dataset Profile、代码和已有项目文档中提取全部可用信息。

使用 Research Brief 模板生成或更新 `RESEARCH_BRIEF.md`，状态设为 `DRAFT`。自动填写已经确定的内容，只把真正影响研究的未决事项标记为 `PENDING`。

最终草案必须明确：

- 研究目标；
- 唯一一个 Primary Metric，以及可由机器判断的 Performance Target；
- Baseline 状态与已知结果，如存在；
- 零个或多个明确声明的 Hard Constraints；
- 至少一个 Research Budget 硬上限；
- AI 被允许和禁止执行的行动；
- 最终确认状态。

Research Brief 中不得写入候选方法、论文列表、实验计划、创新声明、数据集详细统计或运行结果。

## 5. 提出 3–5 个高价值问题

完成项目检查和草案自动填写后，在一次对齐轮次中向用户提出 3–5 个简洁问题。

每个问题都必须解决一个会实质改变以下至少一项内容的决策：

- 研究目标；
- 完成标准；
- Benchmark；
- 资源边界；
- 授权边界。

每个问题都应：

- 清楚指出尚未解决的决策；
- 简要说明它为什么会影响研究；
- 在适合时提供推荐答案或默认选择。

不得询问能够从数据集、代码、日志或已有文档中自行查明的事实，也不得为了凑足问题数量而提出无价值问题。如果用户的初始描述已经非常完整，应使用这些问题审查仍可能存在歧义的完成条件、硬约束、预算或权限。

不得要求用户选择论文、模型组件、候选实验或研究路线；这些应由 AI 在启动后自主决定。

## 6. 修订并请求最终确认

根据用户回答更新 Dataset Profile 或 Research Brief：

- 数据证据和不确定性写入 Dataset Profile；
- 目标、完成标准、预算和权限写入 Research Brief。

随后向用户提供一份简短的最终确认摘要，至少包括：

- 最终研究目标；
- Primary Metric 与 Performance Target；
- Hard Constraints，或者明确声明没有登记 Hard Constraints；
- 当前生效的 Research Budget 硬上限；
- 最重要的允许行动和禁止行动；
- 任何明确移交给下一阶段处理的 `PENDING` Benchmark 项。

只请求用户对 Research Brief 进行一次明确的最终确认。不得要求用户逐实验或逐研究决策审批。

## 7. 冻结并移交

获得用户明确确认后：

1. 将 Research Brief 从 `DRAFT` 改为 `FROZEN`；
2. 记录确认事实并保留全部已确认内容；
3. 不得静默修改已经冻结的目标、性能阈值、预算或授权边界；
4. 如果 Benchmark 或研究状态文档尚不完整，移交给相应初始化阶段；
5. 只有必须的 Benchmark 和比较状态准备完成后，才能启动自主研究循环。

从此以后，除 Research Contract 预先定义的 `HUMAN_REVIEW_REQUIRED` 硬门外，不再要求中间人工审批，并持续执行直到：

- `TARGET_REACHED`；或
- `TARGET_NOT_REACHED`。

## 冻结硬门

只有同时满足以下条件，才能把 Research Brief 标记为 `FROZEN`：

- `CODEBASE_PROFILE.md` 已存在，且现有代码已完成接口映射，或 ReproFlow bootstrap 已通过 validate；
- `DATASET_PROFILE.md` 已存在，并且重要不确定性已经显式暴露；
- 研究目标和目标场景已经足够清楚，可以支持自主决策；
- 已指定且只指定一个 Primary Metric；
- Performance Target 可以由机器判断；
- Hard Constraints 已列出，或明确声明不存在；
- 至少登记了一个 Research Budget 硬上限；
- 允许和禁止执行的行动已经明确；
- 用户已经进行一次明确的最终确认。

Bootstrap 阶段可以把 Benchmark 引用标记为 `PENDING`，但 Benchmark 完成并冻结前不得启动正式实验。

## 禁止事项

- 最终确认与 Benchmark 冻结前，不得启动正式实验。
- 已有代码时不得 clone ReproFlow、覆盖文件或借接入过程强制迁移架构。
- 不得擅自推断会实质改变目标、性能阈值、预算或权限的用户偏好。
- Research Brief 冻结后，不得反复向用户进行启动对齐提问。
- 不得把数据集详细分析复制进 Research Brief。
- Bootstrap 期间不得预选研究方法或制造创新声明。
- 不得覆盖已经冻结的 Brief，也不得删除既有研究历史。

## 必须输出

Bootstrap 结束时必须得到：

- 项目级 `CODEBASE_PROFILE.md`；
- 项目级 `DATASET_PROFILE.md`；
- 项目级 `RESEARCH_BRIEF.md`；
- 一份简短的最终确认请求，或者在 Brief 已冻结时移交给下一研究阶段。
