---
name: academic-paper-polisher
description: 润色既有英文学术论文或用户直接粘贴的英文论文段落，按授权范围处理理论边界、论证结构、参考文献真实性、英文表达、LaTeX 安全和 AI 写作痕迹。用于修改、润色、重写或审计已有内容；不用于从零撰写论文。
---

# 英文学术论文综合润色

## 目标

在不改变研究事实、证据和理论边界的前提下，改善既有英文学术论文的论证结构、段落逻辑、英文表达和 LaTeX 源码质量，核查涉及的参考文献是否真实存在，并减少程式化的 AI 写作痕迹。

本 Skill 是三份既有规则的编排层。三份规则已原样包含在 `references/` 中，执行时按任务需要加载，不得为了统一措辞而改写其具体内容。

## 组成文件

执行任务时，根据实际修改范围读取以下文件：

1. [`references/ml-paper-writing/SKILL.md`](references/ml-paper-writing/SKILL.md)
   用于检查 contribution、理论定位、claim 与 evidence 是否匹配、段落叙事以及 `mechanism`、`proxy`、`association`、`causality` 等表述边界。仅采用其中与既有稿件修改有关的指导，不继承从零生成整篇论文或主动扩展研究内容的行为。
2. [`references/latex-paper-en/SKILL.md`](references/latex-paper-en/SKILL.md)
   用于选择 grammar、sentences、logic、literature、expression、translation、deai、experiment、abstract、format 或 compile 等模块，并遵守 LaTeX 源码保护和最小范围修改要求。
3. [`references/academic-writing-deai.md`](references/academic-writing-deai.md)
   凡是生成或重写可见英文正文，都必须读取此文件，用于检查无必要的 `not X, but Y`、过度防御、AI 高频词语、机械连接、重复解释和模板化段落结构。

不得将以上三个源文件合并后改写，也不得为了统一措辞而修改其中的原始内容。

## 适用范围

适用于已有 `.tex` 稿件、用户粘贴的英文论文段落、审稿回复中准备放回正文的修改内容，以及已有 manuscript 的 Abstract、Introduction、Related Work、Methods、Results、Discussion 和 Conclusion。

不适用于从零撰写整篇论文。遇到从零起草请求时，应明确说明该任务超出本 Skill 的范围。

当任务只是查找 DOI、补全 BibTeX、统一 `.bib` 格式或整理出版元数据时，应使用专门的 DOI/BibTeX 工具。当稿件润色或审计涉及引用时，本 Skill 只负责检查文献是否真实存在以及稿件中的元数据是否对应。

## 工作模式

### 审计模式

当用户要求“检查”“看看哪里有问题”或尚未授权修改时，只给出定位明确的问题、理由和建议，不直接改文件。必须区分确定问题、依赖上下文判断的问题和单纯的词表命中。

### 直接润色模式

当用户明确要求修改稿件时，只修改指定文件和指定范围。若用户只提供一个段落，不扩展到其他章节；若用户只要求语言润色，不主动改变理论结构、实验解释、引文或版式。

## 执行顺序

以下步骤按用户授权范围执行，不要求每次任务都修改所有层面。纯语言润色不得自动升级为理论、贡献或研究设计修改。

### 1. 固定任务边界

确认目标文件、目标章节、目标 venue、用户是否授权直接修改，以及是否需要编译。记录用户明确要求保留的术语、句子、citation key、数据和格式。

### 2. 保护原始研究含义

先识别每段的 claim、evidence、interpretation、theoretical boundary 和必要 limitation。不得通过语言润色新增贡献、补造机制、扩大 generalizability、强化 causal claim，或将 selected examples 写成 prevalence evidence。

### 3. 处理理论边界和论证结构

只有用户要求逻辑、理论、贡献、论证结构或综合润色时，才依据 [`references/ml-paper-writing/SKILL.md`](references/ml-paper-writing/SKILL.md) 修改研究问题、贡献、理论构念、证据和结论之间的对应关系。若用户只要求语法、表达、翻译或去 AI 味，可以识别并单独报告相关风险，但不得在正文中直接修改这些实质性内容。

获得相应授权后，优先修复：

- contribution 与实际结果不一致；
- `proxy` 被写成直接测量；
- predictive association 被写成 causal mechanism；
- 案例说明被写成机制验证；
- 段落之间缺少真实的逻辑关系；
- Introduction、Results 和 Conclusion 对同一贡献的说法发生漂移。

这一阶段只确定“应该表达什么”，暂不追求表面语言的华丽程度。

### 4. 检查参考文献是否真实存在

