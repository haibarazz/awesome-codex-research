#!/usr/bin/env python3
"""Generate the deterministic AutoResearch golden-run example project."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

SCRIPT_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_ROOT.parent
sys.path.insert(0, str(SCRIPT_ROOT))

from autoresearch_runtime_core import RuntimeErrorResponse, RuntimeService  # noqa: E402
from autoresearch_runtime_core import service as runtime_service_module  # noqa: E402

FIXED_TIME = "2026-07-19T12:00:00Z"
PRIMARY_METRIC = "auc"


def _write_text(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_json(root: Path, relative: str, payload: Any) -> None:
    _write_text(
        root,
        relative,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
    )


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _synthetic_fixture_pdf(title: str, mechanism: str) -> bytes:
    lines = (
        "AutoResearch Synthetic Literature Fixture",
        "SYNTHETIC FIXTURE - NOT A SCHOLARLY FULL TEXT",
        title,
        mechanism,
    )
    text_commands = ["BT", "/F1 12 Tf", "72 720 Td"]
    for index, line in enumerate(lines):
        if index:
            text_commands.append("0 -22 Td")
        text_commands.append(f"({_pdf_escape(line)}) Tj")
    text_commands.append("ET")
    stream = ("\n".join(text_commands) + "\n").encode("ascii")

    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"endstream",
    )

    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{object_number} 0 obj\n".encode("ascii"))
        payload.extend(body)
        payload.extend(b"\nendobj\n")

    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(payload)


def _write_source_artifacts(root: Path) -> None:
    _write_text(
        root,
        "RESEARCH_BRIEF.md",
        """# Golden Tabular AUC Research Brief

Improve validation AUC from 0.8000 toward 0.9000 on a frozen synthetic
binary-classification benchmark. The example has a four-experiment budget and
uses GPU_HOURS as its cost unit.
""",
    )
    _write_text(
        root,
        "BENCHMARK.md",
        """# Frozen Golden Benchmark

- Dataset split: `golden-dataset-v1`
- Primary metric: validation AUC, maximize
- Anchor Baseline: 0.8000
- Promotion threshold: 0.005 absolute AUC
- Comparison-switch threshold: 0.010 absolute AUC
- Full-run qualification threshold: 300 seconds
""",
    )
    _write_text(
        root,
        "evidence/baseline.md",
        "# Anchor Baseline Evidence\n\nSeeds 1–3: 0.8000, 0.8010, 0.7990.",
    )
    _write_text(
        root,
        "evidence/weighting-mechanism.md",
        """# Weighting Mechanism Evidence

The frozen literature review predicts that frequency-aware weighting reduces
majority-example dominance without adding a branch.
""",
    )
    _write_text(
        root,
        "evidence/loss-mechanism.md",
        """# Loss Mechanism Evidence

The pivot direction replaces only the calibration loss and leaves the promoted
backbone and data weighting unchanged.
""",
    )
    _write_json(
        root,
        "configs/weighting-replacement.json",
        {
            "dataset": "golden-dataset-v1",
            "model": "small_mlp",
            "seed": 7,
            "weighting": "frequency_aware",
        },
    )
    paper_specs = (
        (
            "paper-1",
            "Frequency-Aware Learning",
            "Reweighting is predicted to reduce high-frequency sample dominance.",
        ),
        (
            "paper-2",
            "Robust Tabular Calibration",
            "Calibration losses can change ranking quality without adding branches.",
        ),
        (
            "paper-3",
            "Mechanism-Guided Ablation",
            "Component replacement gives cleaner attribution than component addition.",
        ),
    )
    for paper_id, title, mechanism in paper_specs:
        pdf_path = root / f"papers/{paper_id}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(_synthetic_fixture_pdf(title, mechanism))
        _write_text(
            root,
            f"evidence/{paper_id}-mechanism.md",
            f"# {title}\n\n{mechanism}",
        )
    _write_text(
        root,
        "logs/research/literature_survey.md",
        """# Focused Literature Survey

