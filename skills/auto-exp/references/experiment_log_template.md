# 实验记录模板

## 目录

1. 卷首
2. 单条实验
3. 失败与重试
4. 清理记录
5. 阶段总结
6. 下一卷承接

使用原则：实验启动前可以完善 working contract；进入 `running` 后不静默改写已有记录，只追加带时间戳的状态更新、结果和勘误。阶段总结另建文件；失败、停止和重试与成功实验同等记录。

## 1. 卷首模板

```markdown
# <项目名> 实验记录 · 第 N 卷（<主题>）

## 本卷定位
- 承接：<上一卷路径与覆盖范围；没有则写“新建”>
- 本卷问题：<一句话>
- 实验编号：<起始编号>

## 固定实验协议
- 数据 release / 标签版本：
- training split：
- selection split：<没有则写“无”>
- evaluation split：
- final holdout：<没有则写“无”>
- selection rule：<固定 epoch / early stopping / checkpoint rule / threshold rule>
- 主指标与噪声尺度：
- 约束指标：
- 固定 baseline：
- selection exposure：<none；或 epoch / checkpoint / threshold / hyperparameter / repeated feedback 等>
- evaluation independence：<independent / non-independent + 理由>

## 权限与资源边界
- 允许自动执行：
- 必须人工确认：<停止健康任务 / 改合同 / 删除 / 覆盖 / 扩大预算 / 关机等>
- 资源预算：

## 本卷目标
- <目标 1>
- <目标 2>
```

## 2. 单条实验模板

```markdown
## E??：<实验名 / 一句话假设>

### 状态
- 当前状态：<proposed / contracted / preflighted / smoke_passed / staged / running / evaluated / verified / synced / logged / archived / failed / diagnosed / retry_planned / stopped>
- run / attempt ID：
- 开始 / 结束时间：

### 背景与假设
- 上一实验暴露的瓶颈：
- 改动层级：<L1 / L2 / L3 / L4 / tuning>
- 核心假设：
- 唯一预期变量：
- 其他不可避免变化：<没有则写“无”>

### 实验合同
- 数据 release / 指纹 / 样本数：
- 标签和预测时点：
- training / selection / evaluation / final holdout：
- 模型 / trainer / 初始化参数：
- epochs / max steps / lr / scheduler / warmup / weight decay：
- batch / eval batch / accumulation / effective batch：
- seed / precision / device：
- 环境指纹：<lockfile / container；runtime / framework / driver / accelerator 版本>
- early stopping / checkpoint / threshold rule：
- 主指标 / 约束指标 / 切片指标：
- 止损条件：
- 资源预算：

### 实现与预检
- 代码版本 / diff / 配置路径：
- 启动命令 / launcher：
- 输出目录 / 日志路径：
- 数据、泄漏、shape、token、资源和 smoke 审计：
- 已知限制：

### 运行过程

按时间追加，不覆盖上一条：

#### Status update <YYYY-MM-DD HH:MM TZ>
- 状态：<使用统一状态枚举>
- 关键里程碑：
- 异常、诊断与修复：
- 合同是否发生变化：<否；若是，记录确认和新 attempt>

### 结果
- 选择的 epoch / checkpoint / threshold 及依据：
- 报告 split：
- selection exposure：<none；或具体选择行为>
- evaluation independence：<independent / non-independent + 理由>

| 方法 | 主指标 | 约束指标 1 | 约束指标 2 | 业务指标 | 备注 |
|---|---:|---:|---:|---:|---|
| 固定 baseline | ... | ... | ... | ... | ... |
| 本实验 | ... | ... | ... | ... | ... |

### 完成审计
- exit code / 完成标记：
- 预测行数 / finite / schema：
- config / metrics / history / predictions / audit / log：
- 数据、代码和产物指纹：
- 环境指纹：
- 本地或长期存档路径：

### 结论与决策
- 是否超过基线及噪声尺度：
- 是否构成 Pareto 改进：
- 可归因结论：
- 不可归因或证据限制：
- 决策：<继续 / 补充归因 / 重试 / 止损 / 归档>
- 下一步：
```

## 3. 失败与重试模板

```markdown
### Attempt <编号>：<失败阶段>
- run ID / 时间：
- 原始命令与配置：
- 已完成进度：
- 完整错误路径：
- 根因分类：<代码 / 数据 / 环境 / 资源 / 科学合同 / 未确定>
- 根因证据：
- 保留产物：
- 修复内容与验证：
- 是否改变科学合同：
- 重试 run ID：<不重试则说明原因>
```

不要覆盖失败 attempt 的日志和配置。

## 4. 清理记录模板

```markdown
## 清理记录 <YYYY-MM-DD>
- 触发原因：
- 建议清理：<路径 / 大小 / 原因 / 风险 / 依赖>
- 必须保留：
- 授权要求：
- 用户确认：<未确认则写“未执行，仅建议”>
- 实际删除：
- 回收空间：
- 删除后审计：
```

## 5. 阶段总结模板

```markdown
# <项目名> 阶段总结（<实验范围>）

## 覆盖范围
- 原始实验日志：
- 实验编号：
- 数据与评估协议：
- 整理日期：

## 一句话结论
- 当前最好：
- 有效方向：
- 无效方向：
- 当前瓶颈：
- 下一决策：

## Leaderboard
| 实验 | 改动层级 | Selection exposure | Evaluation independence | 主指标 | 约束指标 | 结论 |
|---|---|---|---|---:|---:|---|
| ... | ... | none / 具体行为 | independent / non-independent | ... | ... | ... |

## 分方向总结
### <方向 A>
- 实验：
- 证据：
- 结论：
- 是否继续：

## 关键教训
- <教训 1>
- <教训 2>

## 参数与清理建议
- 必须保留：
- 可建议清理：
- 未解决依赖：
```

## 6. 下一卷承接模板

```markdown
# <项目名> 实验记录 · 第 N+1 卷（<主题>）

## 承接上一卷
- 原始日志：
- 阶段总结：
- 当前最好及 selection exposure / evaluation independence：
- 已确认有效：
- 已止损：
- 未解决问题：

## 新卷实验协议
- 数据与标签：
- training / selection / evaluation / final holdout：
- 固定 baseline：
- selection rule：
- 指标和噪声尺度：
- 资源与权限边界：

## 新卷核心假设
- <一句话>
```
