---
doc_id: run-event-log-schema
doc_type: template
title: Run Event Log Schema
status: stable
summary: 定义单个 attempt 的机器可读 JSONL 事件、指标、checkpoint、错误、重试、停止原因和时间字段。
read_when:
  - 创建或验证 Run Event Log 时
depends_on:
  - research-contract
  - experiment-playbook
  - research-records-protocol
activation:
  level: ON_DEMAND
---

# Run Event Log Schema

每行必须是一个独立 JSON object，并至少包含 `event`、`timestamp`、`experiment_id` 与 `attempt_id`。Runtime 独占写入两个生命周期边界：

- `ATTEMPT_STARTED`：Node、Run Kind、seed、代码/数据/配置版本、planned budget 与 Brief 派生的 `cost_unit`；
- `ATTEMPT_FINISHED`：Run Outcome、Hypothesis Verdict、从正式 artifact 读取的 1–3 指标、typed artifact 路径与 hash、时长、成本及同一 `cost_unit`、硬约束、停止原因和 checkpoint。

trainer 可以在两者之间追加：

- `HEARTBEAT`
- `EPOCH_FINISHED`
- `EVALUATION`
- `CHECKPOINT_SAVED`
- `WARNING`
- `ERROR`
- `RESOURCE`

trainer 事件不得伪造 `ATTEMPT_STARTED` 或 `ATTEMPT_FINISHED`，也不得修改旧行。step/batch 高频输出优先写 trainer 自己的日志、TensorBoard 或 W&B；JSONL 只保留监控、恢复和科研判断需要的事件。

```json
{"event":"EPOCH_FINISHED","timestamp":"2026-07-17T08:30:00Z","experiment_id":"E017","attempt_id":"A01","epoch":2,"train_loss":0.143,"selection_metrics":{"auc":0.8134},"checkpoint_ref":"artifacts/E017/best.pt"}
```