Three synthetic mechanism fixtures demonstrate the expected artifact shape and
route two fictional component-level directions: frequency-aware data weighting
and calibration-loss replacement.
""",
    )


def _init_request() -> dict[str, Any]:
    return {
        "request_id": "init-20260719-001",
        "project_id": "golden-tabular-auc",
        "research_brief_ref": "RESEARCH_BRIEF.md",
        "benchmark": {
            "benchmark_id": "golden-benchmark-v1",
            "benchmark_ref": "BENCHMARK.md",
            "display_metrics": [
                {
                    "metric_id": PRIMARY_METRIC,
                    "label": "AUC",
                    "role": "PRIMARY",
                    "direction": "MAXIMIZE",
                    "unit": "RATIO",
                    "precision": 4,
                }
            ],
        },
        "primary_metric": {
            "metric_id": PRIMARY_METRIC,
            "direction": "MAXIMIZE",
            "target": 0.90,
            "promotion_threshold": 0.005,
            "simplification_tolerance": 0.005,
            "branch_replacement_tolerance": 0.001,
            "fast_run_seconds": 300,
        },
        "promotion_confirmation_policy": {
            "mode": "SINGLE_RUN_JUSTIFIED",
            "single_run_threshold": {
                "resource": "DURATION_SECONDS",
                "value": 300,
            },
            "single_run_justification": (
                "The frozen full run exceeds the five-minute qualification "
                "threshold."
            ),
        },
        "budget": {
            "max_experiments": 4,
            "max_run_seconds": 4000,
            "max_cost": 12,
            "cost_unit": "GPU_HOURS",
        },
        "initial_models": [
            {
                "title": "Stable small MLP",
                "roles": [
                    "ANCHOR_BASELINE",
                    "RESEARCH_BASE",
                    "CHAMPION",
                ],
                "metrics": {PRIMARY_METRIC: 0.80},
                "seed_metrics": {"1": 0.80, "2": 0.801, "3": 0.799},
                "evidence_ref": "evidence/baseline.md",
            }
        ],
    }


def _literature_request() -> dict[str, Any]:
    selected_papers = []
    for index, title in enumerate(
        (
            "Frequency-Aware Learning",
            "Robust Tabular Calibration",
            "Mechanism-Guided Ablation",
        ),
        start=1,
    ):
        selected_papers.append(
            {
                "title": title,
                "pdf_ref": f"papers/paper-{index}.pdf",
                "mechanism_card_ref": f"evidence/paper-{index}-mechanism.md",
            }
        )
    return {
        "request_id": "create-literature-20260719-001",
        "action": "CREATE_LITERATURE",
        "title": "Component-level directions for tabular AUC",
        "trigger": {
            "type": "BOOTSTRAP",
            "source_node_ids": [],
            "source_ref": None,
            "reason": "Bootstrap literature research after freezing the benchmark.",
        },
        "research_question": (
            "Which component replacements can improve AUC without changing the "
            "frozen benchmark?"
        ),
        "search_scope": "Synthetic component-mechanism fixtures for tabular classifiers.",
        "search_outcome": "DIRECTIONS_FOUND",
        "outcome_reason": (
            "Three synthetic fixtures demonstrate two testable example directions."
        ),
        "direction_summary": (
            "First replace data weighting; if supported, pivot to a loss-only "
            "replacement while retaining the promoted base."
        ),
        "selected_papers": selected_papers,
        "literature_survey_ref": "logs/research/literature_survey.md",
    }


def _classification(locus: str, layer: str) -> dict[str, str]:
    return {
        "evidence_class": "N",
        "change_scope": "COMPONENT",
        "research_layer": layer,
        "intervention_locus": locus,
        "change_operator": "REPLACE",
    }


def _candidate_request(
    *,
    request_id: str,
    parent_node_id: str,
    literature_node_id: str,
    title: str,
    hypothesis: str,
    mechanism: str,
    single_main_change: str,
    falsification_condition: str,
    classification: dict[str, str],
    evidence_ref: str,
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "action": "CREATE_CANDIDATE",
        "parent_node_id": parent_node_id,
        "research_base_id": parent_node_id,
        "comparison_target_id": parent_node_id,
        "title": title,
        "hypothesis": hypothesis,
        "mechanism": mechanism,
        "single_main_change": single_main_change,
        "falsification_condition": falsification_condition,
        "classification": classification,
        "candidate_priority": "GOLD",
        "priority_reason": (
            "One component replacement with a falsifiable mediator prediction."
        ),
        "source_node_ids": [literature_node_id],
        "source_reason": "Selected by the synthetic golden-run literature fixture.",
        "evidence_refs": [evidence_ref],
        "refs": {"paper_mechanism_cards": [evidence_ref]},
    }


def _start_request(node_id: str, preregistration: dict[str, Any]) -> dict[str, Any]:
    artifact_root = "artifacts/full-run-20260719-001"
    return {
        "request_id": "full-run-20260719-001",
        "node_id": node_id,
        "run_kind": "FULL",
        "seed": 7,
        "command": (
            "python train.py --config configs/weighting-replacement.json"
        ),
        "code_version": "golden-run-v1",
        "data_version": "golden-dataset-v1",
        "planned_max_seconds": 400,
        "planned_max_cost": 2,
        "config_ref": "configs/weighting-replacement.json",
        "expected_artifacts": [],
        "artifact_refs": {
            "resolved_config": f"{artifact_root}/resolved_config.yaml",
            "metrics_json": f"{artifact_root}/metrics.json",
            "artifact_manifest": f"{artifact_root}/artifacts_manifest.json",
            "trainer_log": f"{artifact_root}/trainer.log",
        },
        "preregistration": preregistration,
    }


def _write_formal_artifacts(
    root: Path, started: dict[str, Any], auc: float
) -> None:
    refs = started["artifact_refs"]
    payloads = {
        "resolved_config": (
            "dataset: golden-dataset-v1\n"
            "model: small_mlp\n"
            "seed: 7\n"
            "weighting: frequency_aware\n"
        ),
        "metrics_json": json.dumps(
            {
                "experiment_id": started["experiment_id"],
                "run_id": started["attempt_id"],
                "best_entry": {"val_auc": auc},
            },
            sort_keys=True,
        )
        + "\n",
        "artifact_manifest": json.dumps(
            {
                "experiment_id": started["experiment_id"],
                "run_id": started["attempt_id"],
                "status": "completed",
                "artifacts": {
                    "metrics_json": refs["metrics_json"],
                    "resolved_config_yaml": refs["resolved_config"],
                    "text_log": refs["trainer_log"],
                },
            },
            sort_keys=True,
        )
        + "\n",
        "trainer_log": "epoch=1 val_auc=0.8120 normal_early_stop=true\n",
    }
    for key, text in payloads.items():
        _write_text(root, refs[key], text)


def _finish_request(started: dict[str, Any], auc: float) -> dict[str, Any]:
    return {
        "request_id": "finish-run-20260719-001",
        "experiment_id": started["experiment_id"],
        "attempt_id": started["attempt_id"],
        "run_outcome": "NORMAL_EARLY_STOP",
        "hypothesis_verdict": "SUPPORTED",
        "metrics": {PRIMARY_METRIC: auc},
        "duration_seconds": 301,
        "cost": 1,
        "hard_constraints_passed": True,
        "stop_reason": "The frozen early-stopping rule fired after one epoch.",
        "checkpoint_ref": None,
        "interpretation": (
            "The weighting replacement improved AUC and supports the predicted "
            "direction."
        ),
        "decision": "Promote provisionally, then pivot to the loss bottleneck.",
    }


def _stage_summary() -> str:
    return """# Stage Summary: Weighting Replacement

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
"""


def _write_handoffs(root: Path) -> None:
    _write_text(
        root,
        "controller_handoffs/experiment_finished.yaml",
        """controller_handoff:
  trigger: EXPERIMENT_FINISHED
  current_phase: RESULT_ROUTING
  controller_status: CONTINUE
  evidence_summary: E001/A01 improved AUC from 0.8000 to 0.8120 under the frozen Benchmark.
  graph_operations:
    - operation: AGGREGATE
      target: RN-0002
      reason: Aggregate the completed result before selecting a route.
  artifacts_written:
    - experiments/E001.md
    - logs/runs/E001/A01.jsonl
    - logs/research/volume_001.md
  candidate_drafts: []
  next_phase: STAGE_REFLECTION
  next_action: Run Stage Reflection on E001 and the promoted-base decision.
  next_target: logs/summaries/volume_001_summary.md
