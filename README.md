# awesome-codex-research

<p align="center">
  <img src="docs/assets/research-workflow-hero.png" alt="科研工作流中的 Codex、研究者与远程 GPU 协作" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Codex-Skills%20%2B%20Plugins-2563EB?style=for-the-badge" alt="Codex Skills and Plugins">
  <img src="https://img.shields.io/badge/Research-Workflow-F97316?style=for-the-badge" alt="Research Workflow">
  <img src="https://img.shields.io/badge/License-Mixed%20%2F%20See%20Sources-0F172A?style=for-the-badge" alt="License: mixed">
</p>

这是我的 Codex 科研工作流能力仓库。

我把平时反复使用的能力拆成两类：

- **独立 Skill**：可以单独安装、单独触发的 `SKILL.md` 工作流；
- **Codex Plugin**：可以把多个 Skill、MCP server、脚本和资源一起安装的能力包。

目标是让科研工作中的检索、写作、审稿、实验、远程 GPU、结果核验和资料沉淀，都逐步变成可复用、可检查、可迭代的工作流。

## 当前能力

<table>
  <tr>
    <td width="80" align="center" valign="middle">
      <img src="docs/assets/research-workflow-mascot.png" alt="科研工作流卡通插画" width="60">
    </td>
    <td valign="middle">
      <h3>AutoDL Remote Plugin</h3>
      <p>通过本地 CLI 和 MCP server 控制 AutoDL / SSH 远程机器，支持文件传输、远程命令、后台任务、实验 run metadata、fleet、tmux 和只读 dashboard。</p>
      <p><a href="https://github.com/haibarazz/AutoDL-Remote">查看原始上游仓库</a></p>
    </td>
  </tr>
  <tr>
    <td width="80" align="center" valign="middle">
      <img src="docs/assets/intent-aligner.png" alt="intent-aligner 意图对齐插画" width="60">
    </td>
    <td valign="middle">
      <h3>intent-aligner Skill</h3>
      <p>在实现、实验、写作或规划之前做轻量意图对齐，明确目标、范围、默认假设和不做什么，减少工作流跑偏。</p>
    </td>
  </tr>
  <tr>
    <td width="80" align="center" valign="middle">
      <img src="docs/assets/auto-exp.png" alt="机器学习实验工作流插画" width="60">
    </td>
    <td valign="middle">
      <h3>auto-exp Skill</h3>
      <p>面向机器学习实验的计划、执行、监控、验证、对比和记录，强调实验契约、可复现性与证据链。</p>
    </td>
  </tr>
  <tr>
    <td width="80" align="center" valign="middle">
      <img src="docs/assets/academic-paper-polisher.png" alt="英文学术论文润色插画" width="60">
    </td>
    <td valign="middle">
      <h3>academic-paper-polisher Skill</h3>
      <p>面向已有英文学术论文和段落的综合润色与审计，保护研究事实、主张强度、引文、术语和 LaTeX 结构，并检查论证、表达与 AI 写作痕迹。</p>
    </td>
  </tr>
  <tr>
    <td width="80" align="center" valign="middle">
      <img src="docs/assets/review-comment-decomposer.png" alt="审稿意见拆解与回复规划插画" width="60">
    </td>
    <td valign="middle">
      <h3>review-comment-decomposer Skill</h3>
      <p>结合论文原文，将审稿意见拆成可核验的原子问题，规划补实验与回复构思两条工作线，并生成带中文注释的可编译 LaTeX 回复骨架。</p>
    </td>
  </tr>
  <tr>
    <td width="80" align="center" valign="middle">
      <img src="docs/assets/research-literature-review.png" alt="研究定位与文献对话插画" width="60">
    </td>
    <td valign="middle">
      <h3>research-literature-review Skill</h3>
      <p>面向计算设计科学研究，从同一研究锚点建立问题／理论与技术／算法两条文献线，核验全文、制作对话地图，并澄清最近邻、理论祖先、方法缺口和研究定位。</p>
    </td>
  </tr>
  <tr>
    <td width="80" align="center" valign="middle">
      <img src="docs/assets/autoresearch.png" alt="自主机器学习研究闭环插画" width="60">
    </td>
    <td valign="middle">
      <h3>AutoResearch Skill</h3>
      <p>在冻结 Research Brief、Benchmark 和预算后，自主完成文献机制分析、候选设计、预登记实验、运行修复、实验图路由与阶段反思，直到达到目标或耗尽预登记预算。</p>
    </td>
  </tr>
  <tr>
    <td width="80" align="center" valign="middle">
      <img src="docs/assets/cds-method-innovation.png" alt="计算数据科学方法创新工作流插画" width="60">
    </td>
    <td valign="middle">
      <h3>cds-method-innovation Skill</h3>
      <p>面向计算数据科学方法创新，按阶段完成研究方向发现、常见与近期 baseline 实跑、公平 benchmark、候选创新质询、实验设计与证据记录，并保留方向决策和每次运行历史。</p>
    </td>
  </tr>
</table>

完整来源、版本和本地改动记录见 [`docs/catalog.md`](docs/catalog.md)。

## 目录结构

```text
.
├── .agents/plugins/marketplace.json  # 仓库级 Codex plugin marketplace
├── plugins/                          # 可安装的 plugin 包
│   └── autodl-remote/
│       ├── .codex-plugin/plugin.json
│       ├── skills/
│       ├── mcp/
│       ├── bin/
│       └── config/
├── skills/                           # 不属于某个 plugin 的独立 Skill
│   ├── intent-aligner/
│   ├── auto-exp/
│   ├── academic-paper-polisher/
│   ├── review-comment-decomposer/
│   ├── research-literature-review/
│   ├── autoresearch/
│   └── cds-method-innovation/
├── dist/                             # 可直接分发的安装包
│   └── academic-paper-polisher.skill
├── docs/                             # 目录、来源和视觉资源
└── scripts/                          # 本地验证脚本
```

原则很简单：**plugin 内部拥有的 Skill 就留在 plugin 内部，不重复复制到根目录；真正独立的 Skill 才放进 `skills/`。**

## 快速开始

克隆仓库并检查结构：

```bash
git clone https://github.com/haibarazz/awesome-codex-research.git
cd awesome-codex-research
python3 scripts/validate_repository.py
```

将仓库级 marketplace 加入 Codex：

```bash
codex plugin marketplace add "$PWD"
codex plugin install autodl-remote@awesome-codex-research
```

如果只需要独立 Skill，可以直接把对应目录安装到本机 Codex skills 目录，或通过 Codex 的 skill installer 指向具体路径。
