from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import jsonschema
import yaml

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = SCRIPT_ROOT.parent
GOLDEN_ROOT = SKILL_ROOT / "examples" / "golden-run"
sys.path.insert(0, str(SCRIPT_ROOT))

from autoresearch_runtime_core import RuntimeService  # noqa: E402
from generate_golden_run import generate  # noqa: E402


def _load_json(relative: str) -> dict:
    return json.loads((GOLDEN_ROOT / relative).read_text(encoding="utf-8"))


def _validate_schema(instance: dict, schema_name: str) -> None:
    schema = json.loads(
        (SKILL_ROOT / "assets" / "schemas" / schema_name).read_text(
            encoding="utf-8"
        )
    )
    jsonschema.Draft202012Validator(schema).validate(instance)


def _normalize_role_event_order(graph: dict) -> dict:
    normalized = json.loads(json.dumps(graph))
    normalized["role_events"] = sorted(
        normalized["role_events"],
        key=lambda event: json.dumps(
            event, ensure_ascii=False, sort_keys=True
        ),
    )
    return normalized


def test_golden_run_contains_all_six_example_classes() -> None:
    assert (GOLDEN_ROOT / "EXPERIMENT_GRAPH.json").is_file()
    assert (
        GOLDEN_ROOT / "controller_handoffs/experiment_finished.yaml"
    ).is_file()
    assert (
        GOLDEN_ROOT / "controller_handoffs/stage_summary_completed.yaml"
    ).is_file()
    assert sorted((GOLDEN_ROOT / "experiments").glob("E*.md")) == [
        GOLDEN_ROOT / "experiments/E001.md"
    ]
    assert sorted((GOLDEN_ROOT / "logs/summaries").glob("*.md")) == [
        GOLDEN_ROOT / "logs/summaries/volume_001_summary.md"
    ]
    assert {
        path.name
        for path in (GOLDEN_ROOT / "runtime_interactions").glob("*.json")
    } == {"inspect.json", "rejected_propose.json", "finish_run.json"}


def test_golden_run_graph_state_responses_and_runtime_validate(
    tmp_path: Path,
) -> None:
    graph = _load_json("EXPERIMENT_GRAPH.json")
    state = _load_json(".autoresearch/runtime_state.json")
    _validate_schema(graph, "experiment_graph.schema.json")
    _validate_schema(state, "runtime_state.schema.json")

    response_schema = json.loads(
        (
            SKILL_ROOT
            / "assets"
            / "schemas"
            / "runtime_response.schema.json"
        ).read_text(encoding="utf-8")
    )
    response_validator = jsonschema.Draft202012Validator(response_schema)
    for path in sorted((GOLDEN_ROOT / "runtime_interactions").glob("*.json")):
        response = json.loads(path.read_text(encoding="utf-8"))
        response_validator.validate(response)
        assert "start-run" not in response["allowed_next_actions"]
        assert "finish-run" not in response["allowed_next_actions"]

    for path in GOLDEN_ROOT.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))

    project = tmp_path / "golden-run"
    shutil.copytree(GOLDEN_ROOT, project)
    validation = RuntimeService(project).validate(render=False)
    assert validation["accepted"] is True
    assert validation["result"]["violations"] == []


def test_golden_run_graph_has_required_scientific_shape() -> None:
    graph = _load_json("EXPERIMENT_GRAPH.json")
    research_nodes = [
        node for node in graph["nodes"] if node["node_type"] == "RESEARCH"
    ]
    literature_nodes = [
        node for node in graph["nodes"] if node["node_type"] == "LITERATURE"
    ]
    assert len(research_nodes) == 3
    assert len(literature_nodes) == 1
    literature = literature_nodes[0]
    assert literature["search_outcome"] == "DIRECTIONS_FOUND"
    assert len(literature["selected_papers"]) == 3

    role_state = graph["role_states"][graph["active_benchmark_id"]]
    assert role_state["anchor_baseline_id"] == "RN-0001"
    assert role_state["research_base_id"] == "RN-0002"
    assert role_state["champion_id"] == "RN-0002"
    supported = next(node for node in research_nodes if node["node_id"] == "RN-0002")
    frontier = next(node for node in research_nodes if node["node_id"] == "RN-0003")
    assert supported["hypothesis_verdict"] == "SUPPORTED"
    assert supported["run_outcome"] == "NORMAL_EARLY_STOP"
    assert frontier["hypothesis_verdict"] == "UNTESTED"
    assert frontier["run_outcome"] == "NOT_RUN"
    assert graph["active_frontier"] == ["RN-0003"]
    assert graph["stage_summaries"][0]["route_decision"] == "PIVOT"
    assert any(
        event["role"] == "RESEARCH_BASE"
        and event["node_id"] == "RN-0002"
        and event["single_seed_provisional"] is True
        for event in graph["role_events"]
    )
    assert {edge["edge_type"] for edge in graph["edges"]} >= {
        "PRIMARY_PARENT",
        "DIRECTION",
    }