""",
    )
    _write_text(
        root,
        "controller_handoffs/stage_summary_completed.yaml",
        """controller_handoff:
  trigger: STAGE_SUMMARY_COMPLETED
  current_phase: RESULT_ROUTING
  controller_status: CONTINUE
  evidence_summary: The PIVOT route leaves weighting fixed and tests a loss-only explanation.
  graph_operations:
    - operation: BACKTRACK
      target: RN-0002
      reason: Return to the promoted base before opening a distinct direction.
    - operation: GENERATE
      target: null
      reason: Generate one loss-only Candidate Draft from the unresolved mechanism.
  artifacts_written:
    - logs/summaries/volume_001_summary.md
  candidate_drafts:
    - candidate_id: CD-001
      origin: first_principles
      uncertainty_reduced: Weighting mechanism versus general calibration.
      primary_hypothesis: Replacing only calibration loss improves AUC.
      competing_explanation: The gain is specific to frequency-aware weighting.
      single_main_change: Replace only calibration loss.
      predicted_outcome_and_mediator: AUC rises while calibration error falls.
      falsification_condition: AUC does not rise or calibration error moves oppositely.
      minimal_discriminating_experiment: One full loss-only run from RN-0002.
      cost_class: one_full_run
      dependencies: Frozen Benchmark and RN-0002.
      interaction_candidate: false
  next_phase: CANDIDATE_DESIGN
  next_action: Review CD-001 against the current Research Base, then submit one CREATE_CANDIDATE proposal.
  next_target: CD-001
