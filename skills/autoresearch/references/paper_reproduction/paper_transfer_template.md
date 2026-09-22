---
doc_id: paper-transfer-reference
doc_type: reference
title: Paper Transfer Reference
status: stable
summary: 提供论文机制、全文证据、项目接口、R/A/N Delta Ledger 和实验交付的完整参考结构。
read_when:
  - 需要生成完整论文迁移研究包时
depends_on:
  - research-contract
  - paper-reproduction-and-innovation
activation:
  level: ON_DEMAND
---

# 论文机制迁移与交付模板

## 目录

1. Innovation Brief
2. manifest.csv
3. 逐篇证据卡
4. 调研与创新点带入.md
5. 实验设计与优先级.md

## 1. Innovation Brief

```markdown
# Innovation Brief

## 目标任务
- 输入：
- 输出：
- 标签与时间窗口：
- 评价单位：

## 当前最强基线
- 模型与参数化：
- 数据与划分：
- loss 与训练预算：
- 主结果：
- 已知失败：

## 可替换组件
- 数据/采样：
- 表示/架构：
- PEFT/参数化：
- objective/optimization：
- memory/routing/fusion：
- inference/evaluation：

## 公平比较合同
- 必须固定：
- 允许调节：
- 主指标：
- 机制指标：
- 资源上限：
- 禁止主张：
```

## 2. manifest.csv

建议字段：

```text
paper_id,title,authors,year,venue,acceptance_type,official_url,pdf_url,
local_pdf,fulltext_path,version_scope,sha256,pages,size_bytes,
pdf_magic,mime_type,pdf_parse_status,text_extract_status,text_chars,
verification_tool,verification_result,download_status,review_status,
inclusion_reason,exclusion_reason
```

## 3. 逐篇证据卡

```markdown
# Pxx：论文标题

## 来源与版本
- 正式接收证据：
- 本地全文版本：
- PDF / hash / 页数：
- PDF file type / parser / 抽取验证：
- 验证工具、结果与错误：

## Mechanism Fingerprint
- Problem：
- Original baseline：
- Intervention locus：
- State and signal：
- Operator / parameterization：
- Objective / constraint：
- Training flow：
- Inference flow：
- Claimed mechanism：
- Dependencies and cost：

## 正文证据
1. p./Eq./Alg./Table：
2. p./Eq./Alg./Table：
3. p./Eq./Alg./Table：
4. p./Eq./Alg./Table：
5. p./Eq./Alg./Table：

## 关键结果、消融与限制
- 主结果：
- 机制消融：
- 失败或未验证范围：

## 一段话描述论文流程与创新
[连续段落，覆盖流程、创新位置、训练/推理变化、基线差异和证据。]

## 项目接口映射
| 论文组件 | 目标项目组件 | 是否同构 | 适配变化 | 机制是否保留 |
|---|---|---:|---|---:|

## Delta Ledger
| 原论文操作 | 目标项目操作 | 仅为兼容所必需？ | 改变函数映射/目标/自由度？ | R/A/N 依据 |
|---|---|---:|---:|---|

## 迁移类型
R（算法不变，仅换目标数据/标签实例） | A（必要且功能等价的接口适配） | N candidate | 不可迁移

## 一段话描述完整带入
[连续段落，写清目标基线、替换位置、信号流、公式/伪代码、训练/推理步骤和公平比较。]

## 机制保持测试
- 去掉新算子后退化为什么？
- 原信息流是否存在？
- 接口适配和机制修改分别是什么？
- 支持机制的结果是什么？
- 证伪结果是什么？
- Transfer fidelity：high | medium | low

## 对应主实验
[可迁移时引用实验 ID；不可迁移时写 screened-out / replacement ID]
```

## 4. 调研与创新点带入.md

```markdown
# 调研与创新点带入

## 一、研究合同
[Innovation Brief 摘要]

## 二、检索、纳排与版本口径
- 检索日期与数据库：
- 纳入/排除标准：
- 候选数、入选数和替换数：
- 作者版本与 camera-ready 的区别：

## 三、方法版图
按实际创新位置组织，不按论文逐篇堆叠：
- 数据与采样
- 表示与架构
- PEFT 与参数化
- 目标函数与优化
- RL / post-training
- memory / routing / fusion
- 校准、时序与推理

## 四、逐篇调研与完整带入

### Pxx 论文标题
**论文方法与创新：** [完整段落]

**在目标项目中的完整带入：** [完整段落]

**分类：** R/A/N/不可迁移

**证据锚点：** [页码、公式、算法、表格]

**Transfer fidelity：** high/medium/low

## 五、跨论文碰撞与互补
- 机制重复：
- 互补机制：
- 不可直接组合的冲突：

## 六、事实、推断与尚未验证假设
```

## 5. 实验设计与优先级.md

```markdown
# 实验设计与优先级

## 一、公平比较合同
- 固定的数据、切分、基线、预算、评价代码：
- 统一调参协议：
- 泄漏与版本控制：

## 二、逐篇主实验

### Exx：实验名
- 来源论文 / 类型 R-A-N：
- experiment_decision：Go | Conditional Go | Hold | No-Go
- novelty_status：not_claimed | candidate | unclear | supported_by_current_search | pseudo_innovation
- 研究问题：
- 主假设：
- 竞争解释：
- 唯一主要改动：
- 固定项 / 可调项：
- smoke / full run / seeds：
- 主指标 / 机制指标 / 效率指标：
- 强基线 / 负对照 / 消融：
- 支持预测：
- 证伪预测：
- No-Go：
- 资源、依赖和 artifact：
- 允许 / 禁止措辞：

## 三、新方法扩展候选
- 证据阶段：pre-experiment | results-grounded | deferred
- 最窄创新句：
- 最近近邻与逐项差异：
- 近邻证据账本：查询、日期、数据库、主来源 URL、版本、全文路径、方法锚点
- 新估计对象/信号/约束/参数化/优化过程：
- 不可简化回已有方法的理由：
- 判别实验：

## 四、独立审查
| 实验 | Fidelity | 伪创新？ | 技术创新？ | 关键缺陷 | 判别实验 | experiment_decision | novelty_status |

## 五、优先级
| Rank | 实验 | experiment_decision | novelty_status | 信息增益 | 成本 | 前置依赖 | 排序理由 |

## 六、首批执行队列
1. 最小 smoke：
2. 机制验证：
3. 完整训练：

## 七、停止规则
- 哪个结果关闭整条路线：
- 哪个结果触发下一版本：
- 何时需要重新检索近邻工作：
```
