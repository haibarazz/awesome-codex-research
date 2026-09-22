#!/usr/bin/env python3
"""Lint AutoResearch document routing metadata and workflow anchors."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml

ACTIVATION_LEVELS = {"ALWAYS", "PHASE", "ON_DEMAND"}
FIRST_PARTY_DOC_DIRS = ("prompts", "references", "templates")


def _read_frontmatter(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", text, re.DOTALL)
    if match is None:
        return None, [f"{path}: missing YAML frontmatter"]
    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return None, [f"{path}: invalid YAML frontmatter: {exc}"]
    if not isinstance(metadata, dict):
        errors.append(f"{path}: YAML frontmatter must be a mapping")
        return None, errors
    return metadata, errors


def _first_party_docs(skill_root: Path) -> list[Path]:
    paths: list[Path] = []
    for directory in FIRST_PARTY_DOC_DIRS:
        root = skill_root / directory
        if root.is_dir():
            paths.extend(root.rglob("*.md"))
    return sorted(paths)


def lint_document_metadata(skill_root: Path) -> list[str]:
    """Validate activation metadata and doc_id dependency routing."""
    errors: list[str] = []
    documents: list[tuple[Path, dict[str, Any]]] = []
    doc_ids: dict[str, Path] = {}

    for path in _first_party_docs(skill_root):
        metadata, path_errors = _read_frontmatter(path)
        errors.extend(path_errors)
        if metadata is None:
            continue
        documents.append((path, metadata))

        doc_id = metadata.get("doc_id")
        if not isinstance(doc_id, str) or not doc_id:
            errors.append(f"{path}: doc_id must be a non-empty string")
        elif doc_id in doc_ids:
            errors.append(
                f"{path}: duplicate doc_id {doc_id!r}; first defined by {doc_ids[doc_id]}"
            )
        else:
            doc_ids[doc_id] = path

        activation = metadata.get("activation")
        if not isinstance(activation, dict):
            errors.append(f"{path}: activation must be a mapping")
            continue
        level = activation.get("level")
        if level not in ACTIVATION_LEVELS:
            errors.append(
                f"{path}: activation.level {level!r} is not one of "
                f"{sorted(ACTIVATION_LEVELS)}"
            )
        if level == "ON_DEMAND" and "phases" in activation:
            errors.append(
                f"{path}: ON_DEMAND activation must not carry a phases key"
            )

    for path, metadata in documents:
        dependencies = metadata.get("depends_on", [])
        if not isinstance(dependencies, list):
            errors.append(f"{path}: depends_on must be a list")
            continue
        for dependency in dependencies:
            if not isinstance(dependency, str) or not dependency:
                errors.append(
                    f"{path}: depends_on entries must be non-empty doc_id strings"
                )
            elif dependency not in doc_ids:
                errors.append(
                    f"{path}: depends_on doc_id {dependency!r} does not exist"
                )
    return errors


def lint_activation_router(skill_root: Path) -> list[str]:
    """Ensure Markdown resources linked by the SKILL Activation Router exist."""
    skill_path = skill_root / "SKILL.md"
    if not skill_path.is_file():
        return [f"{skill_path}: missing SKILL.md"]
    text = skill_path.read_text(encoding="utf-8")
    match = re.search(
        r"^## Activation Router\s*$\n(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        return [f"{skill_path}: missing Activation Router section"]

    targets = re.findall(r"\[[^\]]+\]\(([^)]+\.md(?:#[^)]+)?)\)", match.group(1))
    if not targets:
        return [f"{skill_path}: Activation Router contains no Markdown resources"]

    errors: list[str] = []
    for target in targets:
        relative_target = target.split("#", 1)[0]
        resolved = (skill_root / relative_target).resolve()
        if not resolved.is_file():
            errors.append(
                f"{skill_path}: Activation Router target does not exist: {target}"
            )
    return errors


def _html_ids(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"\bid=[\"']([^\"']+)[\"']", text))


def lint_workflow_anchors(skill_root: Path) -> list[str]:
    """Check that Chinese and English workflow pages expose the same anchor IDs."""
    zh_path = skill_root / "workflow.zh.html"
    en_path = skill_root / "workflow.en.html"
    missing = [path for path in (zh_path, en_path) if not path.is_file()]
    if missing:
        return [f"{path}: missing workflow HTML" for path in missing]

    zh_ids = _html_ids(zh_path)
    en_ids = _html_ids(en_path)
    if zh_ids == en_ids:
        return []
    return [
        "workflow anchor ID sets differ: "
        f"zh_only={sorted(zh_ids - en_ids)}, en_only={sorted(en_ids - zh_ids)}"
    ]


def lint_skill_docs(skill_root: Path) -> list[str]:
    """Return all deterministic documentation consistency violations."""
    root = skill_root.resolve()
    return [
        *lint_document_metadata(root),
        *lint_activation_router(root),
        *lint_workflow_anchors(root),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint AutoResearch documentation routing and workflow anchors."
    )
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path containing SKILL.md (defaults to the bundled skill root).",
    )
    args = parser.parse_args()
    errors = lint_skill_docs(args.skill_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} documentation consistency error(s)")
        return 1
    print("OK: document metadata, Activation Router paths, and workflow anchors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
