#!/usr/bin/env python3
"""Generate the exhaustive structural priority table for N candidates."""

from __future__ import annotations

import csv
from pathlib import Path


SCOPES = ("FULL_METHOD", "COMPONENT", "PROTOCOL")
LOCI = (
    "SYSTEM",
    "DATA",
    "FEATURE",
    "BACKBONE",
    "COMPONENT",
    "BRANCH",
    "LOSS",
    "OPTIMIZATION",
    "INFERENCE",
)
OPERATORS = ("ADD", "REPLACE", "DELETE", "REWIRE", "MERGE", "SPLIT")

COMPONENT_MATRIX = {
    "SYSTEM": ("INVALID",) * 6,
    "DATA": ("SILVER", "GOLD", "GOLD", "SILVER", "GOLD", "HOLD"),
    "FEATURE": ("SILVER", "GOLD", "GOLD", "GOLD", "GOLD", "SILVER"),
    "BACKBONE": ("HOLD", "GOLD", "GOLD", "GOLD", "GOLD", "HOLD"),
    "COMPONENT": ("SILVER", "GOLD", "GOLD", "GOLD", "GOLD", "SILVER"),
    "BRANCH": ("SILVER", "GOLD", "GOLD", "GOLD", "GOLD", "HOLD"),
    "LOSS": ("SILVER", "GOLD", "GOLD", "GOLD", "GOLD", "SILVER"),
    "OPTIMIZATION": ("SILVER", "SILVER", "SILVER", "SILVER", "SILVER", "HOLD"),
    "INFERENCE": ("SILVER", "GOLD", "GOLD", "GOLD", "GOLD", "SILVER"),
}

PROTOCOL_ALLOWED_LOCI = {"SYSTEM", "DATA", "OPTIMIZATION", "INFERENCE"}


def classify(scope: str, locus: str, operator: str) -> tuple[str, str, str, str]:
    """Return combination status, priority, rule ids, and rationale."""
    if scope == "COMPONENT":
        priority = COMPONENT_MATRIX[locus][OPERATORS.index(operator)]
        if priority == "INVALID":
            return (
                "INVALID",
                "INVALID",
                "V-SCOPE-LOCUS-01",
                "组件级改动不能同时把主要改动位置标为全系统；应改为全方法，或选择具体组件位置。",
            )
        return (
            "VALID",
            priority,
            f"S-COMPONENT;M-{locus}-{operator}",
            component_rationale(locus, operator, priority),
        )

    if scope == "PROTOCOL":
        if locus not in PROTOCOL_ALLOWED_LOCI:
            return (
                "INVALID",
                "INVALID",
                "V-SCOPE-LOCUS-02",
                "协议级改动只能落在全系统协议、数据协议、优化协议或推理协议；模型内部结构应归为组件级。",
            )
        if locus == "DATA":
            priority = "HOLD"
            rationale = "任何数据协议操作都可能改变固定划分、样本边界或标签口径，先证明 Benchmark 未变。"
            rule = "S-PROTOCOL;H-DATA-CONTRACT"
        elif operator == "SPLIT":
            priority = "HOLD"
            rationale = "协议拆分会增加比较口径或执行路径，必须先证明 Benchmark 仍唯一且可比。"
            rule = "S-PROTOCOL;H-PROTOCOL-SPLIT"
        elif locus == "SYSTEM" and operator == "ADD":
            priority = "HOLD"
            rationale = "新增系统级协议容易形成第二套评测或训练口径，必须先证明不会改变 Benchmark。"
            rule = "S-PROTOCOL;H-SYSTEM-ADD"
        else:
            priority = "SILVER"
            rationale = "协议级候选可运行，但最高为 Silver；必须保持数据划分、指标、预算和评估脚本不变。"
            rule = "S-PROTOCOL;C-SILVER"
        return "VALID", priority, rule, rationale

    if scope == "FULL_METHOD":
        if locus in {"SYSTEM", "BACKBONE", "BRANCH"} and operator in {"ADD", "SPLIT"}:
            return (
                "VALID",
                "REJECT",
                "S-FULL;R-STRUCTURAL-PROLIFERATION",
                "全方法同时在系统、骨干或分支层新增/拆分，改动过多且结构膨胀，无法归因于一个主要假设。",
            )
        return (
            "VALID",
            "HOLD",
            "S-FULL;H-DECOMPOSE",
            "全方法 N candidate 默认暂缓；先拆成可独立证伪的组件级实验，再重新分类。",
        )

    raise ValueError(f"Unknown scope: {scope}")


