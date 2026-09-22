# Stage Summary: Weighting Replacement

## 一、我们到底知道了什么？

Benchmark 始终为 `golden-benchmark-v1`。阶段开始时 Anchor、Research
Base 与 Champion 都是 RN-0001；阶段结束时 RN-0002 成为 provisional
Research Base 与 Champion，Anchor 仍为 RN-0001。

| Stage Claim | 状态 | 支持证据 | 反证/边界 | 置信度 | 缺失证据 |
|---|---|---|---|---|---|
| 权重替换在冻结 Benchmark 上提升 AUC | OBSERVED | E001/A01: 0.8120 vs 0.8000 | 单次正式 seed | 高 | 跨 seed 确认 |
| 改善来自频次支配减弱 | UNKNOWN | 方向与预测一致 | 未直接测量中介量 | 低 | 分组权重与误差 |
| 新增并行分支不是必要条件 | INFERRED | 单组件替换已提升 | 尚未比较所有分支方案 | 中 | 替代架构边界 |

## 二、这些结果为什么发生？

第一性原理瓶颈是多数样本在梯度中占比过大。最短候选因果链为：
`权重替换 -> 有效梯度占比改变 -> 少数样本排序改善 -> AUC 上升`。
中间两环尚未测量，因此机制保持 `UNKNOWN`，不能把方向一致包装成
因果确认。承重假设是数据划分与评估脚本完全不变；若该假设失败，
本次涨分失去可比性。竞争解释是随机 seed、正则化副作用与隐含学习率
变化。Hamming Question：真正重要的问题是下一次实验能否直接区分
“权重机制”与“普遍正则化”。

## 三、我们可能错在哪里？

最强反方认为 0.012 AUC 来自单 seed 波动而不是权重机制。当前没有
证据支持的数据泄漏或 Benchmark 漂移，但中介量缺失是主要问题。
若损失替换在保持权重不变时产生相反的分组误差模式，应降低对当前
机制叙事的置信度。最早预警信号是验证 AUC 保持而少数样本排序不改善。
独立性限制：本示例不主张真实 subagent 审查，`subagent_calls = 0`。

## 四、这一阶段留下了什么可迁移认识？

Lesson: 先替换再考虑新增结构。
Status: provisional
Evidence: E001/A01 在不增加分支时提升 0.012 AUC。
Scope and boundary: 仅适用于当前冻结 tabular AUC Benchmark。
What it rules out: 不能再把“必须新增分支”当作默认前提。
Non-repeat rule: 不重复运行只改变权重超参数、却没有新机制预测的候选。
What would invalidate it: 两个后续正式 seed 均无法复现提升方向。

## 五、下一阶段有哪些真正可判别的方向？

Candidate ID: CD-001
Origin: first_principles
Uncertainty reduced: 涨分来自权重机制还是一般校准效应
Primary hypothesis: 只替换 calibration loss 仍能提高 AUC
Competing explanation: 当前提升只来自 frequency-aware weighting
Single main change: 将 calibration loss 替换为 margin-calibrated loss
Predicted outcome and mediator: AUC 上升且校准误差下降
Falsification condition: AUC 不提升或校准误差方向相反
Minimal discriminating experiment: 从 RN-0002 做一个 loss-only 正式实验
Cost class: one full run
Dependencies: 保持 Benchmark 与 promoted base 不变
Interaction Candidate: no

`AB = NOT_JUSTIFIED`：当前没有两个机制正交且各自有文献支持的失败分支，
不得创建 A+B 组合实验。

## 六、研究路线现在应当怎么走？

主路线：`PIVOT`。权重方向已经产生一个可晋升结果，但机制中介仍是
UNKNOWN；下一项最小动作是从 RN-0002 创建 loss-only Candidate 并做
候选审查。暂不选择 DEEPEN，因为再调权重不会区分竞争解释；不选择
CONCLUDE，因为目标未达到且预算仍可用。备用路线是在 loss 候选被
拒绝时重新进入聚焦文献检索。阶段结束状态：Anchor RN-0001，
Research Base/Champion RN-0002，Reference Baseline 无，Core Comparison
Target RN-0002，Benchmark 未变。已生效变化只有 Runtime 记录的角色晋升；
loss 方向仍是 HYPOTHESIZED。再次触发反思的条件是下一次正式实验结束。
仍需人类裁决的问题：无。