在进入语言润色前，若修改范围包含新增引用、可疑引用、缺失文献或用户要求进行引用真实性检查，先执行参考文献真实性核验。

核验时应使用论文标题、作者、年份和 venue 进行交叉匹配，优先检查 publisher page、DOI landing page、官方会议或数字图书馆页面，以及 PubMed、ACL Anthology、ACM、IEEE、Springer、Oxford、JMIR、INFORMS、Elsevier 等权威记录。Crossref 或其他聚合索引可用于辅助定位，但不能在存在冲突时替代出版方记录。

每条文献应归入以下状态之一：

- `Verified`：找到权威记录，标题、作者、年份和 venue 能够对应；
- `Verified with metadata mismatch`：文献真实存在，但稿件或 BibTeX 中的作者、年份、标题、venue、页码或 DOI 存在不一致；
- `Not independently verified`：目前未找到足够权威的记录，不能据此直接判定文献虚假；
- `Contradictory record`：给定标题、作者、年份或 DOI 指向不同作品，存在较高错误或虚构风险，需要作者确认。

没有 DOI 不等于文献不存在。确认文献真实存在，也不等于它支持稿件中的具体论点。除非已经检查摘要、正文或其他足以判断内容的原始材料，否则只报告 existence 和 metadata status，不声称完成 claim-support verification。

若核验发现元数据问题，保留原 citation key，先报告差异；只有用户授权后才修改 `.bib`。不得根据相似标题猜测 DOI，也不得自动将未核验文献描述为 fabricated citation。

### 5. 进行 LaTeX 安全的英文润色

依据 [`references/latex-paper-en/SKILL.md`](references/latex-paper-en/SKILL.md) 选择最小的必要模块。该 component 中的 `$SKILL_DIR` 指 `references/latex-paper-en/`。保持 `\cite{}`、`\parencite{}`、`\textcite{}`、`\ref{}`、`\label{}`、数学环境、自定义宏、表格和图片引用不变，除非用户明确要求修改这些对象。

润色应优先改善语法、句子长度、指代、信息顺序和段落衔接。不要为追求“高级感”而替换准确的简单词，也不要将作者已经确定的术语改成近义词。

### 6. 执行去 AI 味检查

依据 [`references/academic-writing-deai.md`](references/academic-writing-deai.md) 对所有新写或改写的可见正文进行最后一轮检查。重点检查：

- 无实际分析必要的 `not X, but Y`；
- `We do not claim ...`、`We do not attempt ...` 等过度防御；
- `taken together`、`it is worth noting that`、`pivotal`、`leverage`、`delve into` 等程式化表达；
- 机械的 `First`、`Second`、`Moreover`、`Finally`；
- 不必要的 em dash、加粗和斜体；
- 同一句、同一段或跨章节的重复解释；
- 每段都采用相同开头、三点并列和总结句的模板化结构。

词表只用于触发上下文复查，不得机械删除专业术语。必要的研究限制和证据边界必须保留。

### 7. 一致性与编译验证

直接修改后，对照修改前后的 claim、数据、引文、术语和推断强度。确认没有遗漏或破坏 LaTeX 命令。若项目具备编译条件且用户要求或修改涉及源码结构，按 [`references/latex-paper-en/SKILL.md`](references/latex-paper-en/SKILL.md) 的 compile 流程编译，并检查 unresolved citation、reference、warning 和 PDF 可见异常。仅在相应脚本及其运行依赖可用时执行脚本命令；否则使用可用的 LaTeX 工具完成等价检查，并如实说明验证范围。

静态检查不能被描述为成功编译；未执行编译时必须明确说明。

## 冲突处理

规则优先级为：用户当前明确要求、目标 venue 或官方模板、稿件中已经确认的研究事实和术语、本 Skill 的编排规则、三个组成文件的一般建议。

当 `ml-paper-writing` reference 中的主动起草建议与本 Skill 的既有稿件边界冲突时，以最小范围润色为准。当去 AI 味规则与准确性或必要限定冲突时，保留准确性和必要限定。当语言流畅度与 claim 强度冲突时，保留原有 claim 强度并标记需要作者确认的歧义。

## 输出规范

审计模式下，按影响程度报告问题，并给出精确位置、原文、问题原因和建议修改。直接润色模式下，说明修改了哪些文件和章节，并简要概括理论边界、语言、去 AI 味和 LaTeX 安全方面的实际改动。

不要用“已全面优化”“已完全去除 AI 味”等无法验证的表述。不得把风格词表命中数量当作 AI 生成判定，也不得声称润色结果可以规避 AI detector。
