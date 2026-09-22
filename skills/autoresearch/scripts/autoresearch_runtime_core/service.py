"""Proposal validation and deterministic Graph/Experiment lifecycle."""

from __future__ import annotations

import copy
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from .constants import (
    BRANCH_STATUSES,
    CANDIDATE_PRIORITIES,
    CHANGE_OPERATORS,
    CHANGE_SCOPES,
    CONTROLLER_STATUSES,
    EDGE_TYPES,
    EVIDENCE_CLASSES,
    GRAPH_FILENAME,
    GRAPH_HTML_FILENAME,
    HYPOTHESIS_VERDICTS,
    INTERVENTION_LOCI,
    LITERATURE_NODE_KEYS,
    LITERATURE_OUTCOMES,
    LITERATURE_TRIGGER_TYPES,
    MATRIX_PRIORITIES,
    PROMOTION_CONFIRMATION_POLICIES,
    PROPOSAL_ACTIONS,
    RESEARCH_LAYERS,
    RESEARCH_NODE_KEYS,
    ROLE_NAMES,
    RUNTIME_PHASES,
    RUNTIME_TRIGGERS,
    RUN_KINDS,
    RUN_OUTCOMES,
    RUNTIME_DIRECTORY,
    RUNTIME_STATE_FILENAME,
    RUNTIME_VERSION,
    SCHEMA_VERSION,
    STAGE_ROUTES,
    TERMINAL_STATUSES,
    schema_root,
)
from .render import render_graph_html
from .storage import (
    atomic_write_json,
    atomic_write_text,
    canonical_json,
    graph_path,
    load_project,
    normalize_project_root,
    project_lock,
    read_json,
    relative_project_path,
    resolve_project_path,
    sha256_file,
    sha256_text,
    state_path,
)

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
_RN_RE = re.compile(r"^RN-\d{4}$")
_LN_RE = re.compile(r"^LN-\d{4}$")
_EXPERIMENT_RE = re.compile(r"^E\d{3}$")
_ATTEMPT_RE = re.compile(r"^A\d{2}$")

