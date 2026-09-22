---
doc_id: candidate-priority-rules
doc_type: reference
title: Candidate Priority Rules
status: stable
summary: 定义 N candidate 的五维分类、结构默认优先级、全局硬门和 162 项 Gold/Silver/Hold/Reject/Invalid 组合。
read_when:
  - 生成或审查 N candidate 时
  - 判断伪创新、结构膨胀或候选执行优先级时
depends_on:
  - research-contract
  - benchmark-and-model-roles
activation:
  level: PHASE
  phases:
    - CANDIDATE_DESIGN
---

# Candidate Priority 三维规则

> 状态：已批准。本文及其 162 项组合表是 AutoResearch 的正式候选优先级规范。

本文是五维分类机器枚举、R/A/N 分流与 N candidate 优先级的唯一人读定义；其他协议只链接本文，Schema 与 Runtime 负责机械校验。

## 目录

1. 结论与五维体系
2. 判定顺序
3. Change Scope
4. 组件级矩阵
5. 协议级矩阵
6. 全方法矩阵
7. 各等级含义
8. 与既有规则的连接
9. 已批准的边界规则

## 1. 结论

实验仍完整记录五个维度：

```text
Evidence Class × Change Scope × Research Layer × Intervention Locus × Change Operator
```

但候选优先级只使用三个决策维度：

```text
Change Scope × Intervention Locus × Change Operator
```

- `Evidence Class` 负责前置分流：只有 N candidate 进入 Gold / Silver / Hold / Reject。
- `Research Layer` 负责描述研究贡献属于 L1 / L2 / L3 / L4，不参与机械排名。
- 三个决策维度产生 `Structural Default Priority（结构默认等级）`；它是最终优先级上限，证据、信息价值、成本、泄漏、公平性和可证伪性审查只能维持或降低它。

机器文件统一使用规范英文枚举。`candidate_priority_combinations.csv` 的分类列使用 `N`、`FULL_METHOD|COMPONENT|PROTOCOL`、`SYSTEM|DATA|FEATURE|BACKBONE|COMPONENT|BRANCH|LOSS|OPTIMIZATION|INFERENCE`、`ADD|REPLACE|DELETE|REWIRE|MERGE|SPLIT`；组合状态使用 `VALID|INVALID`，结构优先级使用 `GOLD|SILVER|HOLD|REJECT|INVALID`。本文的中文表格只用于人类阅读，不构成第二套机器值。

逐组合完整结果见 [candidate_priority_combinations.csv](../assets/candidate_priority_combinations.csv)。该表有 162 个组合：

| 结果 | 数量 |
|---|---:|
| Gold | 27 |
| Silver | 30 |
| Hold | 63 |
| Reject | 6 |
| Invalid | 36 |
| 合计 | 162 |

## 2. 判定顺序

必须按照以下顺序判定，不能用后面的高优先级抵消前面的硬门：

1. **建立参照物**：没有明确的当前 Research Base 时，Candidate 尚不可分类；先建立底座，而不是标成 Hold。
2. **语义有效性**：先检查 Change Scope 与 Intervention Locus 是否一致；矛盾组合直接标记 Invalid。
3. **单层归因**：每个实验只允许一个主要 Research Layer；信息激活与建模升级等跨层改动必须先拆开，否则 Hold。
4. **证据分流**：R/A 不评候选优先级；N candidate 继续。
5. **重新分类检查**：如果最近邻检索证明它是已有方法，应改为 R/A，而不是为了保留“创新”标签直接 Reject。
6. **全局 Reject 硬门**：数据泄漏、修改 Benchmark、test 调参、不公平预算、伪创新包装、无法形成单一主要假设。
7. **全局 Hold 硬门**：证据不足、没有可证伪预测、缺少公平实验条件或依赖未验证前提。
8. **三维结构表**：查出 Gold / Silver / Hold / Reject 的 Structural Default Priority。
9. **候选修正**：结合证据强度、预期信息增益、成本和剩余结构风险，只允许维持或降低结构默认等级。
10. **运行后转角色**：实验结束后不再称 Gold/Silver；转为 Research Base、Champion、Reference Baseline 或失败实验。

优先级关系不是分数相加，而是：