""",
    )


def _write_readme(root: Path) -> None:
    _write_text(
        root,
        "README.md",
        """# AutoResearch Golden Run

This fictional tabular-AUC project is generated by the real Runtime and shows
the final contract after W1–W7, W9, and W10.

| Example class | Artifact |
|---|---|
| Canonical graph | `EXPERIMENT_GRAPH.json` |
| EXPERIMENT_FINISHED handoff | `controller_handoffs/experiment_finished.yaml` |
| STAGE_SUMMARY_COMPLETED handoff | `controller_handoffs/stage_summary_completed.yaml` |
| Finished dual-zone Experiment Card | `experiments/E001.md` |
| Six-section Stage Summary | `logs/summaries/volume_001_summary.md` |
| Real Runtime interactions | `runtime_interactions/*.json` |

Regenerate from the Skill root:

```bash
python3 scripts/generate_golden_run.py
```
""",
    )


def generate(output: Path) -> Path:
    output = output.resolve()
    if output.name != "golden-run":
        raise ValueError("Golden-run output directory must be named 'golden-run'")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    _write_source_artifacts(output)

    original_now = runtime_service_module._now
    runtime_service_module._now = lambda: FIXED_TIME
    try:
        runtime = RuntimeService(output)
        runtime.initialize(_init_request())

        literature_id = runtime.propose(_literature_request())["result"]["node_id"]
        weighting_hypothesis = (
            "Frequency-aware weighting improves AUC by more than 0.5 pp."
        )
        weighting_change = "Replace only the example-weighting component."
        weighting_falsifier = "AUC improvement is no greater than 0.5 pp."
        weighting_classification = _classification("DATA", "L1")
        weighting_candidate = _candidate_request(
            request_id="create-candidate-20260719-001",
            parent_node_id="RN-0001",
            literature_node_id=literature_id,
            title="Frequency-aware weighting replacement",
            hypothesis=weighting_hypothesis,
            mechanism=(
                "The replacement reduces majority-example gradient dominance."
            ),
            single_main_change=weighting_change,
            falsification_condition=weighting_falsifier,
            classification=weighting_classification,
            evidence_ref="evidence/weighting-mechanism.md",
        )
        promoted_candidate_id = runtime.propose(weighting_candidate)["result"][
            "node_id"
        ]
        runtime.propose(
            {
                "request_id": "set-frontier-20260719-001",
                "action": "SET_FRONTIER",
                "node_ids": [promoted_candidate_id],
            }
        )

        preregistration = {
            "hypothesis": weighting_hypothesis,
            "single_main_change": weighting_change,
            "falsification_condition": weighting_falsifier,
            "classification": weighting_classification,
        }
        started = runtime.start_run(
            _start_request(promoted_candidate_id, preregistration)
        )["result"]
        card_path = output / f"experiments/{started['experiment_id']}.md"
        with card_path.open("a", encoding="utf-8") as handle:
            handle.write(
                "\n- 2026-07-19 RUNNING repair note: normalized one CSV dtype; "
                "the preregistered hypothesis and model change were unchanged.\n"
            )
        auc = 0.812
        _write_formal_artifacts(output, started, auc)
        finish_response = runtime.finish_run(_finish_request(started, auc))

        runtime.propose(
            {
                "request_id": "promote-research-base-20260719-001",
                "action": "PROMOTE_RESEARCH_BASE",
                "node_id": promoted_candidate_id,
                "attestations": {
                    "stable": True,
                    "general": True,
                    "composable": True,
                    "reproducible": True,
                },
                "reason": (
                    "The justified full run passed the frozen performance and "
                    "structural gates."
                ),
            }
        )

        _write_text(
            output,
            "logs/summaries/volume_001_summary.md",
            _stage_summary(),
        )
        runtime.propose(
            {
                "request_id": "register-stage-summary-20260719-001",
                "action": "REGISTER_STAGE_SUMMARY",
                "covered_node_ids": ["RN-0001", promoted_candidate_id],
                "route_decision": "PIVOT",
                "trigger": "First supported formal experiment completed.",
                "summary_ref": "logs/summaries/volume_001_summary.md",
                "subagent_calls": 0,
            }
        )

        loss_candidate = _candidate_request(
            request_id="create-candidate-20260719-002",
            parent_node_id=promoted_candidate_id,
            literature_node_id=literature_id,
            title="Calibration-loss replacement",
            hypothesis="Replacing only calibration loss improves AUC.",
            mechanism=(
                "A margin-calibrated loss improves ranking without changing the "
                "promoted weighting component."
            ),
            single_main_change="Replace only calibration loss.",
            falsification_condition=(
                "AUC does not improve or calibration error moves oppositely."
            ),
            classification=_classification("LOSS", "L2"),
            evidence_ref="evidence/loss-mechanism.md",
        )
        frontier_candidate_id = runtime.propose(loss_candidate)["result"]["node_id"]
        runtime.propose(
            {
                "request_id": "set-frontier-20260719-002",
                "action": "SET_FRONTIER",
                "node_ids": [frontier_candidate_id],
            }
        )

        try:
            runtime.propose(
                {
                    "request_id": "set-frontier-20260719-003",
                    "action": "SET_FRONTIER",
                    "node_ids": [frontier_candidate_id, frontier_candidate_id],
                }
            )
        except RuntimeErrorResponse as error:
            rejected_response = error.response()
        else:
            raise RuntimeError("Golden rejected-propose example unexpectedly succeeded")

        inspect_response = runtime.inspect()
        _write_json(
            output,
            "runtime_interactions/inspect.json",
            inspect_response,
        )
        _write_json(
            output,
            "runtime_interactions/rejected_propose.json",
            rejected_response,
        )
        _write_json(
            output,
            "runtime_interactions/finish_run.json",
            finish_response,
        )
        _write_handoffs(output)
        _write_readme(output)

        validation = runtime.validate(render=True)
        if validation["accepted"] is not True:
            raise RuntimeError(
                "Generated golden run failed Runtime validation: "
                + json.dumps(validation, ensure_ascii=False)
            )
    finally:
        runtime_service_module._now = original_now
    (output / ".autoresearch" / "runtime.lock").unlink(missing_ok=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=SKILL_ROOT / "examples" / "golden-run",
    )
    args = parser.parse_args()
    generated = generate(args.output)
    print(generated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