PRIORITY_MATRIX: dict[tuple[str, str, str, str], tuple[str, str]] = {
    ("N", "FULL_METHOD", "SYSTEM", "ADD"): ("VALID", "REJECT"),
    ("N", "FULL_METHOD", "SYSTEM", "REPLACE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "SYSTEM", "DELETE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "SYSTEM", "REWIRE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "SYSTEM", "MERGE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "SYSTEM", "SPLIT"): ("VALID", "REJECT"),
    ("N", "FULL_METHOD", "DATA", "ADD"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "DATA", "REPLACE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "DATA", "DELETE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "DATA", "REWIRE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "DATA", "MERGE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "DATA", "SPLIT"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "FEATURE", "ADD"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "FEATURE", "REPLACE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "FEATURE", "DELETE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "FEATURE", "REWIRE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "FEATURE", "MERGE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "FEATURE", "SPLIT"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "BACKBONE", "ADD"): ("VALID", "REJECT"),
    ("N", "FULL_METHOD", "BACKBONE", "REPLACE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "BACKBONE", "DELETE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "BACKBONE", "REWIRE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "BACKBONE", "MERGE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "BACKBONE", "SPLIT"): ("VALID", "REJECT"),
    ("N", "FULL_METHOD", "COMPONENT", "ADD"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "COMPONENT", "REPLACE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "COMPONENT", "DELETE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "COMPONENT", "REWIRE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "COMPONENT", "MERGE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "COMPONENT", "SPLIT"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "BRANCH", "ADD"): ("VALID", "REJECT"),
    ("N", "FULL_METHOD", "BRANCH", "REPLACE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "BRANCH", "DELETE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "BRANCH", "REWIRE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "BRANCH", "MERGE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "BRANCH", "SPLIT"): ("VALID", "REJECT"),
    ("N", "FULL_METHOD", "LOSS", "ADD"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "LOSS", "REPLACE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "LOSS", "DELETE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "LOSS", "REWIRE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "LOSS", "MERGE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "LOSS", "SPLIT"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "OPTIMIZATION", "ADD"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "OPTIMIZATION", "REPLACE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "OPTIMIZATION", "DELETE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "OPTIMIZATION", "REWIRE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "OPTIMIZATION", "MERGE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "OPTIMIZATION", "SPLIT"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "INFERENCE", "ADD"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "INFERENCE", "REPLACE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "INFERENCE", "DELETE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "INFERENCE", "REWIRE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "INFERENCE", "MERGE"): ("VALID", "HOLD"),
    ("N", "FULL_METHOD", "INFERENCE", "SPLIT"): ("VALID", "HOLD"),
    ("N", "COMPONENT", "SYSTEM", "ADD"): ("INVALID", "INVALID"),
    ("N", "COMPONENT", "SYSTEM", "REPLACE"): ("INVALID", "INVALID"),
    ("N", "COMPONENT", "SYSTEM", "DELETE"): ("INVALID", "INVALID"),
    ("N", "COMPONENT", "SYSTEM", "REWIRE"): ("INVALID", "INVALID"),
    ("N", "COMPONENT", "SYSTEM", "MERGE"): ("INVALID", "INVALID"),
    ("N", "COMPONENT", "SYSTEM", "SPLIT"): ("INVALID", "INVALID"),
    ("N", "COMPONENT", "DATA", "ADD"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "DATA", "REPLACE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "DATA", "DELETE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "DATA", "REWIRE"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "DATA", "MERGE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "DATA", "SPLIT"): ("VALID", "HOLD"),
    ("N", "COMPONENT", "FEATURE", "ADD"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "FEATURE", "REPLACE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "FEATURE", "DELETE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "FEATURE", "REWIRE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "FEATURE", "MERGE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "FEATURE", "SPLIT"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "BACKBONE", "ADD"): ("VALID", "HOLD"),
    ("N", "COMPONENT", "BACKBONE", "REPLACE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "BACKBONE", "DELETE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "BACKBONE", "REWIRE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "BACKBONE", "MERGE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "BACKBONE", "SPLIT"): ("VALID", "HOLD"),
    ("N", "COMPONENT", "COMPONENT", "ADD"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "COMPONENT", "REPLACE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "COMPONENT", "DELETE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "COMPONENT", "REWIRE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "COMPONENT", "MERGE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "COMPONENT", "SPLIT"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "BRANCH", "ADD"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "BRANCH", "REPLACE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "BRANCH", "DELETE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "BRANCH", "REWIRE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "BRANCH", "MERGE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "BRANCH", "SPLIT"): ("VALID", "HOLD"),
    ("N", "COMPONENT", "LOSS", "ADD"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "LOSS", "REPLACE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "LOSS", "DELETE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "LOSS", "REWIRE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "LOSS", "MERGE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "LOSS", "SPLIT"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "OPTIMIZATION", "ADD"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "OPTIMIZATION", "REPLACE"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "OPTIMIZATION", "DELETE"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "OPTIMIZATION", "REWIRE"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "OPTIMIZATION", "MERGE"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "OPTIMIZATION", "SPLIT"): ("VALID", "HOLD"),
    ("N", "COMPONENT", "INFERENCE", "ADD"): ("VALID", "SILVER"),
    ("N", "COMPONENT", "INFERENCE", "REPLACE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "INFERENCE", "DELETE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "INFERENCE", "REWIRE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "INFERENCE", "MERGE"): ("VALID", "GOLD"),
    ("N", "COMPONENT", "INFERENCE", "SPLIT"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "SYSTEM", "ADD"): ("VALID", "HOLD"),
    ("N", "PROTOCOL", "SYSTEM", "REPLACE"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "SYSTEM", "DELETE"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "SYSTEM", "REWIRE"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "SYSTEM", "MERGE"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "SYSTEM", "SPLIT"): ("VALID", "HOLD"),
    ("N", "PROTOCOL", "DATA", "ADD"): ("VALID", "HOLD"),
    ("N", "PROTOCOL", "DATA", "REPLACE"): ("VALID", "HOLD"),
    ("N", "PROTOCOL", "DATA", "DELETE"): ("VALID", "HOLD"),
    ("N", "PROTOCOL", "DATA", "REWIRE"): ("VALID", "HOLD"),
    ("N", "PROTOCOL", "DATA", "MERGE"): ("VALID", "HOLD"),
    ("N", "PROTOCOL", "DATA", "SPLIT"): ("VALID", "HOLD"),
    ("N", "PROTOCOL", "FEATURE", "ADD"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "FEATURE", "REPLACE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "FEATURE", "DELETE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "FEATURE", "REWIRE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "FEATURE", "MERGE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "FEATURE", "SPLIT"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "BACKBONE", "ADD"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "BACKBONE", "REPLACE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "BACKBONE", "DELETE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "BACKBONE", "REWIRE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "BACKBONE", "MERGE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "BACKBONE", "SPLIT"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "COMPONENT", "ADD"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "COMPONENT", "REPLACE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "COMPONENT", "DELETE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "COMPONENT", "REWIRE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "COMPONENT", "MERGE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "COMPONENT", "SPLIT"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "BRANCH", "ADD"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "BRANCH", "REPLACE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "BRANCH", "DELETE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "BRANCH", "REWIRE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "BRANCH", "MERGE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "BRANCH", "SPLIT"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "LOSS", "ADD"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "LOSS", "REPLACE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "LOSS", "DELETE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "LOSS", "REWIRE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "LOSS", "MERGE"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "LOSS", "SPLIT"): ("INVALID", "INVALID"),
    ("N", "PROTOCOL", "OPTIMIZATION", "ADD"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "OPTIMIZATION", "REPLACE"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "OPTIMIZATION", "DELETE"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "OPTIMIZATION", "REWIRE"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "OPTIMIZATION", "MERGE"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "OPTIMIZATION", "SPLIT"): ("VALID", "HOLD"),
    ("N", "PROTOCOL", "INFERENCE", "ADD"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "INFERENCE", "REPLACE"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "INFERENCE", "DELETE"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "INFERENCE", "REWIRE"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "INFERENCE", "MERGE"): ("VALID", "SILVER"),
    ("N", "PROTOCOL", "INFERENCE", "SPLIT"): ("VALID", "HOLD"),
}

_REJECTED_PRIORITY_REASON = (
    "全方法同时在系统、骨干或分支层新增/拆分，改动过多且结构膨胀，"
    "无法归因于一个主要假设。"
)
_FORMAL_RUN_KINDS = {"FULL", "PROMOTION_CONFIRMATION", "RETRY"}
_SUCCESSFUL_RUN_OUTCOMES = {"COMPLETED", "NORMAL_EARLY_STOP"}
_FORMAL_ARTIFACT_KEYS = (
    "resolved_config",
    "metrics_json",
    "artifact_manifest",
    "trainer_log",
)
STABLE_ERROR_CODES = frozenset(
    {
        "ALREADY_INITIALIZED",
        "ARTIFACT_ID_MISMATCH",
        "ARTIFACT_LINK_MISMATCH",
        "ARTIFACT_METRICS_MISMATCH",
        "BENCHMARK_MISMATCH",
        "BRANCH_ADDITION_GATE",
        "BUDGET_AVAILABLE",
        "BUDGET_EXHAUSTED",
        "CANDIDATE_REJECTED",
        "CANONICAL_INCONSISTENCY",
        "EXPERIMENT_BUDGET_EXHAUSTED",
        "FORMAL_ARTIFACTS_REQUIRED",
        "FORMAL_ARTIFACT_MISSING",
        "FRONTIER_GATE_FAILED",
        "FROZEN_CONTRACT_CHANGED",
        "HUMAN_REVIEW_REQUIRED",
        "IDEMPOTENCY_CONFLICT",
        "IMMUTABLE_SEED_EVIDENCE",
        "INSUFFICIENT_COST_BUDGET",
        "INSUFFICIENT_TIME_BUDGET",
        "INTERACTION_GATE_FAILED",
        "INVALID_ARTIFACT_REFS",
        "INVALID_BENCHMARK",
        "INVALID_BUDGET",
        "INVALID_CANDIDATE",
        "INVALID_CLASSIFICATION",
        "INVALID_FORMAL_ARTIFACT",
        "INVALID_FRONTIER",
        "INVALID_INITIAL_MODEL",
        "INVALID_INITIAL_MODELS",
        "INVALID_INITIAL_ROLES",
        "INVALID_LITERATURE_NODE",
        "INVALID_LITERATURE_TRIGGER",
        "INVALID_MERGE",
        "INVALID_METRICS",
        "INVALID_NODE_TYPE",
        "INVALID_PDF_ARTIFACT",
        "INVALID_PRIMARY_METRIC",
        "INVALID_PRIMARY_PARENT",
        "INVALID_PRIORITY",
        "INVALID_PROMOTION_CONFIRMATION",
        "INVALID_REFS",
        "INVALID_REPLACEMENT",
        "INVALID_REQUEST",
        "INVALID_REQUEST_ID",
        "INVALID_REQUEST_JSON",
        "INVALID_RETRY",
        "INVALID_ROLE_ASSIGNMENT",
        "INVALID_SIMPLIFICATION_CAMPAIGN",
        "INVALID_STAGE_ROUTE",
        "INVALID_TRANSITION",
        "INVALID_VERDICT",
        "MISSING_EVIDENCE",
        "MISSING_REQUEST",
        "NODE_NOT_SELECTED",
        "NO_ACTIVE_RUN",
        "PAPER_REPAIR_LIMIT",
        "PREREGISTRATION_MISMATCH",
        "PRIORITY_UPGRADE_FORBIDDEN",
        "PROMOTION_GATE_FAILED",
        "PROPOSAL_REJECTED",
        "PROTECTED_ROLE_NODE",
        "REPLACEMENT_EVIDENCE_PENDING",
        "REPLACEMENT_REQUIRED",
        "RESEARCH_TERMINATED",
        "RUN_ALREADY_ACTIVE",
        "RUN_ID_MISMATCH",
        "RUNTIME_ERROR",
        "SIMPLIFICATION_ANCHOR_MISMATCH",
        "SIMPLIFICATION_CAMPAIGN_INCOMPLETE",
        "STALE_RESEARCH_BASE",
        "UNKNOWN_BENCHMARK",
        "UNKNOWN_COMMAND",
        "UNKNOWN_NODE",
        "VALIDATION_FAILED",
    }
)
ALLOWED_NEXT_ACTIONS = frozenset(
    set(PROPOSAL_ACTIONS)
    | {
        "inspect",
        "validate",
    }
)
_ALLOWED_ACTION_ALIASES = {
    "BACKTRACK": "CREATE_LITERATURE",
    "CHOOSE_LOWER_COST_CANDIDATE": "SET_FRONTIER",
    "CORRECT_CANDIDATE": "CREATE_CANDIDATE",
    "CORRECT_PROPOSAL": "inspect",
    "CREATE_REPLACEMENT_CANDIDATE": "CREATE_CANDIDATE",
    "FINISH_EXISTING_EXPERIMENT": "inspect",
    "FINISH_RUN": "inspect",
    "HUMAN_REVIEW": "inspect",
    "INSPECT": "inspect",
    "PIVOT": "CREATE_LITERATURE",
    "PRODUCE_MISSING_ARTIFACT": "inspect",
    "PROMOTE_RESEARCH_BASE": "PROMOTE_RESEARCH_BASE",
    "PROPOSE": "inspect",
    "RECLASSIFY_CANDIDATE": "CREATE_CANDIDATE",
    "RECREATE_CANDIDATE": "CREATE_CANDIDATE",
    "REDUCE_PLANNED_RUN_WITHIN_BENCHMARK": "inspect",
    "REGENERATE_ARTIFACT": "inspect",
    "RESTORE_ATTEMPT_ARTIFACT_REFS": "inspect",
    "RESTORE_CANONICAL_CONSISTENCY": "validate",
    "RESTORE_PREREGISTRATION": "inspect",
    "RUN_COMBINED_DELETION_EXPERIMENT": "inspect",
    "RUN_REPLACEMENT_EXPERIMENT": "inspect",
    "SPLIT_CANDIDATE": "CREATE_CANDIDATE",
    "START_RUN": "inspect",
    "START_RUN_FULL": "inspect",
    "START_RUN_PROMOTION_CONFIRMATION": "inspect",
    "START_RUN_RETRY": "inspect",
    "USE_ARTIFACT_METRICS": "inspect",
    "USE_CURRENT_RESEARCH_BASE": "inspect",
    "USE_PRIORITY": "CREATE_CANDIDATE",
    "VALIDATE": "validate",
}
_RUNTIME_RECORD_HEADING = "## Runtime Record"
_RESEARCH_NOTES_HEADING = "## Research Notes"


def _normalize_allowed_next_actions(actions: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for value in actions:
        base = value.split(":", 1)[0]
        action = (
            base
            if base in ALLOWED_NEXT_ACTIONS
            else _ALLOWED_ACTION_ALIASES.get(base)
        )
        if action is None:
            raise ValueError(f"Unknown allowed_next_actions token: {value}")
        if action not in normalized:
            normalized.append(action)
    return normalized


def _with_success_result(response: dict[str, Any]) -> dict[str, Any]:
    if response.get("accepted") is not True:
        return response
    envelope_keys = {
        "accepted",
        "revision",
        "result",
        "allowed_next_actions",
    }
    result = response.get("result", {})
    if not isinstance(result, dict):
        raise ValueError("Successful Runtime response result must be an object")
    for key in list(response):
        if key not in envelope_keys:
            result[key] = response.pop(key)
    response["result"] = result
    return response


def _experiment_card_sections(card_text: str) -> tuple[str, str]:
    lines = card_text.splitlines(keepends=True)
    runtime_indexes = [
        index
        for index, line in enumerate(lines)
        if line.rstrip("\r\n") == _RUNTIME_RECORD_HEADING
    ]
    notes_indexes = [
        index
        for index, line in enumerate(lines)
        if line.rstrip("\r\n") == _RESEARCH_NOTES_HEADING
    ]
    if len(runtime_indexes) != 1 or len(notes_indexes) != 1:
        raise ValueError(
            "Experiment Card must contain exactly one Runtime Record and one Research Notes section"
        )
    runtime_index = runtime_indexes[0]
    notes_index = notes_indexes[0]
    if runtime_index >= notes_index:
        raise ValueError("Runtime Record must precede Research Notes")
    return "".join(lines[runtime_index:notes_index]), "".join(lines[notes_index + 1 :])


class RuntimeErrorResponse(Exception):
    """An expected rejection that should be returned to the calling LLM."""

    def __init__(
        self,
        code: str,
        *violations: str,
        controller_status: str = "CONTINUE",
        allowed_next_actions: Iterable[str] = (),
    ) -> None:
        super().__init__("; ".join(violations))
        if code not in STABLE_ERROR_CODES:
            raise ValueError(f"Unknown stable Runtime error code: {code}")
        self.code = code
        self.violations = list(violations) or [code]
        self.controller_status = controller_status
        self.allowed_next_actions = _normalize_allowed_next_actions(
            allowed_next_actions
        )

    def response(self) -> dict[str, Any]:
        return {
            "accepted": False,
            "error_code": self.code,
            "controller_status": self.controller_status,
            "violations": [
                {
                    "code": self.code,
                    "path": "$",
                    "message": message,
                }
                for message in self.violations
            ],
            "allowed_next_actions": self.allowed_next_actions,
        }


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeErrorResponse("INVALID_REQUEST", f"{name} must be an object")
    return value


def _require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise RuntimeErrorResponse("INVALID_REQUEST", f"{name} must be an array")
    return value


def _require_string(value: Any, name: str, *, max_length: int = 2000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeErrorResponse(
            "INVALID_REQUEST", f"{name} must be a non-empty string"
        )
    text = value.strip()
    if len(text) > max_length:
        raise RuntimeErrorResponse(
            "INVALID_REQUEST", f"{name} exceeds {max_length} characters"
        )
    return text


def _optional_string(value: Any, name: str, *, max_length: int = 2000) -> str | None:
    if value is None:
        return None
    return _require_string(value, name, max_length=max_length)


def _require_number(value: Any, name: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeErrorResponse("INVALID_REQUEST", f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise RuntimeErrorResponse("INVALID_REQUEST", f"{name} must be finite")
    if minimum is not None and number < minimum:
        raise RuntimeErrorResponse(
            "INVALID_REQUEST", f"{name} must be at least {minimum}"
        )
    return number


def _require_enum(value: Any, name: str, allowed: set[str]) -> str:
    if value not in allowed:
        expected = ", ".join(sorted(allowed))
        raise RuntimeErrorResponse(
            "INVALID_REQUEST", f"{name} must be one of: {expected}"
        )
    return str(value)


def _metric_is_better(candidate: float, reference: float, direction: str) -> bool:
    return candidate > reference if direction == "MAXIMIZE" else candidate < reference


def _oriented_delta(candidate: float, reference: float, direction: str) -> float:
    return candidate - reference if direction == "MAXIMIZE" else reference - candidate


def _target_reached(value: float, target: float, direction: str) -> bool:
    return value >= target if direction == "MAXIMIZE" else value <= target


class RuntimeService:
    """Operate one AutoResearch project through six deterministic interfaces."""

    def __init__(self, project_root: str | Path) -> None:
        self.root = normalize_project_root(project_root)

    # ------------------------------------------------------------------
    # Public interfaces
    # ------------------------------------------------------------------

    def initialize(self, request: dict[str, Any]) -> dict[str, Any]:
        request = _require_mapping(request, "request")
        with project_lock(self.root):
            if graph_path(self.root).exists() or state_path(self.root).exists():
                raise RuntimeErrorResponse(
                    "ALREADY_INITIALIZED",
                    "Canonical AutoResearch artifacts already exist",
                    allowed_next_actions=["INSPECT", "VALIDATE"],
                )

            request_id = self._request_id(request)
            project_id = _require_string(request.get("project_id"), "project_id", max_length=96)
            brief_ref = self._existing_ref(request.get("research_brief_ref"), "research_brief_ref")
            benchmark = self._validate_benchmark(request.get("benchmark"))
            benchmark_ref = self._existing_ref(
                benchmark["benchmark_ref"], "benchmark.benchmark_ref"
            )
            benchmark["benchmark_ref"] = benchmark_ref
            primary_metric = self._validate_primary_metric(
                request.get("primary_metric"), benchmark
            )
            promotion_confirmation_policy = (
                self._validate_promotion_confirmation_policy(
                    request.get("promotion_confirmation_policy")
                )
            )
            budget = self._validate_budget(request.get("budget"))
            initial_models = _require_list(request.get("initial_models"), "initial_models")
            if not initial_models:
                raise RuntimeErrorResponse(
                    "INVALID_INITIAL_MODELS", "At least one initial model is required"
                )

            timestamp = _now()
            prepared_models: list[dict[str, Any]] = []
            role_holders: dict[str, list[str]] = {role: [] for role in ROLE_NAMES}
            for index, raw_model in enumerate(initial_models, start=1):
                model = self._validate_initial_model(raw_model, benchmark, index)
                model["node_id"] = f"RN-{index:04d}"
                prepared_models.append(model)
                for role in model["roles"]:
                    role_holders[role].append(model["node_id"])

            for role in ("ANCHOR_BASELINE", "RESEARCH_BASE", "CHAMPION"):
                if len(role_holders[role]) != 1:
                    raise RuntimeErrorResponse(
                        "INVALID_INITIAL_ROLES",
                        f"Exactly one initial model must hold {role}",
                    )

            anchor_id = role_holders["ANCHOR_BASELINE"][0]
            research_base_id = role_holders["RESEARCH_BASE"][0]
            champion_id = role_holders["CHAMPION"][0]
            reference_ids = role_holders["REFERENCE_BASELINE"]
            models_by_id = {model["node_id"]: model for model in prepared_models}
            base_metrics = models_by_id[research_base_id]["metrics"]
            champion_metrics = models_by_id[champion_id]["metrics"]

            nodes = [
                self._root_research_node(
                    model=model,
                    benchmark=benchmark,
                    research_base_id=research_base_id,
                    comparison_target_id=research_base_id,
                    base_metrics=base_metrics,
                    champion_metrics=champion_metrics,
                    created_at=timestamp,
                )
                for model in prepared_models
            ]
            role_state = {
                "anchor_baseline_id": anchor_id,
                "research_base_id": research_base_id,
                "champion_id": champion_id,
                "reference_baseline_ids": reference_ids,
                "simplification_anchor_id": research_base_id,
            }
            role_events = []
            for role, node_ids in role_holders.items():
                for node_id in node_ids:
                    role_events.append(
                        {
                            "benchmark_id": benchmark["benchmark_id"],
                            "created_at": timestamp,
                            "event_type": "ASSIGNED",
                            "role": role,
                            "node_id": node_id,
                            "reason": "Initial frozen role",
                            "evidence_ref": benchmark_ref,
                        }
                    )

            graph = {
                "schema_version": SCHEMA_VERSION,
                "project_id": project_id,
                "revision": 1,
                "created_at": timestamp,
                "updated_at": timestamp,
                "benchmarks": [benchmark],
                "active_benchmark_id": benchmark["benchmark_id"],
                "role_states": {benchmark["benchmark_id"]: role_state},
                "role_events": role_events,
                "active_frontier": [],
                "stage_summaries": [],
                "nodes": nodes,
                "edges": [],
            }
            state = {
                "schema_version": SCHEMA_VERSION,
                "runtime_version": RUNTIME_VERSION,
                "project_id": project_id,
                "revision": 1,
                "controller_status": "CONTINUE",
                "current_phase": "BOOTSTRAP",
                "last_trigger": "BOOTSTRAP_FROZEN",
                "contract_hashes": {
                    "research_brief_ref": brief_ref,
                    "research_brief_sha256": sha256_file(self.root / brief_ref),
                    "benchmark_ref": benchmark_ref,
                    "benchmark_sha256": sha256_file(self.root / benchmark_ref),
                },
                "primary_metric": primary_metric,
                "promotion_confirmation_policy": promotion_confirmation_policy,
                "budget": budget,
                "next_ids": {
                    "research_node": len(nodes) + 1,
                    "literature_node": 1,
                    "experiment": 1,
                    "stage_summary": 1,
                },
                "active_run": None,
                "experiments": {},
                "node_seed_metrics": {
                    model["node_id"]: model["seed_metrics"] for model in prepared_models
                },
                "node_seed_evidence": {
                    model["node_id"]: {
                        seed: model["evidence_ref"]
                        for seed in model["seed_metrics"]
                    }
                    for model in prepared_models
                },
                "audit_counters": {
                    "stage_reflections": 0,
                    "subagent_calls": 0,
                },
                "applied_requests": [],
            }
            response = {
                "accepted": True,
                "command": "init",
                "controller_status": "CONTINUE",
                "project_id": project_id,
                "revision": 1,
                "artifacts_written": [
                    GRAPH_FILENAME,
                    GRAPH_HTML_FILENAME,
                    f"{RUNTIME_DIRECTORY}/{RUNTIME_STATE_FILENAME}",
                ],
                "allowed_next_actions": [
                    "CREATE_LITERATURE",
                    "CREATE_CANDIDATE",
                    "inspect",
                ],
            }
            _with_success_result(response)
            self._remember_request(state, request_id, request, response)
            self._validate_all(
                graph,
                state,
                check_contract_hashes=False,
                check_artifacts=False,
            )
            self._write_initial_project(graph, state)
            return response

    def inspect(self) -> dict[str, Any]:
        with project_lock(self.root):
            graph, state = load_project(self.root)
            self._assert_contracts_unchanged(state)
            self._assert_canonical_consistency(graph, state)
            benchmark_id = graph["active_benchmark_id"]
            roles = graph["role_states"][benchmark_id]
            node_index = self._node_index(graph)
            primary = state["primary_metric"]
            response = {
                "accepted": True,
                "command": "inspect",
                "controller_status": state["controller_status"],
                "current_phase": state["current_phase"],
                "last_trigger": state["last_trigger"],
                "project_id": graph["project_id"],
                "revision": graph["revision"],
                "benchmark_id": benchmark_id,
                "primary_metric": primary,
                "promotion_confirmation_policy": copy.deepcopy(
                    state["promotion_confirmation_policy"]
                ),
                "budget": self._budget_summary(state),
                "roles": {
                    role: {
                        "node_id": node_id,
                        "title": node_index[node_id]["title"],
                        "primary_value": self._node_primary_value(
                            node_index[node_id], primary["metric_id"]
                        ),
                    }
                    for role, node_id in {
                        "anchor_baseline": roles["anchor_baseline_id"],
                        "research_base": roles["research_base_id"],
                        "champion": roles["champion_id"],
                    }.items()
                },
                "reference_baseline_ids": roles["reference_baseline_ids"],
                "active_frontier": [
                    {
                        "node_id": node_id,
                        "title": node_index[node_id]["title"],
                        "priority": node_index[node_id]["candidate_priority"],
                    }
                    for node_id in graph["active_frontier"]
                ],
                "active_run": state["active_run"],
                "audit_counters": copy.deepcopy(state["audit_counters"]),
                "node_counts": {
                    "research": sum(
                        node["node_type"] == "RESEARCH" for node in graph["nodes"]
                    ),
                    "literature": sum(
                        node["node_type"] == "LITERATURE" for node in graph["nodes"]
                    ),
                },
                "validation": {"valid": True, "violations": []},
                "allowed_next_actions": self._allowed_actions(graph, state),
            }
            response["roles"]["research_base"]["single_seed_provisional"] = (
                self._current_research_base_provisional(graph)
            )
            return _with_success_result(response)

    def propose(self, request: dict[str, Any]) -> dict[str, Any]:
        request = _require_mapping(request, "request")
        with project_lock(self.root):
            graph, state = load_project(self.root)
            self._assert_contracts_unchanged(state)
            self._assert_canonical_consistency(graph, state)
            cached = self._cached_response(state, request)
            if cached is not None:
                return cached
            self._assert_mutable(state)

            action = _require_enum(request.get("action"), "action", PROPOSAL_ACTIONS)
            graph = copy.deepcopy(graph)
            state = copy.deepcopy(state)
            operation_result = self._apply_proposal(action, request, graph, state)
            self._advance_phase_after_proposal(action, state)
            response = {
                "accepted": True,
                "command": "propose",
                "action": action,
                "controller_status": state["controller_status"],
                "result": operation_result,
                "revision": graph["revision"] + 1,
                "allowed_next_actions": self._allowed_actions(graph, state),
            }
            _with_success_result(response)
            self._commit_mutation(graph, state, request, response)
            return response

    def start_run(self, request: dict[str, Any]) -> dict[str, Any]:
        request = _require_mapping(request, "request")
        with project_lock(self.root):
            graph, state = load_project(self.root)
            self._assert_contracts_unchanged(state)
            self._assert_canonical_consistency(graph, state)
            cached = self._cached_response(state, request)
            if cached is not None:
                return cached
            self._assert_mutable(state)
            if state["active_run"] is not None:
                raise RuntimeErrorResponse(
                    "RUN_ALREADY_ACTIVE",
                    f'Attempt {state["active_run"]["attempt_id"]} is already active',
                    allowed_next_actions=["FINISH_RUN", "INSPECT"],
                )
            if self._time_or_cost_exhausted(state):
                raise RuntimeErrorResponse(
                    "BUDGET_EXHAUSTED",
                    "The preregistered time or cost budget is exhausted",
                    controller_status="TARGET_NOT_REACHED",
                    allowed_next_actions=[],
                )

            graph = copy.deepcopy(graph)
            state = copy.deepcopy(state)
            node_id = _require_string(request.get("node_id"), "node_id", max_length=16)
            run_kind = _require_enum(request.get("run_kind"), "run_kind", RUN_KINDS)
            seed = request.get("seed")
            if isinstance(seed, bool) or not isinstance(seed, int):
                raise RuntimeErrorResponse("INVALID_REQUEST", "seed must be an integer")
            command = _require_string(request.get("command"), "command", max_length=4000)
            code_version = _require_string(
                request.get("code_version"), "code_version", max_length=300
            )
            data_version = _require_string(
                request.get("data_version"), "data_version", max_length=300
            )
            planned_max_seconds = _require_number(
                request.get("planned_max_seconds"),
                "planned_max_seconds",
                minimum=0.001,
            )
            planned_max_cost = _require_number(
                request.get("planned_max_cost"),
                "planned_max_cost",
                minimum=0,
            )
            cost_unit = state["budget"]["limits"]["cost_unit"]
            config_ref = self._existing_ref(request.get("config_ref"), "config_ref")
            artifact_refs = self._validate_artifact_refs(
                request.get("artifact_refs"),
                required=run_kind in _FORMAL_RUN_KINDS,
            )
            expected_artifacts = [
                self._future_ref(item, f"expected_artifacts[{index}]")
                for index, item in enumerate(
                    _require_list(
                        request.get("expected_artifacts", []), "expected_artifacts"
                    )
                )
            ]

            node = self._research_node(graph, node_id)
            preregistration = self._validate_start_preregistration(request, node)
            if node["experiment_id"] is not None:
                existing_experiment = state["experiments"][node["experiment_id"]]
                if existing_experiment["preregistration"] != preregistration:
                    raise RuntimeErrorResponse(
                        "PREREGISTRATION_MISMATCH",
                        "start-run preregistration differs from the frozen Experiment Card facts",
                        allowed_next_actions=["INSPECT", "RESTORE_PREREGISTRATION"],
                    )
            self._validate_start_transition(graph, state, node, run_kind)
            self._validate_planned_budget(
                state,
                planned_max_seconds=planned_max_seconds,
                planned_max_cost=planned_max_cost,
            )
            if node["experiment_id"] is None and self._new_experiment_limit_reached(state):
                raise RuntimeErrorResponse(
                    "EXPERIMENT_BUDGET_EXHAUSTED",
                    "No new Experiment ID may be allocated, but existing Experiment attempts may still finish",
                    allowed_next_actions=["INSPECT", "FINISH_EXISTING_EXPERIMENT"],
                )
            experiment_id, attempt_id, is_new_experiment = self._allocate_run_ids(
                graph, state, node
            )
            started_at = _now()
            card_ref = f"experiments/{experiment_id}.md"
            run_directory_ref = f"logs/runs/{experiment_id}"
            run_log_ref = f"{run_directory_ref}/{attempt_id}.jsonl"

            if is_new_experiment:
                state["experiments"][experiment_id] = {
                    "experiment_id": experiment_id,
                    "node_id": node_id,
                    "created_at": started_at,
                    "card_ref": card_ref,
                    "run_directory_ref": run_directory_ref,
                    "preregistration": preregistration,
                    "runtime_record_sha256": "",
                    "attempts": [],
                }
                state["budget"]["consumed"]["experiments_started"] += 1
                node["experiment_id"] = experiment_id
                node["refs"]["experiment_card"] = card_ref
                node["refs"]["run_directory"] = f"{run_directory_ref}/"

            attempt = {
                "attempt_id": attempt_id,
                "run_kind": run_kind,
                "seed": seed,
                "status": "RUNNING",
                "started_at": started_at,
                "finished_at": None,
                "command": command,
                "code_version": code_version,
                "data_version": data_version,
                "planned_max_seconds": planned_max_seconds,
                "planned_max_cost": planned_max_cost,
                "cost_unit": cost_unit,
                "config_ref": config_ref,
                "artifact_refs": artifact_refs,
                "artifact_sha256": {},
                "expected_artifacts": expected_artifacts,
                "run_log_ref": run_log_ref,
                "run_outcome": None,
                "hypothesis_verdict": None,
                "metrics": {},
                "duration_seconds": None,
                "cost": None,
                "hard_constraints_passed": None,
                "stop_reason": None,
                "checkpoint_ref": None,
            }
            experiment = state["experiments"][experiment_id]
            experiment["attempts"].append(attempt)
            state["budget"]["consumed"]["attempts_started"] += 1
            state["active_run"] = {
                "node_id": node_id,
                "experiment_id": experiment_id,
                "attempt_id": attempt_id,
                "run_kind": run_kind,
                "started_at": started_at,
                "card_ref": card_ref,
                "run_log_ref": run_log_ref,
            }
            state["current_phase"] = "EXPERIMENT_EXECUTION"
            state["last_trigger"] = "EXPERIMENT_STARTED"
            if run_kind in {"FULL", "RETRY"} and node_id in graph["active_frontier"]:
                graph["active_frontier"].remove(node_id)

            start_event = {
                "event": "ATTEMPT_STARTED",
                "timestamp": started_at,
                "experiment_id": experiment_id,
                "attempt_id": attempt_id,
                "node_id": node_id,
                "run_kind": run_kind,
                "seed": seed,
                "code_version": code_version,
                "data_version": data_version,
                "planned_max_seconds": planned_max_seconds,
                "planned_max_cost": planned_max_cost,
                "cost_unit": cost_unit,
                "config_ref": config_ref,
                "artifact_refs": artifact_refs,
            }
            card_text = self._render_experiment_card(graph, state, experiment_id)
            experiment["runtime_record_sha256"] = sha256_text(
                _experiment_card_sections(card_text)[0]
            )
            extra_files = {
                card_ref: card_text,
                run_log_ref: json.dumps(
                    start_event, ensure_ascii=False, sort_keys=True
                )
                + "\n",
            }
            response = {
                "accepted": True,
                "command": "start-run",
                "controller_status": "CONTINUE",
                "node_id": node_id,
                "experiment_id": experiment_id,
                "attempt_id": attempt_id,
                "run_kind": run_kind,
                "cost_unit": cost_unit,
                "artifact_refs": artifact_refs,
                "revision": graph["revision"] + 1,
                "artifacts_written": [card_ref, run_log_ref],
                "allowed_next_actions": ["inspect"],
            }
            _with_success_result(response)
            self._commit_mutation(graph, state, request, response, extra_files=extra_files)
            return response

    def finish_run(self, request: dict[str, Any]) -> dict[str, Any]:
        request = _require_mapping(request, "request")
        with project_lock(self.root):
            graph, state = load_project(self.root)
            self._assert_contracts_unchanged(state)
            self._assert_canonical_consistency(graph, state)
            cached = self._cached_response(state, request)
            if cached is not None:
                return cached
            active = state.get("active_run")
            if active is None:
                raise RuntimeErrorResponse(
                    "NO_ACTIVE_RUN",
                    "No active attempt can be finished",
                    allowed_next_actions=["INSPECT", "START_RUN"],
                )
            for field in ("experiment_id", "attempt_id"):
                if request.get(field) != active[field]:
                    raise RuntimeErrorResponse(
                        "RUN_ID_MISMATCH",
                        f'{field} must match active value {active[field]}',
                        allowed_next_actions=["INSPECT", "FINISH_RUN"],
                    )

            graph = copy.deepcopy(graph)
            state = copy.deepcopy(state)
            active = state["active_run"]
            experiment = state["experiments"][active["experiment_id"]]
            attempt = next(
                item
                for item in experiment["attempts"]
                if item["attempt_id"] == active["attempt_id"]
            )
            node = self._research_node(graph, active["node_id"])

            outcome = _require_enum(request.get("run_outcome"), "run_outcome", RUN_OUTCOMES - {"NOT_RUN"})
            formal_success = (
                attempt["run_kind"] in _FORMAL_RUN_KINDS
                and outcome in _SUCCESSFUL_RUN_OUTCOMES
            )
            artifact_sha256: dict[str, str] = {}
            if formal_success:
                metrics, artifact_sha256 = self._load_formal_run_artifacts(
                    attempt=attempt,
                    request_metrics=request.get("metrics"),
                    graph=graph,
                    experiment_id=active["experiment_id"],
                    attempt_id=active["attempt_id"],
                )
            else:
                metrics = self._validate_result_metrics(
                    request.get("metrics", {}), graph, outcome
                )
            duration = _require_number(
                request.get("duration_seconds"), "duration_seconds", minimum=0
            )
            cost = _require_number(request.get("cost", 0), "cost", minimum=0)
            hard_constraints = request.get("hard_constraints_passed")
            if not isinstance(hard_constraints, bool):
                raise RuntimeErrorResponse(
                    "INVALID_REQUEST", "hard_constraints_passed must be boolean"
                )
            stop_reason = _require_string(
                request.get("stop_reason"), "stop_reason", max_length=1000
            )
            checkpoint_ref = self._optional_existing_ref(
                request.get("checkpoint_ref"), "checkpoint_ref"
            )
            budget_overruns = []
            if duration > attempt["planned_max_seconds"]:
                budget_overruns.append(
                    f"duration {duration} exceeded planned maximum {attempt['planned_max_seconds']}"
                )
            if cost > attempt["planned_max_cost"]:
                budget_overruns.append(
                    f"cost {cost} exceeded planned maximum {attempt['planned_max_cost']}"
                )
            effective_hard_constraints = hard_constraints and not budget_overruns
            interpretation = _optional_string(
                request.get("interpretation"), "interpretation", max_length=2000
            )
            decision = _optional_string(
                request.get("decision"), "decision", max_length=1000
            )
            verdict = self._validate_finish_verdict(
                attempt["run_kind"], outcome, request.get("hypothesis_verdict")
            )
            if budget_overruns:
                verdict = "NOT_EVALUABLE"
            if attempt["run_kind"] != "SMOKE" and outcome != "TECHNICAL_FAILURE":
                if interpretation is None or decision is None:
                    raise RuntimeErrorResponse(
                        "INVALID_REQUEST",
                        "interpretation and decision are required for scientific results",
                    )

            finished_at = _now()
            attempt.update(
                {
                    "status": "FINISHED",
                    "finished_at": finished_at,
                    "run_outcome": outcome,
                    "hypothesis_verdict": verdict,
                    "metrics": metrics,
                    "artifact_sha256": artifact_sha256,
                    "duration_seconds": duration,
                    "cost": cost,
                    "hard_constraints_passed": effective_hard_constraints,
                    "budget_overruns": budget_overruns,
                    "stop_reason": stop_reason,
                    "checkpoint_ref": checkpoint_ref,
                    "interpretation": interpretation,
                    "decision": decision,
                }
            )
            state["active_run"] = None
            state["current_phase"] = "RESULT_ROUTING"
            state["last_trigger"] = "EXPERIMENT_FINISHED"
            state["budget"]["consumed"]["run_seconds"] += duration
            state["budget"]["consumed"]["cost"] += cost

            scientific = attempt["run_kind"] != "SMOKE"
            full_comparable = (
                attempt["run_kind"] in {"FULL", "PROMOTION_CONFIRMATION", "RETRY"}
                and outcome in {"COMPLETED", "NORMAL_EARLY_STOP"}
                and effective_hard_constraints
            )
            if scientific and attempt["run_kind"] != "PROMOTION_CONFIRMATION":
                node["run_outcome"] = outcome
                node["hypothesis_verdict"] = verdict
            if scientific and metrics:
                node["metric_summary"] = self._aggregate_metric_summary(
                    graph, state, node, experiment
                )

            role_events: list[dict[str, Any]] = []
            if full_comparable:
                role_events = self._reconcile_champion(graph, state, finished_at)

            promotion_gate = self._promotion_gate(graph, state, node)
            primary = state["primary_metric"]
            primary_value = metrics.get(primary["metric_id"])
            if (
                full_comparable
                and primary_value is not None
                and _target_reached(
                    primary_value, primary["target"], primary["direction"]
                )
            ):
                state["controller_status"] = "TARGET_REACHED"
            elif self._terminal_budget_exhausted(
                state,
                run_kind=attempt["run_kind"],
                run_outcome=outcome,
                promotion_gate=promotion_gate,
            ):
                state["controller_status"] = "TARGET_NOT_REACHED"

            finish_event = {
                "event": "ATTEMPT_FINISHED",
                "timestamp": finished_at,
                "experiment_id": active["experiment_id"],
                "attempt_id": active["attempt_id"],
                "node_id": node["node_id"],
                "run_kind": attempt["run_kind"],
                "run_outcome": outcome,
                "hypothesis_verdict": verdict,
                "metrics": metrics,
                "artifact_refs": attempt["artifact_refs"],
                "artifact_sha256": artifact_sha256,
                "duration_seconds": duration,
                "cost": cost,
                "cost_unit": attempt["cost_unit"],
                "hard_constraints_passed": effective_hard_constraints,
                "budget_overruns": budget_overruns,
                "stop_reason": stop_reason,
                "checkpoint_ref": checkpoint_ref,
            }
            run_log_path = self.root / active["run_log_ref"]
            previous_log = (
                run_log_path.read_text(encoding="utf-8") if run_log_path.exists() else ""
            )
            card_text = self._render_experiment_card(
                graph, state, active["experiment_id"]
            )
            experiment["runtime_record_sha256"] = sha256_text(
                _experiment_card_sections(card_text)[0]
            )
            extra_files = {
                active["run_log_ref"]: previous_log
                + json.dumps(finish_event, ensure_ascii=False, sort_keys=True)
                + "\n",
                experiment["card_ref"]: card_text,
            }
            if scientific:
                research_log_ref = "logs/research/volume_001.md"
                node["refs"]["research_log"] = research_log_ref
                extra_files[research_log_ref] = self._updated_research_log(
                    research_log_ref, node, attempt
                )

            response = {
                "accepted": True,
                "command": "finish-run",
                "controller_status": state["controller_status"],
                "node_id": node["node_id"],
                "experiment_id": active["experiment_id"],
                "attempt_id": active["attempt_id"],
                "run_outcome": outcome,
                "hypothesis_verdict": verdict,
                "promotion_gate": promotion_gate,
                "budget_overruns": budget_overruns,
                "role_events": role_events,
                "budget": self._budget_summary(state),
                "revision": graph["revision"] + 1,
                "artifacts_written": sorted(extra_files),
                "allowed_next_actions": self._finish_allowed_actions(
                    state, outcome, promotion_gate, attempt["run_kind"]
                ),
            }
            _with_success_result(response)
            self._commit_mutation(graph, state, request, response, extra_files=extra_files)
            return response

    def validate(self, *, render: bool = True) -> dict[str, Any]:
        with project_lock(self.root):
            graph, state = load_project(self.root)
            violations = self._validate_all(graph, state)
            schema_violations = self._json_schema_violations(graph, state)
            violations.extend(schema_violations)
            artifacts_written: list[str] = []
            if not violations and render:
                atomic_write_text(
                    self.root / GRAPH_HTML_FILENAME, render_graph_html(graph)
                )
                artifacts_written.append(GRAPH_HTML_FILENAME)
            if violations:
                response = RuntimeErrorResponse(
                    "VALIDATION_FAILED",
                    *violations,
                    controller_status="HUMAN_REVIEW_REQUIRED",
                    allowed_next_actions=["validate", "inspect"],
                ).response()
                response.update(
                    {
                        "command": "validate",
                        "project_id": graph.get("project_id"),
                        "revision": graph.get("revision"),
                        "artifacts_written": artifacts_written,
                    }
                )
                return response
            response = {
                "accepted": not violations,
                "command": "validate",
                "controller_status": state["controller_status"],
                "project_id": graph.get("project_id"),
                "revision": graph.get("revision"),
                "violations": violations,
                "artifacts_written": artifacts_written,
                "allowed_next_actions": self._allowed_actions(graph, state),
            }
            return _with_success_result(response)

    # ------------------------------------------------------------------
    # Proposal operations
    # ------------------------------------------------------------------

    def _apply_proposal(
        self,
        action: str,
        request: dict[str, Any],
        graph: dict[str, Any],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        handlers = {
            "CREATE_LITERATURE": self._create_literature,
            "CREATE_CANDIDATE": self._create_candidate,
            "CREATE_REPAIR": self._create_candidate,
            "CREATE_MERGE": self._create_candidate,
            "SET_FRONTIER": self._set_frontier,
            "HOLD_NODE": self._hold_node,
            "REOPEN_NODE": self._reopen_node,
            "CLOSE_NODE": self._close_node,
            "PROMOTE_RESEARCH_BASE": self._promote_research_base,
            "ASSIGN_REFERENCE_BASELINE": self._assign_reference_baseline,
            "REGISTER_STAGE_SUMMARY": self._register_stage_summary,
            "REGISTER_BASELINE_SEED_EVIDENCE": self._register_baseline_seed_evidence,
            "FINALIZE_RESEARCH": self._finalize_research,
        }
        return handlers[action](request, graph, state)

    def _advance_phase_after_proposal(
        self, action: str, state: dict[str, Any]
    ) -> None:
        if action == "CREATE_LITERATURE":
            state["current_phase"] = "LITERATURE_RESEARCH"
            state["last_trigger"] = "LITERATURE_COMPLETED"
        elif action in {
            "CREATE_CANDIDATE",
            "CREATE_REPAIR",
            "CREATE_MERGE",
            "SET_FRONTIER",
        }:
            state["current_phase"] = "CANDIDATE_DESIGN"
            state["last_trigger"] = "CANDIDATES_READY"
        elif action == "REGISTER_STAGE_SUMMARY":
            state["current_phase"] = "RESULT_ROUTING"
            state["last_trigger"] = "STAGE_SUMMARY_COMPLETED"
        elif action == "FINALIZE_RESEARCH":
            state["current_phase"] = "TERMINATION"
            state["last_trigger"] = "RESEARCH_FINALIZED"

    def _create_literature(
        self, request: dict[str, Any], graph: dict[str, Any], state: dict[str, Any]
    ) -> dict[str, Any]:
        trigger = _require_mapping(request.get("trigger"), "trigger")
        trigger_type = _require_enum(
            trigger.get("type"), "trigger.type", LITERATURE_TRIGGER_TYPES
        )
        source_node_ids = [
            _require_string(value, f"trigger.source_node_ids[{index}]", max_length=16)
            for index, value in enumerate(
                _require_list(
                    trigger.get("source_node_ids", []), "trigger.source_node_ids"
                )
            )
        ]
        node_index = self._node_index(graph)
        for node_id in source_node_ids:
            if node_id not in node_index:
                raise RuntimeErrorResponse(
                    "UNKNOWN_NODE", f"Unknown trigger source node: {node_id}"
                )
        source_ref = self._optional_existing_ref(
            trigger.get("source_ref"), "trigger.source_ref"
        )
        if (
            trigger_type not in {"BOOTSTRAP"}
            and not source_node_ids
            and source_ref is None
        ):
            raise RuntimeErrorResponse(
                "INVALID_LITERATURE_TRIGGER",
                f"{trigger_type} requires a source node or source artifact",
            )
        if trigger_type == "NO_DIRECTION_RECOVERY":
            if len(source_node_ids) != 1:
                raise RuntimeErrorResponse(
                    "INVALID_LITERATURE_TRIGGER",
                    "NO_DIRECTION_RECOVERY requires exactly one source Literature Node",
                )
            source_node = node_index[source_node_ids[0]]
            if (
                source_node["node_type"] != "LITERATURE"
                or source_node["search_outcome"] != "NO_DIRECTION"
            ):
                raise RuntimeErrorResponse(
                    "INVALID_LITERATURE_TRIGGER",
                    "NO_DIRECTION_RECOVERY source must be a NO_DIRECTION Literature Node",
                )
        outcome = _require_enum(
            request.get("search_outcome"), "search_outcome", LITERATURE_OUTCOMES
        )
        selected_papers_raw = _require_list(
            request.get("selected_papers", []), "selected_papers"
        )
        if len(selected_papers_raw) > 4:
            raise RuntimeErrorResponse(
                "INVALID_LITERATURE_NODE", "selected_papers cannot exceed four"
            )
        selected_papers = []
        for index, raw_paper in enumerate(selected_papers_raw):
            paper = _require_mapping(raw_paper, f"selected_papers[{index}]")
            selected_papers.append(
                {
                    "title": _require_string(
                        paper.get("title"),
                        f"selected_papers[{index}].title",
                        max_length=500,
                    ),
                    "pdf_ref": self._existing_pdf_ref(
                        paper.get("pdf_ref"),
                        f"selected_papers[{index}].pdf_ref",
                    ),
                    "mechanism_card_ref": self._existing_ref(
                        paper.get("mechanism_card_ref"),
                        f"selected_papers[{index}].mechanism_card_ref",
                    ),
                }
            )
        direction_summary = _optional_string(
            request.get("direction_summary"), "direction_summary", max_length=1200
        )
        if outcome == "DIRECTIONS_FOUND":
            if not selected_papers or direction_summary is None:
                raise RuntimeErrorResponse(
                    "INVALID_LITERATURE_NODE",
                    "DIRECTIONS_FOUND requires 1–4 selected PDFs and a direction summary",
                )
        elif direction_summary is not None:
            raise RuntimeErrorResponse(
                "INVALID_LITERATURE_NODE",
                "NO_DIRECTION requires direction_summary = null",
            )

        number = state["next_ids"]["literature_node"]
        node_id = f"LN-{number:04d}"
        state["next_ids"]["literature_node"] += 1
        node = {
            "node_id": node_id,
            "node_type": "LITERATURE",
            "created_at": _now(),
            "title": _require_string(request.get("title"), "title", max_length=300),
            "trigger": {
                "type": trigger_type,
                "source_node_ids": source_node_ids,
                "source_ref": source_ref,
                "reason": _require_string(
                    trigger.get("reason"), "trigger.reason", max_length=800
                ),
            },
            "research_question": _require_string(
                request.get("research_question"), "research_question", max_length=1000
            ),
            "search_scope": _require_string(
                request.get("search_scope"), "search_scope", max_length=1200
            ),
            "search_outcome": outcome,
            "outcome_reason": _require_string(
                request.get("outcome_reason"), "outcome_reason", max_length=1200
            ),
            "direction_summary": direction_summary,
            "selected_papers": selected_papers,
            "literature_survey_ref": self._existing_ref(
                request.get("literature_survey_ref"), "literature_survey_ref"
            ),
        }
        graph["nodes"].append(node)
        for source_node_id in source_node_ids:
            graph["edges"].append(
                {
                    "from_node_id": source_node_id,
                    "to_node_id": node_id,
                    "edge_type": "SOURCE",
                    "reason": trigger["reason"],
                    "evidence_ref": source_ref,
                }
            )
        return {"node_id": node_id, "search_outcome": outcome}

    def _create_candidate(
        self, request: dict[str, Any], graph: dict[str, Any], state: dict[str, Any]
    ) -> dict[str, Any]:
        action = request["action"]
        reviewed_subagents = 0
        benchmark_id = graph["active_benchmark_id"]
        role_state = graph["role_states"][benchmark_id]
        current_base_id = role_state["research_base_id"]
        parent_id = _require_string(
            request.get("parent_node_id"), "parent_node_id", max_length=16
        )
        parent = self._research_node(graph, parent_id)
        if parent["benchmark_id"] != benchmark_id:
            raise RuntimeErrorResponse(
                "BENCHMARK_MISMATCH", "Parent is not on the active Benchmark"
            )
        if action in {"CREATE_CANDIDATE", "CREATE_MERGE"} and parent_id != current_base_id:
            raise RuntimeErrorResponse(
                "INVALID_PRIMARY_PARENT",
                f"{action} must use current Research Base {current_base_id} as Primary Parent",
                allowed_next_actions=["USE_CURRENT_RESEARCH_BASE", "CREATE_REPAIR"],
            )
        submitted_base = _require_string(
            request.get("research_base_id"), "research_base_id", max_length=16
        )
        if submitted_base != current_base_id:
            raise RuntimeErrorResponse(
                "STALE_RESEARCH_BASE",
                f"Candidate must be classified relative to current Research Base {current_base_id}",
                allowed_next_actions=["INSPECT", "RECLASSIFY_CANDIDATE"],
            )
        comparison_target_id = _require_string(
            request.get("comparison_target_id"),
            "comparison_target_id",
            max_length=16,
        )
        comparison_target = self._research_node(graph, comparison_target_id)
        if comparison_target["benchmark_id"] != benchmark_id:
            raise RuntimeErrorResponse(
                "BENCHMARK_MISMATCH", "Comparison target uses another Benchmark"
            )

        classification = self._validate_classification(request.get("classification"))
        priority, priority_reason, branch_status, branch_reason, release_condition = (
            self._validate_candidate_priority(request, classification)
        )
        if action == "CREATE_MERGE" and classification["change_operator"] != "MERGE":
            raise RuntimeErrorResponse(
                "INVALID_MERGE", "CREATE_MERGE requires change_operator = MERGE"
            )
        if action != "CREATE_MERGE" and classification["change_operator"] == "MERGE":
            raise RuntimeErrorResponse(
                "INVALID_CANDIDATE",
                "MERGE classifications must use CREATE_MERGE",
            )

        source_node_ids = [
            _require_string(value, f"source_node_ids[{index}]", max_length=16)
            for index, value in enumerate(
                _require_list(request.get("source_node_ids", []), "source_node_ids")
            )
        ]
        node_index = self._node_index(graph)
        for source_id in source_node_ids:
            if source_id not in node_index:
                raise RuntimeErrorResponse(
                    "UNKNOWN_NODE", f"Unknown source node: {source_id}"
                )
        evidence_refs = [
            self._existing_ref(value, f"evidence_refs[{index}]")
            for index, value in enumerate(
                _require_list(request.get("evidence_refs"), "evidence_refs")
            )
        ]
        if not evidence_refs:
            raise RuntimeErrorResponse(
                "MISSING_EVIDENCE", "Candidate requires at least one evidence artifact"
            )
        refs = self._candidate_refs(request.get("refs", {}), action)

        extra_edges: list[dict[str, Any]] = []
        if action == "CREATE_REPAIR":
            experimental_parent_id = _require_string(
                request.get("experimental_parent_id"),
                "experimental_parent_id",
                max_length=16,
            )
            self._research_node(graph, experimental_parent_id)
            repairs = sum(
                edge["edge_type"] == "SOURCE"
                and edge["from_node_id"] == experimental_parent_id
                and str(edge.get("reason", "")).startswith("Paper Repair:")
                for edge in graph["edges"]
            )
            if repairs >= 3:
                raise RuntimeErrorResponse(
                    "PAPER_REPAIR_LIMIT",
                    "Experimental Parent already has three Paper Repair candidates",
                    allowed_next_actions=["CLOSE_NODE", "BACKTRACK", "CREATE_LITERATURE"],
                )
            extra_edges.append(
                {
                    "from_node_id": experimental_parent_id,
                    "edge_type": "SOURCE",
                    "reason": "Paper Repair: "
                    + _require_string(
                        request.get("repair_reason"), "repair_reason", max_length=700
                    ),
                    "evidence_ref": evidence_refs[0],
                }
            )
        elif action == "CREATE_MERGE":
            merge_source_ids = [
                _require_string(value, f"merge_source_node_ids[{index}]", max_length=16)
                for index, value in enumerate(
                    _require_list(
                        request.get("merge_source_node_ids"),
                        "merge_source_node_ids",
                    )
                )
            ]
            if len(set(merge_source_ids)) != 2:
                raise RuntimeErrorResponse(
                    "INVALID_MERGE", "MERGE requires exactly two distinct source nodes"
                )
            for source_id in merge_source_ids:
                source = self._research_node(graph, source_id)
                if source["research_base_id"] != current_base_id:
                    raise RuntimeErrorResponse(
                        "INVALID_MERGE",
                        "Both MERGE sources must have the current Research Base",
                    )
            interaction_pack = self._existing_ref(
                request.get("interaction_review_pack"),
                "interaction_review_pack",
            )
            reviews = _require_list(
                request.get("interaction_reviews"), "interaction_reviews"
            )
            if len(reviews) != 3:
                raise RuntimeErrorResponse(
                    "INTERACTION_GATE_FAILED",
                    "Interaction Review requires exactly three final reviews",
                )
            reviewer_ids: set[str] = set()
            pass_count = 0
            for index, raw_review in enumerate(reviews):
                review = _require_mapping(raw_review, f"interaction_reviews[{index}]")
                reviewer_id = _require_string(
                    review.get("reviewer_id"),
                    f"interaction_reviews[{index}].reviewer_id",
                    max_length=100,
                )
                reviewer_ids.add(reviewer_id)
                vote = _require_enum(
                    review.get("vote"),
                    f"interaction_reviews[{index}].vote",
                    {"PASS", "FAIL"},
                )
                pass_count += vote == "PASS"
                veto_state = _require_enum(
                    review.get("hard_veto_state", "NONE"),
                    f"interaction_reviews[{index}].hard_veto_state",
                    {"NONE", "RESOLVED", "UNRESOLVED", "CONFIRMED"},
                )
                if veto_state in {"UNRESOLVED", "CONFIRMED"}:
                    raise RuntimeErrorResponse(
                        "INTERACTION_GATE_FAILED",
                        "An unresolved or confirmed hard veto keeps MERGE on HOLD",
                    )
            if len(reviewer_ids) != 3 or pass_count < 2:
                raise RuntimeErrorResponse(
                    "INTERACTION_GATE_FAILED",
                    "MERGE requires three independent reviewers and at least two PASS votes",
                )
            reviewed_subagents = len(reviews)
            refs["interaction_review_pack"] = interaction_pack
            for source_id in merge_source_ids:
                extra_edges.append(
                    {
                        "from_node_id": source_id,
                        "edge_type": "MERGE",
                        "reason": _require_string(
                            request.get("merge_reason"), "merge_reason", max_length=700
                        ),
                        "evidence_ref": interaction_pack,
                    }
                )

        number = state["next_ids"]["research_node"]
        node_id = f"RN-{number:04d}"
        state["next_ids"]["research_node"] += 1
        node = {
            "node_id": node_id,
            "node_type": "RESEARCH",
            "created_at": _now(),
            "title": _require_string(request.get("title"), "title", max_length=300),
            "benchmark_id": benchmark_id,
            "research_base_id": current_base_id,
            "comparison_target_id": comparison_target_id,
            "experiment_id": None,
            "hypothesis": _require_string(
                request.get("hypothesis"), "hypothesis", max_length=1200
            ),
            "mechanism": _require_string(
                request.get("mechanism"), "mechanism", max_length=1200
            ),
            "single_main_change": _require_string(
                request.get("single_main_change"),
                "single_main_change",
                max_length=1200,
            ),
            "falsification_condition": _require_string(
                request.get("falsification_condition"),
                "falsification_condition",
                max_length=1200,
            ),
            "branch_status": branch_status,
            "branch_reason": branch_reason,
            "release_condition": release_condition,
            "run_outcome": "NOT_RUN",
            "hypothesis_verdict": "UNTESTED",
            "candidate_priority": priority,
            "priority_reason": priority_reason,
            "classification": classification,
            "metric_summary": self._empty_metric_summary(graph, benchmark_id),
            "refs": refs,
        }
        graph["nodes"].append(node)
        graph["edges"].append(
            {
                "from_node_id": parent_id,
                "to_node_id": node_id,
                "edge_type": "PRIMARY_PARENT",
                "reason": None,
                "evidence_ref": None,
            }
        )
        for source_id in source_node_ids:
            source = node_index[source_id]
            graph["edges"].append(
                {
                    "from_node_id": source_id,
                    "to_node_id": node_id,
                    "edge_type": (
                        "DIRECTION"
                        if source["node_type"] == "LITERATURE"
                        else "SOURCE"
                    ),
                    "reason": _require_string(
                        request.get("source_reason"),
                        "source_reason",
                        max_length=700,
                    ),
                    "evidence_ref": evidence_refs[0],
                }
            )
        for edge in extra_edges:
            edge["to_node_id"] = node_id
            graph["edges"].append(edge)
        state["audit_counters"]["subagent_calls"] += reviewed_subagents
        return {
            "node_id": node_id,
            "branch_status": branch_status,
            "candidate_priority": priority,
        }

    def _set_frontier(
        self, request: dict[str, Any], graph: dict[str, Any], state: dict[str, Any]
    ) -> dict[str, Any]:
        node_ids = [
            _require_string(value, f"node_ids[{index}]", max_length=16)
            for index, value in enumerate(
                _require_list(request.get("node_ids"), "node_ids")
            )
        ]
        if len(node_ids) > 3 or len(node_ids) != len(set(node_ids)):
            raise RuntimeErrorResponse(
                "INVALID_FRONTIER",
                "Active Frontier requires at most three distinct Research Nodes",
            )
        for node_id in node_ids:
            node = self._research_node(graph, node_id)
            self._assert_frontier_eligible(graph, node)
        graph["active_frontier"] = node_ids
        return {"active_frontier": node_ids}

    def _hold_node(
        self, request: dict[str, Any], graph: dict[str, Any], state: dict[str, Any]
    ) -> dict[str, Any]:
        node = self._research_node(
            graph, _require_string(request.get("node_id"), "node_id", max_length=16)
        )
        node["branch_status"] = "HOLD"
        node["branch_reason"] = _require_string(
            request.get("reason"), "reason", max_length=900
        )
        node["release_condition"] = _require_string(
            request.get("release_condition"), "release_condition", max_length=900
        )
        if node["node_id"] in graph["active_frontier"]:
            graph["active_frontier"].remove(node["node_id"])
        return {"node_id": node["node_id"], "branch_status": "HOLD"}

    def _reopen_node(
        self, request: dict[str, Any], graph: dict[str, Any], state: dict[str, Any]
    ) -> dict[str, Any]:
        node = self._research_node(
            graph, _require_string(request.get("node_id"), "node_id", max_length=16)
        )
        if node["branch_status"] != "HOLD":
            raise RuntimeErrorResponse(
                "INVALID_TRANSITION", "Only a HOLD node can be reopened"
            )
        evidence_refs = [
            self._existing_ref(value, f"evidence_refs[{index}]")
            for index, value in enumerate(
                _require_list(request.get("evidence_refs"), "evidence_refs")
            )
        ]
        if not evidence_refs:
            raise RuntimeErrorResponse(
                "MISSING_EVIDENCE", "Reopening HOLD requires release evidence"
            )
        node["branch_status"] = "OPEN"
        node["branch_reason"] = None
        node["release_condition"] = None
        return {"node_id": node["node_id"], "branch_status": "OPEN"}

    def _close_node(
        self, request: dict[str, Any], graph: dict[str, Any], state: dict[str, Any]
    ) -> dict[str, Any]:
        node = self._research_node(
            graph, _require_string(request.get("node_id"), "node_id", max_length=16)
        )
        role_state = graph["role_states"][graph["active_benchmark_id"]]
        protected = {
            role_state["anchor_baseline_id"],
            role_state["research_base_id"],
            role_state["champion_id"],
        }
        if node["node_id"] in protected:
            raise RuntimeErrorResponse(
                "PROTECTED_ROLE_NODE",
                "Current Anchor, Research Base, or Champion cannot be closed",
            )
        node["branch_status"] = "CLOSED"
        node["branch_reason"] = _require_string(
            request.get("reason"), "reason", max_length=900
        )
        node["release_condition"] = None
        if node["node_id"] in graph["active_frontier"]:
            graph["active_frontier"].remove(node["node_id"])
        return {"node_id": node["node_id"], "branch_status": "CLOSED"}

    def _promote_research_base(
        self, request: dict[str, Any], graph: dict[str, Any], state: dict[str, Any]
    ) -> dict[str, Any]:
        node = self._research_node(
            graph, _require_string(request.get("node_id"), "node_id", max_length=16)
        )
        benchmark_id = graph["active_benchmark_id"]
        role_state = graph["role_states"][benchmark_id]
        current_base_id = role_state["research_base_id"]
        if node["node_id"] == current_base_id:
            raise RuntimeErrorResponse(
                "PROMOTION_GATE_FAILED", "Node is already the current Research Base"
            )
        if node["research_base_id"] != current_base_id:
            raise RuntimeErrorResponse(
                "STALE_RESEARCH_BASE",
                f"Promotion candidate was evaluated against {node['research_base_id']}, not current Research Base {current_base_id}",
                allowed_next_actions=["RECREATE_CANDIDATE", "ASSIGN_REFERENCE_BASELINE"],
            )
        attestations = _require_mapping(request.get("attestations"), "attestations")
        required_attestations = ("stable", "general", "composable", "reproducible")
        failed = [name for name in required_attestations if attestations.get(name) is not True]
        if failed:
            raise RuntimeErrorResponse(
                "PROMOTION_GATE_FAILED",
                "Research Base structural attestations failed: " + ", ".join(failed),
                allowed_next_actions=["ASSIGN_REFERENCE_BASELINE", "INSPECT"],
            )
        gate = self._promotion_gate(graph, state, node)
        if gate["status"] != "ELIGIBLE":
            raise RuntimeErrorResponse(
                "PROMOTION_GATE_FAILED",
                gate["reason"],
                allowed_next_actions=gate["allowed_next_actions"],
            )

        classification = node["classification"]
        if classification["change_operator"] == "ADD":
            if request.get("replacement_node_id") is None:
                raise RuntimeErrorResponse(
                    "BRANCH_ADDITION_GATE",
                    "ADD promotion requires a completed replacement experiment",
                    allowed_next_actions=["CREATE_REPLACEMENT_CANDIDATE"],
                )
            replacement_id = _require_string(
                request.get("replacement_node_id"),
                "replacement_node_id",
                max_length=16,
            )
            independent = request.get("independent_function_attestation") is True
            replacement = self._research_node(graph, replacement_id)
            if (
                replacement["classification"] is None
                or replacement["classification"]["change_operator"] != "REPLACE"
            ):
                raise RuntimeErrorResponse(
                    "INVALID_REPLACEMENT",
                    "Branch Addition Gate replacement must use REPLACE",
                )
            if replacement["research_base_id"] != node["research_base_id"]:
                raise RuntimeErrorResponse(
                    "INVALID_REPLACEMENT",
                    "ADD and replacement experiments must use the same Research Base",
                )
            primary = state["primary_metric"]
            replacement_value = self._node_primary_value(
                replacement, primary["metric_id"]
            )
            if (
                replacement["run_outcome"]
                not in {"COMPLETED", "NORMAL_EARLY_STOP"}
                or replacement_value is None
            ):
                raise RuntimeErrorResponse(
                    "INVALID_REPLACEMENT",
                    "Branch Addition Gate requires a completed, hard-constraint-valid replacement result",
                    allowed_next_actions=[
                        f"RUN_REPLACEMENT_EXPERIMENT:{replacement['node_id']}"
                    ],
                )
            replacement_gate = self._promotion_gate(graph, state, replacement)
            if replacement_gate["status"] in {
                "NEEDS_SEEDS",
                "MISSING_BASELINE_SEEDS",
            }:
                raise RuntimeErrorResponse(
                    "REPLACEMENT_EVIDENCE_PENDING",
                    replacement_gate["reason"],
                    allowed_next_actions=replacement_gate["allowed_next_actions"],
                )
            add_value = self._node_primary_value(node, primary["metric_id"])
            base = self._research_node(graph, node["research_base_id"])
            base_value = self._node_primary_value(base, primary["metric_id"])
            if add_value is None or base_value is None:
                raise RuntimeErrorResponse(
                    "BRANCH_ADDITION_GATE",
                    "ADD or Research Base primary metric is unavailable",
                )
            replacement_improvement = _oriented_delta(
                replacement_value, base_value, primary["direction"]
            )
            loss = _oriented_delta(
                add_value, replacement_value, primary["direction"]
            )
            if (
                replacement_improvement > primary["promotion_threshold"]
                and loss <= primary["branch_replacement_tolerance"]
            ):
                raise RuntimeErrorResponse(
                    "REPLACEMENT_REQUIRED",
                    "Effective replacement is within the frozen tolerance; promote replacement instead",
                    allowed_next_actions=[
                        f"PROMOTE_RESEARCH_BASE:{replacement['node_id']}"
                    ],
                )
            if not independent:
                raise RuntimeErrorResponse(
                    "BRANCH_ADDITION_GATE",
                    "ADD promotion requires a failed replacement test and an independent-function attestation",
                    allowed_next_actions=[
                        "CREATE_REPLACEMENT_CANDIDATE",
                        "ASSIGN_REFERENCE_BASELINE",
                    ],
                )

        if (
            classification["change_operator"] == "DELETE"
            and classification["intervention_locus"] == "BRANCH"
        ):
            campaign = _require_mapping(
                request.get("simplification_campaign"),
                "simplification_campaign",
            )
            if campaign.get("campaign_complete") is not True:
                raise RuntimeErrorResponse(
                    "SIMPLIFICATION_CAMPAIGN_INCOMPLETE",
                    "All planned branch deletions must be evaluated together before promotion",
                    allowed_next_actions=["RUN_COMBINED_DELETION_EXPERIMENT"],
                )
            anchor_id = _require_string(
                campaign.get("anchor_node_id"),
                "simplification_campaign.anchor_node_id",
                max_length=16,
            )
            if anchor_id != role_state["simplification_anchor_id"]:
                raise RuntimeErrorResponse(
                    "SIMPLIFICATION_ANCHOR_MISMATCH",
                    f"Campaign must compare with {role_state['simplification_anchor_id']}",
                )
            deleted_branches = [
                _require_string(
                    value,
                    f"simplification_campaign.deleted_branches[{index}]",
                    max_length=200,
                )
                for index, value in enumerate(
                    _require_list(
                        campaign.get("deleted_branches"),
                        "simplification_campaign.deleted_branches",
                    )
                )
            ]
            if not deleted_branches or len(deleted_branches) != len(set(deleted_branches)):
                raise RuntimeErrorResponse(
                    "INVALID_SIMPLIFICATION_CAMPAIGN",
                    "deleted_branches must contain distinct planned branch names",
                )

        old_base_id = role_state["research_base_id"]
        role_state["research_base_id"] = node["node_id"]
        if classification["change_operator"] != "DELETE":
            role_state["simplification_anchor_id"] = node["node_id"]
        event = {
            "benchmark_id": benchmark_id,
            "created_at": _now(),
            "event_type": "REPLACED",
            "role": "RESEARCH_BASE",
            "node_id": node["node_id"],
            "previous_node_id": old_base_id,
            "reason": _require_string(request.get("reason"), "reason", max_length=900),
            "evidence_ref": node["refs"]["experiment_card"],
            "single_seed_provisional": (
                state["promotion_confirmation_policy"]["mode"]
                == "SINGLE_RUN_JUSTIFIED"
            ),
        }
        graph["role_events"].append(event)
        for frontier_id in list(graph["active_frontier"]):
            frontier_node = self._research_node(graph, frontier_id)
            if frontier_node["research_base_id"] != node["node_id"]:
                frontier_node["branch_status"] = "CLOSED"
                frontier_node["branch_reason"] = (
                    f"Stale after Research Base promotion to {node['node_id']}"
                )
                frontier_node["release_condition"] = None
                graph["active_frontier"].remove(frontier_id)
        return {
            "node_id": node["node_id"],
            "previous_research_base_id": old_base_id,
            "promotion_gate": gate,
        }

    def _assign_reference_baseline(
        self, request: dict[str, Any], graph: dict[str, Any], state: dict[str, Any]
    ) -> dict[str, Any]:
        node = self._research_node(
            graph, _require_string(request.get("node_id"), "node_id", max_length=16)
        )
        if node["run_outcome"] not in {"COMPLETED", "NORMAL_EARLY_STOP"}:
            raise RuntimeErrorResponse(
                "INVALID_ROLE_ASSIGNMENT",
                "Reference Baseline requires a complete comparable result",
            )
        primary = state["primary_metric"]
        if self._node_primary_value(node, primary["metric_id"]) is None:
            raise RuntimeErrorResponse(
                "INVALID_ROLE_ASSIGNMENT",
                "Reference Baseline requires a hard-constraint-valid primary metric",
            )
        role_state = graph["role_states"][graph["active_benchmark_id"]]
        if node["node_id"] not in role_state["reference_baseline_ids"]:
            role_state["reference_baseline_ids"].append(node["node_id"])
            graph["role_events"].append(
                {
                    "benchmark_id": graph["active_benchmark_id"],
                    "created_at": _now(),
                    "event_type": "ASSIGNED",
                    "role": "REFERENCE_BASELINE",
                    "node_id": node["node_id"],
                    "reason": _require_string(
                        request.get("reason"), "reason", max_length=900
                    ),
                    "evidence_ref": node["refs"]["experiment_card"],
                }
            )
        return {"node_id": node["node_id"], "role": "REFERENCE_BASELINE"}

    def _register_stage_summary(
        self, request: dict[str, Any], graph: dict[str, Any], state: dict[str, Any]
    ) -> dict[str, Any]:
        subagent_calls = request.get("subagent_calls")
        if (
            isinstance(subagent_calls, bool)
            or not isinstance(subagent_calls, int)
            or subagent_calls < 0
        ):
            raise RuntimeErrorResponse(
                "INVALID_REQUEST",
                "REGISTER_STAGE_SUMMARY requires non-negative integer subagent_calls",
            )
        covered = [
            _require_string(value, f"covered_node_ids[{index}]", max_length=16)
            for index, value in enumerate(
                _require_list(request.get("covered_node_ids"), "covered_node_ids")
            )
        ]
        node_index = self._node_index(graph)
        unknown = [node_id for node_id in covered if node_id not in node_index]
        if unknown:
            raise RuntimeErrorResponse(
                "UNKNOWN_NODE", "Unknown covered nodes: " + ", ".join(unknown)
            )
        summary_id = f"SS-{state['next_ids']['stage_summary']:03d}"
        state["next_ids"]["stage_summary"] += 1
        route = _require_enum(
            request.get("route_decision"), "route_decision", STAGE_ROUTES
        )
        if route == "CONCLUDE" and state["controller_status"] not in TERMINAL_STATUSES:
            raise RuntimeErrorResponse(
                "INVALID_STAGE_ROUTE",
                "CONCLUDE is legal only after target reached or budget exhausted",
                allowed_next_actions=["PIVOT", "CREATE_LITERATURE", "CREATE_CANDIDATE"],
            )
        graph["stage_summaries"].append(
            {
                "summary_id": summary_id,
                "created_at": _now(),
                "trigger": _require_string(
                    request.get("trigger"), "trigger", max_length=500
                ),
                "covered_node_ids": covered,
                "route_decision": route,
                "summary_ref": self._existing_ref(
                    request.get("summary_ref"), "summary_ref"
                ),
            }
        )
        state["audit_counters"]["stage_reflections"] += 1
        state["audit_counters"]["subagent_calls"] += subagent_calls
        return {"summary_id": summary_id, "route_decision": route}

    def _register_baseline_seed_evidence(
        self, request: dict[str, Any], graph: dict[str, Any], state: dict[str, Any]
    ) -> dict[str, Any]:
        node_id = _require_string(
            request.get("node_id"), "node_id", max_length=16
        )
        current_base_id = graph["role_states"][graph["active_benchmark_id"]][
            "research_base_id"
        ]
        if node_id != current_base_id:
            raise RuntimeErrorResponse(
                "STALE_RESEARCH_BASE",
                f"Seed evidence can be registered only for current Research Base {current_base_id}",
            )
        seed = request.get("seed")
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise RuntimeErrorResponse("INVALID_REQUEST", "seed must be an integer")
        value = _require_number(request.get("primary_value"), "primary_value")
        evidence_ref = self._existing_ref(
            request.get("evidence_ref"), "evidence_ref"
        )
        seed_map = state["node_seed_metrics"].setdefault(node_id, {})
        evidence_map = state["node_seed_evidence"].setdefault(node_id, {})
        key = str(seed)
        if key in seed_map and seed_map[key] != value:
            raise RuntimeErrorResponse(
                "IMMUTABLE_SEED_EVIDENCE",
                f"Seed {seed} already has a different registered value",
            )
        seed_map[key] = value
        evidence_map[key] = evidence_ref
        return {
            "node_id": node_id,
            "seed": seed,
            "primary_value": value,
            "evidence_ref": evidence_ref,
        }

    def _finalize_research(
        self, request: dict[str, Any], graph: dict[str, Any], state: dict[str, Any]
    ) -> dict[str, Any]:
        if state["active_run"] is not None:
            raise RuntimeErrorResponse(
                "RUN_ALREADY_ACTIVE", "Cannot finalize while an attempt is active"
            )
        if not (
            self._new_experiment_limit_reached(state)
            or self._time_or_cost_exhausted(state)
        ):
            raise RuntimeErrorResponse(
                "BUDGET_AVAILABLE",
                "Research cannot finalize while all hard budgets remain available",
                allowed_next_actions=["PROPOSE", "START_RUN"],
            )
        state["controller_status"] = "TARGET_NOT_REACHED"
        return {
            "controller_status": "TARGET_NOT_REACHED",
            "reason": _require_string(
                request.get("reason"), "reason", max_length=1000
            ),
        }

    # ------------------------------------------------------------------
    # Validation, promotion, and rendering helpers
    # ------------------------------------------------------------------

    def _request_id(self, request: dict[str, Any]) -> str:
        request_id = request.get("request_id")
        if not isinstance(request_id, str) or not _REQUEST_ID_RE.fullmatch(request_id):
            raise RuntimeErrorResponse(
                "INVALID_REQUEST_ID",
                "request_id must be 3–128 safe characters",
            )
        return request_id

    def _cached_response(
        self, state: dict[str, Any], request: dict[str, Any]
    ) -> dict[str, Any] | None:
        request_id = self._request_id(request)
        fingerprint = sha256_text(canonical_json(request))
        for record in state["applied_requests"]:
            if record["request_id"] == request_id:
                if record["fingerprint"] != fingerprint:
                    raise RuntimeErrorResponse(
                        "IDEMPOTENCY_CONFLICT",
                        "request_id was already used with a different payload",
                    )
                return copy.deepcopy(record["response"])
        return None

    def _remember_request(
        self,
        state: dict[str, Any],
        request_id: str,
        request: dict[str, Any],
        response: dict[str, Any],
    ) -> None:
        state["applied_requests"].append(
            {
                "request_id": request_id,
                "fingerprint": sha256_text(canonical_json(request)),
                "response": copy.deepcopy(response),
            }
        )
        state["applied_requests"] = state["applied_requests"][-100:]

    def _commit_mutation(
        self,
        graph: dict[str, Any],
        state: dict[str, Any],
        request: dict[str, Any],
        response: dict[str, Any],
        *,
        extra_files: dict[str, str] | None = None,
    ) -> None:
        next_revision = graph["revision"] + 1
        graph["revision"] = next_revision
        graph["updated_at"] = _now()
        state["revision"] = next_revision
        response["revision"] = next_revision
        self._remember_request(state, self._request_id(request), request, response)
        violations = self._validate_all(
            graph, state, check_artifacts=False
        )
        if violations:
            raise RuntimeErrorResponse(
                "PROPOSAL_REJECTED",
                *violations,
                allowed_next_actions=["INSPECT", "CORRECT_PROPOSAL"],
            )
        html_text = render_graph_html(graph)
        for relative_path, text in (extra_files or {}).items():
            target = resolve_project_path(self.root, relative_path)
            atomic_write_text(target, text)
        atomic_write_json(state_path(self.root), state)
        atomic_write_text(self.root / GRAPH_HTML_FILENAME, html_text)
        atomic_write_json(graph_path(self.root), graph)

    def _write_initial_project(
        self, graph: dict[str, Any], state: dict[str, Any]
    ) -> None:
        for relative in (
            "experiments",
            "logs/research",
            "logs/runs",
            "logs/summaries",
            RUNTIME_DIRECTORY,
        ):
            (self.root / relative).mkdir(parents=True, exist_ok=True)
        atomic_write_json(state_path(self.root), state)
        atomic_write_text(
            self.root / GRAPH_HTML_FILENAME, render_graph_html(graph)
        )
        atomic_write_json(graph_path(self.root), graph)

    def _assert_mutable(self, state: dict[str, Any]) -> None:
        if state["controller_status"] in TERMINAL_STATUSES:
            raise RuntimeErrorResponse(
                "RESEARCH_TERMINATED",
                f'Research already ended with {state["controller_status"]}',
                controller_status=state["controller_status"],
            )
        if state["controller_status"] == "HUMAN_REVIEW_REQUIRED":
            raise RuntimeErrorResponse(
                "HUMAN_REVIEW_REQUIRED",
                "Frozen contract requires human review before more mutations",
                controller_status="HUMAN_REVIEW_REQUIRED",
            )

    def _assert_canonical_consistency(
        self, graph: dict[str, Any], state: dict[str, Any]
    ) -> None:
        violations = self._validate_all(
            graph,
            state,
            check_contract_hashes=False,
            check_artifacts=True,
        )
        if violations:
            raise RuntimeErrorResponse(
                "CANONICAL_INCONSISTENCY",
                *violations,
                controller_status="HUMAN_REVIEW_REQUIRED",
                allowed_next_actions=[
                    "VALIDATE",
                    "RESTORE_CANONICAL_CONSISTENCY",
                    "HUMAN_REVIEW",
                ],
            )

    def _assert_contracts_unchanged(self, state: dict[str, Any]) -> None:
        contract = state["contract_hashes"]
        violations = []
        for label in ("research_brief", "benchmark"):
            relative = contract[f"{label}_ref"]
            path = self.root / relative
            if not path.exists():
                violations.append(f"Frozen {label} artifact is missing: {relative}")
                continue
            actual = sha256_file(path)
            if actual != contract[f"{label}_sha256"]:
                violations.append(f"Frozen {label} artifact changed: {relative}")
        if violations:
            raise RuntimeErrorResponse(
                "FROZEN_CONTRACT_CHANGED",
                *violations,
                controller_status="HUMAN_REVIEW_REQUIRED",
                allowed_next_actions=["HUMAN_REVIEW"],
            )

    def _validate_benchmark(self, raw: Any) -> dict[str, Any]:
        benchmark = _require_mapping(raw, "benchmark")
        benchmark_id = _require_string(
            benchmark.get("benchmark_id"), "benchmark.benchmark_id", max_length=100
        )
        benchmark_ref = _require_string(
            benchmark.get("benchmark_ref"), "benchmark.benchmark_ref", max_length=500
        )
        raw_metrics = _require_list(
            benchmark.get("display_metrics"), "benchmark.display_metrics"
        )
        if not 1 <= len(raw_metrics) <= 3:
            raise RuntimeErrorResponse(
                "INVALID_BENCHMARK", "display_metrics must contain 1–3 metrics"
            )
        metrics = []
        metric_ids: set[str] = set()
        for index, raw_metric in enumerate(raw_metrics):
            metric = _require_mapping(raw_metric, f"display_metrics[{index}]")
            metric_id = _require_string(
                metric.get("metric_id"),
                f"display_metrics[{index}].metric_id",
                max_length=80,
            )
            if metric_id in metric_ids:
                raise RuntimeErrorResponse(
                    "INVALID_BENCHMARK", f"Duplicate metric_id: {metric_id}"
                )
            metric_ids.add(metric_id)
            precision = metric.get("precision")
            if isinstance(precision, bool) or not isinstance(precision, int) or not 0 <= precision <= 12:
                raise RuntimeErrorResponse(
                    "INVALID_BENCHMARK",
                    f"display_metrics[{index}].precision must be an integer from 0 to 12",
                )
            metrics.append(
                {
                    "metric_id": metric_id,
                    "label": _require_string(
                        metric.get("label"),
                        f"display_metrics[{index}].label",
                        max_length=100,
                    ),
                    "role": _require_enum(
                        metric.get("role"),
                        f"display_metrics[{index}].role",
                        {"PRIMARY", "SECONDARY"},
                    ),
                    "direction": _require_enum(
                        metric.get("direction"),
                        f"display_metrics[{index}].direction",
                        {"MAXIMIZE", "MINIMIZE"},
                    ),
                    "unit": _require_string(
                        metric.get("unit"),
                        f"display_metrics[{index}].unit",
                        max_length=50,
                    ),
                    "precision": precision,
                }
            )
        if metrics[0]["role"] != "PRIMARY" or sum(
            metric["role"] == "PRIMARY" for metric in metrics
        ) != 1:
            raise RuntimeErrorResponse(
                "INVALID_BENCHMARK",
                "The first display metric must be the only PRIMARY metric",
            )
        return {
            "benchmark_id": benchmark_id,
            "benchmark_ref": benchmark_ref,
            "display_metrics": metrics,
        }

    def _validate_primary_metric(
        self, raw: Any, benchmark: dict[str, Any]
    ) -> dict[str, Any]:
        metric = _require_mapping(raw, "primary_metric")
        benchmark_metric = benchmark["display_metrics"][0]
        metric_id = _require_string(metric.get("metric_id"), "primary_metric.metric_id")
        if metric_id != benchmark_metric["metric_id"]:
            raise RuntimeErrorResponse(
                "INVALID_PRIMARY_METRIC",
                "primary_metric.metric_id must match the first Benchmark display metric",
            )
        direction = _require_enum(
            metric.get("direction"),
            "primary_metric.direction",
            {"MAXIMIZE", "MINIMIZE"},
        )
        if direction != benchmark_metric["direction"]:
            raise RuntimeErrorResponse(
                "INVALID_PRIMARY_METRIC",
                "Primary metric direction conflicts with Benchmark",
            )
        return {
            "metric_id": metric_id,
            "direction": direction,
            "target": _require_number(metric.get("target"), "primary_metric.target"),
            "promotion_threshold": _require_number(
                metric.get("promotion_threshold"),
                "primary_metric.promotion_threshold",
                minimum=0,
            ),
            "simplification_tolerance": _require_number(
                metric.get("simplification_tolerance"),
                "primary_metric.simplification_tolerance",
                minimum=0,
            ),
            "branch_replacement_tolerance": _require_number(
                metric.get("branch_replacement_tolerance"),
                "primary_metric.branch_replacement_tolerance",
                minimum=0,
            ),
            "fast_run_seconds": _require_number(
                metric.get("fast_run_seconds", 300),
                "primary_metric.fast_run_seconds",
                minimum=1,
            ),
        }

    def _validate_promotion_confirmation_policy(
        self, raw: Any
    ) -> dict[str, Any]:
        policy = _require_mapping(raw, "promotion_confirmation_policy")
        mode = _require_enum(
            policy.get("mode"),
            "promotion_confirmation_policy.mode",
            PROMOTION_CONFIRMATION_POLICIES,
        )
        threshold = policy.get("single_run_threshold")
        justification = policy.get("single_run_justification")
        if mode != "SINGLE_RUN_JUSTIFIED":
            if threshold is not None or justification is not None:
                raise RuntimeErrorResponse(
                    "INVALID_BENCHMARK",
                    "Only SINGLE_RUN_JUSTIFIED may define a single-run threshold or justification",
                )
            return {
                "mode": mode,
                "single_run_threshold": None,
                "single_run_justification": None,
            }

        threshold = _require_mapping(
            threshold, "promotion_confirmation_policy.single_run_threshold"
        )
        resource = _require_enum(
            threshold.get("resource"),
            "promotion_confirmation_policy.single_run_threshold.resource",
            {"DURATION_SECONDS", "COST"},
        )
        value = _require_number(
            threshold.get("value"),
            "promotion_confirmation_policy.single_run_threshold.value",
            minimum=0.000001,
        )
        return {
            "mode": mode,
            "single_run_threshold": {
                "resource": resource,
                "value": value,
            },
            "single_run_justification": _require_string(
                justification,
                "promotion_confirmation_policy.single_run_justification",
                max_length=1200,
            ),
        }

    def _validate_budget(self, raw: Any) -> dict[str, Any]:
        budget = _require_mapping(raw, "budget")
        limits: dict[str, int | float | str | None] = {}
        for name in ("max_experiments", "max_run_seconds", "max_cost"):
            value = budget.get(name)
            if value is None:
                limits[name] = None
                continue
            number = _require_number(value, f"budget.{name}", minimum=0)
            if name == "max_experiments":
                if not number.is_integer() or number < 1:
                    raise RuntimeErrorResponse(
                        "INVALID_BUDGET",
                        "max_experiments must be a positive integer",
                    )
                limits[name] = int(number)
            else:
                if number <= 0:
                    raise RuntimeErrorResponse(
                        "INVALID_BUDGET", f"{name} must be greater than zero"
                    )
                limits[name] = number
        if all(
            limits[name] is None
            for name in ("max_experiments", "max_run_seconds", "max_cost")
        ):
            raise RuntimeErrorResponse(
                "INVALID_BUDGET", "At least one hard budget limit is required"
            )
        cost_unit = budget.get("cost_unit")
        if cost_unit is not None:
            cost_unit = _require_string(
                cost_unit,
                "budget.cost_unit",
                max_length=32,
            )
        if limits["max_cost"] is not None and cost_unit is None:
            raise RuntimeErrorResponse(
                "INVALID_BUDGET",
                "budget.max_cost requires cost_unit from the frozen Research Brief",
            )
        limits["cost_unit"] = cost_unit
        return {
            "limits": limits,
            "consumed": {
                "experiments_started": 0,
                "attempts_started": 0,
                "run_seconds": 0.0,
                "cost": 0.0,
            },
        }

    def _validate_initial_model(
        self, raw: Any, benchmark: dict[str, Any], index: int
    ) -> dict[str, Any]:
        model = _require_mapping(raw, f"initial_models[{index - 1}]")
        roles = [
            _require_enum(role, f"initial_models[{index - 1}].roles", ROLE_NAMES)
            for role in _require_list(
                model.get("roles"), f"initial_models[{index - 1}].roles"
            )
        ]
        if len(roles) != len(set(roles)):
            raise RuntimeErrorResponse(
                "INVALID_INITIAL_ROLES", "Initial model roles cannot repeat"
            )
        metrics = self._validate_metric_mapping(
            model.get("metrics"), benchmark, require_all=True
        )
        raw_seed_metrics = _require_mapping(
            model.get("seed_metrics", {}),
            f"initial_models[{index - 1}].seed_metrics",
        )
        seed_metrics = {}
        for seed, value in raw_seed_metrics.items():
            try:
                normalized_seed = str(int(seed))
            except (TypeError, ValueError) as error:
                raise RuntimeErrorResponse(
                    "INVALID_INITIAL_MODEL", f"Invalid seed key: {seed}"
                ) from error
            seed_metrics[normalized_seed] = _require_number(
                value, f"seed_metrics.{seed}"
            )
        return {
            "title": _require_string(
                model.get("title"), f"initial_models[{index - 1}].title", max_length=300
            ),
            "roles": roles,
            "metrics": metrics,
            "seed_metrics": seed_metrics,
            "evidence_ref": self._existing_ref(
                model.get("evidence_ref"),
                f"initial_models[{index - 1}].evidence_ref",
            ),
        }

    def _root_research_node(
        self,
        *,
        model: dict[str, Any],
        benchmark: dict[str, Any],
        research_base_id: str,
        comparison_target_id: str,
        base_metrics: dict[str, float],
        champion_metrics: dict[str, float],
        created_at: str,
    ) -> dict[str, Any]:
        metric_summary = []
        for metric in benchmark["display_metrics"]:
            metric_id = metric["metric_id"]
            direction = metric["direction"]
            value = model["metrics"][metric_id]
            metric_summary.append(
                {
                    "metric_id": metric_id,
                    "label": metric["label"],
                    "value": value,
                    "delta_vs_research_base": _oriented_delta(
                        value, base_metrics[metric_id], direction
                    ),
                    "delta_vs_champion": _oriented_delta(
                        value, champion_metrics[metric_id], direction
                    ),
                }
            )
        return {
            "node_id": model["node_id"],
            "node_type": "RESEARCH",
            "created_at": created_at,
            "title": model["title"],
            "benchmark_id": benchmark["benchmark_id"],
            "research_base_id": research_base_id,
            "comparison_target_id": comparison_target_id,
            "experiment_id": None,
            "hypothesis": None,
            "mechanism": None,
            "single_main_change": None,
            "falsification_condition": None,
            "branch_status": "OPEN",
            "branch_reason": None,
            "release_condition": None,
            "run_outcome": "COMPLETED",
            "hypothesis_verdict": "NOT_EVALUABLE",
            "candidate_priority": None,
            "priority_reason": None,
            "classification": None,
            "metric_summary": metric_summary,
            "refs": {
                "experiment_card": None,
                "research_log": None,
                "run_directory": None,
                "paper_mechanism_cards": [],
                "interaction_review_pack": None,
            },
        }

    def _validate_classification(self, raw: Any) -> dict[str, str]:
        classification = _require_mapping(raw, "classification")
        return {
            "evidence_class": _require_enum(
                classification.get("evidence_class"),
                "classification.evidence_class",
                EVIDENCE_CLASSES,
            ),
            "change_scope": _require_enum(
                classification.get("change_scope"),
                "classification.change_scope",
                CHANGE_SCOPES,
            ),
            "research_layer": _require_enum(
                classification.get("research_layer"),
                "classification.research_layer",
                RESEARCH_LAYERS,
            ),
            "intervention_locus": _require_enum(
                classification.get("intervention_locus"),
                "classification.intervention_locus",
                INTERVENTION_LOCI,
            ),
            "change_operator": _require_enum(
                classification.get("change_operator"),
                "classification.change_operator",
                CHANGE_OPERATORS,
            ),
        }

    def _priority_matrix(self) -> dict[tuple[str, str, str, str], dict[str, str]]:
        return {
            key: {
                "combination_status": status,
                "structural_default_priority": priority,
                "decision_reason": _REJECTED_PRIORITY_REASON,
            }
            for key, (status, priority) in PRIORITY_MATRIX.items()
        }

    def _validate_candidate_priority(
        self, request: dict[str, Any], classification: dict[str, str]
    ) -> tuple[str | None, str | None, str, str | None, str | None]:
        evidence_class = classification["evidence_class"]
        if evidence_class != "N":
            if request.get("candidate_priority") is not None:
                raise RuntimeErrorResponse(
                    "INVALID_PRIORITY", "R/A candidates require candidate_priority = null"
                )
            return None, None, "OPEN", None, None

        requested = _require_enum(
            request.get("candidate_priority"),
            "candidate_priority",
            CANDIDATE_PRIORITIES,
        )
        key = (
            evidence_class,
            classification["change_scope"],
            classification["intervention_locus"],
            classification["change_operator"],
        )
        row = self._priority_matrix().get(key)
        if row is None or row["combination_status"] != "VALID":
            raise RuntimeErrorResponse(
                "INVALID_CLASSIFICATION",
                "Classification combination is absent or invalid in the canonical matrix",
            )
        structural = _require_enum(
            row["structural_default_priority"],
            "structural_default_priority",
            MATRIX_PRIORITIES,
        )
        if structural in {"REJECT", "INVALID"}:
            raise RuntimeErrorResponse(
                "CANDIDATE_REJECTED",
                row["decision_reason"],
                allowed_next_actions=["SPLIT_CANDIDATE", "RECLASSIFY_CANDIDATE"],
            )
        rank = {"GOLD": 3, "SILVER": 2, "HOLD": 1}
        if rank[requested] > rank[structural]:
            raise RuntimeErrorResponse(
                "PRIORITY_UPGRADE_FORBIDDEN",
                f"Requested {requested} exceeds structural ceiling {structural}",
                allowed_next_actions=[f"USE_PRIORITY:{structural}"],
            )
        reason = _require_string(
            request.get("priority_reason"), "priority_reason", max_length=800
        )
        if requested == "HOLD":
            branch_reason = _require_string(
                request.get("branch_reason"), "branch_reason", max_length=800
            )
            release_condition = _require_string(
                request.get("release_condition"),
                "release_condition",
                max_length=800,
            )
            return requested, reason, "HOLD", branch_reason, release_condition
        return requested, reason, "OPEN", None, None

    def _candidate_refs(self, raw: Any, action: str) -> dict[str, Any]:
        refs = _require_mapping(raw, "refs")
        paper_cards = [
            self._existing_ref(value, f"refs.paper_mechanism_cards[{index}]")
            for index, value in enumerate(
                _require_list(
                    refs.get("paper_mechanism_cards", []),
                    "refs.paper_mechanism_cards",
                )
            )
        ]
        interaction = self._optional_existing_ref(
            refs.get("interaction_review_pack"), "refs.interaction_review_pack"
        )
        if action != "CREATE_MERGE" and interaction is not None:
            raise RuntimeErrorResponse(
                "INVALID_REFS",
                "Only MERGE may set interaction_review_pack",
            )
        return {
            "experiment_card": None,
            "research_log": None,
            "run_directory": None,
            "paper_mechanism_cards": paper_cards,
            "interaction_review_pack": interaction,
        }

    def _validate_start_preregistration(
        self, request: dict[str, Any], node: dict[str, Any]
    ) -> dict[str, Any]:
        raw = _require_mapping(request.get("preregistration"), "preregistration")
        preregistration = {
            "hypothesis": _require_string(
                raw.get("hypothesis"), "preregistration.hypothesis", max_length=1200
            ),
            "single_main_change": _require_string(
                raw.get("single_main_change"),
                "preregistration.single_main_change",
                max_length=1200,
            ),
            "falsification_condition": _require_string(
                raw.get("falsification_condition"),
                "preregistration.falsification_condition",
                max_length=1200,
            ),
            "classification": self._validate_classification(raw.get("classification")),
        }
        expected = {
            "hypothesis": node["hypothesis"],
            "single_main_change": node["single_main_change"],
            "falsification_condition": node["falsification_condition"],
            "classification": node["classification"],
        }
        mismatches = [
            field
            for field in preregistration
            if preregistration[field] != expected[field]
        ]
        if mismatches:
            raise RuntimeErrorResponse(
                "PREREGISTRATION_MISMATCH",
                "start-run preregistration differs from the Research Node: "
                + ", ".join(mismatches),
                allowed_next_actions=["INSPECT", "RESTORE_PREREGISTRATION"],
            )
        return preregistration

    def _validate_start_transition(
        self,
        graph: dict[str, Any],
        state: dict[str, Any],
        node: dict[str, Any],
        run_kind: str,
    ) -> None:
        if run_kind in {"FULL", "SMOKE"}:
            if node["node_id"] not in graph["active_frontier"]:
                raise RuntimeErrorResponse(
                    "NODE_NOT_SELECTED",
                    "FULL/SMOKE can start only from Active Frontier",
                    allowed_next_actions=["SET_FRONTIER", "INSPECT"],
                )
            self._assert_frontier_eligible(graph, node)
        elif run_kind == "RETRY":
            if node["run_outcome"] != "TECHNICAL_FAILURE":
                raise RuntimeErrorResponse(
                    "INVALID_RETRY",
                    "RETRY requires a prior TECHNICAL_FAILURE",
                )
            if node["experiment_id"] is None:
                raise RuntimeErrorResponse(
                    "INVALID_RETRY", "RETRY must reuse an existing Experiment ID"
                )
        elif run_kind == "PROMOTION_CONFIRMATION":
            gate = self._promotion_gate(graph, state, node)
            if gate["status"] not in {"NEEDS_SEEDS", "MISSING_BASELINE_SEEDS"}:
                raise RuntimeErrorResponse(
                    "INVALID_PROMOTION_CONFIRMATION",
                    "Promotion confirmation is allowed only when seed evidence is pending",
                )

    def _allocate_run_ids(
        self,
        graph: dict[str, Any],
        state: dict[str, Any],
        node: dict[str, Any],
    ) -> tuple[str, str, bool]:
        if node["experiment_id"] is None:
            number = state["next_ids"]["experiment"]
            experiment_id = f"E{number:03d}"
            state["next_ids"]["experiment"] += 1
            return experiment_id, "A01", True
        experiment_id = node["experiment_id"]
        experiment = state["experiments"].get(experiment_id)
        if experiment is None:
            raise RuntimeErrorResponse(
                "CANONICAL_INCONSISTENCY",
                f"Graph references missing runtime experiment {experiment_id}",
                controller_status="HUMAN_REVIEW_REQUIRED",
            )
        attempt_id = f"A{len(experiment['attempts']) + 1:02d}"
        return experiment_id, attempt_id, False

    def _validate_finish_verdict(
        self, run_kind: str, outcome: str, raw_verdict: Any
    ) -> str:
        if run_kind == "SMOKE" or outcome == "TECHNICAL_FAILURE":
            expected = "NOT_EVALUABLE"
        elif outcome == "STOP_LOSS":
            expected = "NOT_SUPPORTED"
        else:
            expected = _require_enum(
                raw_verdict,
                "hypothesis_verdict",
                {"SUPPORTED", "NOT_SUPPORTED", "INCONCLUSIVE"},
            )
        if raw_verdict is not None and raw_verdict != expected:
            raise RuntimeErrorResponse(
                "INVALID_VERDICT",
                f"{run_kind}/{outcome} requires hypothesis_verdict = {expected}",
            )
        return expected

    def _validate_artifact_refs(
        self,
        raw: Any,
        *,
        required: bool,
    ) -> dict[str, str]:
        if raw is None:
            if required:
                raise RuntimeErrorResponse(
                    "FORMAL_ARTIFACTS_REQUIRED",
                    "Formal runs must preregister resolved_config, metrics_json, "
                    "artifact_manifest, and trainer_log paths",
                )
            return {}
        refs = _require_mapping(raw, "artifact_refs")
        unknown = set(refs) - set(_FORMAL_ARTIFACT_KEYS)
        if unknown:
            raise RuntimeErrorResponse(
                "INVALID_ARTIFACT_REFS",
                "Unknown artifact_refs keys: " + ", ".join(sorted(unknown)),
            )
        if required:
            missing = set(_FORMAL_ARTIFACT_KEYS) - set(refs)
            if missing:
                raise RuntimeErrorResponse(
                    "FORMAL_ARTIFACTS_REQUIRED",
                    "Missing formal artifact refs: " + ", ".join(sorted(missing)),
                )
        normalized = {
            key: self._future_ref(value, f"artifact_refs.{key}")
            for key, value in refs.items()
        }
        if len(set(normalized.values())) != len(normalized):
            raise RuntimeErrorResponse(
                "INVALID_ARTIFACT_REFS",
                "Each formal artifact type must use a distinct path",
            )
        return normalized

    def _load_formal_run_artifacts(
        self,
        *,
        attempt: dict[str, Any],
        request_metrics: Any,
        graph: dict[str, Any],
        experiment_id: str,
        attempt_id: str,
    ) -> tuple[dict[str, float], dict[str, str]]:
        refs = attempt.get("artifact_refs", {})
        missing_keys = set(_FORMAL_ARTIFACT_KEYS) - set(refs)
        if missing_keys:
            raise RuntimeErrorResponse(
                "FORMAL_ARTIFACTS_REQUIRED",
                "Missing formal artifact refs: " + ", ".join(sorted(missing_keys)),
                allowed_next_actions=["RESTORE_ATTEMPT_ARTIFACT_REFS", "FINISH_RUN"],
            )

        paths: dict[str, Path] = {}
        for key in _FORMAL_ARTIFACT_KEYS:
            relative = refs[key]
            try:
                paths[key] = resolve_project_path(
                    self.root,
                    relative,
                    must_exist=True,
                    allow_directory=False,
                )
            except ValueError as error:
                raise RuntimeErrorResponse(
                    "FORMAL_ARTIFACT_MISSING",
                    f"artifact_refs.{key}: {error}",
                    allowed_next_actions=["PRODUCE_MISSING_ARTIFACT", "FINISH_RUN"],
                ) from error

        for key in ("resolved_config", "trainer_log"):
            if paths[key].stat().st_size == 0:
                raise RuntimeErrorResponse(
                    "INVALID_FORMAL_ARTIFACT",
                    f"artifact_refs.{key} must not be empty",
                    allowed_next_actions=["REGENERATE_ARTIFACT", "FINISH_RUN"],
                )

        metrics_payload = self._read_json_artifact(
            paths["metrics_json"], "artifact_refs.metrics_json"
        )
        manifest_payload = self._read_json_artifact(
            paths["artifact_manifest"], "artifact_refs.artifact_manifest"
        )
        self._validate_artifact_identity(
            metrics_payload,
            name="metrics_json",
            experiment_id=experiment_id,
            attempt_id=attempt_id,
        )
        self._validate_artifact_identity(
            manifest_payload,
            name="artifact_manifest",
            experiment_id=experiment_id,
            attempt_id=attempt_id,
        )
        self._validate_manifest_artifact_links(manifest_payload, paths)
        if str(manifest_payload.get("status", "")).lower() != "completed":
            raise RuntimeErrorResponse(
                "INVALID_FORMAL_ARTIFACT",
                "artifact_manifest.status must be completed for a successful run",
            )

        artifact_metrics = self._extract_artifact_metrics(metrics_payload, graph)
        metrics = self._validate_result_metrics(
            artifact_metrics,
            graph,
            "COMPLETED",
        )
        if request_metrics is not None:
            submitted = self._validate_result_metrics(
                request_metrics,
                graph,
                "COMPLETED",
            )
            mismatches = [
                metric_id
                for metric_id in metrics
                if not math.isclose(
                    metrics[metric_id],
                    submitted[metric_id],
                    rel_tol=0,
                    abs_tol=1e-12,
                )
            ]
            if mismatches:
                raise RuntimeErrorResponse(
                    "ARTIFACT_METRICS_MISMATCH",
                    "Submitted metrics differ from metrics_json: "
                    + ", ".join(sorted(mismatches)),
                    allowed_next_actions=["USE_ARTIFACT_METRICS", "FINISH_RUN"],
                )

        hashes = {
            key: sha256_file(path)
            for key, path in paths.items()
        }
        return metrics, hashes

    def _read_json_artifact(self, path: Path, name: str) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeErrorResponse(
                "INVALID_FORMAL_ARTIFACT",
                f"{name} must be a readable JSON object: {error}",
            ) from error
        if not isinstance(payload, dict):
            raise RuntimeErrorResponse(
                "INVALID_FORMAL_ARTIFACT",
                f"{name} must contain a JSON object",
            )
        return payload

    def _validate_artifact_identity(
        self,
        payload: dict[str, Any],
        *,
        name: str,
        experiment_id: str,
        attempt_id: str,
    ) -> None:
        recorded_experiment = payload.get("experiment_id")
        if recorded_experiment != experiment_id:
            raise RuntimeErrorResponse(
                "ARTIFACT_ID_MISMATCH",
                f"{name}.experiment_id must equal {experiment_id}",
            )
        recorded_run = payload.get("run_id")
        if recorded_run != attempt_id:
            raise RuntimeErrorResponse(
                "ARTIFACT_ID_MISMATCH",
                f"{name}.run_id must equal {attempt_id}",
            )

    def _validate_manifest_artifact_links(
        self,
        manifest: dict[str, Any],
        paths: dict[str, Path],
    ) -> None:
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, dict):
            raise RuntimeErrorResponse(
                "INVALID_FORMAL_ARTIFACT",
                "artifact_manifest.artifacts must be an object",
            )
        manifest_keys = {
            "resolved_config": "resolved_config_yaml",
            "metrics_json": "metrics_json",
            "trainer_log": "text_log",
        }
        for artifact_key, manifest_key in manifest_keys.items():
            value = artifacts.get(manifest_key)
            if not isinstance(value, str) or not value.strip():
                raise RuntimeErrorResponse(
                    "INVALID_FORMAL_ARTIFACT",
                    f"artifact_manifest.artifacts.{manifest_key} is required",
                )
            try:
                linked = resolve_project_path(self.root, value, must_exist=True)
            except ValueError as error:
                raise RuntimeErrorResponse(
                    "INVALID_FORMAL_ARTIFACT",
                    f"artifact_manifest.artifacts.{manifest_key}: {error}",
                ) from error
            if linked != paths[artifact_key]:
                raise RuntimeErrorResponse(
                    "ARTIFACT_LINK_MISMATCH",
                    f"artifact_manifest.artifacts.{manifest_key} does not match "
                    f"artifact_refs.{artifact_key}",
                )

    def _extract_artifact_metrics(
        self,
        payload: dict[str, Any],
        graph: dict[str, Any],
    ) -> dict[str, Any]:
        direct = payload.get("metrics")
        if isinstance(direct, dict):
            return direct
        best_entry = payload.get("best_entry")
        if not isinstance(best_entry, dict):
            raise RuntimeErrorResponse(
                "INVALID_FORMAL_ARTIFACT",
                "metrics_json must contain a metrics object or ReproFlow best_entry",
            )
        benchmark = self._benchmark(graph, graph["active_benchmark_id"])
        extracted: dict[str, Any] = {}
        for metric in benchmark["display_metrics"]:
            metric_id = metric["metric_id"]
            for key in (metric_id, f"val_{metric_id}", f"test_{metric_id}"):
                if key in best_entry:
                    extracted[metric_id] = best_entry[key]
                    break
        return extracted

    def _validate_result_metrics(
        self, raw: Any, graph: dict[str, Any], outcome: str
    ) -> dict[str, float]:
        benchmark = self._benchmark(graph, graph["active_benchmark_id"])
        require_all = outcome in {"COMPLETED", "NORMAL_EARLY_STOP"}
        return self._validate_metric_mapping(raw, benchmark, require_all=require_all)

    def _validate_metric_mapping(
        self, raw: Any, benchmark: dict[str, Any], *, require_all: bool
    ) -> dict[str, float]:
        metrics = _require_mapping(raw, "metrics")
        allowed = {item["metric_id"] for item in benchmark["display_metrics"]}
        unknown = set(metrics) - allowed
        if unknown:
            raise RuntimeErrorResponse(
                "INVALID_METRICS", "Unknown metrics: " + ", ".join(sorted(unknown))
            )
        if require_all and set(metrics) != allowed:
            missing = allowed - set(metrics)
            raise RuntimeErrorResponse(
                "INVALID_METRICS",
                "Complete result is missing metrics: " + ", ".join(sorted(missing)),
            )
        return {
            metric_id: _require_number(value, f"metrics.{metric_id}")
            for metric_id, value in metrics.items()
        }

    def _aggregate_metric_summary(
        self,
        graph: dict[str, Any],
        state: dict[str, Any],
        node: dict[str, Any],
        experiment: dict[str, Any],
    ) -> list[dict[str, Any]]:
        benchmark = self._benchmark(graph, node["benchmark_id"])
        role_state = graph["role_states"][node["benchmark_id"]]
        base = self._research_node(graph, node["research_base_id"])
        champion = self._research_node(graph, role_state["champion_id"])
        valid_attempts = [
            attempt
            for attempt in experiment["attempts"]
            if attempt["run_kind"] != "SMOKE"
            and attempt["run_outcome"] in {"COMPLETED", "NORMAL_EARLY_STOP"}
            and attempt["hard_constraints_passed"]
        ]
        summary = []
        for metric in benchmark["display_metrics"]:
            metric_id = metric["metric_id"]
            values = [
                attempt["metrics"][metric_id]
                for attempt in valid_attempts
                if metric_id in attempt["metrics"]
            ]
            value = mean(values) if values else None
            base_value = self._node_primary_value(base, metric_id)
            champion_value = self._node_primary_value(champion, metric_id)
            summary.append(
                {
                    "metric_id": metric_id,
                    "label": metric["label"],
                    "value": value,
                    "delta_vs_research_base": (
                        _oriented_delta(value, base_value, metric["direction"])
                        if value is not None and base_value is not None
                        else None
                    ),
                    "delta_vs_champion": (
                        _oriented_delta(value, champion_value, metric["direction"])
                        if value is not None and champion_value is not None
                        else None
                    ),
                }
            )
        return summary

    def _reconcile_champion(
        self,
        graph: dict[str, Any],
        state: dict[str, Any],
        timestamp: str,
    ) -> list[dict[str, Any]]:
        primary = state["primary_metric"]
        role_state = graph["role_states"][graph["active_benchmark_id"]]
        current = self._research_node(graph, role_state["champion_id"])
        eligible = [
            node
            for node in graph["nodes"]
            if node["node_type"] == "RESEARCH"
            and node["benchmark_id"] == graph["active_benchmark_id"]
            and node["run_outcome"] in {"COMPLETED", "NORMAL_EARLY_STOP"}
            and self._node_primary_value(node, primary["metric_id"]) is not None
        ]
        if not eligible:
            return []
        reverse = primary["direction"] == "MAXIMIZE"
        best = sorted(
            eligible,
            key=lambda candidate: (
                self._node_primary_value(candidate, primary["metric_id"]),
                candidate["node_id"],
            ),
            reverse=reverse,
        )[0]
        current_value = self._node_primary_value(current, primary["metric_id"])
        best_value = self._node_primary_value(best, primary["metric_id"])
        current_is_eligible = current in eligible
        if (
            current_is_eligible
            and current_value is not None
            and best_value is not None
            and not _metric_is_better(
                best_value, current_value, primary["direction"]
            )
        ):
            return []
        if best["node_id"] == current["node_id"]:
            return []
        old_id = current["node_id"]
        role_state["champion_id"] = best["node_id"]
        benchmark_ref = self._benchmark(
            graph, graph["active_benchmark_id"]
        )["benchmark_ref"]
        event = {
            "benchmark_id": graph["active_benchmark_id"],
            "created_at": timestamp,
            "event_type": "REPLACED",
            "role": "CHAMPION",
            "node_id": best["node_id"],
            "previous_node_id": old_id,
            "reason": "Reconciled the best valid primary metric after result writeback",
            "evidence_ref": best["refs"]["experiment_card"] or benchmark_ref,
        }
        graph["role_events"].append(event)
        return [event]

    def _promotion_gate(
        self,
        graph: dict[str, Any],
        state: dict[str, Any],
        node: dict[str, Any],
    ) -> dict[str, Any]:
        if node["classification"] is None:
            return self._gate("NOT_APPLICABLE", "Baseline roots are not promotion candidates")
        if node["run_outcome"] not in {"COMPLETED", "NORMAL_EARLY_STOP"}:
            return self._gate(
                "INELIGIBLE",
                "Promotion requires COMPLETED or NORMAL_EARLY_STOP",
            )
        if node["hypothesis_verdict"] != "SUPPORTED":
            return self._gate("INELIGIBLE", "Promotion requires a supported hypothesis")
        experiment = state["experiments"].get(node["experiment_id"])
        if experiment is None:
            return self._gate("INELIGIBLE", "Promotion evidence is missing")
        valid_attempts = [
            attempt
            for attempt in experiment["attempts"]
            if attempt["run_kind"] != "SMOKE"
            and attempt["run_outcome"] in {"COMPLETED", "NORMAL_EARLY_STOP"}
            and attempt["hard_constraints_passed"]
        ]
        if not valid_attempts:
            return self._gate("INELIGIBLE", "No full comparable attempt passed hard constraints")

        primary = state["primary_metric"]
        metric_id = primary["metric_id"]
        role_state = graph["role_states"][graph["active_benchmark_id"]]
        base = self._research_node(graph, node["research_base_id"])
        base_value = self._node_primary_value(base, metric_id)
        node_value = self._node_primary_value(node, metric_id)
        if base_value is None or node_value is None:
            return self._gate("INELIGIBLE", "Primary metric comparison is unavailable")

        classification = node["classification"]
        if classification["change_operator"] == "DELETE":
            if classification["intervention_locus"] != "BRANCH":
                return self._gate(
                    "INELIGIBLE",
                    "Only branch deletion may consume simplification tolerance",
                )
            anchor_id = role_state["simplification_anchor_id"]
            anchor = self._research_node(graph, anchor_id)
            anchor_value = self._node_primary_value(anchor, metric_id)
            if anchor_value is None:
                return self._gate("INELIGIBLE", "Simplification Anchor metric is unavailable")
            cumulative_delta = _oriented_delta(
                node_value, anchor_value, primary["direction"]
            )
            if cumulative_delta < -primary["simplification_tolerance"]:
                return self._gate(
                    "INELIGIBLE",
                    "Cumulative simplification loss exceeds the frozen tolerance",
                )
            return self._gate(
                "ELIGIBLE",
                "Branch deletion stays within cumulative simplification tolerance",
            )

        policy = state["promotion_confirmation_policy"]
        policy_mode = policy["mode"]
        if policy_mode == "SINGLE_RUN_JUSTIFIED":
            first_attempt = valid_attempts[0]
            threshold = policy["single_run_threshold"]
            resource_value = (
                first_attempt["duration_seconds"]
                if threshold["resource"] == "DURATION_SECONDS"
                else first_attempt["cost"]
            )
            if resource_value is None:
                return self._gate(
                    "INELIGIBLE",
                    "Single-run qualification evidence is missing",
                )
            if resource_value <= threshold["value"]:
                return self._gate(
                    "INELIGIBLE",
                    "Single run does not exceed the frozen qualification threshold",
                )
            improvement = _oriented_delta(
                node_value, base_value, primary["direction"]
            )
            if improvement <= primary["promotion_threshold"]:
                return self._gate(
                    "INELIGIBLE",
                    "Primary improvement does not exceed the frozen threshold",
                )
            return self._gate(
                "ELIGIBLE",
                "Justified single run passed provisionally",
            )

        required_attempts = 3 if policy_mode == "TWO_SEEDS" else 2
        additional_seeds = required_attempts - 1
        confirmation_attempts: list[dict[str, Any]] = []
        distinct_seeds: set[int] = set()
        for attempt in valid_attempts:
            if attempt["seed"] in distinct_seeds:
                continue
            distinct_seeds.add(attempt["seed"])
            confirmation_attempts.append(attempt)
        if len(confirmation_attempts) < required_attempts:
            return self._gate(
                "NEEDS_SEEDS",
                f"{policy_mode} requires {additional_seeds} additional full seed"
                + ("s" if additional_seeds != 1 else ""),
                ["START_RUN_PROMOTION_CONFIRMATION"],
            )
        base_seed_metrics = self._seed_metrics_for_node(graph, state, base["node_id"])
        candidate_seed_values: list[float] = []
        base_seed_values: list[float] = []
        for attempt in confirmation_attempts:
            seed = str(attempt["seed"])
            if seed not in base_seed_metrics:
                return self._gate(
                    "MISSING_BASELINE_SEEDS",
                    f"Research Base has no corresponding result for seed {seed}",
                    ["REGISTER_BASELINE_SEED_EVIDENCE"],
                )
            candidate_value = attempt["metrics"].get(metric_id)
            if candidate_value is None:
                return self._gate("INELIGIBLE", f"Attempt {attempt['attempt_id']} lacks primary metric")
            base_seed_value = base_seed_metrics[seed]
            if not _metric_is_better(
                candidate_value, base_seed_value, primary["direction"]
            ):
                return self._gate(
                    "INELIGIBLE",
                    f"Seed {seed} does not beat the corresponding Research Base seed",
                )
            candidate_seed_values.append(candidate_value)
            base_seed_values.append(base_seed_value)
        mean_improvement = _oriented_delta(
            mean(candidate_seed_values), mean(base_seed_values), primary["direction"]
        )
        if mean_improvement <= primary["promotion_threshold"]:
            return self._gate(
                "INELIGIBLE",
                "Mean multi-seed improvement does not exceed the frozen threshold",
            )
        return self._gate(
            "ELIGIBLE",
            f"{policy_mode} passed multi-seed confirmation",
        )

    def _current_research_base_provisional(
        self, graph: dict[str, Any]
    ) -> bool:
        benchmark_id = graph["active_benchmark_id"]
        research_base_id = graph["role_states"][benchmark_id]["research_base_id"]
        for event in reversed(graph["role_events"]):
            if (
                event["benchmark_id"] == benchmark_id
                and event["role"] == "RESEARCH_BASE"
                and event["node_id"] == research_base_id
                and event["event_type"] in {"ASSIGNED", "REPLACED"}
            ):
                return event.get("single_seed_provisional") is True
        return False

    def _gate(
        self,
        status: str,
        reason: str,
        allowed_next_actions: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "status": status,
            "reason": reason,
            "allowed_next_actions": _normalize_allowed_next_actions(
                allowed_next_actions or []
            ),
        }

    def _seed_metrics_for_node(
        self, graph: dict[str, Any], state: dict[str, Any], node_id: str
    ) -> dict[str, float]:
        seed_metrics = dict(state["node_seed_metrics"].get(node_id, {}))
        node = self._research_node(graph, node_id)
        if node["experiment_id"] in state["experiments"]:
            metric_id = state["primary_metric"]["metric_id"]
            for attempt in state["experiments"][node["experiment_id"]]["attempts"]:
                if (
                    attempt["run_outcome"] in {"COMPLETED", "NORMAL_EARLY_STOP"}
                    and attempt["hard_constraints_passed"]
                    and metric_id in attempt["metrics"]
                ):
                    seed_metrics[str(attempt["seed"])] = attempt["metrics"][metric_id]
        return seed_metrics

    def _new_experiment_limit_reached(self, state: dict[str, Any]) -> bool:
        limits = state["budget"]["limits"]
        consumed = state["budget"]["consumed"]
        return (
            limits["max_experiments"] is not None
            and consumed["experiments_started"] >= limits["max_experiments"]
        )

    def _time_or_cost_exhausted(self, state: dict[str, Any]) -> bool:
        limits = state["budget"]["limits"]
        consumed = state["budget"]["consumed"]
        return any(
            limits[limit] is not None and consumed[used] >= limits[limit]
            for limit, used in (
                ("max_run_seconds", "run_seconds"),
                ("max_cost", "cost"),
            )
        )

    def _terminal_budget_exhausted(
        self,
        state: dict[str, Any],
        *,
        run_kind: str,
        run_outcome: str,
        promotion_gate: dict[str, Any],
    ) -> bool:
        if self._time_or_cost_exhausted(state):
            return True
        experiment_complete = (
            run_kind != "SMOKE" and run_outcome != "TECHNICAL_FAILURE"
        )
        if promotion_gate["status"] in {"NEEDS_SEEDS", "MISSING_BASELINE_SEEDS"}:
            experiment_complete = False
        return experiment_complete and self._new_experiment_limit_reached(state)

    def _validate_planned_budget(
        self,
        state: dict[str, Any],
        *,
        planned_max_seconds: float,
        planned_max_cost: float,
    ) -> None:
        limits = state["budget"]["limits"]
        consumed = state["budget"]["consumed"]
        if planned_max_cost > 0 and limits["cost_unit"] is None:
            raise RuntimeErrorResponse(
                "INVALID_BUDGET",
                "planned_max_cost requires a cost unit frozen in the Research Brief",
            )
        if limits["max_run_seconds"] is not None:
            remaining_seconds = limits["max_run_seconds"] - consumed["run_seconds"]
            if planned_max_seconds > remaining_seconds:
                raise RuntimeErrorResponse(
                    "INSUFFICIENT_TIME_BUDGET",
                    f"Planned run needs {planned_max_seconds}s but only {remaining_seconds}s remain",
                    allowed_next_actions=["REDUCE_PLANNED_RUN_WITHIN_BENCHMARK", "FINALIZE_RESEARCH"],
                )
        if limits["max_cost"] is not None:
            remaining_cost = limits["max_cost"] - consumed["cost"]
            if planned_max_cost > remaining_cost:
                raise RuntimeErrorResponse(
                    "INSUFFICIENT_COST_BUDGET",
                    f"Planned run needs {planned_max_cost} cost units but only {remaining_cost} remain",
                    allowed_next_actions=["CHOOSE_LOWER_COST_CANDIDATE", "FINALIZE_RESEARCH"],
                )

    def _budget_summary(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "limits": copy.deepcopy(state["budget"]["limits"]),
            "consumed": copy.deepcopy(state["budget"]["consumed"]),
            "new_experiment_limit_reached": self._new_experiment_limit_reached(state),
            "time_or_cost_exhausted": self._time_or_cost_exhausted(state),
            "terminal": state["controller_status"] == "TARGET_NOT_REACHED",
        }

    def _allowed_actions(
        self, graph: dict[str, Any], state: dict[str, Any]
    ) -> list[str]:
        if state["controller_status"] in TERMINAL_STATUSES:
            return []
        if state["controller_status"] == "HUMAN_REVIEW_REQUIRED":
            return ["inspect", "validate"]
        if state["active_run"] is not None:
            return ["inspect"]
        actions = ["inspect", "validate"]
        if not graph["active_frontier"]:
            actions.extend(["CREATE_LITERATURE", "CREATE_CANDIDATE"])
        return actions

    def _finish_allowed_actions(
        self,
        state: dict[str, Any],
        outcome: str,
        promotion_gate: dict[str, Any],
        run_kind: str,
    ) -> list[str]:
        if state["controller_status"] in TERMINAL_STATUSES:
            return []
        if outcome == "TECHNICAL_FAILURE":
            return ["inspect"]
        if run_kind == "SMOKE":
            return ["inspect"]
        if promotion_gate["status"] == "NEEDS_SEEDS":
            return ["inspect"]
        if promotion_gate["status"] == "ELIGIBLE":
            return [
                "PROMOTE_RESEARCH_BASE",
                "ASSIGN_REFERENCE_BASELINE",
                "inspect",
            ]
        return [
            "SET_FRONTIER",
            "CREATE_LITERATURE",
            "CREATE_CANDIDATE",
            "inspect",
        ]

    def _assert_frontier_eligible(
        self, graph: dict[str, Any], node: dict[str, Any]
    ) -> None:
        current_base = graph["role_states"][graph["active_benchmark_id"]][
            "research_base_id"
        ]
        violations = []
        if node["benchmark_id"] != graph["active_benchmark_id"]:
            violations.append("candidate uses a non-active Benchmark")
        if node["research_base_id"] != current_base:
            violations.append("candidate is stale relative to current Research Base")
        if node["branch_status"] != "OPEN":
            violations.append("branch_status is not OPEN")
        if node["run_outcome"] != "NOT_RUN":
            violations.append("run_outcome is not NOT_RUN")
        if node["hypothesis_verdict"] != "UNTESTED":
            violations.append("hypothesis_verdict is not UNTESTED")
        if node["candidate_priority"] == "HOLD":
            violations.append("candidate priority is HOLD")
        for field in (
            "hypothesis",
            "mechanism",
            "single_main_change",
            "falsification_condition",
            "classification",
        ):
            if node[field] is None:
                violations.append(f"{field} is missing")
        if violations:
            raise RuntimeErrorResponse(
                "FRONTIER_GATE_FAILED",
                *[f"{node['node_id']}: {item}" for item in violations],
                allowed_next_actions=["HOLD_NODE", "CORRECT_CANDIDATE"],
            )

    def _validate_all(
        self,
        graph: dict[str, Any],
        state: dict[str, Any],
        *,
        check_contract_hashes: bool = True,
        check_artifacts: bool = True,
    ) -> list[str]:
        violations: list[str] = []
        if graph.get("schema_version") != SCHEMA_VERSION:
            violations.append("Graph schema_version is unsupported")
        if state.get("schema_version") != SCHEMA_VERSION:
            violations.append("Runtime state schema_version is unsupported")
        if graph.get("project_id") != state.get("project_id"):
            violations.append("Graph and runtime project_id differ")
        if graph.get("revision") != state.get("revision"):
            violations.append("Graph and runtime revision differ")
        if state.get("controller_status") not in CONTROLLER_STATUSES:
            violations.append("Unknown controller_status")
        if state.get("current_phase") not in RUNTIME_PHASES:
            violations.append("Unknown current_phase")
        if state.get("last_trigger") not in RUNTIME_TRIGGERS:
            violations.append("Unknown last_trigger")
        audit_counters = state.get("audit_counters")
        if not isinstance(audit_counters, dict) or any(
            isinstance(audit_counters.get(name), bool)
            or not isinstance(audit_counters.get(name), int)
            or audit_counters[name] < 0
            for name in ("stage_reflections", "subagent_calls")
        ):
            violations.append("audit_counters must contain non-negative integers")
        budget_limits = state.get("budget", {}).get("limits", {})
        if (
            budget_limits.get("max_cost") is not None
            and not budget_limits.get("cost_unit")
        ):
            violations.append("Cost budget requires a frozen cost_unit")
        promotion_policy = state.get("promotion_confirmation_policy")
        if not isinstance(promotion_policy, dict):
            violations.append("promotion_confirmation_policy is missing")
        elif promotion_policy.get("mode") not in PROMOTION_CONFIRMATION_POLICIES:
            violations.append("Unknown promotion_confirmation_policy mode")
        elif promotion_policy["mode"] == "SINGLE_RUN_JUSTIFIED":
            threshold = promotion_policy.get("single_run_threshold")
            if (
                not isinstance(threshold, dict)
                or threshold.get("resource") not in {"DURATION_SECONDS", "COST"}
                or not isinstance(threshold.get("value"), (int, float))
                or isinstance(threshold.get("value"), bool)
                or threshold["value"] <= 0
                or not promotion_policy.get("single_run_justification")
            ):
                violations.append(
                    "SINGLE_RUN_JUSTIFIED requires a positive threshold and written justification"
                )
        elif (
            promotion_policy.get("single_run_threshold") is not None
            or promotion_policy.get("single_run_justification") is not None
        ):
            violations.append(
                "Multi-seed promotion policy cannot carry single-run fields"
            )
        node_index: dict[str, dict[str, Any]] = {}
        for node in graph.get("nodes", []):
            node_id = node.get("node_id")
            if node_id in node_index:
                violations.append(f"Duplicate node ID: {node_id}")
                continue
            node_index[node_id] = node
            if node.get("node_type") == "RESEARCH":
                missing = RESEARCH_NODE_KEYS - set(node)
                extra = set(node) - RESEARCH_NODE_KEYS
                if missing or extra:
                    violations.append(
                        f"{node_id} Research Node keys differ; missing={sorted(missing)}, extra={sorted(extra)}"
                    )
                if not _RN_RE.fullmatch(str(node_id)):
                    violations.append(f"Invalid Research Node ID: {node_id}")
                if node.get("branch_status") not in BRANCH_STATUSES:
                    violations.append(f"{node_id} has invalid branch_status")
                if node.get("run_outcome") not in RUN_OUTCOMES:
                    violations.append(f"{node_id} has invalid run_outcome")
                if node.get("hypothesis_verdict") not in HYPOTHESIS_VERDICTS:
                    violations.append(f"{node_id} has invalid hypothesis_verdict")
                if node.get("branch_status") == "OPEN" and (
                    node.get("branch_reason") is not None
                    or node.get("release_condition") is not None
                ):
                    violations.append(f"{node_id} OPEN cannot have hold/close metadata")
                if node.get("branch_status") == "HOLD" and (
                    not node.get("branch_reason") or not node.get("release_condition")
                ):
                    violations.append(f"{node_id} HOLD requires reason and release condition")
                if node.get("branch_status") == "CLOSED" and (
                    not node.get("branch_reason")
                    or node.get("release_condition") is not None
                ):
                    violations.append(f"{node_id} CLOSED requires only a reason")
            elif node.get("node_type") == "LITERATURE":
                missing = LITERATURE_NODE_KEYS - set(node)
                extra = set(node) - LITERATURE_NODE_KEYS
                if missing or extra:
                    violations.append(
                        f"{node_id} Literature Node keys differ; missing={sorted(missing)}, extra={sorted(extra)}"
                    )
                if not _LN_RE.fullmatch(str(node_id)):
                    violations.append(f"Invalid Literature Node ID: {node_id}")
            else:
                violations.append(f"Unknown node_type for {node_id}")

        edge_keys: set[tuple[str, str, str]] = set()
        incoming_primary: dict[str, int] = {}
        adjacency: dict[str, list[str]] = {}
        for edge in graph.get("edges", []):
            source = edge.get("from_node_id")
            target = edge.get("to_node_id")
            edge_type = edge.get("edge_type")
            key = (source, target, edge_type)
            if key in edge_keys:
                violations.append(f"Duplicate edge: {key}")
            edge_keys.add(key)
            if source not in node_index or target not in node_index:
                violations.append(f"Edge references unknown node: {key}")
                continue
            if edge_type not in EDGE_TYPES:
                violations.append(f"Invalid edge type: {edge_type}")
                continue
            adjacency.setdefault(source, []).append(target)
            if edge_type == "PRIMARY_PARENT":
                incoming_primary[target] = incoming_primary.get(target, 0) + 1
                if (
                    node_index[source]["node_type"] != "RESEARCH"
                    or node_index[target]["node_type"] != "RESEARCH"
                ):
                    violations.append("PRIMARY_PARENT must connect Research Nodes")
            if edge_type == "DIRECTION" and (
                node_index[source]["node_type"] != "LITERATURE"
                or node_index[target]["node_type"] != "RESEARCH"
            ):
                violations.append("DIRECTION must connect Literature to Research")
        for node_id, node in node_index.items():
            if node["node_type"] == "RESEARCH" and node["hypothesis"] is not None:
                if incoming_primary.get(node_id, 0) != 1:
                    violations.append(
                        f"{node_id} must have exactly one PRIMARY_PARENT"
                    )
        if self._has_cycle(adjacency):
            violations.append("Experiment Graph contains a cycle")

        benchmark_ids = {
            benchmark["benchmark_id"] for benchmark in graph.get("benchmarks", [])
        }
        active_benchmark = graph.get("active_benchmark_id")
        if active_benchmark not in benchmark_ids:
            violations.append("active_benchmark_id is not registered")
        role_state = graph.get("role_states", {}).get(active_benchmark, {})
        for field in (
            "anchor_baseline_id",
            "research_base_id",
            "champion_id",
            "simplification_anchor_id",
        ):
            if role_state.get(field) not in node_index:
                violations.append(f"Role state {field} references an unknown node")
        references = role_state.get("reference_baseline_ids", [])
        if len(references) != len(set(references)):
            violations.append("Reference Baseline IDs repeat")
        for node_id in references:
            if node_id not in node_index:
                violations.append(f"Unknown Reference Baseline: {node_id}")

        frontier = graph.get("active_frontier", [])
        if len(frontier) > 3 or len(frontier) != len(set(frontier)):
            violations.append("Active Frontier must contain at most three distinct IDs")
        for node_id in frontier:
            if node_id not in node_index:
                violations.append(f"Frontier references unknown node: {node_id}")
                continue
            try:
                self._assert_frontier_eligible(graph, node_index[node_id])
            except RuntimeErrorResponse as error:
                violations.extend(error.violations)

        experiments = state.get("experiments", {})
        for experiment_id, experiment in experiments.items():
            if not _EXPERIMENT_RE.fullmatch(experiment_id):
                violations.append(f"Invalid Experiment ID: {experiment_id}")
            if experiment.get("node_id") not in node_index:
                violations.append(f"{experiment_id} references unknown node")
            elif node_index[experiment["node_id"]].get("experiment_id") != experiment_id:
                violations.append(f"{experiment_id} and Graph node disagree")
            else:
                node = node_index[experiment["node_id"]]
                expected_preregistration = {
                    "hypothesis": node["hypothesis"],
                    "single_main_change": node["single_main_change"],
                    "falsification_condition": node["falsification_condition"],
                    "classification": node["classification"],
                }
                if experiment.get("preregistration") != expected_preregistration:
                    violations.append(
                        f"{experiment_id} preregistration differs from its Research Node"
                    )
            attempt_ids = [item.get("attempt_id") for item in experiment.get("attempts", [])]
            if len(attempt_ids) != len(set(attempt_ids)):
                violations.append(f"{experiment_id} has duplicate attempt IDs")
            for attempt_id in attempt_ids:
                if not _ATTEMPT_RE.fullmatch(str(attempt_id)):
                    violations.append(f"Invalid Attempt ID: {attempt_id}")
            for attempt in experiment.get("attempts", []):
                if (
                    attempt.get("planned_max_cost", 0) > 0
                    and not attempt.get("cost_unit")
                ):
                    violations.append(
                        f"{experiment_id}/{attempt.get('attempt_id')} cost has no frozen unit"
                    )
        active_run = state.get("active_run")
        if active_run is not None:
            experiment = experiments.get(active_run.get("experiment_id"))
            if experiment is None:
                violations.append("active_run references unknown experiment")
            elif not any(
                attempt["attempt_id"] == active_run.get("attempt_id")
                and attempt["status"] == "RUNNING"
                for attempt in experiment["attempts"]
            ):
                violations.append("active_run does not match a RUNNING attempt")
        running_attempts = [
            (experiment_id, attempt["attempt_id"])
            for experiment_id, experiment in experiments.items()
            for attempt in experiment["attempts"]
            if attempt["status"] == "RUNNING"
        ]
        if len(running_attempts) > 1:
            violations.append("More than one attempt is RUNNING")
        if bool(running_attempts) != (active_run is not None):
            violations.append("active_run and attempt statuses disagree")

        if check_contract_hashes:
            contract = state.get("contract_hashes", {})
            for label in ("research_brief", "benchmark"):
                relative = contract.get(f"{label}_ref")
                expected = contract.get(f"{label}_sha256")
                if not relative or not (self.root / relative).is_file():
                    violations.append(f"Frozen {label} artifact is missing")
                elif sha256_file(self.root / relative) != expected:
                    violations.append(f"Frozen {label} hash changed")
        if check_artifacts:
            violations.extend(
                self._artifact_consistency_violations(graph, state)
            )
        return violations

    def _artifact_consistency_violations(
        self, graph: dict[str, Any], state: dict[str, Any]
    ) -> list[str]:
        violations: list[str] = []

        def check_ref(
            relative: str | None,
            label: str,
            *,
            directory: bool = False,
            any_type: bool = False,
        ) -> Path | None:
            if relative is None:
                return None
            try:
                path = resolve_project_path(
                    self.root,
                    relative,
                    must_exist=True,
                    allow_directory=directory or any_type,
                )
            except ValueError as error:
                violations.append(f"{label}: {error}")
                return None
            if directory and not path.is_dir():
                violations.append(f"{label} is not a directory: {relative}")
                return None
            if not directory and not any_type and not path.is_file():
                violations.append(f"{label} is not a file: {relative}")
                return None
            return path

        for node in graph["nodes"]:
            if node["node_type"] == "RESEARCH":
                refs = node["refs"]
                check_ref(refs["experiment_card"], f"{node['node_id']} experiment_card")
                check_ref(refs["research_log"], f"{node['node_id']} research_log")
                check_ref(
                    refs["run_directory"],
                    f"{node['node_id']} run_directory",
                    directory=True,
                )
                for index, relative in enumerate(refs["paper_mechanism_cards"]):
                    check_ref(
                        relative,
                        f"{node['node_id']} paper_mechanism_cards[{index}]",
                    )
                check_ref(
                    refs["interaction_review_pack"],
                    f"{node['node_id']} interaction_review_pack",
                )
            else:
                check_ref(
                    node["literature_survey_ref"],
                    f"{node['node_id']} literature_survey_ref",
                )
                for index, paper in enumerate(node["selected_papers"]):
                    pdf_path = check_ref(
                        paper["pdf_ref"],
                        f"{node['node_id']} selected_papers[{index}].pdf_ref",
                    )
                    if pdf_path is not None and pdf_path.read_bytes()[:5] != b"%PDF-":
                        violations.append(
                            f"{node['node_id']} selected_papers[{index}] is not a valid PDF"
                        )
                    check_ref(
                        paper["mechanism_card_ref"],
                        f"{node['node_id']} selected_papers[{index}].mechanism_card_ref",
                    )
        for index, edge in enumerate(graph["edges"]):
            check_ref(edge["evidence_ref"], f"edges[{index}].evidence_ref")
        for index, event in enumerate(graph["role_events"]):
            check_ref(event["evidence_ref"], f"role_events[{index}].evidence_ref")
        for index, summary in enumerate(graph["stage_summaries"]):
            check_ref(summary["summary_ref"], f"stage_summaries[{index}].summary_ref")

        for experiment_id, experiment in state["experiments"].items():
            card_path = check_ref(
                experiment["card_ref"], f"{experiment_id} Experiment Card"
            )
            check_ref(
                experiment["run_directory_ref"],
                f"{experiment_id} run directory",
                directory=True,
            )
            expected_status = (
                "RUNNING"
                if any(
                    attempt["status"] == "RUNNING"
                    for attempt in experiment["attempts"]
                )
                else "FINISHED"
            )
            if card_path is not None:
                card_text = card_path.read_text(encoding="utf-8")
                try:
                    runtime_record, _ = _experiment_card_sections(card_text)
                except ValueError as error:
                    violations.append(f"{experiment_id} Experiment Card: {error}")
                    runtime_record = ""
                if runtime_record:
                    expected_hash = experiment.get("runtime_record_sha256")
                    actual_hash = sha256_text(runtime_record)
                    if not expected_hash:
                        violations.append(
                            f"{experiment_id} Experiment Card is missing Runtime Record hash"
                        )
                    elif actual_hash != expected_hash:
                        violations.append(
                            f"{experiment_id} Experiment Card Runtime Record hash changed"
                        )
                    required_card_facts = (
                        f"experiment_id: {experiment_id}",
                        f"research_node_id: {experiment['node_id']}",
                        f"status: {expected_status}",
                    )
                    for fact in required_card_facts:
                        if fact not in runtime_record:
                            violations.append(
                                f"{experiment_id} Experiment Card is missing canonical fact: {fact}"
                            )

            for attempt in experiment["attempts"]:
                attempt_id = attempt["attempt_id"]
                check_ref(
                    attempt["config_ref"],
                    f"{experiment_id}/{attempt_id} config_ref",
                )
                artifact_refs = attempt.get("artifact_refs", {})
                if attempt["run_kind"] in _FORMAL_RUN_KINDS:
                    missing = set(_FORMAL_ARTIFACT_KEYS) - set(artifact_refs)
                    if missing:
                        violations.append(
                            f"{experiment_id}/{attempt_id} missing formal artifact refs: "
                            + ", ".join(sorted(missing))
                        )
                log_path = check_ref(
                    attempt["run_log_ref"],
                    f"{experiment_id}/{attempt_id} Run Event Log",
                )
                if log_path is not None:
                    events = []
                    for line_number, line in enumerate(
                        log_path.read_text(encoding="utf-8").splitlines(),
                        start=1,
                    ):
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError as error:
                            violations.append(
                                f"{experiment_id}/{attempt_id} JSONL line {line_number}: {error}"
                            )
                            continue
                        if not isinstance(event, dict):
                            violations.append(
                                f"{experiment_id}/{attempt_id} JSONL line {line_number} is not an object"
                            )
                            continue
                        if (
                            event.get("experiment_id") != experiment_id
                            or event.get("attempt_id") != attempt_id
                        ):
                            violations.append(
                                f"{experiment_id}/{attempt_id} JSONL line {line_number} has mismatched IDs"
                            )
                        events.append(event)
                    if not events or events[0].get("event") != "ATTEMPT_STARTED":
                        violations.append(
                            f"{experiment_id}/{attempt_id} must begin with ATTEMPT_STARTED"
                        )
                    if (
                        attempt["status"] == "FINISHED"
                        and (not events or events[-1].get("event") != "ATTEMPT_FINISHED")
                    ):
                        violations.append(
                            f"{experiment_id}/{attempt_id} must end with ATTEMPT_FINISHED"
                        )
                if attempt["status"] == "FINISHED" and attempt["run_outcome"] in {
                    "COMPLETED",
                    "NORMAL_EARLY_STOP",
                }:
                    formal_paths: dict[str, Path] = {}
                    if attempt["run_kind"] in _FORMAL_RUN_KINDS:
                        for key in _FORMAL_ARTIFACT_KEYS:
                            if key not in artifact_refs:
                                continue
                            path = check_ref(
                                artifact_refs[key],
                                f"{experiment_id}/{attempt_id} artifact_refs.{key}",
                            )
                            if path is not None:
                                formal_paths[key] = path
                                expected_hash = attempt.get("artifact_sha256", {}).get(
                                    key
                                )
                                if not expected_hash:
                                    violations.append(
                                        f"{experiment_id}/{attempt_id} missing artifact hash for {key}"
                                    )
                                elif sha256_file(path) != expected_hash:
                                    violations.append(
                                        f"{experiment_id}/{attempt_id} {key} hash changed"
                                    )
                        metrics_path = formal_paths.get("metrics_json")
                        if metrics_path is not None:
                            try:
                                payload = self._read_json_artifact(
                                    metrics_path,
                                    f"{experiment_id}/{attempt_id} metrics_json",
                                )
                                artifact_metrics = self._validate_result_metrics(
                                    self._extract_artifact_metrics(payload, graph),
                                    graph,
                                    "COMPLETED",
                                )
                                if artifact_metrics != attempt["metrics"]:
                                    violations.append(
                                        f"{experiment_id}/{attempt_id} stored metrics differ from metrics_json"
                                    )
                            except RuntimeErrorResponse as error:
                                violations.extend(
                                    f"{experiment_id}/{attempt_id}: {item}"
                                    for item in error.violations
                                )
                    for index, relative in enumerate(attempt["expected_artifacts"]):
                        check_ref(
                            relative,
                            f"{experiment_id}/{attempt_id} expected_artifacts[{index}]",
                            any_type=True,
                        )
                check_ref(
                    attempt["checkpoint_ref"],
                    f"{experiment_id}/{attempt_id} checkpoint_ref",
                )
        for node_id, seed_refs in state["node_seed_evidence"].items():
            for seed, relative in seed_refs.items():
                check_ref(
                    relative,
                    f"node_seed_evidence[{node_id}][{seed}]",
                )
        return violations

    def _json_schema_violations(
        self, graph: dict[str, Any], state: dict[str, Any]
    ) -> list[str]:
        try:
            import jsonschema
        except ImportError:
            return []
        violations = []
        for name, instance in (
            ("experiment_graph.schema.json", graph),
            ("runtime_state.schema.json", state),
        ):
            schema_file = schema_root() / name
            if not schema_file.exists():
                violations.append(f"Missing runtime schema: {name}")
                continue
            schema = read_json(schema_file)
            validator = jsonschema.Draft202012Validator(schema)
            for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
                path = ".".join(str(part) for part in error.path) or "<root>"
                violations.append(f"{name}:{path}: {error.message}")
        return violations

    def _has_cycle(self, adjacency: dict[str, list[str]]) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> bool:
            if node_id in visiting:
                return True
            if node_id in visited:
                return False
            visiting.add(node_id)
            for child in adjacency.get(node_id, []):
                if visit(child):
                    return True
            visiting.remove(node_id)
            visited.add(node_id)
            return False

        return any(visit(node_id) for node_id in list(adjacency))

    def _render_experiment_card(
        self, graph: dict[str, Any], state: dict[str, Any], experiment_id: str
    ) -> str:
        experiment = state["experiments"][experiment_id]
        node = self._research_node(graph, experiment["node_id"])
        card_path = self.root / experiment["card_ref"]
        if card_path.is_file():
            _, research_notes = _experiment_card_sections(
                card_path.read_text(encoding="utf-8")
            )
        else:
            research_notes = (
                "\n<!-- Append-only: add dated research rationale, engineering notes, "
                "interpretation, and decisions below. -->\n"
            )
        active_attempts = [
            attempt for attempt in experiment["attempts"] if attempt["status"] == "RUNNING"
        ]
        status = "RUNNING" if active_attempts else (
            "FINISHED" if experiment["attempts"] else "PLANNED"
        )
        attempts = []
        attempt_details = []
        for attempt in experiment["attempts"]:
            metrics = ", ".join(
                f"{key}={value}" for key, value in attempt["metrics"].items()
            ) or "—"
            cost_unit = attempt["cost_unit"] or "UNMETERED"
            actual_budget = (
                f"{attempt['duration_seconds']}s / {attempt['cost']} {cost_unit}"
                if attempt["duration_seconds"] is not None
                else "—"
            )
            attempts.append(
                f"| {attempt['attempt_id']} | {attempt['run_kind']} | {attempt['seed']} | "
                f"{attempt['status']} | {attempt['started_at']} | "
                f"{attempt['finished_at'] or '—'} | {attempt['run_outcome'] or '—'} | "
                f"{metrics} | ≤{attempt['planned_max_seconds']}s / "
                f"≤{attempt['planned_max_cost']} {cost_unit}; actual {actual_budget} |"
            )
            attempt_details.append(
                f"- `{attempt['attempt_id']}`: "
                + json.dumps(
                    {
                        "command": attempt["command"],
                        "config_ref": attempt["config_ref"],
                        "code_version": attempt["code_version"],
                        "data_version": attempt["data_version"],
                        "artifact_refs": attempt["artifact_refs"],
                        "artifact_sha256": attempt["artifact_sha256"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
        runtime_card = "\n".join(
            [
                f"# Experiment {experiment_id}",
                "",
                _RUNTIME_RECORD_HEADING,
                "",
                "### Identity",
                "",
                f"- experiment_id: {experiment_id}",
                f"- research_node_id: {node['node_id']}",
                f"- benchmark_id: {node['benchmark_id']}",
                f"- research_base_id: {node['research_base_id']}",
                f"- comparison_target_id: {node['comparison_target_id']}",
                f"- status: {status}",
                f"- created_at: {experiment['created_at']}",
                "",
                "### Frozen Preregistration",
                "",
                f"- hypothesis: {experiment['preregistration']['hypothesis']}",
                f"- single_main_change: {experiment['preregistration']['single_main_change']}",
                f"- falsification_condition: {experiment['preregistration']['falsification_condition']}",
                "",
                "- classification: "
                + json.dumps(
                    experiment["preregistration"]["classification"],
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                f"- mechanism: {node['mechanism'] or '—'}",
                "",
                "### Attempts",
                "",
                "| Attempt | Kind | Seed | Status | Started | Finished | Outcome | Metrics | Planned / actual budget |",
                "|---|---|---:|---|---|---|---|---|---|",
                *(
                    attempts
                    or ["| — | — | — | PLANNED | — | — | — | — | — |"]
                ),
                "",
                "### Attempt Runtime Details",
                "",
                *(attempt_details or ["- —"]),
                "",
                "### Result",
                "",
                f"- Run outcome: `{node['run_outcome']}`",
                f"- Hypothesis verdict: `{node['hypothesis_verdict']}`",
                f"- Metrics: {json.dumps(node['metric_summary'], ensure_ascii=False)}",
                "",
                _RESEARCH_NOTES_HEADING,
            ]
        )
        return runtime_card + "\n" + research_notes

    def _updated_research_log(
        self,
        relative_path: str,
        node: dict[str, Any],
        attempt: dict[str, Any],
    ) -> str:
        path = self.root / relative_path
        previous = (
            path.read_text(encoding="utf-8")
            if path.exists()
            else "# Research Experiment Log · Volume 001\n\n"
        )
        entry = "\n".join(
            [
                f"## {node['experiment_id']} · {node['title']}",
                "",
                f"- Hypothesis: {node['hypothesis']}",
                f"- Change: {node['single_main_change']}",
                f"- Result: `{attempt['run_outcome']}` / `{attempt['hypothesis_verdict']}`; "
                f"{json.dumps(attempt['metrics'], ensure_ascii=False)}",
                f"- Interpretation: {attempt.get('interpretation') or 'Technical evidence only'}",
                f"- Decision: {attempt.get('decision') or 'Recover the technical path'}",
                f"- Evidence: `{attempt['run_log_ref']}`",
                "",
            ]
        )
        return previous.rstrip() + "\n\n" + entry

    def _empty_metric_summary(
        self, graph: dict[str, Any], benchmark_id: str
    ) -> list[dict[str, Any]]:
        return [
            {
                "metric_id": metric["metric_id"],
                "label": metric["label"],
                "value": None,
                "delta_vs_research_base": None,
                "delta_vs_champion": None,
            }
            for metric in self._benchmark(graph, benchmark_id)["display_metrics"]
        ]

    def _node_primary_value(
        self, node: dict[str, Any], metric_id: str
    ) -> float | None:
        for metric in node["metric_summary"]:
            if metric["metric_id"] == metric_id:
                return metric["value"]
        return None

    def _node_index(self, graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {node["node_id"]: node for node in graph["nodes"]}

    def _research_node(
        self, graph: dict[str, Any], node_id: str
    ) -> dict[str, Any]:
        node = self._node_index(graph).get(node_id)
        if node is None:
            raise RuntimeErrorResponse("UNKNOWN_NODE", f"Unknown node: {node_id}")
        if node["node_type"] != "RESEARCH":
            raise RuntimeErrorResponse(
                "INVALID_NODE_TYPE", f"{node_id} is not a Research Node"
            )
        return node

    def _benchmark(
        self, graph: dict[str, Any], benchmark_id: str
    ) -> dict[str, Any]:
        for benchmark in graph["benchmarks"]:
            if benchmark["benchmark_id"] == benchmark_id:
                return benchmark
        raise RuntimeErrorResponse(
            "UNKNOWN_BENCHMARK", f"Unknown Benchmark: {benchmark_id}"
        )

    def _existing_ref(self, value: Any, name: str) -> str:
        text = _require_string(value, name, max_length=1000)
        path = resolve_project_path(
            self.root, text, must_exist=True, allow_directory=False
        )
        return relative_project_path(self.root, path)

    def _optional_existing_ref(self, value: Any, name: str) -> str | None:
        if value is None:
            return None
        return self._existing_ref(value, name)

    def _existing_pdf_ref(self, value: Any, name: str) -> str:
        relative = self._existing_ref(value, name)
        path = self.root / relative
        if path.suffix.lower() != ".pdf" or path.read_bytes()[:5] != b"%PDF-":
            raise RuntimeErrorResponse(
                "INVALID_PDF_ARTIFACT",
                f"{name} must reference a downloaded PDF file with a valid PDF header",
            )
        return relative

    def _future_ref(self, value: Any, name: str) -> str:
        text = _require_string(value, name, max_length=1000)
        path = resolve_project_path(self.root, text, must_exist=False)
        return relative_project_path(self.root, path)
