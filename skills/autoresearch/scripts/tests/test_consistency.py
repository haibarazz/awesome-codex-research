from __future__ import annotations

import ast
import csv
import sys
from pathlib import Path

import pytest

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = SCRIPT_ROOT.parent
sys.path.insert(0, str(SCRIPT_ROOT))

import generate_candidate_priority_matrix as priority_generator  # noqa: E402
from autoresearch_runtime_core import RuntimeService  # noqa: E402
from lint_docs import lint_skill_docs  # noqa: E402

SCOPES = {
    "## 4. 组件级矩阵": "COMPONENT",
    "## 5. 协议级矩阵": "PROTOCOL",
    "## 6. 全方法矩阵": "FULL_METHOD",
}
LOCI = {
    "全系统": "SYSTEM",
    "数据": "DATA",
    "特征": "FEATURE",
    "骨干": "BACKBONE",
    "组件": "COMPONENT",
    "分支": "BRANCH",
    "loss": "LOSS",
    "优化": "OPTIMIZATION",
    "推理": "INFERENCE",
}
OPERATORS = ("ADD", "REPLACE", "DELETE", "REWIRE", "MERGE", "SPLIT")


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _markdown_priority_matrix() -> dict[tuple[str, str, str, str], tuple[str, str]]:
    path = SKILL_ROOT / "references" / "candidate_priority_rules.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    parsed: dict[tuple[str, str, str, str], tuple[str, str]] = {}

    for heading, scope in SCOPES.items():
        try:
            heading_index = lines.index(heading)
            header_index = next(
                index
                for index in range(heading_index + 1, len(lines))
                if lines[index].startswith("| Intervention Locus |")
            )
        except (ValueError, StopIteration) as exc:
            raise AssertionError(
                f"Markdown matrix for {scope} could not be parsed"
            ) from exc

        assert _cells(lines[header_index]) == [
            "Intervention Locus",
            "新增",
            "替换",
            "删除",
            "重连",
            "合并",
            "拆分",
        ]
        separator = _cells(lines[header_index + 1])
        assert len(separator) == 7
        assert all(set(cell) <= {":", "-"} and "-" in cell for cell in separator)

        rows = lines[header_index + 2 : header_index + 11]
        assert len(rows) == 9
        for row in rows:
            cells = _cells(row)
            assert len(cells) == 7
            assert cells[0] in LOCI
            for operator, priority in zip(OPERATORS, cells[1:], strict=True):
                canonical_priority = priority.upper()
                assert canonical_priority in {
                    "GOLD",
                    "SILVER",
                    "HOLD",
                    "REJECT",
                    "INVALID",
                }
                status = (
                    "INVALID" if canonical_priority == "INVALID" else "VALID"
                )
                key = ("N", scope, LOCI[cells[0]], operator)
                assert key not in parsed
                parsed[key] = (status, canonical_priority)

    assert len(parsed) == 162
    return parsed


def _csv_priority_matrix() -> dict[tuple[str, str, str, str], tuple[str, str]]:
    path = SKILL_ROOT / "assets" / "candidate_priority_combinations.csv"
    parsed: dict[tuple[str, str, str, str], tuple[str, str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 162
    for row in rows:
        key = (
            row["evidence_class"],
            row["change_scope"],
            row["intervention_locus"],
            row["change_operator"],
        )
        assert key not in parsed
        parsed[key] = (
            row["combination_status"],
            row["structural_default_priority"],
        )
    return parsed


def _generated_priority_matrix() -> dict[
    tuple[str, str, str, str], tuple[str, str]
]:
    parsed: dict[tuple[str, str, str, str], tuple[str, str]] = {}
    for scope in priority_generator.SCOPES:
        for locus in priority_generator.LOCI:
            for operator in priority_generator.OPERATORS:
                status, priority, _, _ = priority_generator.classify(
                    scope, locus, operator
                )
                parsed[("N", scope, locus, operator)] = (status, priority)
    assert len(parsed) == 162
    return parsed


def _runtime_priority_matrix(
    tmp_path: Path,
) -> dict[tuple[str, str, str, str], tuple[str, str]]:
    rows = RuntimeService(tmp_path)._priority_matrix()
    assert len(rows) == 162
    return {
        key: (
            row["combination_status"],
            row["structural_default_priority"],
        )
        for key, row in rows.items()
    }


def _service_priority_matrix_constant() -> dict[
    tuple[str, str, str, str], tuple[str, str]
]:
    service_path = (
        SCRIPT_ROOT / "autoresearch_runtime_core" / "service.py"
    )
    tree = ast.parse(service_path.read_text(encoding="utf-8"))
    assignment = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "PRIORITY_MATRIX"
        ),
        None,
    )
    assert assignment is not None
    value = ast.literal_eval(assignment.value)
    assert isinstance(value, dict)
    assert len(value) == 162
    return value


def test_candidate_priority_representations_match(tmp_path: Path) -> None:
    markdown = _markdown_priority_matrix()
    csv_matrix = _csv_priority_matrix()
    generated = _generated_priority_matrix()
    service_constant = _service_priority_matrix_constant()
    runtime = _runtime_priority_matrix(tmp_path)
    assert markdown == csv_matrix == generated == service_constant == runtime


def test_current_document_routes_and_workflow_anchors_are_consistent() -> None:
    assert lint_skill_docs(SKILL_ROOT) == []


