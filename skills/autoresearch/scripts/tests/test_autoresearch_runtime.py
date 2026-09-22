from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

from autoresearch_runtime_core import RuntimeErrorResponse, RuntimeService  # noqa: E402
from autoresearch_runtime_core import service as runtime_service_module  # noqa: E402
from autoresearch_runtime_core.service import (  # noqa: E402
    ALLOWED_NEXT_ACTIONS,
    STABLE_ERROR_CODES,
)


def _write_project_files(root: Path) -> None:
    (root / "RESEARCH_BRIEF.md").write_text(
        "# Research Brief\n\nTarget AUC: 0.90\n", encoding="utf-8"
    )
    (root / "BENCHMARK.md").write_text(
        "# Benchmark\n\nFrozen split, seed, training budget, and AUC evaluator.\n",
        encoding="utf-8",
    )
    (root / "configs").mkdir()
    (root / "configs/base.json").write_text("{}\n", encoding="utf-8")
    (root / "configs/candidate.json").write_text("{}\n", encoding="utf-8")
    (root / "evidence").mkdir()
    (root / "evidence/baseline.md").write_text(
        "# Baseline evidence\n", encoding="utf-8"
    )
    (root / "evidence/mechanism.md").write_text(
        "# Mechanism evidence\n", encoding="utf-8"
    )


def _promotion_policy(mode: str) -> dict:
    if mode == "SINGLE_RUN_JUSTIFIED":
        return {
            "mode": mode,
            "single_run_threshold": {
                "resource": "DURATION_SECONDS",
                "value": 300,
            },
            "single_run_justification": (
                "A full run exceeds the Benchmark's frozen five-minute "
                "single-run qualification threshold."
            ),
        }
    return {
        "mode": mode,
        "single_run_threshold": None,
        "single_run_justification": None,
    }


def _init_request(
    *,
    max_experiments: int = 8,
    promotion_policy: str = "SINGLE_RUN_JUSTIFIED",
) -> dict:
    return {
        "request_id": "init-001",
        "project_id": "runtime-test",
        "research_brief_ref": "RESEARCH_BRIEF.md",
        "benchmark": {
            "benchmark_id": "benchmark-v1",
            "benchmark_ref": "BENCHMARK.md",
            "display_metrics": [
                {
                    "metric_id": "auc",
                    "label": "AUC",
                    "role": "PRIMARY",
                    "direction": "MAXIMIZE",
                    "unit": "RATIO",
                    "precision": 4,
                }
            ],
        },
        "primary_metric": {
            "metric_id": "auc",
            "direction": "MAXIMIZE",
            "target": 0.90,
            "promotion_threshold": 0.005,
            "simplification_tolerance": 0.005,
            "branch_replacement_tolerance": 0.001,
            "fast_run_seconds": 300,
        },
        "promotion_confirmation_policy": _promotion_policy(promotion_policy),
        "budget": {
            "max_experiments": max_experiments,
            "max_run_seconds": 10000,
            "max_cost": 100,
            "cost_unit": "GPU_HOURS",
        },
        "initial_models": [
            {
                "title": "Stable baseline",
                "roles": [
                    "ANCHOR_BASELINE",
                    "RESEARCH_BASE",
                    "CHAMPION",
                ],
                "metrics": {"auc": 0.80},
                "seed_metrics": {"1": 0.80, "2": 0.801, "3": 0.799},
                "evidence_ref": "evidence/baseline.md",
            }
        ],
    }


def _candidate_request(request_id: str = "candidate-001") -> dict:
    return {
        "request_id": request_id,
        "action": "CREATE_CANDIDATE",
        "parent_node_id": "RN-0001",
        "research_base_id": "RN-0001",
        "comparison_target_id": "RN-0001",
        "title": "Replace the data weighting component",
        "hypothesis": "A mechanism-aligned weighting rule improves AUC by more than 0.5 pp.",
        "mechanism": "The replacement reduces dominance by high-frequency examples.",
        "single_main_change": "Replace only the data weighting component.",
        "falsification_condition": "AUC improvement is no greater than 0.5 pp.",
        "classification": {
            "evidence_class": "N",
            "change_scope": "COMPONENT",
            "research_layer": "L1",
            "intervention_locus": "DATA",
            "change_operator": "REPLACE",
        },
        "candidate_priority": "GOLD",
        "priority_reason": "Single replace operation with direct mechanism evidence.",
        "source_node_ids": [],
        "evidence_refs": ["evidence/mechanism.md"],
        "refs": {"paper_mechanism_cards": ["evidence/mechanism.md"]},
    }


