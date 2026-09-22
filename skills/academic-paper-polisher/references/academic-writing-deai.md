# 英文学术写作去 AI 味指南

## 用途

本指南用于减少既有英文学术论文中程式化的 AI 写作痕迹，同时保留原文的研究主张、证据、理论边界、引文、术语和 LaTeX 结构。目标是让论文表达克制、准确、自然，而不是将所有句子改得口语化，也不是用另一套固定模板替换作者原有的写作风格。

本文件是一个独立的润色组件，不承担从零撰写论文的任务。后续可以将它与 `ml-paper-writing` 的高层论证指导以及 `latex-paper-en` 的 LaTeX 安全编辑流程组合成一个新的 Skill。

## 不可突破的边界

不得为了改善语言风格而增加或删除实质性主张。不得编造证据、作用机制、因果解释、研究局限、引文、指标或实验细节。除非用户明确授权修改相应内容，否则必须保留所有 LaTeX 命令、citation key、`\ref{}`、`\label{}`、公式、表格、图片、自定义宏和技术术语。

去 AI 味不能降低论文的严谨性。凡是用于界定研究对象、情境、设计、推断范围或证据边界的必要限定，都应保留。需要删除的是防御性的表达方式，不是方法透明度和必要的研究边界。

## 1. 减少无必要的对比句

AI 生成的文本经常通过否定式对照制造强调，常见形式包括 `not X, but Y`、`not merely X, but Y`、`rather than X, the study Y` 和 `the issue is not X; it is Y`。当 X 与 Y 之间确实存在需要澄清的分析区别时，这类结构可以使用。若否定 X 只是为了让普通陈述显得更有力量，就应直接陈述 Y。

保留对比句之前，需要判断：读者是否真的可能混淆 X 与 Y，以及否定 X 是否是建立当前论点所必需的。如果两个条件都不满足，直接写出作者真正想表达的内容。

示例：

```text
AI 味较重：
The contribution of online consultations lies not in the clinical
information itself, but in the interaction process captured by the dialogue.

建议修改：
Online consultations provide additional information through the interaction
process captured in the dialogue.
```

```text
AI 味较重：
This module is not a causal test of coping appraisal; rather, it is a
theory-informed feature integrator.

建议修改：
We interpret this module as a theory-informed feature integrator. Its
predictive contribution does not establish a causal coping-appraisal mechanism.
```

不要机械删除所有否定结构。当作者需要纠正审稿人的具体误解、区分两个具有正式定义的概念，或者直接回答某项审稿意见时，可以保留一次明确的对比，但不要在同一段或全文中反复使用相同结构。

## 2. 严禁过度防御性表达

过度防御的文本会反复声明研究不解释什么、不证明什么、不声称什么、不意味着什么、不涵盖什么或不尝试什么。常见形式包括：

```text
We do not claim that ...
We do not attempt to explain ...
This analysis does not prove ...
This should not be interpreted as ...
It is important to clarify that ...
We acknowledge that we cannot rule out ...
We make no claim regarding ...
```

当这些句子提前为尚未出现的质疑辩护、在多个章节中重复出现，或者占用的篇幅超过正面研究发现时，应视为红线。这样的写法容易使论文看起来一直在与一个想象中的审稿人争论。

优先使用正面的证据范围表述：

```text
防御性写法：
We do not claim that physician credentials causally determine patients'
coping appraisal.

建议修改：
The observational design supports a predictive interpretation of physician
credentials, while the underlying mechanism remains untested.
```

```text
防御性写法：
We do not attempt to explain every reason why a patient subsequently visits
the hospital.

建议修改：
The study predicts subsequent offline utilization from information available
at the end of the online consultation.
```

```text
防御性写法：
These examples do not prove that the identified mechanisms drive conversion.

建议修改：
These examples provide contextual illustrations of patterns observed in the
consultations; mechanism prevalence and causal effects require separate analysis.
```

当某项限制确实会改变结果的解释方式时，应保留这项限制。具体写明限制是什么、它约束论文中的哪一项结论，然后停止，不要继续增加第二轮或第三轮自我辩护。必要的限制通常应放在 Methods、Discussion、Limitations，或者针对该问题的审稿回复中，不要将同一免责声明分散到 Abstract、Introduction、Results 和 Conclusion。

## 3. 优先使用朴实、准确的词汇

在不损失技术含义的前提下，选择最简单、最准确的单词。不要为了显得高级而将常见学术词汇替换成装饰性表达。例如，通常优先使用 `use` 而不是 `leverage`，使用 `investigate` 而不是 `delve into`，并用具体研究情境替代 `landscape`、`realm` 或 `tapestry` 等模糊表达。

以下词汇属于复查词表，不是绝对禁用词表：

```text
Accentuate, Adorn, Amass, Ameliorate, Amplify, Alleviate, Ascertain,
Advocate, Articulate, Bear, Bolster, Bustling, Cherish, Conceptualize,
Conjecture, Consolidate, Convey, Culminate, Decipher, Demonstrate,
Depict, Devise, Delineate, Delve, Delve Into, Diverge, Disseminate,
Elucidate, Endeavor, Engage, Enumerate, Envision, Enduring, Exacerbate,
Expedite, Foster, Galvanize, Harmonize, Hone, Innovate, Inscription,
Integrate, Interpolate, Intricate, Lasting, Leverage, Manifest, Mediate,
Nurture, Nuance, Nuanced, Obscure, Opt, Originates, Perceive,
Perpetuate, Permeate, Pivotal, Ponder, Prescribe, Prevailing, Profound,
Recapitulate, Reconcile, Rectify, Rekindle, Reimagine, Scrutinize,
Substantiate, Tailor, Testament, Transcend, Traverse, Underscore,
Unveil, Vibrant
```

