# 方向日志与实验日志

记录写在用户项目中，不写在 Skill 包中。首次使用先读已有索引和相关记录；一个项目保留一套权威日志。执行本包脚本时始终传 `--root` 的实际路径，避免工作目录导致误写。脚本仅使用 Python 3 标准库，单写入者串行执行，不同时分配记录编号。

所有示例命令执行前，在同一次 shell 调用中设置实际路径；不能原样使用占位路径，也不要依赖先前 shell 的变量：

```sh
SKILL_DIR="/absolute/path/to/cds-method-innovation"
PROJECT_DIR="/absolute/path/to/research-project"
```

## 两类记录的边界

| 记录 | 保存什么 | 不保存什么 |
|---|---|---|
| 方向日志（paper-log） | 问题、候选、作者选择、放弃理由、重启条件及证据链接 | 重复抄录整份运行指标或把 AI 建议写成作者决定 |
| 实验日志（experiment-log） | 一个科学比较及其每次实际运行、配置、结果、失败和产物 | 仅准备好的命令所“预期”产生的结果 |

方向日志回答“走过什么路，为什么改变”；实验日志回答“真正跑了什么，得到什么”。完整工作流包含自动记录；解释/预览不写文件。记录动作的委托不等于代研究者选择。

## 方向记录

使用 [paper_log.py](../scripts/paper_log.py)。一次实质改变应说明：发生了什么、为何重要、依据是什么、下一步或重启条件。来源归属可以是作者决定、团队决定、AI 建议未接受、观察证据或未确认解释。

```sh
python3 "${SKILL_DIR}/scripts/paper_log.py" --root "${PROJECT_DIR}/research-records/paper-log" add \
  --title "<方向或决定>" --kind idea --ownership "AI suggestion — not accepted" \
  --changed "<具体建议>" --matters "<研究意义>" \
  --basis "<证据链接或未验证>" --next-step "<判别实验或选择问题>" \
  --related "<相关材料位置>"
```

`--kind` 允许 idea、decision、writing、meeting、checkpoint、other。在本流程中主要用前两项和 checkpoint。

含义改变时使用 `revise <实际 PAPER 编号>`，同时提供与 `add` 相同的全部内容参数；它建立下一版本而不覆盖旧版。先读取旧版以保留未改变的信息。修正简单错字可直接编辑；手动编辑后运行 `rebuild` 更新索引。

检索和总结读取 Markdown，无需新的检索服务。区分当前和 superseded 版本，回答时引用依据，不能用条目数衡量研究进展。重新提出旧方向前，说明什么新证据改变了当初放弃的理由。

## 科学比较与运行

使用 [experiment_log.py](../scripts/experiment_log.py)。新问题或比较建立 experiment；同一比较的 seed、调参和重试分别建立 run。记录前先查同一作业/产物是否已入日志，避免重复登记。

```sh
python3 "${SKILL_DIR}/scripts/experiment_log.py" --root "${PROJECT_DIR}/research-records/experiment-log" new-experiment \
  --title "<比较名称>" --question "<待验证问题>" \
  --comparison "<候选对哪些 baseline>" --primary-metric "<指标与方向>" \
  --decision-logic "<事先规则或明确事后探索>" --constraints "<限制、方向及方案链接>"
```

使用返回路径中的真实 EXP 编号，不假定总是 EXP-0001。实验概述在运行前创建，run 在有真实执行事实后记录：

```sh
python3 "${SKILL_DIR}/scripts/experiment_log.py" --root "${PROJECT_DIR}/research-records/experiment-log" add-run "<实际 EXP 编号>" \
  --title "<方法与运行>" --outcome failed \
  --changed "<与前一次的差异、retry_of 或无>" \
  --data "<数据版本、split、协议、evidence_phase>" \
  --configuration "<方法、seed、环境、预算、选模型规则、run_role>" \
  --results "<真实结果；失败时不要填预计指标>" \
  --interpretation "<解释及不确定性>" --next-step "<下一步>" \
  --artifacts "<实际配置、代码、指标、预测及原始日志位置>"
```

按事实选择 `--outcome`：completed、failed、null、abandoned、partial；示例中的 failed 不是默认成功状态。需要时加 `--execution` 和 `--external-id`，没有就留空。保留实际运行日期；脚本自动写本机记录日期，历史导入或跨时区运行须在字段内另写真实时间，不冒充当天执行。

### 在现有字段内记录 benchmark 信息

| 现有字段 | 必须记录的相关信息 |
|---|---|
| Data | 数据/split/协议版本、`evidence_phase`：开发选择、独立最终测试或探索性测试 |
| Configuration | 方法版本、seed、预算、checkpoint 规则、`run_role`：smoke/tuning/full；是否按预定规则选出的配置 |
| What changed | 本次改动；重试单列 `retry_of`，不覆盖原运行用途 |
| Observed results | 真实数值、单位、不确定性、失败；未知保持未知 |
| Artifact paths | 指标、合法可保存的预测、代码、配置、环境及训练日志 |

元数据不证明科学成功。比较前核对协议、数据、调参资源及选择规则；指标矩阵回查原始产物。主排名只用选定配置的完整、兼容运行，运行数不等于独立方法数。benchmark 产物的详细字段见 [benchmark-records.md](benchmark-records.md)。

## 校验、修订与回退

写完后执行相应命令：

```sh
python3 "${SKILL_DIR}/scripts/paper_log.py" --root "${PROJECT_DIR}/research-records/paper-log" validate
python3 "${SKILL_DIR}/scripts/experiment_log.py" --root "${PROJECT_DIR}/research-records/experiment-log" validate
```

索引可用各脚本的 `rebuild` 重建，它是记录的视图，不是原始证据。校验只检查基础结构，不验证数字、文件真实性或研究结论。不要把校验通过写成已复现。

既有日志不兼容或 Python 不可用时，沿用原格式或参考 [方向模板](../assets/paper-entry-template.md) 和 [运行模板](../assets/run-template.md) 手工记录上述字段。没有实验概述时先写“问题、比较、主指标、决定规则、限制”；不要求外部 Skill 或数据库。更正运行记录时保留原始日志和更正说明，不篡改历史结果；重试另建记录。

## 示例（虚构）

作者选择先核验 R1，方向日志记选择及预算理由。R1 首次 OOM，实验日志保留 failed；修复后另记一次实际重试并引用前次 run。如果后来发现候选与既有方法等价，方向条目建立新版本写“暂缓、依据、重启条件”，原建议和两次运行都保留。