def _start_request(request_id: str, node_id: str, run_kind: str, seed: int) -> dict:
    request = {
        "request_id": request_id,
        "node_id": node_id,
        "run_kind": run_kind,
        "seed": seed,
        "command": "python train.py --config configs/candidate.json",
        "code_version": "deadbeef",
        "data_version": "dataset-v1",
        "planned_max_seconds": 400,
        "planned_max_cost": 2,
        "config_ref": "configs/candidate.json",
        "expected_artifacts": [],
        "preregistration": {
            "hypothesis": "A mechanism-aligned weighting rule improves AUC by more than 0.5 pp.",
            "single_main_change": "Replace only the data weighting component.",
            "falsification_condition": "AUC improvement is no greater than 0.5 pp.",
            "classification": {
                "evidence_class": "N",
                "change_scope": "COMPONENT",
                "research_layer": "L1",
                "intervention_locus": "DATA",
                "change_operator": "REPLACE",
            },
        },
    }
    if run_kind != "SMOKE":
        artifact_root = f"artifacts/{request_id}"
        request["artifact_refs"] = {
            "resolved_config": f"{artifact_root}/resolved_config.yaml",
            "metrics_json": f"{artifact_root}/metrics.json",
            "artifact_manifest": f"{artifact_root}/artifacts_manifest.json",
            "trainer_log": f"{artifact_root}/trainer.log",
        }
    return request


def _start_result(service: RuntimeService, request: dict) -> dict:
    return service.start_run(request)["result"]


def _inspect_result(service: RuntimeService) -> dict:
    return service.inspect()["result"]


def _finish_request(
    request_id: str,
    experiment_id: str,
    attempt_id: str,
    *,
    auc: float,
    duration: float,
) -> dict:
    return {
        "request_id": request_id,
        "experiment_id": experiment_id,
        "attempt_id": attempt_id,
        "run_outcome": "NORMAL_EARLY_STOP",
        "hypothesis_verdict": "SUPPORTED",
        "metrics": {"auc": auc},
        "duration_seconds": duration,
        "cost": 1,
        "hard_constraints_passed": True,
        "stop_reason": "Frozen early-stopping rule fired.",
        "checkpoint_ref": None,
        "interpretation": "The result supports the preregistered direction.",
        "decision": "Evaluate Research Base promotion.",
    }


