---
doc_id: benchmark-and-model-roles
doc_type: reference
title: Benchmark and Model Roles
status: stable
summary: 定义固定评测契约、模型角色、比较目标、Research Base 晋升、seed 确认、精简交易与新增分支门。
read_when:
  - 建立或变更 Benchmark 时
  - 比较 Candidate、Research Base 与 Champion 时
  - 判断模型角色、底座晋升或结构精简时
depends_on:
  - research-contract
  - governance-and-autonomy
activation:
  level: PHASE
  phases:
    - BOOTSTRAP
    - CANDIDATE_DESIGN
    - RESULT_ROUTING
    - HUMAN_REVIEW
---

# Benchmark and Model Roles

## Contents

1. Purpose
2. Required Inputs
3. Canonical Terms
4. Benchmark Integrity and Versioning
5. Model Role Relationships
6. Research Base Promotion
7. Simplification Campaign
8. Branch Addition Gate
9. Required Writeback
10. Exceptions and Recovery
11. Related Modules

## 1. Purpose

本模块统一 Benchmark、模型角色、性能比较和 Research Base 晋升。所有 Candidate 的项目价值与晋升始终相对当前 Research Base 判断。

## 2. Required Inputs

- 冻结的 `RESEARCH_BRIEF.md`
- 当前 `BENCHMARK.md`
- Anchor Baseline、Research Base、Champion 与 Reference Baseline 的有效结果
- Candidate 的 Experiment Card 与完整可比结果

## 3. Canonical Terms

| Term | 含义 |
|---|---|
| `Benchmark` | 固定的数据划分、指标、随机种子、训练预算、评估脚本与约束集合 |
| `Anchor Baseline` | 长期保留的原始稳定模型，用于衡量累计提升 |
| `Research Base` | 稳定、通用、可组合、可复现且允许后续实验继续生长的当前底座 |
| `Champion` | 当前 Benchmark 下指标最好的合格模型 |
| `Reference Baseline` | 长期保留比较、但不作为后续父模型的强方法 |
| `Experimental Parent` | Paper Repair 中用于局部比较的直接实验父模型 |
| `Candidate` | 相对当前 Research Base 检验一个主要假设的实验变体 |
| `Core Comparison Target` | 结果解释时优先强调的 Research Base 或 Champion |
| `Promotion Confirmation` | Candidate 拟晋升 Research Base 时执行的额外确认 |
| `Simplification Campaign` | 针对同一底座的一组分支删除，作为一次原子精简判断 |

## 4. Benchmark Integrity and Versioning

一个 Benchmark 对应一个长期保留的 Anchor Baseline。数据划分、指标、seed、训练预算、早停、评估脚本和硬约束不得随 Candidate 改变。

发现数据泄漏、错误划分、标签或样本语义错误、评估脚本错误等根本有效性问题时：

1. 立即停止启动新的正式实验；
2. 进入 `HUMAN_REVIEW_REQUIRED`；
3. 人工确认修正后建立新的 Benchmark 版本；
4. 永久保留旧版本、旧实验和旧结果；
5. 先重跑 Anchor Baseline、当前 Research Base，以及与 Research Base 不同的 Champion；
6. 重新建立锚点后才能运行新 Candidate。

不同 Benchmark 版本的结果不得直接比较。Candidate 效果差、论文复现失败或暂时无涨点不是修改 Benchmark 的理由。

## 5. Model Role Relationships

一个研究时点：

- 只有一个当前 Research Base；
- 可以有多个 Reference Baseline；
- Champion 可以与 Research Base 相同，也可以不同；
- Research Base 晋升不替换 Anchor Baseline；
- Candidate 可以成为 Champion、Reference Baseline、Research Base 或失败实验。

“最好模型”只表示 Champion。高分、专用、复杂或难以继续扩展的模型可以成为 Champion，但不能因此自动成为 Research Base。

`finish-run` 根据 artifact 指标自动判定 Champion 与 Core Comparison Target，
并为 Champion 变化写入 role event；Research Base 与 Reference Baseline
分别通过 `PROMOTE_RESEARCH_BASE` 和 `ASSIGN_REFERENCE_BASELINE` 提案授予。

每个 Candidate 必须冻结：

- 当前 Research Base；
- 同一 Benchmark 版本；
- 必要时的 Experimental Parent；
- Core Comparison Target。

结果表始终保留 Research Base 和 Champion。百分比型主指标下：