```text
Invalid / 未建立 Research Base > Reject 硬门 > Hold 硬门 > Structural Default Priority > 候选修正
```

### 候选修正规则

- 结构默认 Gold 只有在以下三项全部成立时才能保留 Gold：机制证据与近邻检索充分；实验能区分关键竞争解释或关闭主要不确定性；已经选择成本最低的判别实验且成本与信息价值相称。
- 结构默认 Gold 若仍可执行但上述任一项仅为中等，则降为 Silver；若关键证据、判别价值或执行依赖缺失，则降为 Hold。
- 结构默认 Silver 不能因证据很好而升级为 Gold；结构风险上限仍然有效。
- 结构默认 Hold/Reject 只能通过改变实验定义重新分类，不能靠高预期收益直接升级。

## 3. Change Scope 的作用

| Change Scope | 结构上限 | 默认处理 |
|---|---|---|
| 组件级 | Gold | 允许直接查“位置 × 算子”矩阵 |
| 协议级 | Silver | 只有全系统、数据、优化、推理四类位置有效；不得改变 Benchmark |
| 全方法 | Hold | N candidate 必须先拆成组件级；结构性新增/拆分可能直接 Reject |

注意：全方法 R/A 忠实复现不受“全方法 N 默认 Hold”限制，因为它不是创新候选排序。

## 4. 组件级矩阵

这是主要创新执行矩阵。

| Intervention Locus | 新增 | 替换 | 删除 | 重连 | 合并 | 拆分 |
|---|---|---|---|---|---|---|
| 全系统 | Invalid | Invalid | Invalid | Invalid | Invalid | Invalid |
| 数据 | Silver | Gold | Gold | Silver | Gold | Hold |
| 特征 | Silver | Gold | Gold | Gold | Gold | Silver |
| 骨干 | Hold | Gold | Gold | Gold | Gold | Hold |
| 组件 | Silver | Gold | Gold | Gold | Gold | Silver |
| 分支 | Silver | Gold | Gold | Gold | Gold | Hold |
| loss | Silver | Gold | Gold | Gold | Gold | Silver |
| 优化 | Silver | Silver | Silver | Silver | Silver | Hold |
| 推理 | Silver | Gold | Gold | Gold | Gold | Silver |

### 组件级矩阵的核心逻辑

- **替换优先**：替换保持结构数量不增加，对照最清晰，通常进入 Gold。
- **删除与合并优先**：容易归因且具有精简价值；但只有删除分支才能使用累计 0.5 pp 的精简退化额度。
- **新增默认 Silver**：先验证价值，但防止将涨分等同于底座晋升。
- **新增分支是 Silver**：允许首次实验；有效后必须补替换实验，通过 Branch Addition Gate 才能晋升。
- **拆分谨慎**：拆分通常增加路径与自由度；分支拆分、骨干拆分和数据拆分进入 Hold。
- **优化最高 Silver**：优化位置容易退化成调参循环，不因换了优化器名称就进入 Gold。

## 5. 协议级矩阵

协议级候选最高为 Silver。模型内部位置与“协议级”语义冲突，因此标记 Invalid。

| Intervention Locus | 新增 | 替换 | 删除 | 重连 | 合并 | 拆分 |
|---|---|---|---|---|---|---|
| 全系统 | Hold | Silver | Silver | Silver | Silver | Hold |
| 数据 | Hold | Hold | Hold | Hold | Hold | Hold |
| 特征 | Invalid | Invalid | Invalid | Invalid | Invalid | Invalid |
| 骨干 | Invalid | Invalid | Invalid | Invalid | Invalid | Invalid |
| 组件 | Invalid | Invalid | Invalid | Invalid | Invalid | Invalid |
| 分支 | Invalid | Invalid | Invalid | Invalid | Invalid | Invalid |
| loss | Invalid | Invalid | Invalid | Invalid | Invalid | Invalid |
| 优化 | Silver | Silver | Silver | Silver | Silver | Hold |
| 推理 | Silver | Silver | Silver | Silver | Silver | Hold |

协议级数据的全部算子都进入 Hold，因为增删替换、重连或合并都可能偷偷改变固定数据划分、标签边界、样本定义或采样口径。证明 Benchmark 未变后，才可释放为 Silver。

## 6. 全方法矩阵