def _write_formal_artifacts(
    service: RuntimeService,
    started: dict,
    *,
    auc: float,
) -> None:
    started = started.get("result", started)
    refs = started["artifact_refs"]
    payloads = {
        "resolved_config": "seed: 1\n",
        "metrics_json": json.dumps(
            {
                "experiment_id": started["experiment_id"],
                "run_id": started["attempt_id"],
                "best_entry": {"val_auc": auc},
            }
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
            }
        )
        + "\n",
        "trainer_log": "training complete\n",
    }
    for key, text in payloads.items():
        path = service.root / refs[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _finish_formal_run(
    service: RuntimeService,
    started: dict,
    request_id: str,
    *,
    auc: float,
    duration: float,
    envelope: bool = False,
) -> dict:
    _write_formal_artifacts(service, started, auc=auc)
    started = started.get("result", started)
    response = service.finish_run(
        _finish_request(
            request_id,
            started["experiment_id"],
            started["attempt_id"],
            auc=auc,
            duration=duration,
        )
    )
    return response if envelope else response["result"]


@pytest.fixture()
def service(tmp_path: Path) -> RuntimeService:
    _write_project_files(tmp_path)
    runtime = RuntimeService(tmp_path)
    runtime.initialize(_init_request())
    return runtime


def _create_and_select(service: RuntimeService) -> str:
    created = service.propose(_candidate_request())
    node_id = created["result"]["node_id"]
    service.propose(
        {
            "request_id": "frontier-001",
            "action": "SET_FRONTIER",
            "node_ids": [node_id],
        }
    )
    return node_id


def test_init_creates_canonical_graph_state_and_html(service: RuntimeService) -> None:
    root = service.root
    assert (root / "EXPERIMENT_GRAPH.json").is_file()
    assert (root / "EXPERIMENT_GRAPH.html").is_file()
    assert (root / ".autoresearch/runtime_state.json").is_file()
    result = service.validate()
    assert result["accepted"] is True
    assert result["result"]["violations"] == []


def test_init_requires_explicit_promotion_confirmation_policy(
    tmp_path: Path,
) -> None:
    _write_project_files(tmp_path)
    request = _init_request()
    request.pop("promotion_confirmation_policy")
    with pytest.raises(RuntimeErrorResponse):
        RuntimeService(tmp_path).initialize(request)


def test_runtime_phase_last_trigger_and_reflection_counter(
    service: RuntimeService,
) -> None:
    inspected = _inspect_result(service)
    assert inspected["current_phase"] == "BOOTSTRAP"
    assert inspected["last_trigger"] == "BOOTSTRAP_FROZEN"

    node_id = _create_and_select(service)
    started = _start_result(
        service,
        _start_request("phase-run-001", node_id, "FULL", 1),
    )
    inspected = _inspect_result(service)
    assert inspected["current_phase"] == "EXPERIMENT_EXECUTION"
    assert inspected["last_trigger"] == "EXPERIMENT_STARTED"

    _finish_formal_run(
        service,
        started,
        "phase-finish-001",
        auc=0.81,
        duration=301,
    )
    inspected = _inspect_result(service)
    assert inspected["current_phase"] == "RESULT_ROUTING"
    assert inspected["last_trigger"] == "EXPERIMENT_FINISHED"

    summary_ref = service.root / "logs/summaries/volume_001_summary.md"
    summary_ref.parent.mkdir(parents=True, exist_ok=True)
    summary_ref.write_text("# Stage Summary\n", encoding="utf-8")
    service.propose(
        {
            "request_id": "register-stage-summary-001",
            "action": "REGISTER_STAGE_SUMMARY",
            "covered_node_ids": [node_id],
            "route_decision": "DEEPEN",
            "trigger": "First formal experiment completed.",
            "summary_ref": "logs/summaries/volume_001_summary.md",
            "subagent_calls": 2,
        }
    )
    inspected = _inspect_result(service)
    assert inspected["current_phase"] == "RESULT_ROUTING"
    assert inspected["last_trigger"] == "STAGE_SUMMARY_COMPLETED"
    assert inspected["audit_counters"]["stage_reflections"] == 1
    assert inspected["audit_counters"]["subagent_calls"] == 2


def _build_runtime_response_examples(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, object]:
    monkeypatch.setattr(
        runtime_service_module,
        "_now",
        lambda: "2026-07-19T00:00:00Z",
    )
    _write_project_files(root)
    runtime = RuntimeService(root)
    responses = [runtime.initialize(_init_request())]

    first = runtime.propose(_candidate_request("response-candidate-001"))
    responses.append(first)
    first_node_id = first["result"]["node_id"]
    responses.append(
        runtime.propose(
            {
                "request_id": "response-frontier-001",
                "action": "SET_FRONTIER",
                "node_ids": [first_node_id],
            }
        )
    )
    inspected = runtime.inspect()
    responses.append(inspected)

    node_ids = [first_node_id]
    for index in range(1, 4):
        candidate = _candidate_request(f"response-candidate-{index + 1:03d}")
        candidate["title"] += f" {index + 1}"
        response = runtime.propose(candidate)
        responses.append(response)
        node_ids.append(response["result"]["node_id"])
    with pytest.raises(RuntimeErrorResponse) as captured:
        runtime.propose(
            {
                "request_id": "response-frontier-rejected-001",
                "action": "SET_FRONTIER",
                "node_ids": node_ids,
            }
        )
    rejection = captured.value.response()
    responses.append(rejection)

    started = runtime.start_run(
        _start_request("response-run-001", first_node_id, "FULL", 1)
    )
    responses.append(started)
    finished = _finish_formal_run(
        runtime,
        started,
        "response-finish-001",
        auc=0.81,
        duration=301,
        envelope=True,
    )
    responses.append(finished)
    responses.append(runtime.validate(render=False))
    return {
        "all": responses,
        "inspect": inspected,
        "rejected_propose": rejection,
        "finish_run": finished,
    }


def test_runtime_response_schema_validates_real_responses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    schema = json.loads(
        (
            SCRIPT_ROOT.parent
            / "assets/schemas/runtime_response.schema.json"
        ).read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(schema)
    examples = _build_runtime_response_examples(tmp_path, monkeypatch)
    inspected = examples["inspect"]
    rejection = examples["rejected_propose"]
    assert isinstance(inspected, dict)
    assert isinstance(rejection, dict)
    assert inspected["result"]["current_phase"] == "CANDIDATE_DESIGN"
    assert inspected["result"]["last_trigger"] == "CANDIDATES_READY"
    assert rejection["error_code"] == "INVALID_FRONTIER"

    responses = examples["all"]
    assert isinstance(responses, list)
    for response in responses:
        assert isinstance(response, dict)
        validator.validate(response)
        assert set(response["allowed_next_actions"]) <= ALLOWED_NEXT_ACTIONS


def test_documented_runtime_examples_match_real_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    examples = _build_runtime_response_examples(tmp_path, monkeypatch)
    runtime_api = (
        SCRIPT_ROOT.parent / "references/runtime_api.md"
    ).read_text(encoding="utf-8")
    assert "PROVENANCE:" in runtime_api
    for name in ("inspect", "rejected_propose", "finish_run"):
        section = runtime_api.split(
            f"<!-- RUNTIME_RESPONSE_EXAMPLE:{name}:START -->", 1
        )[1].split(
            f"<!-- RUNTIME_RESPONSE_EXAMPLE:{name}:END -->", 1
        )[0]
        match = re.search(r"```json\n(.*?)\n```", section, re.DOTALL)
        assert match is not None
        assert json.loads(match.group(1)) == examples[name]


def _runtime_error_codes(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name)
            and node.func.id == "RuntimeErrorResponse"
        )
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    }


