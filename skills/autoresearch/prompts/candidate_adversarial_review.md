---
doc_id: candidate-adversarial-review
doc_type: prompt
title: Candidate Adversarial Review Prompt
status: skeleton
summary: 为普通 Candidate REVIEW 提供主 AI 单次自审提示，当前由 Candidate Priority Rules 代行完整规则。
read_when:
  - 普通候选需要固定 REVIEW 输出格式时
depends_on:
  - research-contract
  - candidate-priority-rules
  - research-graph-protocol
activation:
  level: ON_DEMAND
---

# Candidate Adversarial Review Prompt

## 职责

在投入显著算力前，对 Candidate 进行对抗审查。正式 Prompt 必须检查 Evidence Class、Scope–Locus–Operator 一致性、伪创新风险、分支膨胀、可证伪性、信息价值、实验成本、比较公平性和最便宜的判别实验。

在本 Prompt 完成开发前，直接应用 `../references/candidate_priority_rules.md`；如果没有改变实验定义，不得擅自提高结构组合的默认优先级。