全方法 N candidate 默认 Hold，要求先拆解。只有结构膨胀最明显的六个组合默认 Reject。

| Intervention Locus | 新增 | 替换 | 删除 | 重连 | 合并 | 拆分 |
|---|---|---|---|---|---|---|
| 全系统 | Reject | Hold | Hold | Hold | Hold | Reject |
| 数据 | Hold | Hold | Hold | Hold | Hold | Hold |
| 特征 | Hold | Hold | Hold | Hold | Hold | Hold |
| 骨干 | Reject | Hold | Hold | Hold | Hold | Reject |
| 组件 | Hold | Hold | Hold | Hold | Hold | Hold |
| 分支 | Reject | Hold | Hold | Hold | Hold | Reject |
| loss | Hold | Hold | Hold | Hold | Hold | Hold |
| 优化 | Hold | Hold | Hold | Hold | Hold | Hold |
| 推理 | Hold | Hold | Hold | Hold | Hold | Hold |

这里的 Reject 不代表研究方向永远无价值，而是**当前实验定义不可执行**：全方法同时在全系统、骨干或分支位置新增/拆分，无法用一个主要假设解释结果。拆成组件级替换、删除、重连或合并后，可以重新分类。

## 7. 各等级的实际含义

### Gold

- 通过全局硬门后优先运行。
- 典型结构是组件级替换、删除、重连或合并。
- Gold 只表示“最值得先验证”，不表示已经有效，更不表示已证明创新。

### Silver

- 值得运行，但存在新增成本、结构风险、调参风险或较弱归因。
- 仍必须遵守与 Gold 完全相同的 Benchmark、记录和公平比较要求。
- Silver 有效后可以成为 Research Base 候选，不是永久低一等。

### Hold

- 没有命中不可修复的 Reject 硬门，但当前定义不能直接开跑。
- 解除方式必须明确，例如拆成组件级、证明不改变 Benchmark、补充可证伪预测或设计替换实验。

### Reject

- 当前实验定义不应运行。
- 如果方向仍有价值，必须改变实验定义，而不是仅补一句解释后继续运行。

### Invalid

- 三维标签自身矛盾，不是研究优先级。
- 例如“组件级 × 全系统”，或者“协议级 × 模型分支”。

## 8. 与既有规则的连接

- `组件级 × 分支 × 新增 = Silver`：首次结果若提升超过 0.5 pp，只获得晋升候选资格；必须执行替换实验。
- `组件级 × 分支 × 替换 = Gold`：若替换有效且与新增方案相差不超过 0.1 pp，强制采用替换。
- `组件级 × 分支 × 删除 = Gold`：纳入同一次 Simplification Campaign；既要把最终联合删除结果与本次精简前的 Research Base 比较，也要把谱系累计退化与同一个 Simplification Anchor 比较，不能逐次重置 0.5 pp。
- 其他位置的删除虽然可能是 Gold，但不能消耗“删除分支专属”的 0.5 pp 退化额度。
- Gold/Silver/Hold/Reject 是开跑前优先级，不替代实验后的 Research Base 晋升确认。

## 9. 已批准的边界规则

以下边界已由研究者确认：

1. `组件级 × 数据 × 新增` 默认 Silver，而不是 Gold；原因是三维系统无法区分“激活已有闲置信息”和“接入高风险外部数据”。
2. `组件级 × 骨干 × 新增` 默认 Hold；要求先考虑替换骨干，避免变成双骨干堆叠。
3. `组件级 × 优化 × 任意算子` 最高 Silver；防止把常规优化器或 schedule 调整包装成高优先级创新。
4. `协议级 × loss` 标记 Invalid；loss 被视为模型目标/组件改动，而不是协议改动。
5. 所有全方法 N candidate 都不能直接开跑，必须先拆成组件级；其中 `全系统/骨干/分支 × 新增/拆分` 六种组合直接 Reject，而不是普通 Hold。
6. `协议级 × 数据 × 任意算子` 全部 Hold，只有证明数据划分、标签、样本边界和采样口径均不改变 Benchmark 后才能释放为 Silver。
7. 三维表给出的是结构优先级上限，而不是无条件最终等级；证据、信息增益和成本可以把 Gold 降为 Silver/Hold，但不能把 Silver 升为 Gold。