def test_error_code_table_and_allowed_actions_match_runtime() -> None:
    expected_allowed_actions = {
        "CREATE_LITERATURE",
        "CREATE_CANDIDATE",
        "CREATE_REPAIR",
        "CREATE_MERGE",
        "SET_FRONTIER",
        "HOLD_NODE",
        "REOPEN_NODE",
        "CLOSE_NODE",
        "PROMOTE_RESEARCH_BASE",
        "ASSIGN_REFERENCE_BASELINE",
        "REGISTER_STAGE_SUMMARY",
        "REGISTER_BASELINE_SEED_EVIDENCE",
        "FINALIZE_RESEARCH",
        "inspect",
        "validate",
    }
    assert ALLOWED_NEXT_ACTIONS == expected_allowed_actions

    used_codes = _runtime_error_codes(
        SCRIPT_ROOT / "autoresearch_runtime_core/service.py"
    )
    used_codes |= _runtime_error_codes(SCRIPT_ROOT / "autoresearch_runtime.py")
    assert used_codes == STABLE_ERROR_CODES

    runtime_api = (
        SCRIPT_ROOT.parent / "references/runtime_api.md"
    ).read_text(encoding="utf-8")
    error_table = runtime_api.split(
        "<!-- STABLE_ERROR_CODES:START -->", 1
    )[1].split("<!-- STABLE_ERROR_CODES:END -->", 1)[0]
    documented_codes = set(
        re.findall(r"^\| `([A-Z][A-Z0-9_]+)` \|", error_table, re.MULTILINE)
    )
    assert documented_codes == STABLE_ERROR_CODES

    response_schema = json.loads(
        (
            SCRIPT_ROOT.parent
            / "assets/schemas/runtime_response.schema.json"
        ).read_text(encoding="utf-8")
    )
    schema_actions = set(
        response_schema["$defs"]["allowedAction"]["enum"]
    )
    assert schema_actions == expected_allowed_actions