def test_lint_docs_reports_each_required_violation(tmp_path: Path) -> None:
    (tmp_path / "prompts").mkdir()
    (tmp_path / "prompts/on_demand.md").write_text(
        """---
doc_id: on-demand
depends_on: [missing-doc]
activation:
  level: ON_DEMAND
  phases: [BOOTSTRAP]
---
# On demand
""",
        encoding="utf-8",
    )
    (tmp_path / "prompts/bad_level.md").write_text(
        """---
doc_id: bad-level
depends_on: []
activation:
  level: SOMETIMES
---
# Bad level
""",
        encoding="utf-8",
    )
    (tmp_path / "SKILL.md").write_text(
        """---
name: test
description: test
---
# Test
## Activation Router
| Phase | Resource |
|---|---|
| BOOTSTRAP | [missing](prompts/missing.md) |
## Next
""",
        encoding="utf-8",
    )
    (tmp_path / "workflow.zh.html").write_text(
        '<section id="shared"></section><section id="zh-only"></section>',
        encoding="utf-8",
    )
    (tmp_path / "workflow.en.html").write_text(
        '<section id="shared"></section><section id="en-only"></section>',
        encoding="utf-8",
    )

    errors = lint_skill_docs(tmp_path)
    assert any("ON_DEMAND activation must not carry a phases key" in e for e in errors)
    assert any("activation.level 'SOMETIMES'" in e for e in errors)
    assert any("depends_on doc_id 'missing-doc' does not exist" in e for e in errors)
    assert any("Activation Router target does not exist" in e for e in errors)
    assert any("workflow anchor ID sets differ" in e for e in errors)


@pytest.mark.parametrize("path", [SKILL_ROOT / "workflow.zh.html", SKILL_ROOT / "workflow.en.html"])
def test_workflow_pages_have_anchor_ids(path: Path) -> None:
    assert 'id="' in path.read_text(encoding="utf-8")


def test_stage_reflection_draft_limit_and_degradation_policy() -> None:
    text = (SKILL_ROOT / "prompts" / "stage_reflection.md").read_text(
        encoding="utf-8"
    )
    assert "生成 0–3 个实验候选" in text
    assert "通常应保留 2–3 个竞争候选" in text
    assert "0–5" not in text
    assert "未晋级方向" in text
    assert "降级政策不同且互不适用" in text


def test_interaction_gate_has_distinct_degradation_policy() -> None:
    text = (
        SKILL_ROOT / "references" / "interaction_review_gate.md"
    ).read_text(encoding="utf-8")
    assert "降级政策不同且互不适用" in text
    assert "候选一律 Hold" in text


def test_runtime_smoke_semantics_route_to_playbook() -> None:
    runtime = (SKILL_ROOT / "references" / "runtime_api.md").read_text(
        encoding="utf-8"
    )
    section = runtime.split("## 5. Deterministic Enforcement", 1)[1].split(
        "### 5.1 Stable Error Codes", 1
    )[0]
    assert section.count("`SMOKE`") == 1
    assert (
        "[Experiment Playbook §9]"
        "(experiment_playbook.md#9-technical-smoke-and-retry)"
    ) in section


def test_research_contract_records_language_baseline() -> None:
    text = (SKILL_ROOT / "references" / "research_contract.md").read_text(
        encoding="utf-8"
    )
    assert "正文语言保持各文件现状，不强制统一" in text
    assert "同一文件内标题语言必须与正文语言一致" in text
    assert "不要求回溯重写已有文件" in text


def test_fixed_decision_read_bundles_stay_within_attention_budget() -> None:
    controller_path = SKILL_ROOT / "prompts" / "research_graph_controller.md"
    controller_text = controller_path.read_text(encoding="utf-8")
    stage_summary_rows = [
        line
        for line in controller_text.splitlines()
        if line.startswith("| `STAGE_SUMMARY_COMPLETED` |")
    ]
    assert len(stage_summary_rows) == 2
    stage_summary_row = stage_summary_rows[-1]
    assert "Stage Reflection" not in stage_summary_row

    controller = len(controller_text.splitlines())
    graph = len(
        (
            SKILL_ROOT / "references" / "research_graph_protocol.md"
        ).read_text(encoding="utf-8").splitlines()
    )

    def lines(relative_path: str) -> int:
        return len(
            (SKILL_ROOT / relative_path)
            .read_text(encoding="utf-8")
            .splitlines()
        )

    bundles = {
        "BOOTSTRAP_FROZEN": (
            controller
            + graph
            + lines("references/governance_and_autonomy.md")
            + lines("references/benchmark_and_model_roles.md")
        ),
        "LITERATURE_COMPLETED": (
            controller
            + graph
            + lines("references/paper_reproduction_and_innovation.md")
        ),
        "CANDIDATES_READY": (
            controller
            + graph
            + lines("references/candidate_priority_rules.md")
        ),
        "CANDIDATES_READY_MERGE": (
            controller
            + graph
            + lines("references/candidate_priority_rules.md")
            + lines("references/interaction_review_gate.md")
        ),
        "EXPERIMENT_FINISHED": (
            controller
            + graph
            + lines("references/experiment_playbook.md")
            + lines("references/benchmark_and_model_roles.md")
            + lines("references/research_records_protocol.md")
        ),
        "STAGE_SUMMARY_COMPLETED": (
            controller
            + graph
            + lines("references/research_records_protocol.md")
        ),
        "STAGE_REFLECTION": (
            lines("prompts/stage_reflection.md")
            + lines("references/research_records_protocol.md")
        ),
        "STAGE_REFLECTION_MERGE": (
            lines("prompts/stage_reflection.md")
            + lines("references/research_records_protocol.md")
            + lines("references/interaction_review_gate.md")
        ),
    }
    assert max(bundles.values()) <= 1000, bundles