def component_rationale(locus: str, operator: str, priority: str) -> str:
    if priority == "GOLD":
        if operator in {"DELETE", "MERGE"}:
            return "组件级删除/合并具有高可归因性和精简价值；优先验证，但只有分支删除可使用 0.5 pp 精简额度。"
        if operator == "REPLACE":
            return "组件级替换保持对照清晰且不增加结构数量，是优先级最高的验证形式。"
        return "不增加主要结构数量，且能隔离验证单一机制，默认进入 Gold。"
    if priority == "SILVER":
        if locus == "BRANCH" and operator == "ADD":
            return "新增分支具有结构膨胀风险；可验证但仅为 Silver，成功后必须执行 Branch Addition Gate。"
        if operator == "ADD":
            return "新增容易带来堆叠或额外预算，值得验证但默认不进入 Gold。"
        if operator == "SPLIT":
            return "拆分提高结构或执行复杂度，只有在假设清晰且不形成分支膨胀时才运行。"
        if locus == "OPTIMIZATION":
            return "优化位置容易退化为调参；只有改变机制且遵守同方向最多三次调参时才运行。"
        return "候选具有可测试价值，但归因、通用性或结构风险弱于 Gold。"
    if locus == "DATA" and operator == "SPLIT":
        return "数据拆分可能改变 Benchmark 固定划分；先证明只是训练机制而非评测契约变化。"
    if locus == "BACKBONE" and operator in {"ADD", "SPLIT"}:
        return "新增或拆分骨干接近多骨干堆叠；先设计单骨干替换实验并证明并行结构不可替代。"
    if locus == "BRANCH" and operator == "SPLIT":
        return "拆分已有分支会直接增加分支数量；先证明不能通过替换、重连或合并验证同一假设。"
    if locus == "OPTIMIZATION" and operator == "SPLIT":
        return "多优化路径会降低归因并增加调参空间；先压缩为一个可证伪的优化假设。"
    return "当前组合存在可修复的结构或归因阻塞，修复后重新分类。"


def release_condition(scope: str, locus: str, operator: str, priority: str) -> str:
    if priority == "INVALID":
        return "重新填写互相一致的 Change Scope 与 Intervention Locus。"
    if priority == "REJECT":
        return "不得按当前组合运行；必须拆成单一组件假设，或改为替换/合并方案。"
    if priority == "HOLD":
        if scope == "FULL_METHOD":
            return "拆成组件级候选，并为每个候选定义独立支持预测与证伪条件。"
        if scope == "PROTOCOL":
            return "证明 Benchmark、预算和评估脚本保持不变，再重新评为 Silver。"
        if locus == "BRANCH":
            return "先证明替换、重连或合并不能检验同一假设。"
        if locus == "BACKBONE":
            return "先设计骨干替换方案，避免并行骨干堆叠。"
        if locus == "DATA":
            return "证明不改变固定数据划分及标签口径。"
        return "补齐可归因的单一假设和公平实验条件。"
    if locus == "BRANCH" and operator == "ADD":
        return "允许首次验证；若有效，必须执行替换实验，通过 Branch Addition Gate 后才可能晋升底座。"
    if scope == "COMPONENT" and locus == "BRANCH" and operator == "DELETE":
        return "纳入同一次 Simplification Campaign：既比较最终联合删除结果与本次精简前 Research Base，也比较谱系累计退化与 Simplification Anchor。"
    if priority == "GOLD":
        return "通过全局证据、公平性和可证伪硬门后优先运行；实验结果仍按 Research Base 晋升规则处理。"
    return "通过全局硬门后进入普通执行队列；不得因 Silver 降低实验记录与公平比较要求。"


def generate(output: Path) -> dict[str, int]:
    output.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    rows = []
    row_number = 0
    for scope in SCOPES:
        for locus in LOCI:
            for operator in OPERATORS:
                row_number += 1
                status, priority, rule_ids, rationale = classify(scope, locus, operator)
                counts[priority] = counts.get(priority, 0) + 1
                rows.append(
                    {
                        "combination_id": f"N-{row_number:03d}",
                        "evidence_class": "N",
                        "change_scope": scope,
                        "intervention_locus": locus,
                        "change_operator": operator,
                        "combination_status": status,
                        "structural_default_priority": priority,
                        "rule_ids": rule_ids,
                        "decision_reason": rationale,
                        "release_or_next_step": release_condition(scope, locus, operator, priority),
                    }
                )

    assert len(rows) == 162
    assert len({row["combination_id"] for row in rows}) == 162
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return counts


if __name__ == "__main__":
    destination = Path(__file__).resolve().parents[1] / "assets" / "candidate_priority_combinations.csv"
    result = generate(destination)
    print(f"generated={destination}")
    print("counts=" + ",".join(f"{key}:{result[key]}" for key in sorted(result)))
