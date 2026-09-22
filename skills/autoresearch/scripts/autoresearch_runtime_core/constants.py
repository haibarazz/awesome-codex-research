"""Canonical machine values shared by the AutoResearch runtime."""

from __future__ import annotations

from pathlib import Path

GRAPH_FILENAME = "EXPERIMENT_GRAPH.json"
GRAPH_HTML_FILENAME = "EXPERIMENT_GRAPH.html"
RUNTIME_DIRECTORY = ".autoresearch"
RUNTIME_STATE_FILENAME = "runtime_state.json"
RUNTIME_LOCK_FILENAME = "runtime.lock"

SCHEMA_VERSION = "1.0"
RUNTIME_VERSION = "0.1.0"

TERMINAL_STATUSES = {"TARGET_REACHED", "TARGET_NOT_REACHED"}
CONTROLLER_STATUSES = TERMINAL_STATUSES | {"CONTINUE", "HUMAN_REVIEW_REQUIRED"}
RUNTIME_PHASES = {
    "BOOTSTRAP",
    "LITERATURE_RESEARCH",
    "CANDIDATE_DESIGN",
    "EXPERIMENT_EXECUTION",
    "RESULT_ROUTING",
    "STAGE_REFLECTION",
    "TERMINATION",
    "HUMAN_REVIEW",
}
RUNTIME_TRIGGERS = {
    "BOOTSTRAP_FROZEN",
    "LITERATURE_COMPLETED",
    "CANDIDATES_READY",
    "EXPERIMENT_STARTED",
    "EXPERIMENT_FINISHED",
    "STAGE_SUMMARY_COMPLETED",
    "RESEARCH_FINALIZED",
}

NODE_TYPES = {"RESEARCH", "LITERATURE"}
BRANCH_STATUSES = {"OPEN", "HOLD", "CLOSED"}
RUN_OUTCOMES = {
    "NOT_RUN",
    "COMPLETED",
    "NORMAL_EARLY_STOP",
    "STOP_LOSS",
    "TECHNICAL_FAILURE",
}
HYPOTHESIS_VERDICTS = {
    "UNTESTED",
    "SUPPORTED",
    "NOT_SUPPORTED",
    "INCONCLUSIVE",
    "NOT_EVALUABLE",
}

EVIDENCE_CLASSES = {"R", "A", "N"}
CHANGE_SCOPES = {"FULL_METHOD", "COMPONENT", "PROTOCOL"}
RESEARCH_LAYERS = {"L1", "L2", "L3", "L4"}
INTERVENTION_LOCI = {
    "SYSTEM",
    "DATA",
    "FEATURE",
    "BACKBONE",
    "COMPONENT",
    "BRANCH",
    "LOSS",
    "OPTIMIZATION",
    "INFERENCE",
}
CHANGE_OPERATORS = {"ADD", "REPLACE", "DELETE", "REWIRE", "MERGE", "SPLIT"}
CANDIDATE_PRIORITIES = {"GOLD", "SILVER", "HOLD"}
MATRIX_PRIORITIES = CANDIDATE_PRIORITIES | {"REJECT", "INVALID"}

EDGE_TYPES = {"PRIMARY_PARENT", "DIRECTION", "SOURCE", "MERGE"}
ROLE_NAMES = {
    "ANCHOR_BASELINE",
    "RESEARCH_BASE",
    "CHAMPION",
    "REFERENCE_BASELINE",
}
RUN_KINDS = {"FULL", "SMOKE", "PROMOTION_CONFIRMATION", "RETRY"}
PROMOTION_CONFIRMATION_POLICIES = {
    "TWO_SEEDS",
    "ONE_CONFIRM_SEED",
    "SINGLE_RUN_JUSTIFIED",
}

LITERATURE_OUTCOMES = {"DIRECTIONS_FOUND", "NO_DIRECTION"}
LITERATURE_TRIGGER_TYPES = {
    "BOOTSTRAP",
    "BOTTLENECK",
    "BRANCH_CLOSED",
    "FRONTIER_EMPTY",
    "BASE_PROMOTION",
    "STAGE_PIVOT",
    "INTERACTION_REVIEW",
    "NO_DIRECTION_RECOVERY",
}
STAGE_ROUTES = {"DEEPEN", "BROADEN", "REPAIR", "PIVOT", "CONCLUDE"}

PROPOSAL_ACTIONS = {
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
}

RESEARCH_NODE_KEYS = {
    "node_id",
    "node_type",
    "created_at",
    "title",
    "benchmark_id",
    "research_base_id",
    "comparison_target_id",
    "experiment_id",
    "hypothesis",
    "mechanism",
    "single_main_change",
    "falsification_condition",
    "branch_status",
    "branch_reason",
    "release_condition",
    "run_outcome",
    "hypothesis_verdict",
    "candidate_priority",
    "priority_reason",
    "classification",
    "metric_summary",
    "refs",
}

LITERATURE_NODE_KEYS = {
    "node_id",
    "node_type",
    "created_at",
    "title",
    "trigger",
    "research_question",
    "search_scope",
    "search_outcome",
    "outcome_reason",
    "direction_summary",
    "selected_papers",
    "literature_survey_ref",
}


def skill_root() -> Path:
    return Path(__file__).resolve().parents[2]


def schema_root() -> Path:
    return skill_root() / "assets" / "schemas"
