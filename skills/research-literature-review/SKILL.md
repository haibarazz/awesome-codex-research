---
name: research-literature-review
description: 面向信息系统计算设计科学（CDS）研究，根据用户的数据、研究情境与研究问题，分别识别问题／理论视角和技术／算法两条文献对话线，检索并核验全文，制作可追溯的文献对话地图，最终澄清研究的最近邻、理论祖先、方法缺口与可辩护定位。适用于选题定位、相关工作规划、方法定位和后续综述；核心不是代写文献综述。
---

# CDS 研究定位与文献对话

本 Skill 的首要任务是回答：**这项研究必须与哪些文献对话，为什么，以及它可能站在什么位置？** 文献综述只是定位完成后的可选写作产物。

## 默认工作流

**研究锚点 → 两条文献线 → 检索与筛选 → 核验全文 → 单篇对话地图 → 研究定位 → 可选综述。**

1. **建立研究锚点。** 写清数据对象、分析单位、场景、行动者、时间结构、标签／结果、拟回答的研究问题，以及当前最不确定的贡献主张。研究问题用现象或决策困难表述，不先写成“提出某模型”。
2. **生成问题／视角线。** 读取 [problem-perspective-prompt.md](references/problem-perspective-prompt.md)，先从用户研究提出候选现象、领域与理论文献流，再生成查询式。初筛后通常保留 1–2 条核心流。
3. **生成技术／算法线。** 读取 [technical-method-prompt.md](references/technical-method-prompt.md)，从数据结构、计算任务和设计挑战推出候选技术流与查询式；通常保留 2–4 条，不能按模型名堆砌。
4. **检索并按对话角色筛选。** 同时寻找最近邻、理论／技术祖先、桥接论文和关键对照。摘要只用于初筛；记录查询、来源、日期、纳入理由与尚未覆盖的相邻词。
5. **取得并核验全文。** 读取 [paper-positioning-card.md](references/paper-positioning-card.md)。优先复用本地文件；缺失时使用合法的开放来源或用户已有访问权限。核对标题、作者、版本、页数和正文身份后再阅读。
6. **逐篇制作对话地图。** 重点阅读 Introduction、Literature Review／Related Work、理论与方法概览，复原每篇论文怎样组织问题线和技术线；重要判断附原文位置，并区分作者明示与阅读者归纳。
7. **综合研究定位。** 读取 [research-positioning.md](references/research-positioning.md)，说明用户工作继承什么、连接什么、与最近邻有何具体差异、哪些空间尚未被覆盖，以及下一轮需要补检索或补证什么。只有用户明确需要时，才把定位材料改写成文献综述。

## 推荐工作目录

```text
positioning/
├── research-brief.md
├── problem-perspective/
│   ├── prompt.md
│   ├── search-log.csv
│   └── stream-map.md
├── technical-method/
│   ├── prompt.md
│   ├── search-log.csv
│   └── stream-map.md
├── papers/                 # 已核验全文
├── dialogue-maps/          # 每篇一张定位卡
└── research-positioning.md
```

`search-log.csv` 的最小字段为：`paper_id,citation,doi_or_url,source,version,local_file,status,dialogue_role,stream,reason`。状态至少区分 `candidate`、`excluded`、`pending_fulltext`、`verified`、`mapped`；排除必须写理由。同一版本跨文献线沿用稳定 ID 和已核验全文，但可在不同 stream 中承担不同角色。

## 产出门槛

- 两条线都从同一份研究锚点出发，技术线必须服务研究问题，问题线也要能解释为何需要某类制品。
- 每条核心文献流都回答：已经知道什么、留下什么问题、与用户工作是什么关系、下一轮怎样搜索。
- “最相关”不等于关键词最像。最近邻共享问题与贡献比较面；祖先提供理论或技术机制；桥接论文连接两条线；对照论文帮助说明为何不用更常见的方案。
- 不能用摘要完成单篇定位，也不能把作者未回顾的技术补写成作者的缺口。推论标为“阅读者归纳”。
- 未完成系统检索时不声称穷尽性；未找到最近邻不等于没有最近邻；预测增益不自动证明构念、机制、因果或真实部署价值。
- 注意力、学习图和潜在表示默认是模型内代理。理论进入设计应能追到表示、约束、损失、模块或人机流程，而不只是写在动机里。

需要校准输出时，读取 [examples/index.md](examples/index.md)，只选与当前定位机制最接近的 few-shot，不机械复制其领域名称或结论。
