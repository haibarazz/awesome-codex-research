# 包内来源与微调说明

本包按用户确认的单 Skill 交付方式整合。以下是开发来源，不是运行依赖；已将需要的内容和脚本实际纳入本目录。来源名称用于追溯，不要求在其他机器上存在这些包。

| 本包内容 | 项目内直接来源 | 采用方式与保留的判断 |
|---|---|---|
| 项目初始化 | research-project-init 的入口、intake guidance、脚本及模板 | 融合改写指引、原样复制脚本/模板；最小化、不覆盖、不编造历史 |
| 方向探索 | cds-research-direction-discovery | 微调为内部阶段；保留竞争方向、作者选择、可证伪观察、历史恢复 |
| baseline 阶段及两个详解 | cds-baseline-and-benchmark | 保留方法数量、机制核验、公平协议、真实运行、用途分类、失败及测试隔离；改成本地引用 |
| 两模式质询及创新审查 | cds-innovation-grill | 保留文档定位、一轮一问、R/A/N、最近邻等价检查及实验决定/新颖性分列 |
| 实验设计及方案模板 | cds-research-design | 复制主要科研内容，微调为同包阶段；保留主张/反证、公平对照、消融、重复与资源设计 |
| 方向记录 | research-paper-log 的入口、content guidance、脚本及模板 | 融合简明使用说明，复制脚本/模板并补明细目录校验；版本保留、决策归属与放弃理由 |
| 实验记录 | research-experiment-log 的入口、content guidance、脚本及模板 | 融合字段指引，复制脚本/模板并补比较及运行目录校验；experiment/run 区分、每次失败和重试、证据链接 |
| 实施与反馈 | 上述 baseline 执行纪律、实验设计与两类日志 | 融合为执行阶段；方案落地、最小证伪、相容协议、失败保留和结论收缩 |

上述三个新阶段来源包本身已经融合 academic-brainstorming、cds-research-ideation、reference-paper-deconstructor、academic-grill-with-docs 及 llm-algorithm-innovation 的有关方法。这里使用这些项目内整合稿，不声称本轮重新审计所有间接上游包。

本次新增的组织规则是：单入口按阶段加载、包内脚本路径、研究产物与 Skill 目录分离、无需外部 Skill。这些是用户的交付要求与 skill-creator 的包装原则，不冒充新科研方法。5–10 常见＋约 3 近期方法和两个质询模式来自用户要求，不是普适的质量阈值。

所有脚本只使用 Python 标准库；不包含训练框架、数据或模型。实际检索和训练仍需要运行环境提供工具与资源。示例为虚构，不能当作已执行的研究证据；脚本校验成功也不证明科研质量。