def test_golden_run_markdown_and_handoffs_follow_final_contract() -> None:
    card = (GOLDEN_ROOT / "experiments/E001.md").read_text(encoding="utf-8")
    assert card.count("## Runtime Record") == 1
    assert card.count("## Research Notes") == 1
    assert "- status: FINISHED" in card
    assert "RUNNING repair note" in card

    summary = (
        GOLDEN_ROOT / "logs/summaries/volume_001_summary.md"
    ).read_text(encoding="utf-8")
    expected_headings = [
        "## 一、我们到底知道了什么？",
        "## 二、这些结果为什么发生？",
        "## 三、我们可能错在哪里？",
        "## 四、这一阶段留下了什么可迁移认识？",
        "## 五、下一阶段有哪些真正可判别的方向？",
        "## 六、研究路线现在应当怎么走？",
    ]
    assert [
        line for line in summary.splitlines() if line.startswith("## ")
    ] == expected_headings
    assert "UNKNOWN" in summary
    assert "Non-repeat rule:" in summary
    assert "AB = NOT_JUSTIFIED" in summary

    finished_handoff = yaml.safe_load(
        (
            GOLDEN_ROOT
            / "controller_handoffs/experiment_finished.yaml"
        ).read_text(encoding="utf-8")
    )["controller_handoff"]
    assert finished_handoff["trigger"] == "EXPERIMENT_FINISHED"
    assert finished_handoff["controller_status"] == "CONTINUE"
    assert finished_handoff["next_action"]
    assert [item["operation"] for item in finished_handoff["graph_operations"]] == [
        "AGGREGATE"
    ]

    summary_handoff = yaml.safe_load(
        (
            GOLDEN_ROOT
            / "controller_handoffs/stage_summary_completed.yaml"
        ).read_text(encoding="utf-8")
    )["controller_handoff"]
    assert summary_handoff["trigger"] == "STAGE_SUMMARY_COMPLETED"
    assert summary_handoff["controller_status"] == "CONTINUE"
    assert len(summary_handoff["candidate_drafts"]) == 1
    assert {
        item["operation"] for item in summary_handoff["graph_operations"]
    } == {"BACKTRACK", "GENERATE"}
    assert summary_handoff["next_action"]


def test_golden_run_generator_reproduces_canonical_graph(tmp_path: Path) -> None:
    generated = generate(tmp_path / "golden-run")
    generated_graph = json.loads(
        (generated / "EXPERIMENT_GRAPH.json").read_text(encoding="utf-8")
    )
    committed_graph = _load_json("EXPERIMENT_GRAPH.json")
    assert _normalize_role_event_order(
        generated_graph
    ) == _normalize_role_event_order(committed_graph)


def test_golden_run_generator_writes_self_identified_synthetic_fixtures(
    tmp_path: Path,
) -> None:
    generated = generate(tmp_path / "golden-run")

    for pdf_path in sorted((generated / "papers").glob("*.pdf")):
        payload = pdf_path.read_bytes()
        startxref_marker = b"startxref\n"
        assert payload.startswith(b"%PDF-1.4\n")
        assert b"SYNTHETIC FIXTURE - NOT A SCHOLARLY FULL TEXT" in payload
        assert b"xref\n" in payload
        assert b"trailer\n" in payload
        assert payload.endswith(b"%%EOF\n")

        startxref = int(
            payload.split(startxref_marker, maxsplit=1)[1]
            .splitlines()[0]
        )
        assert payload[startxref:].startswith(b"xref\n")

    graph_text = (generated / "EXPERIMENT_GRAPH.json").read_text(encoding="utf-8")
    survey_text = (generated / "logs/research/literature_survey.md").read_text(
        encoding="utf-8"
    )
    assert "synthetic" in graph_text.lower()
    assert "synthetic" in survey_text.lower()
    assert "full-text" not in graph_text.lower()
    assert "full-text" not in survey_text.lower()


def test_skill_and_workflows_route_first_run_to_golden_example() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    instruction = (
        "Before the first execution, browse "
        "[`examples/golden-run/`](examples/golden-run/) "
        "to understand the expected artifact shapes."
    )
    assert instruction in skill
    assert skill.index(instruction) < skill.index("## Activation Router")
    for workflow in ("workflow.zh.html", "workflow.en.html"):
        text = (SKILL_ROOT / workflow).read_text(encoding="utf-8")
        assert 'href="examples/golden-run/README.md"' in text