其中部分单词在特定研究中具有准确的技术含义。例如，`mediate`、`perceive`、`integrate` 和 `demonstrate` 可能分别用于 mediation analysis、PMT 构念、模型架构或证据报告。当这些词表达已经定义的概念时应保留；只有在它们只是装饰、夸大或模糊强调时才考虑替换。

还应重点检查以下常见的 AI 式短语和连接表达：

```text
taken together
it is worth noting that
it is important to note that
importantly
notably
crucially
in today's rapidly evolving landscape
plays a pivotal role
sheds light on
offers valuable insights
paves the way for
serves as a testament to
provides a comprehensive understanding
from a holistic perspective
the multifaceted nature of
```

不要将一个套话替换成另一个套话。应删除无实质信息的引导语，直接陈述研究发现、关系或含义。只有在前文确实呈现了多个不同结果，而且接下来要给出此前没有表达过的综合判断时，才保留 `taken together`。

## 4. 让结构自然，而不是模板化

去 AI 味润色生成的论文正文应使用逻辑连贯的普通段落，不要主动将内容改成编号列表或项目符号，也不要用连续的 item 代替论证。若原文中的列表是模板、期刊规范、正式贡献、假设、实验步骤或技术规格所要求的，应保持原结构；未经用户授权，不要擅自重排。

减少 `First and foremost`、`Secondly`、`Furthermore`、`Moreover`、`It is worth noting that` 和 `Finally` 等机械路标。句子之间应通过研究对象、证据以及因果或比较关系自然连接。过渡句应说明两个观点之间的实际关系，而不是简单宣布下一句话即将开始。

尽量减少 em dash（`—`）的使用。在关系表达更清楚时，优先使用逗号、括号、冒号、从句或单独成句。不要为了强调普通观点而在论文正文中新增加粗或斜体。数学符号、已定义术语、标题、表格规范、期刊名称和模板要求的格式应保留。

避免所有段落都采用完全对称的固定模板，例如每段都以宏观陈述开头，中间排列三个并列观点，最后再加一句泛化意义。段落长度和结构应服务于实际论证，而不是追求形式上的整齐。

## 5. 删除过度解释和重复解释

AI 生成的草稿经常先陈述一个观点，再解释一次，随后换一种说法重复，最后在段末再次总结。同一内容还可能在 Introduction、Discussion 和 Conclusion 中反复出现。

检查每个句子的功能：它是在提出 claim、提供 evidence、进行 interpretation、限定 boundary、完成 transition，还是说明 implication。相邻两个句子若承担相同功能且表达相同事实，只保留更准确的一个。段末句应提供新的综合、后果或过渡，不应只改写本段第一句。

需要在三个层级检查重复：句子内部是否存在没有增加含义的同义词和双重修饰；同一段落是否在结尾重复开头的观点；不同章节之间是否重复完整的动机、结果或解释。Conclusion 可以综合研究发现，但不应重新复制 Introduction 的研究动机或 Results 中的详细数字描述。

示例：

```text
重复写法：
Online dialogue records the interaction process between patients and
physicians. This interaction process is preserved in the multi-turn dialogue.
Therefore, the dialogue provides information about how the interaction unfolds.

建议修改：
Multi-turn dialogue preserves how patients and physicians exchange and refine
information during the consultation.
```

当术语需要重新定位、假设需要结合结果再次检验，或者 Conclusion 必须直接回答 research question 时，可以保留必要的再次出现。判断标准是后一个句子是否承担了新的论证功能，而不是它是否使用了不同的词。

## 6. 校准主张强度，避免夸大后再撤退

应使用证据能够支持的最强表述，替代空泛赞美和绝对化结论。不要先用宣传性语言夸大研究贡献，再用多轮免责声明收回前面的主张。

可以根据证据选择以下类型的表达：

```text
The ablation results show an incremental predictive contribution.
The association is consistent with the proposed theoretical interpretation.
The examples illustrate that these concerns occur in this setting.
The observational design cannot distinguish the proposed mechanism from the
proxy explanation.
```

动词强度必须与证据类型对应。`shows` 或 `indicates` 可用于报告观察到的结果；`is consistent with` 可用于理论一致性证据；`illustrates` 可用于少量案例；`predicts` 可用于预测关联。只有研究设计支持 causal identification 时，才可使用因果动词。去 AI 味润色不得将 `is associated with` 强化为 `drives`、`leads to` 或 `determines`。

## 编辑流程

去 AI 味处理应在理解原文论证和证据边界后进行。首先保护 LaTeX 语法、引文、标签、公式、数值和已定义术语，并记录段落中的 claim、evidence、interpretation 和必要 limitation。随后检查无必要的 `not X, but Y`、反复出现的免责声明、词表中的装饰性表达、机械连接和重复解释。完成语言调整后，应逐段对照原文，确认事实、理论定位和推断强度保持一致。

若无法确定某个句子是必要边界还是多余防御，应保留原文并标记给作者确认。不得通过语言润色擅自解决实质性的理论或方法歧义。

## 输出规范

当任务是审计而不是直接修改时，每个问题应包含位置、问题类型、判断理由和建议写法。必须区分确定存在的问题与依赖上下文判断的复查词。不得仅因为某个单词出现在词表中，就认定它存在问题。

当用户授权直接修改源文件时，只进行局部修改，并在完成后简要说明删除了哪些无必要对比、减少了哪些防御性表达、简化了哪些词汇、合并了哪些重复解释，以及哪些句子因承担必要的技术含义或研究边界而保持不变。

最终文本应体现一种明确状态：作者清楚证据能够支持什么，并用一次直接、准确的陈述将其表达出来，不使用装饰性语言，也不反复道歉或自我辩护。
