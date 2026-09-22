# CDS 文献对话地图 few-shot

这 6 篇示例用于校准“研究需要与哪些文献对话、为什么”。它们展示不同的定位路径，不是用来复制结论，也不代表已经完成系统综述。

## 六种定位路径

| 示例 | 适合校准的定位方式 | 需要守住的边界 |
| --- | --- | --- |
| [P01 HyperCARS](dialogue-maps/P01.md) | 从层级数据结构推出表示学习文献线 | 有层级不等于必须用双曲空间 |
| [P04 GDCM](dialogue-maps/P04.md) | 用概念理论定义算法应发现什么 | 结果相关概念不是已验证构念 |
| [P15 DSDL](dialogue-maps/P15.md) | 从客户体验现象推出多模态、动态建模挑战 | 结果监督表示不是真实心理状态 |
| [P05 MS2RSF](dialogue-maps/P05.md) | 用领域关系理论细化动态图预测要求 | 学习图不是真实经济或因果关系 |
| [P06 GACE](dialogue-maps/P06.md) | 用行为理论限定异质图的候选元路径 | attention 权重不是真实参与动机 |
| [P08 IA-HMC](dialogue-maps/P08.md) | 让行为偏差同时改变目标函数与协作接口 | 领域先验和事后收缩不等于因果纠偏 |

## 选择方法

- 先读与用户研究的**定位机制**最接近的 1–2 篇，而不是行业名称最接近的论文。
- 需要从研究问题生成文献流时，对照 [问题／视角 prompt](../references/problem-perspective-prompt.md)。
- 需要从数据挑战生成方法流时，对照 [技术／算法 prompt](../references/technical-method-prompt.md)。
- 真实交付必须回到当前论文全文；示例中的文献、页码和判断不能替代新论文证据。

## 语料边界

6 篇均来自本项目已核验的 ISR 论文全文。示例只复原其 Introduction、Literature Review／Related Work、理论与方法概览中的定位逻辑；没有附原 PDF，也不声称复现实验或认证论文主张。
