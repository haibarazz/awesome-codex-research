---
name: cds-method-innovation
description: Guide a complete baseline-first ML or computational data-science method-innovation project, from workspace and direction discovery through finding and running common and recent baselines, diagnosing failures, interrogating candidate novelty, designing and executing experiments, and preserving research history. Use for this integrated workflow or to resume one of its stages. Does not include full literature review, manuscript writing, or unattended autoresearch.
---

# CDS Method Innovation

一个独立 Skill 完成这条研究工作流。相关指引、初始化、方向日志和实验日志都在本包内；无需安装其他研究 Skill。baseline 指作为比较起点的现有方法，benchmark 指本项目约定的数据、指标和评价协议。

## 开始与接续

先确认研究项目目录，读取已有概况、方向决策及与当前问题相关的实验结果。项目目录是研究产物的位置；本 Skill 目录只放指引和工具，不在其中写研究记录。

依据已有证据定位当前阶段，不强迫从头重做。已有的方向、协议或运行必须检查内容和可比性后复用，不能因文件存在便宣称验证完成。缺失信息只问当前决定真正需要的部分。

只读取当前阶段的指引。首次需要读取或写入历史时，同时读 [research-records.md](references/research-records.md)。引用相对所在文档解析；命令中的 `SKILL_DIR` 是本文件所在目录的绝对路径，`PROJECT_DIR` 是用户的项目目录，运行前替换为实际路径。

在每次执行命令的同一 shell 中先设置下面两个变量，替换为本次真实路径；不要假定上一次工具调用保留环境变量：

```sh
SKILL_DIR="/absolute/path/to/cds-method-innovation"
PROJECT_DIR="/absolute/path/to/research-project"
```

## 按研究进展选择阶段

| 阶段 | 何时进入与必须读取的指引 | 产出与下一步 |
|---|---|---|
| 1. 初始化 | 新项目或需要补记录空间；[project-init.md](references/project-init.md) | 最小项目概况和两类日志；有现成项目则接续 |
| 2. 寻找方向 | 问题尚不清楚或需要重新选题；[direction-discovery.md](references/direction-discovery.md) | 比较方向、证伪条件、选择/放弃理由；研究者选定后建立 baseline |
| 3. Baseline 与 benchmark | 缺乏可信比较或需补方法；[baseline-benchmark.md](references/baseline-benchmark.md) | 查找、拆解并实际运行 5–10 常见方法＋约 3 近期方法；记录结果和失败 |
| 4. 创新质询 | 有 baseline 观察或候选；[innovation-grill.md](references/innovation-grill.md) | A 找可改进处；B 多轮审查候选；分开记录“值得实验”与“是否新颖” |
| 5. 设计与验证 | 已选择要检验的候选；先读 [experiment-design.md](references/experiment-design.md)，执行前读 [execution-and-feedback.md](references/execution-and-feedback.md) | 形成方案并在委托范围内实施、运行、记录；结果回到阶段 4 |

阶段不是另一个 Skill 的调用，也不是机器状态。不要只把任务转交给一个不存在的外部研究工具；使用包内指引和当前可用的检索、文件、编码及训练工具完成工作。

## 贯穿全程的约束

- 完整工作流中，实质方向选择和每次真实运行自动入日志；方向改变保留旧版本。纯讨论、解释或预览只返回草案，不写文件。
- 常见方法包含简单方法及项目现有方法，另加近期方法；重复方法、seed、重试不增加独立方法数。数量不足如实报告，不能用论文分数或小规模检查凑数。
- Baseline 和近期方法既是比较对象，也是创新思路的来源；日常主 baseline 不取代整个方法组合和强比较方法。
- 训练/开发集用于选方法和找问题。最终测试集参与方向或模型选择后，不再称为独立确认；改为探索证据并另找确认数据。
- 发散讨论和质询均一轮一个关键问题，等待真实用户回答。AI 推荐不能自动变为作者决定；不要模拟研究者答案推进全流程。
- 查找/设计请求不授权训练。执行委托、范围和预算明确时继续实施，不反复审批；新增付费资源、重要成本不明或实质扩范围时先询问。
- 只执行本次委托范围内的循环。当前验证完成后说明下一步选择；研究方向取舍、质询回答或新预算需要用户决定时停下，不无限自动搜索和训练。
- 不含 `autoresearch`，不依赖意图对齐 Skill，不在此包实施完整文献综述。为选 baseline 和判断近邻做必要的针对性检索；无检索/训练工具时报告具体缺口，不伪造完成。

## 每次收口

说明当前阶段、实际完成了什么、证据和记录在哪里、仍有哪些缺口及下一步。只有配置或计划时写“尚未运行”；比较不充分时不宣布创新成立。更新已有项目概况的当前阶段和实际产物链接，保留历史记录与原始证据。

## 简短示例（虚构）

研究者已有九个方法的开发集记录：七个完整运行、一个 OOM、一个尚未运行。先核查协议与日志，接续阶段 3 或按其请求进入阶段 4，不重新初始化或声称九个都跑完。若长文本退化可能来自类别组成，先问这一混杂是否排除；不能直接把加 gate 写成创新。研究者选择判别实验后才设计、执行，并保留原候选和新结果。

包内来源与微调说明见 [sources.md](references/sources.md)，仅在审计来源或修改本 Skill 时读取。
