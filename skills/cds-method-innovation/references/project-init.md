# 项目初始化与接续

只在用户需要建立持久研究空间时使用。先确认项目根目录，检查现有文件；不得把 Skill 安装目录当成项目根目录。

## 最小资料

记录项目名称、当前问题、研究线、当前阶段和眼前里程碑；未知项写“待确认”或“暂定”，不为初始化展开长访谈。已有代码、数据、结果表只记录真实位置，不搬运、不制造历史。

默认布局：

```text
<项目目录>/research-records/
├── project.md
├── paper-log/
│   ├── index.md
│   └── entries/
└── experiment-log/
    ├── index.md
    └── experiments/
```

用户已有不同布局时优先接续；不能为了使用脚本自动迁移或新建第二套日志。格式有冲突时说明具体路径，请用户选择，不覆盖内容。

## 内置初始化

脚本 [init_project.py](../scripts/init_project.py) 只用 Python 3 标准库，保留已有文件，只补缺失文件。先检查现有目录类型与内容，再运行以下命令；尖括号为需替换的真实资料，不原样执行。

```sh
SKILL_DIR="/absolute/path/to/cds-method-innovation"
PROJECT_DIR="/absolute/path/to/research-project"
python3 "${SKILL_DIR}/scripts/init_project.py" "${PROJECT_DIR}" \
  --title "<项目名称>" --question "<当前问题或暂定>" \
  --research-line cds --stage "<当前阶段>" \
  --milestone "<下一项具体成果>" --locations "<已有材料路径>"
python3 "${SKILL_DIR}/scripts/init_project.py" "${PROJECT_DIR}" --validate
```

返回实际创建与保留的路径。重复运行不会更新旧概况；需要修改时先读内容，只改本次相关字段，不丢已有笔记。不要自动生成第一条虚构方向或运行记录。

Python 不可用时可按 [project-template.md](../assets/project-template.md) 手工建立同样的 Markdown 概况，日志格式见 [research-records.md](research-records.md)；不要求安装平台或数据库。

## 示例（虚构）

现有文本分类代码和结果表没有研究历史。建立两个空日志，阶段写“核查已有 baseline”，概况链接真实结果表。接着核验运行证据，不凭结果表存在就补写“已复现”或先前方向选择。当前方向、benchmark 与实验方案形成后再把真实链接补入概况。