def test_frozen_benchmark_change_requires_human_review(service: RuntimeService) -> None:
    benchmark = service.root / "BENCHMARK.md"
    benchmark.write_text(benchmark.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
    with pytest.raises(RuntimeErrorResponse) as captured:
        service.inspect()
    assert captured.value.code == "FROZEN_CONTRACT_CHANGED"
    assert captured.value.controller_status == "HUMAN_REVIEW_REQUIRED"


def test_illegal_frontier_is_rejected_without_mutating_graph(service: RuntimeService) -> None:
    created_ids = []
    for index in range(4):
        request = _candidate_request(f"candidate-{index + 1:03d}")
        request["title"] += f" {index}"
        created_ids.append(service.propose(request)["result"]["node_id"])
    before = json.loads(
        (service.root / "EXPERIMENT_GRAPH.json").read_text(encoding="utf-8")
    )
    with pytest.raises(RuntimeErrorResponse) as captured:
        service.propose(
            {
                "request_id": "frontier-too-large",
                "action": "SET_FRONTIER",
                "node_ids": created_ids,
            }
        )
    after = json.loads(
        (service.root / "EXPERIMENT_GRAPH.json").read_text(encoding="utf-8")
    )
    assert captured.value.code == "INVALID_FRONTIER"
    assert after["revision"] == before["revision"]
    assert after["active_frontier"] == []


def test_single_run_justified_promotes_provisionally(
    service: RuntimeService,
) -> None:
    node_id = _create_and_select(service)
    started = _start_result(service, _start_request("run-001", node_id, "FULL", 1))
    finished = _finish_formal_run(
        service,
        started,
        "finish-001",
        auc=0.81,
        duration=301,
    )
    assert finished["promotion_gate"]["status"] == "ELIGIBLE"
    promoted = service.propose(
        {
            "request_id": "promote-001",
            "action": "PROMOTE_RESEARCH_BASE",
            "node_id": node_id,
            "attestations": {
                "stable": True,
                "general": True,
                "composable": True,
                "reproducible": True,
            },
            "reason": "Justified single run passed performance and structural gates.",
        }
    )
    assert promoted["result"]["previous_research_base_id"] == "RN-0001"
    research_base = _inspect_result(service)["roles"]["research_base"]
    assert research_base["node_id"] == node_id
    assert research_base["single_seed_provisional"] is True
    graph = json.loads(
        (service.root / "EXPERIMENT_GRAPH.json").read_text(encoding="utf-8")
    )
    event = graph["role_events"][-1]
    assert event["role"] == "RESEARCH_BASE"
    assert event["single_seed_provisional"] is True
    assert (service.root / f"experiments/{started['experiment_id']}.md").is_file()
    assert (
        service.root
        / f"logs/runs/{started['experiment_id']}/{started['attempt_id']}.jsonl"
    ).is_file()
    assert service.validate()["accepted"] is True


def test_single_run_justified_requires_frozen_cost_threshold(
    tmp_path: Path,
) -> None:
    _write_project_files(tmp_path)
    service = RuntimeService(tmp_path)
    request = _init_request()
    request["promotion_confirmation_policy"]["single_run_threshold"]["value"] = 600
    service.initialize(request)
    node_id = _create_and_select(service)
    started = _start_result(
        service,
        _start_request("single-threshold-run", node_id, "FULL", 1),
    )
    finished = _finish_formal_run(
        service,
        started,
        "single-threshold-finish",
        auc=0.81,
        duration=301,
    )
    assert finished["promotion_gate"]["status"] == "INELIGIBLE"
    assert "qualification threshold" in finished["promotion_gate"]["reason"]


def test_one_confirm_seed_requires_one_additional_full_seed(
    tmp_path: Path,
) -> None:
    _write_project_files(tmp_path)
    service = RuntimeService(tmp_path)
    init_request = _init_request(promotion_policy="ONE_CONFIRM_SEED")
    init_request["initial_models"][0]["seed_metrics"] = {"1": 0.80}
    service.initialize(init_request)
    node_id = _create_and_select(service)
    started = _start_result(
        service, _start_request("one-seed-run-1", node_id, "FULL", 1)
    )
    finished = _finish_formal_run(
        service,
        started,
        "one-seed-finish-1",
        auc=0.81,
        duration=301,
    )
    assert finished["promotion_gate"]["status"] == "NEEDS_SEEDS"

    started = _start_result(
        service,
        _start_request(
            "one-seed-run-2",
            node_id,
            "PROMOTION_CONFIRMATION",
            2,
        ),
    )
    finished = _finish_formal_run(
        service,
        started,
        "one-seed-finish-2",
        auc=0.811,
        duration=301,
    )
    assert finished["promotion_gate"]["status"] == "MISSING_BASELINE_SEEDS"
    (service.root / "evidence/baseline-seed-2.md").write_text(
        "# Baseline seed 2 evidence\n",
        encoding="utf-8",
    )
    service.propose(
        {
            "request_id": "register-baseline-seed-2",
            "action": "REGISTER_BASELINE_SEED_EVIDENCE",
            "node_id": "RN-0001",
            "seed": 2,
            "primary_value": 0.801,
            "evidence_ref": "evidence/baseline-seed-2.md",
        }
    )
    promoted = service.propose(
        {
            "request_id": "promote-one-confirm-seed",
            "action": "PROMOTE_RESEARCH_BASE",
            "node_id": node_id,
            "attestations": {
                "stable": True,
                "general": True,
                "composable": True,
                "reproducible": True,
            },
            "reason": "Two full seeds passed the frozen confirmation policy.",
        }
    )
    assert promoted["result"]["promotion_gate"]["status"] == "ELIGIBLE"
    assert (
        _inspect_result(service)["roles"]["research_base"][
            "single_seed_provisional"
        ]
        is False
    )
    assert service.validate()["accepted"] is True


def test_two_seeds_requires_two_additional_full_seeds(
    tmp_path: Path,
) -> None:
    _write_project_files(tmp_path)
    service = RuntimeService(tmp_path)
    service.initialize(_init_request(promotion_policy="TWO_SEEDS"))
    node_id = _create_and_select(service)
    started = _start_result(
        service, _start_request("fast-run-1", node_id, "FULL", 1)
    )
    finished = _finish_formal_run(
        service,
        started,
        "fast-finish-1",
        auc=0.81,
        duration=100,
    )
    assert finished["promotion_gate"]["status"] == "NEEDS_SEEDS"

    for ordinal, seed, auc in ((2, 2, 0.811), (3, 3, 0.809)):
        started = _start_result(
            service,
            _start_request(
                f"fast-run-{ordinal}",
                node_id,
                "PROMOTION_CONFIRMATION",
                seed,
            )
        )
        finished = _finish_formal_run(
            service,
            started,
            f"fast-finish-{ordinal}",
            auc=auc,
            duration=100,
        )
    assert finished["promotion_gate"]["status"] == "ELIGIBLE"
    assert service.validate()["accepted"] is True


def test_request_id_is_idempotent_and_conflicts_are_rejected(
    service: RuntimeService,
) -> None:
    first = service.propose(_candidate_request())
    second = service.propose(_candidate_request())
    assert first == second
    conflicting = _candidate_request()
    conflicting["title"] = "Different payload"
    with pytest.raises(RuntimeErrorResponse) as captured:
        service.propose(conflicting)
    assert captured.value.code == "IDEMPOTENCY_CONFLICT"


def test_closed_node_cannot_be_reopened(service: RuntimeService) -> None:
    node_id = service.propose(_candidate_request())["result"]["node_id"]
    service.propose(
        {
            "request_id": "close-candidate-001",
            "action": "CLOSE_NODE",
            "node_id": node_id,
            "reason": "The route has no remaining research value.",
        }
    )

    with pytest.raises(RuntimeErrorResponse) as captured:
        service.propose(
            {
                "request_id": "reopen-closed-001",
                "action": "REOPEN_NODE",
                "node_id": node_id,
                "evidence_refs": ["evidence/mechanism.md"],
            }
        )

    assert captured.value.code == "INVALID_TRANSITION"
    graph = json.loads(
        (service.root / "EXPERIMENT_GRAPH.json").read_text(encoding="utf-8")
    )
    node = next(item for item in graph["nodes"] if item["node_id"] == node_id)
    assert node["branch_status"] == "CLOSED"


def test_smoke_does_not_consume_the_last_experiment_before_full_run(
    tmp_path: Path,
) -> None:
    _write_project_files(tmp_path)
    service = RuntimeService(tmp_path)
    service.initialize(_init_request(max_experiments=1))
    node_id = _create_and_select(service)
    smoke = _start_result(
        service, _start_request("smoke-run", node_id, "SMOKE", 1)
    )
    smoke_result = service.finish_run(
        {
            "request_id": "smoke-finish",
            "experiment_id": smoke["experiment_id"],
            "attempt_id": smoke["attempt_id"],
            "run_outcome": "COMPLETED",
            "hypothesis_verdict": "NOT_EVALUABLE",
            "metrics": {"auc": 0.80},
            "duration_seconds": 2,
            "cost": 0,
            "hard_constraints_passed": True,
            "stop_reason": "Engineering path completed.",
            "checkpoint_ref": None,
        }
    )["result"]
    assert smoke_result["controller_status"] == "CONTINUE"
    full = _start_result(
        service, _start_request("full-after-smoke", node_id, "FULL", 1)
    )
    assert full["experiment_id"] == smoke["experiment_id"]
    assert full["attempt_id"] == "A02"


def test_formal_run_requires_typed_artifact_refs(service: RuntimeService) -> None:
    node_id = _create_and_select(service)
    request = _start_request("missing-formal-refs", node_id, "FULL", 1)
    request.pop("artifact_refs")

    with pytest.raises(RuntimeErrorResponse) as captured:
        service.start_run(request)

    assert captured.value.code == "FORMAL_ARTIFACTS_REQUIRED"
    assert _inspect_result(service)["active_run"] is None


def test_formal_finish_rejects_missing_artifacts_without_mutation(
    service: RuntimeService,
) -> None:
    node_id = _create_and_select(service)
    started = _start_result(
        service,
        _start_request("missing-formal-artifacts", node_id, "FULL", 1)
    )
    revision = service.inspect()["revision"]

    with pytest.raises(RuntimeErrorResponse) as captured:
        service.finish_run(
            _finish_request(
                "missing-formal-finish",
                started["experiment_id"],
                started["attempt_id"],
                auc=0.81,
                duration=100,
            )
        )

    assert captured.value.code == "FORMAL_ARTIFACT_MISSING"
    assert service.inspect()["revision"] == revision
    assert _inspect_result(service)["active_run"]["attempt_id"] == started["attempt_id"]


def test_formal_finish_uses_metrics_json_and_rejects_inline_mismatch(
    service: RuntimeService,
) -> None:
    node_id = _create_and_select(service)
    started = _start_result(
        service,
        _start_request("artifact-metric-run", node_id, "FULL", 1)
    )
    _write_formal_artifacts(service, started, auc=0.81)
    mismatched = _finish_request(
        "artifact-metric-mismatch",
        started["experiment_id"],
        started["attempt_id"],
        auc=0.82,
        duration=100,
    )
    with pytest.raises(RuntimeErrorResponse) as captured:
        service.finish_run(mismatched)
    assert captured.value.code == "ARTIFACT_METRICS_MISMATCH"

    accepted = dict(mismatched)
    accepted["request_id"] = "artifact-metric-authoritative"
    accepted.pop("metrics")
    result = service.finish_run(accepted)
    assert result["accepted"] is True
    state = json.loads(
        (service.root / ".autoresearch/runtime_state.json").read_text(
            encoding="utf-8"
        )
    )
    attempt = state["experiments"][started["experiment_id"]]["attempts"][0]
    assert attempt["metrics"] == {"auc": 0.81}
    assert set(attempt["artifact_sha256"]) == {
        "resolved_config",
        "metrics_json",
        "artifact_manifest",
        "trainer_log",
    }

    metrics_path = service.root / started["artifact_refs"]["metrics_json"]
    metrics_path.write_text('{"metrics":{"auc":0.99}}\n', encoding="utf-8")
    validation = service.validate(render=False)
    assert validation["accepted"] is False
    assert any(
        "hash changed" in item["message"] for item in validation["violations"]
    )


def test_cli_init_and_inspect_emit_machine_readable_json(tmp_path: Path) -> None:
    _write_project_files(tmp_path)
    request_file = tmp_path / "init.json"
    request_file.write_text(
        json.dumps(_init_request(), ensure_ascii=False), encoding="utf-8"
    )
    cli = SCRIPT_ROOT / "autoresearch_runtime.py"
    initialized = subprocess.run(
        [
            sys.executable,
            str(cli),
            "--project-root",
            str(tmp_path),
            "init",
            "--request",
            str(request_file),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert initialized.returncode == 0
    assert json.loads(initialized.stdout)["accepted"] is True
    inspected = subprocess.run(
        [
            sys.executable,
            str(cli),
            "--project-root",
            str(tmp_path),
            "inspect",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(inspected.stdout)
    assert inspected.returncode == 0
    assert payload["result"]["roles"]["research_base"]["node_id"] == "RN-0001"


def test_fast_confirmation_remains_available_at_experiment_limit(
    tmp_path: Path,
) -> None:
    _write_project_files(tmp_path)
    service = RuntimeService(tmp_path)
    service.initialize(
        _init_request(
            max_experiments=1,
            promotion_policy="TWO_SEEDS",
        )
    )
    node_id = _create_and_select(service)
    started = _start_result(
        service, _start_request("limit-fast-run", node_id, "FULL", 1)
    )
    finished = _finish_formal_run(
        service,
        started,
        "limit-fast-finish",
        auc=0.81,
        duration=100,
    )
    assert finished["controller_status"] == "CONTINUE"
    assert finished["promotion_gate"]["status"] == "NEEDS_SEEDS"
    confirmation = _start_result(
        service,
        _start_request(
            "limit-confirmation",
            node_id,
            "PROMOTION_CONFIRMATION",
            2,
        )
    )
    assert confirmation["experiment_id"] == started["experiment_id"]


def test_start_run_rejects_plan_larger_than_remaining_hard_budget(
    tmp_path: Path,
) -> None:
    _write_project_files(tmp_path)
    init = _init_request()
    init["budget"]["max_run_seconds"] = 100
    service = RuntimeService(tmp_path)
    service.initialize(init)
    node_id = _create_and_select(service)
    request = _start_request("oversized-plan", node_id, "FULL", 1)
    request["planned_max_seconds"] = 101
    with pytest.raises(RuntimeErrorResponse) as captured:
        service.start_run(request)
    assert captured.value.code == "INSUFFICIENT_TIME_BUDGET"


def test_start_run_rejects_cost_without_frozen_unit(
    tmp_path: Path,
) -> None:
    _write_project_files(tmp_path)
    init = _init_request()
    init["budget"]["max_cost"] = None
    init["budget"]["cost_unit"] = None
    service = RuntimeService(tmp_path)
    service.initialize(init)
    node_id = _create_and_select(service)
    request = _start_request("unitless-cost-plan", node_id, "FULL", 1)
    with pytest.raises(RuntimeErrorResponse) as captured:
        service.start_run(request)
    assert captured.value.code == "INVALID_BUDGET"
    assert "cost unit" in captured.value.violations[0]


def test_stale_candidate_cannot_replace_a_new_research_base(
    service: RuntimeService,
) -> None:
    first_id = _create_and_select(service)
    second_request = _candidate_request("candidate-002")
    second_request["title"] = "Second candidate from the original base"
    second_id = service.propose(second_request)["result"]["node_id"]

    first_run = _start_result(
        service, _start_request("first-run", first_id, "FULL", 1)
    )
    _finish_formal_run(
        service,
        first_run,
        "first-finish",
        auc=0.81,
        duration=301,
    )
    service.propose(
        {
            "request_id": "frontier-second",
            "action": "SET_FRONTIER",
            "node_ids": [second_id],
        }
    )
    second_run = _start_result(
        service,
        _start_request("second-run", second_id, "FULL", 1)
    )
    _finish_formal_run(
        service,
        second_run,
        "second-finish",
        auc=0.812,
        duration=301,
    )
    service.propose(
        {
            "request_id": "promote-second",
            "action": "PROMOTE_RESEARCH_BASE",
            "node_id": second_id,
            "attestations": {
                "stable": True,
                "general": True,
                "composable": True,
                "reproducible": True,
            },
            "reason": "Second candidate passed all promotion gates.",
        }
    )
    with pytest.raises(RuntimeErrorResponse) as captured:
        service.propose(
            {
                "request_id": "promote-stale-first",
                "action": "PROMOTE_RESEARCH_BASE",
                "node_id": first_id,
                "attestations": {
                    "stable": True,
                    "general": True,
                    "composable": True,
                    "reproducible": True,
                },
                "reason": "Attempt an obsolete promotion.",
            }
        )
    assert captured.value.code == "STALE_RESEARCH_BASE"


def test_add_promotion_requires_a_real_replacement_experiment(
    service: RuntimeService,
) -> None:
    request = _candidate_request()
    request["classification"]["change_operator"] = "ADD"
    request["candidate_priority"] = "SILVER"
    node_id = service.propose(request)["result"]["node_id"]
    service.propose(
        {
            "request_id": "frontier-add",
            "action": "SET_FRONTIER",
            "node_ids": [node_id],
        }
    )
    start_request = _start_request("add-run", node_id, "FULL", 1)
    start_request["preregistration"]["classification"]["change_operator"] = "ADD"
    started = _start_result(service, start_request)
    _finish_formal_run(
        service,
        started,
        "add-finish",
        auc=0.81,
        duration=301,
    )
    with pytest.raises(RuntimeErrorResponse) as captured:
        service.propose(
            {
                "request_id": "promote-add-without-replacement",
                "action": "PROMOTE_RESEARCH_BASE",
                "node_id": node_id,
                "attestations": {
                    "stable": True,
                    "general": True,
                    "composable": True,
                    "reproducible": True,
                },
                "independent_function_attestation": True,
                "reason": "Attempt to bypass replacement.",
            }
        )
    assert captured.value.code == "BRANCH_ADDITION_GATE"

    replacement_request = _candidate_request("replacement-unrun")
    replacement_request["title"] = "Unrun replacement control"
    replacement_id = service.propose(replacement_request)["result"]["node_id"]
    with pytest.raises(RuntimeErrorResponse) as captured:
        service.propose(
            {
                "request_id": "promote-add-with-unrun-replacement",
                "action": "PROMOTE_RESEARCH_BASE",
                "node_id": node_id,
                "replacement_node_id": replacement_id,
                "attestations": {
                    "stable": True,
                    "general": True,
                    "composable": True,
                    "reproducible": True,
                },
                "independent_function_attestation": True,
                "reason": "Attempt to use an unrun replacement.",
            }
        )
    assert captured.value.code == "INVALID_REPLACEMENT"


def test_start_run_rejects_preregistration_mismatch(
    service: RuntimeService,
) -> None:
    node_id = _create_and_select(service)
    request = _start_request("mismatched-preregistration", node_id, "FULL", 1)
    request["preregistration"]["hypothesis"] = "A different post-selection hypothesis."

    with pytest.raises(RuntimeErrorResponse) as captured:
        service.start_run(request)

    assert captured.value.code == "PREREGISTRATION_MISMATCH"
    assert _inspect_result(service)["active_run"] is None


def test_research_notes_survive_runtime_card_updates(
    service: RuntimeService,
) -> None:
    node_id = _create_and_select(service)
    started = _start_result(
        service, _start_request("notes-run", node_id, "FULL", 1)
    )
    card_path = service.root / f"experiments/{started['experiment_id']}.md"
    note = "- 2026-07-19: Engineering repair changed only the launcher."
    card_path.write_text(
        card_path.read_text(encoding="utf-8") + note + "\n",
        encoding="utf-8",
    )

    assert service.validate(render=False)["accepted"] is True
    _finish_formal_run(
        service,
        started,
        "notes-finish",
        auc=0.81,
        duration=301,
    )

    finished_card = card_path.read_text(encoding="utf-8")
    assert finished_card.count("## Runtime Record") == 1
    assert finished_card.count("## Research Notes") == 1
    assert note in finished_card
    assert service.validate(render=False)["accepted"] is True


def test_runtime_record_tampering_blocks_validate_and_finish(
    service: RuntimeService,
) -> None:
    node_id = _create_and_select(service)
    started = _start_result(
        service, _start_request("tampered-card-run", node_id, "FULL", 1)
    )
    card_path = service.root / f"experiments/{started['experiment_id']}.md"
    card_path.write_text(
        card_path.read_text(encoding="utf-8").replace(
            "- status: RUNNING", "- status: FINISHED", 1
        ),
        encoding="utf-8",
    )
    _write_formal_artifacts(service, started, auc=0.81)

    validation = service.validate(render=False)
    assert validation["accepted"] is False
    assert any(
        "Runtime Record hash changed" in violation["message"]
        for violation in validation["violations"]
    )
    with pytest.raises(RuntimeErrorResponse) as captured:
        service.finish_run(
            _finish_request(
                "tampered-card-finish",
                started["experiment_id"],
                started["attempt_id"],
                auc=0.81,
                duration=301,
            )
        )
    assert captured.value.code == "CANONICAL_INCONSISTENCY"
    assert any(
        "Runtime Record hash changed" in violation
        for violation in captured.value.violations
    )


def test_validate_detects_missing_runtime_owned_card(service: RuntimeService) -> None:
    node_id = _create_and_select(service)
    started = _start_result(
        service, _start_request("missing-card-run", node_id, "FULL", 1)
    )
    (service.root / f"experiments/{started['experiment_id']}.md").unlink()
    result = service.validate(render=False)
    assert result["accepted"] is False
    assert any(
        "Experiment Card" in violation["message"]
        for violation in result["violations"]
    )


def test_champion_is_reconciled_after_multi_seed_average_falls(
    tmp_path: Path,
) -> None:
    _write_project_files(tmp_path)
    service = RuntimeService(tmp_path)
    service.initialize(_init_request(promotion_policy="TWO_SEEDS"))
    node_id = _create_and_select(service)
    first = _start_result(
        service, _start_request("champion-seed-1", node_id, "FULL", 1)
    )
    first_result = _finish_formal_run(
        service,
        first,
        "champion-finish-1",
        auc=0.82,
        duration=100,
    )
    assert any(
        event["role"] == "CHAMPION" and event["node_id"] == node_id
        for event in first_result["role_events"]
    )
    assert _inspect_result(service)["roles"]["champion"]["node_id"] == node_id
    for ordinal, seed in ((2, 2), (3, 3)):
        started = _start_result(
            service,
            _start_request(
                f"champion-seed-{ordinal}",
                node_id,
                "PROMOTION_CONFIRMATION",
                seed,
            )
        )
        _finish_formal_run(
            service,
            started,
            f"champion-finish-{ordinal}",
            auc=0.78,
            duration=100,
        )
    assert _inspect_result(service)["roles"]["champion"]["node_id"] == "RN-0001"


def test_actual_attempt_overrun_is_recorded_but_not_scientific_evidence(
    service: RuntimeService,
) -> None:
    node_id = _create_and_select(service)
    request = _start_request("overrun-run", node_id, "FULL", 1)
    request["planned_max_seconds"] = 100
    started = _start_result(service, request)
    finished = _finish_formal_run(
        service,
        started,
        "overrun-finish",
        auc=0.82,
        duration=101,
    )
    assert finished["budget_overruns"]
    assert finished["hypothesis_verdict"] == "NOT_EVALUABLE"
    assert finished["promotion_gate"]["status"] == "INELIGIBLE"
    assert _inspect_result(service)["roles"]["champion"]["node_id"] == "RN-0001"
