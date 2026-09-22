---
doc_id: research-experiment-log-template
doc_type: template
title: Research Experiment Log Template
status: stable
summary: 定义日志卷中的精简科研叙事、正式结果、归因、角色变化和相关 artifact 链接。
read_when:
  - 创建或追加 Research Experiment Log volume 时
depends_on:
  - research-contract
  - research-records-protocol
activation:
  level: ON_DEMAND
---

# Research Experiment Log Template

Runtime 只在正式 attempt 收口并形成科研判断时追加一条；不记录 PLANNED、RUNNING、step/batch 或一般工程状态。

```markdown
## E017 · <short title>

- Hypothesis: <preregistered hypothesis>
- Change: <single main change>
- Result: `<Run Outcome>` / `<Hypothesis Verdict>`; <1–3 metrics>
- Interpretation: <one concise causal or competing explanation>
- Decision: <keep, rollback, repair, promote, hold, close, or backtrack>
- Evidence: `logs/runs/E017/A01.jsonl`
```

每条记录保持短小。完整配置、命令、错误、checkpoint、slice 指标与 trainer 原始输出只通过 Experiment Card、Run Event Log 或 artifact 路径下钻。