- 二者相差不超过 1.0 个绝对百分点：核心比较 Research Base；
- 二者相差超过 1.0 个绝对百分点：核心比较 Champion。

非百分比指标的等价阈值由 Benchmark 预登记。Core Comparison Target 不改变晋升锚点：底座晋升仍比较 Research Base，Champion 更新仍要求超过当前 Champion。

## 6. Research Base Promotion

Research Base 的标准条件是：

- 取得 Effective Improvement；
- 结果可复现；
- 结构稳定；
- 对研究主线具有通用性；
- 能与后续候选组合；
- 仍适合作为清晰父模型。

小幅组件替换、架构改进或结构精简均可获得晋升资格；随意叠加分支和难以归因的结构膨胀需要额外审查。

非精简型 Candidate 在百分比主指标上必须相对当前 Research Base 提升超过 0.5 个绝对百分点。非百分比指标的等价筛选线由 Benchmark 冻结。

普通探索默认一个 seed。Benchmark 冻结时必须显式登记 `promotion_confirmation_policy`：

- `TWO_SEEDS`：快跑默认；首次达标后追加两个不同 seed 的完整可比 attempt。三个 seed 都必须优于对应 Research Base seed，平均提升仍超过 0.5 个百分点。
- `ONE_CONFIRM_SEED`：慢跑默认；首次达标后追加一个不同 seed 的完整可比 attempt。两个 seed 都必须优于对应 Research Base seed，平均提升仍超过 0.5 个百分点。
- `SINGLE_RUN_JUSTIFIED`：仅当单次完整训练成本超过 Benchmark 冻结的绝对时长或成本门槛时允许，并必须书面登记理由。性能达标后只取得 provisional 晋升资格。

`SINGLE_RUN_JUSTIFIED` 晋升事件必须标记 `single_seed_provisional: true`。下一个以该底座创建的实验若产生与晋升方向矛盾的证据，Controller 必须先把晋升复核写为决策债务并完成复核，再选择新的正式实验。不得通过减少 epoch、减少训练数据或改变评测口径制造“快速验证”。

通过性能侧确认只是必要条件。结构不稳定、不通用、不可组合或难以继续研究的模型仍可只保留为 Champion 或 Reference Baseline。

## 7. Simplification Campaign

只有删除模型分支可以使用 Simplification Trade-off。百分比主指标允许的绝对退化总额最多为 0.5 个百分点，且不得突破任何 Hard Constraint。

同一次精简中：

- 可以分别运行删除 A、删除 B 等诊断实验；
- 最终晋升必须把全部计划删除后的模型与精简前同一个 Research Base 比较；
- 删除次数不能分别消费 0.5 个百分点；
- 整条后续精简谱系还必须与最近一个非精简型 Research Base，即 Simplification Anchor，累计比较。

精简结果晋升为新 Research Base 不重置 Simplification Anchor。只有新的非精简 Effective Improvement 晋升，或 Benchmark 正式变更，才能建立新锚点。

## 8. Branch Addition Gate

新增分支即使单次提升超过 0.5 个百分点，也只取得晋升候选资格。

晋升前必须尝试用新分支替换功能最相似的旧分支：

- 替换方案相对 Research Base 提升超过 0.5 个百分点；
- 且与新增方案相差不超过 0.1 个百分点；
- 则强制采用替换，并将改动归类为 `REPLACE`。

当前 Research Base 已经是不含新分支的对照，因此不重复运行“删除新分支”消融。只有替换无法保留增益，且新分支具有不可替代的独立功能时，新增形式才可进入 Research Base；否则只保留为 Champion 或 Reference Baseline。

## 9. Required Writeback

- Benchmark 版本和比较锚点
- 每个模型获得或失去角色的事件
- Candidate 相对 Research Base、Champion 与 Experimental Parent 的结果
- Promotion Confirmation attempts
- Simplification Anchor 与 Campaign 累计结果
- Branch Addition Gate 的替换实验和最终裁决

## 10. Exceptions and Recovery

Benchmark 失效时执行第 4 节，不得在旧版本上静默修复。训练失败与 attempt 重试由 [Experiment Playbook](experiment_playbook.md) 管理。

## 11. Related Modules

- [Research Contract](research_contract.md)
- [Governance and Autonomy](governance_and_autonomy.md)
- [Candidate Priority Rules](candidate_priority_rules.md)
- [Experiment Playbook](experiment_playbook.md)
- [Research Graph Protocol](research_graph_protocol.md)
