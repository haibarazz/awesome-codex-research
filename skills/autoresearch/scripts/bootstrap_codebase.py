#!/usr/bin/env python3
"""Inspect a research workspace and bootstrap ReproFlow only when code is absent."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

DEFAULT_REPO_URL = "https://github.com/haibarazz/ReproFlow.git"
DEFAULT_REF = "main"
PROFILE_PATH = Path("CODEBASE_PROFILE.md")
STATE_PATH = Path(".autoresearch/codebase_bootstrap.json")

REPROFLOW_MARKERS = (
    Path("main.py"),
    Path("scripts/doctor.py"),
    Path("reproflow"),
    Path("configs/config.yaml"),
)
CODE_MARKER_FILES = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "environment.yml",
    "environment.yaml",
    "Pipfile",
    "poetry.lock",
    "uv.lock",
    "train.py",
    "main.py",
    "run.py",
}
CODE_SUFFIXES = {
    ".py",
    ".ipynb",
    ".r",
    ".jl",
    ".cpp",
    ".cc",
    ".c",
    ".java",
    ".go",
    ".rs",
    ".ts",
}
INFRASTRUCTURE_DIRS = {
    ".agents",
    ".autoresearch",
    ".claude",
    ".codex",
    ".cursor",
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "artifacts",
    "checkpoints",
    "data",
    "dataset",
    "docs",
    "literature",
    "logs",
    "outputs",
    "papers",
    "result",
    "results",
}
WALK_PRUNE_DIRS = {
    ".agents",
    ".claude",
    ".codex",
    ".cursor",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "site-packages",
    "venv",
    ".venv",
}
PRESERVE_EXISTING_FILES = {
    "README",
    "README.md",
    "README.rst",
    "LICENSE",
    "LICENSE.md",
}
PRESERVE_EXISTING_PREFIXES = ("data/", "dataset/")


class BootstrapError(Exception):
    """A stable, user-actionable bootstrap rejection."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        violations: list[str] | None = None,
        allowed_next_actions: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.violations = violations or [message]
        self.allowed_next_actions = allowed_next_actions or []


@dataclass
class ImportPlan:
    copy_files: list[tuple[Path, Path]]
    preserved_paths: list[str]
    identical_paths: list[str]
    conflicts: list[str]
    merged_gitignore: str | None


@dataclass
class ImportMutation:
    created_files: list[Path]
    created_dirs: list[Path]
    gitignore: Path
    original_gitignore: str | None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_repo_url(repo_url: str) -> str:
    parts = urlsplit(repo_url)
    if not parts.scheme or not parts.netloc:
        return repo_url
    hostname = parts.hostname or ""
    if parts.port:
        hostname = f"{hostname}:{parts.port}"
    return urlunsplit((parts.scheme, hostname, parts.path, parts.query, parts.fragment))


def _run_git(args: list[str], *, cwd: Path | None = None) -> str:
    if shutil.which("git") is None:
        raise BootstrapError(
            "GIT_NOT_AVAILABLE",
            "git is required to bootstrap ReproFlow.",
            allowed_next_actions=["INSTALL_GIT", "USE_EXISTING_CODEBASE"],
        )
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        summary = detail[-1] if detail else "git command failed"
        summary = re.sub(r"(https?://)[^/@\s]+@", r"\1***@", summary)
        raise BootstrapError(
            "GIT_COMMAND_FAILED",
            summary,
            allowed_next_actions=["RETRY_ONCE", "USE_EXISTING_CODEBASE"],
        )
    return completed.stdout.strip()


def _safe_relative(project_root: Path, path: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def _embedded_skill_root(project_root: Path) -> Path | None:
    skill_root = Path(__file__).resolve().parents[1]
    try:
        skill_root.relative_to(project_root.resolve())
    except ValueError:
        return None
    return skill_root


def _is_ignored_path(
    path: Path,
    project_root: Path,
    embedded_skill_root: Path | None,
) -> bool:
    resolved = path.resolve()
    if embedded_skill_root is not None:
        try:
            resolved.relative_to(embedded_skill_root)
            return True
        except ValueError:
            pass
    try:
        relative = resolved.relative_to(project_root.resolve())
    except ValueError:
        return True
    return bool(relative.parts and relative.parts[0] in INFRASTRUCTURE_DIRS)


def _is_reproflow_root(path: Path) -> bool:
    return all((path / marker).exists() for marker in REPROFLOW_MARKERS)


def _find_reproflow_roots(project_root: Path) -> list[Path]:
    embedded_skill_root = _embedded_skill_root(project_root)
    candidates = [project_root]
    for child in project_root.iterdir():
        if not child.is_dir() or child.is_symlink():
            continue
        if _is_ignored_path(child, project_root, embedded_skill_root):
            continue
        candidates.append(child)
    return [candidate for candidate in candidates if _is_reproflow_root(candidate)]


def _code_evidence(project_root: Path, limit: int = 20) -> list[str]:
    embedded_skill_root = _embedded_skill_root(project_root)
    evidence: list[str] = []
    for current, dirnames, filenames in os.walk(project_root):
        current_path = Path(current)
        if _is_ignored_path(current_path, project_root, embedded_skill_root):
            dirnames[:] = []
            continue
        dirnames[:] = [
            name
            for name in dirnames
            if name not in WALK_PRUNE_DIRS
            and not _is_ignored_path(
                current_path / name,
                project_root,
                embedded_skill_root,
            )
        ]
        for filename in filenames:
            path = current_path / filename
            if filename in CODE_MARKER_FILES or path.suffix.lower() in CODE_SUFFIXES:
                evidence.append(_safe_relative(project_root, path))
                if len(evidence) >= limit:
                    return sorted(evidence)
    return sorted(evidence)


def inspect_codebase(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    if not project_root.is_dir():
        raise BootstrapError(
            "PROJECT_ROOT_NOT_FOUND",
            f"Project root is not a directory: {project_root}",
        )
    reproflow_roots = _find_reproflow_roots(project_root)
    if len(reproflow_roots) > 1:
        roots = [_safe_relative(project_root, root) or "." for root in reproflow_roots]
        raise BootstrapError(
            "MULTIPLE_REPROFLOW_ROOTS",
            "Multiple ReproFlow code roots were detected.",
            violations=[f"Detected ReproFlow roots: {', '.join(roots)}"],
            allowed_next_actions=["SELECT_ONE_CODE_ROOT"],
        )
    if reproflow_roots:
        code_root = _safe_relative(project_root, reproflow_roots[0]) or "."
        return {
            "accepted": True,
            "action": "INSPECT_CODEBASE",
            "codebase_status": "REPROFLOW_PRESENT",
            "code_root": code_root,
            "evidence": [str(marker) for marker in REPROFLOW_MARKERS],
            "allowed_next_actions": ["ADOPT_REPROFLOW", "VALIDATE_CODEBASE"],
        }

    evidence = _code_evidence(project_root)
    if evidence:
        return {
            "accepted": True,
            "action": "INSPECT_CODEBASE",
            "codebase_status": "EXISTING_CODE",
            "code_root": ".",
            "evidence": evidence,
            "allowed_next_actions": ["PROFILE_EXISTING_CODEBASE"],
        }
    return {
        "accepted": True,
        "action": "INSPECT_CODEBASE",
        "codebase_status": "NO_CODE",
        "code_root": None,
        "evidence": [],
        "allowed_next_actions": ["BOOTSTRAP_REPROFLOW"],
    }


def _clone_repo(repo_url: str, ref: str, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run_git(
        [
            "clone",
            "--depth",
            "1",
            "--branch",
            ref,
            "--",
            repo_url,
            str(destination),
        ]
    )
    if not _is_reproflow_root(destination):
        raise BootstrapError(
            "INVALID_REPROFLOW_SOURCE",
            "The cloned repository does not satisfy the ReproFlow fingerprint.",
            violations=[
                "Required markers: "
                + ", ".join(marker.as_posix() for marker in REPROFLOW_MARKERS)
            ],
            allowed_next_actions=["CHECK_REPOSITORY_AND_REF"],
        )
    return _run_git(["rev-parse", "HEAD"], cwd=destination)


def _merge_gitignore(existing: str, incoming: str) -> str:
    existing_lines = existing.splitlines()
    existing_set = set(existing_lines)
    additions = [line for line in incoming.splitlines() if line not in existing_set]
    if not additions:
        return existing if existing.endswith("\n") else existing + "\n"
    merged = existing.rstrip() + "\n\n# ReproFlow bootstrap\n" + "\n".join(additions)
    return merged.rstrip() + "\n"


def _should_preserve_existing(relative: str) -> bool:
    if relative in PRESERVE_EXISTING_FILES:
        return True
    return relative.startswith(PRESERVE_EXISTING_PREFIXES)


def _plan_import(source: Path, destination: Path) -> ImportPlan:
    copy_files: list[tuple[Path, Path]] = []
    preserved_paths: list[str] = []
    identical_paths: list[str] = []
    conflicts: list[str] = []
    merged_gitignore: str | None = None

    for source_path in sorted(source.rglob("*")):
        relative_path = source_path.relative_to(source)
        if not relative_path.parts or relative_path.parts[0] == ".git":
            continue
        relative = relative_path.as_posix()
        target_path = destination / relative_path
        if source_path.is_symlink():
            conflicts.append(f"{relative}: symlinks are not imported")
            continue
        if source_path.is_dir():
            if target_path.exists() and not target_path.is_dir():
                conflicts.append(f"{relative}: target is not a directory")
            continue
        if not target_path.exists():
            copy_files.append((source_path, target_path))
            continue
        if not target_path.is_file():
            conflicts.append(f"{relative}: target is not a regular file")
            continue
        if _sha256(source_path) == _sha256(target_path):
            identical_paths.append(relative)
        elif relative == ".gitignore":
            merged_gitignore = _merge_gitignore(
                target_path.read_text(encoding="utf-8"),
                source_path.read_text(encoding="utf-8"),
            )
        elif _should_preserve_existing(relative):
            preserved_paths.append(relative)
        else:
            conflicts.append(f"{relative}: existing file differs")

    return ImportPlan(
        copy_files=copy_files,
        preserved_paths=preserved_paths,
        identical_paths=identical_paths,
        conflicts=conflicts,
        merged_gitignore=merged_gitignore,
    )


def _rollback_import(mutation: ImportMutation) -> None:
    for path in reversed(mutation.created_files):
        path.unlink(missing_ok=True)
    if mutation.original_gitignore is not None:
        mutation.gitignore.write_text(
            mutation.original_gitignore,
            encoding="utf-8",
        )
    for path in sorted(
        set(mutation.created_dirs),
        key=lambda value: len(value.parts),
        reverse=True,
    ):
        try:
            path.rmdir()
        except OSError:
            pass


def _apply_import(plan: ImportPlan, destination: Path) -> ImportMutation:
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    if not destination.exists():
        created_dirs.append(destination)
    gitignore = destination / ".gitignore"
    original_gitignore = (
        gitignore.read_text(encoding="utf-8") if gitignore.is_file() else None
    )
    mutation = ImportMutation(
        created_files=created_files,
        created_dirs=created_dirs,
        gitignore=gitignore,
        original_gitignore=original_gitignore,
    )
    try:
        for source_path, target_path in plan.copy_files:
            missing_parents: list[Path] = []
            parent = target_path.parent
            while parent != destination and not parent.exists():
                missing_parents.append(parent)
                parent = parent.parent
            target_path.parent.mkdir(parents=True, exist_ok=True)
            created_dirs.extend(reversed(missing_parents))
            shutil.copy2(source_path, target_path)
            created_files.append(target_path)
        if plan.merged_gitignore is not None:
            gitignore.write_text(plan.merged_gitignore, encoding="utf-8")
    except Exception:
        _rollback_import(mutation)
        raise
    return mutation


def _safe_destination(project_root: Path, requested: str) -> Path:
    relative = Path(requested)
    if relative.is_absolute() or ".." in relative.parts:
        raise BootstrapError(
            "INVALID_DESTINATION",
            "Bootstrap destination must stay inside the project root.",
        )
    destination = (project_root / relative).resolve()
    try:
        destination.relative_to(project_root.resolve())
    except ValueError as exc:
        raise BootstrapError(
            "INVALID_DESTINATION",
            "Bootstrap destination must stay inside the project root.",
        ) from exc
    if destination in {
        (project_root / ".git").resolve(),
        (project_root / ".autoresearch").resolve(),
    }:
        raise BootstrapError(
            "INVALID_DESTINATION",
            "Bootstrap destination cannot be a control-state directory.",
        )
    embedded_skill_root = _embedded_skill_root(project_root)
    if embedded_skill_root is not None and destination == embedded_skill_root:
        raise BootstrapError(
            "INVALID_DESTINATION",
            "Bootstrap destination cannot overwrite the embedded Skill.",
        )
    return destination


def _render_profile(
    *,
    code_root: str,
    bootstrap_mode: str,
    repo_url: str,
    ref: str,
    resolved_commit: str,
) -> str:
    command_prefix = "" if code_root == "." else f"cd {shlex.quote(code_root)} && "
    return f"""---
artifact: codebase-profile
schema_version: 1
status: ACTIVE
---

# Codebase Profile

## Source

- Framework: `ReproFlow`
- Code root: `{code_root}`
- Bootstrap mode: `{bootstrap_mode}`
- Repository: `{_display_repo_url(repo_url)}`
- Requested ref: `{ref}`
- Resolved commit: `{resolved_commit}`

## Required Entrypoints

- Contract: `{code_root}/AGENTS.md`
- Architecture: `{code_root}/docs/architecture.md`
- Dataset doctor: `{command_prefix}python scripts/doctor.py data=<dataset> model=<model> trainer=<trainer> metrics=default`
- Training: `{command_prefix}python main.py data=<dataset> model=<model> trainer=<trainer> metrics=default`
- ML baseline: `{command_prefix}python run_ml_benchmark.py data=<dataset>`

## AutoResearch Bridge

- Pass the Runtime Experiment ID through `tracking.experiment_id` and the Attempt ID through `tracking.run_id`.
- Formal runs must enable `tracking.enabled=true`, `artifacts.save_metrics_json=true`, and `artifacts.save_manifest=true`.
- Preregister the resolved config, metrics JSON, artifact manifest, and trainer log in Runtime `artifact_refs`.
- Benchmark-owned data split, metrics, evaluator, seed protocol, and training budget remain frozen.

## Verification

- ReproFlow fingerprint: `PASSED`
- Dataset-specific doctor: `PENDING`
- One-epoch technical smoke: `PENDING`
"""


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    _write_text_atomic(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _preflight_control_paths(project_root: Path) -> None:
    state_parent = project_root / STATE_PATH.parent
    state_path = project_root / STATE_PATH
    profile_path = project_root / PROFILE_PATH
    violations: list[str] = []
    if state_parent.exists() and (
        not state_parent.is_dir() or state_parent.is_symlink()
    ):
        violations.append(
            f"{STATE_PATH.parent.as_posix()} must be a directory."
        )
    if state_path.exists() and (
        not state_path.is_file() or state_path.is_symlink()
    ):
        violations.append(f"{STATE_PATH.as_posix()} must be a regular file.")
    if profile_path.exists() and (
        not profile_path.is_file() or profile_path.is_symlink()
    ):
        violations.append(f"{PROFILE_PATH.as_posix()} must be a regular file.")
    if violations:
        raise BootstrapError(
            "CONTROL_ARTIFACT_BLOCKED",
            "Bootstrap control artifacts cannot be written safely.",
            violations=violations,
            allowed_next_actions=["REPAIR_CONTROL_ARTIFACT_PATHS"],
        )


def _write_bootstrap_artifacts(
    project_root: Path,
    *,
    code_root: str,
    bootstrap_mode: str,
    repo_url: str,
    ref: str,
    resolved_commit: str,
    preserved_paths: list[str],
) -> dict[str, bool]:
    _preflight_control_paths(project_root)
    state_path = project_root / STATE_PATH
    profile_path = project_root / PROFILE_PATH
    state = {
        "schema_version": 1,
        "framework": "REPROFLOW",
        "code_root": code_root,
        "bootstrap_mode": bootstrap_mode,
        "source": {
            "repository": _display_repo_url(repo_url),
            "requested_ref": ref,
            "resolved_commit": resolved_commit,
        },
        "preserved_paths": sorted(preserved_paths),
        "created_at": _utc_now(),
    }
    state_parent_preexisting = state_path.parent.exists()
    profile_preexisting = profile_path.exists()
    state_created = False
    profile_created = False
    try:
        _write_json_atomic(state_path, state)
        state_created = True
        if not profile_path.exists():
            _write_text_atomic(
                profile_path,
                _render_profile(
                    code_root=code_root,
                    bootstrap_mode=bootstrap_mode,
                    repo_url=repo_url,
                    ref=ref,
                    resolved_commit=resolved_commit,
                ),
            )
            profile_created = True
    except Exception:
        if not profile_preexisting:
            profile_path.unlink(missing_ok=True)
        if state_created:
            state_path.unlink(missing_ok=True)
        if not state_parent_preexisting:
            try:
                state_path.parent.rmdir()
            except OSError:
                pass
        raise
    return {"state_created": state_created, "profile_created": profile_created}


def _git_metadata(code_root: Path) -> tuple[str, str, str]:
    resolved_commit = _run_git(["rev-parse", "HEAD"], cwd=code_root)
    try:
        repo_url = _run_git(["remote", "get-url", "origin"], cwd=code_root)
    except BootstrapError:
        repo_url = DEFAULT_REPO_URL
    try:
        ref = _run_git(["branch", "--show-current"], cwd=code_root) or DEFAULT_REF
    except BootstrapError:
        ref = DEFAULT_REF
    return repo_url, ref, resolved_commit


def _adopt_existing_reproflow(
    project_root: Path,
    inspection: dict[str, Any],
) -> dict[str, Any]:
    code_root_relative = str(inspection["code_root"])
    code_root = project_root if code_root_relative == "." else project_root / code_root_relative
    existing_state_path = project_root / STATE_PATH
    existing_state: dict[str, Any] | None = None
    if existing_state_path.is_file():
        existing_state = json.loads(existing_state_path.read_text(encoding="utf-8"))
        source = existing_state.get("source", {})
        repo_url = str(source.get("repository", DEFAULT_REPO_URL))
        ref = str(source.get("requested_ref", DEFAULT_REF))
        resolved_commit = str(source.get("resolved_commit", "UNKNOWN"))
    else:
        try:
            repo_url, ref, resolved_commit = _git_metadata(code_root)
        except BootstrapError:
            repo_url = "UNRECORDED"
            ref = "UNVERSIONED"
            resolved_commit = "UNVERSIONED"

    if existing_state is None:
        artifacts = _write_bootstrap_artifacts(
            project_root,
            code_root=code_root_relative,
            bootstrap_mode="ADOPT_EXISTING",
            repo_url=repo_url,
            ref=ref,
            resolved_commit=resolved_commit,
            preserved_paths=[],
        )
    else:
        profile_path = project_root / PROFILE_PATH
        profile_created = False
        if not profile_path.exists():
            _write_text_atomic(
                profile_path,
                _render_profile(
                    code_root=code_root_relative,
                    bootstrap_mode=str(
                        existing_state.get("bootstrap_mode", "ADOPT_EXISTING")
                    ),
                    repo_url=repo_url,
                    ref=ref,
                    resolved_commit=resolved_commit,
                ),
            )
            profile_created = True
        artifacts = {"state_created": False, "profile_created": profile_created}
    return {
        "accepted": True,
        "action": "ADOPT_REPROFLOW",
        "codebase_status": "REPROFLOW_PRESENT",
        "code_root": code_root_relative,
        "source": {
            "repository": _display_repo_url(repo_url),
            "requested_ref": ref,
            "resolved_commit": resolved_commit,
        },
        "artifacts": artifacts,
        "allowed_next_actions": ["READ_REPROFLOW_CONTRACT", "RUN_DATASET_DOCTOR"],
    }


def bootstrap_reproflow(
    project_root: Path,
    *,
    repo_url: str = DEFAULT_REPO_URL,
    ref: str = DEFAULT_REF,
    destination: str = "auto",
) -> dict[str, Any]:
    project_root = project_root.resolve()
    inspection = inspect_codebase(project_root)
    status = inspection["codebase_status"]
    if status == "REPROFLOW_PRESENT":
        return _adopt_existing_reproflow(project_root, inspection)
    if status == "EXISTING_CODE":
        raise BootstrapError(
            "EXISTING_CODE_PRESENT",
            "Runnable project code already exists; ReproFlow bootstrap is forbidden.",
            violations=[
                "Code evidence: " + ", ".join(inspection.get("evidence", [])[:10])
            ],
            allowed_next_actions=["PROFILE_EXISTING_CODEBASE"],
        )
    if (project_root / STATE_PATH).exists():
        raise BootstrapError(
            "STALE_BOOTSTRAP_STATE",
            "Bootstrap state exists but no ReproFlow codebase was detected.",
            allowed_next_actions=["VALIDATE_OR_RECOVER_BOOTSTRAP_STATE"],
        )
    _preflight_control_paths(project_root)

    if destination == "auto":
        requested_destinations = [".", "codebase"]
    else:
        requested_destinations = [destination]

    if requested_destinations[0] == "." and not any(project_root.iterdir()):
        with tempfile.TemporaryDirectory(
            prefix=f".{project_root.name}.autoresearch-",
            dir=project_root.parent,
        ) as temporary:
            staged_project = Path(temporary) / "project"
            resolved_commit = _clone_repo(repo_url, ref, staged_project)
            artifacts = _write_bootstrap_artifacts(
                staged_project,
                code_root=".",
                bootstrap_mode="DIRECT_CLONE",
                repo_url=repo_url,
                ref=ref,
                resolved_commit=resolved_commit,
                preserved_paths=[],
            )
            project_root.rmdir()
            try:
                os.replace(staged_project, project_root)
            except Exception:
                project_root.mkdir()
                raise
        return {
            "accepted": True,
            "action": "BOOTSTRAP_REPROFLOW",
            "codebase_status": "REPROFLOW_PRESENT",
            "code_root": ".",
            "bootstrap_mode": "DIRECT_CLONE",
            "source": {
                "repository": _display_repo_url(repo_url),
                "requested_ref": ref,
                "resolved_commit": resolved_commit,
            },
            "preserved_paths": [],
            "artifacts": artifacts,
            "allowed_next_actions": ["READ_REPROFLOW_CONTRACT", "RUN_DATASET_DOCTOR"],
        }

    with tempfile.TemporaryDirectory(prefix="autoresearch-reproflow-") as temporary:
        source = Path(temporary) / "source"
        resolved_commit = _clone_repo(repo_url, ref, source)
        attempted_conflicts: dict[str, list[str]] = {}
        for requested_destination in requested_destinations:
            target = _safe_destination(project_root, requested_destination)
            plan = _plan_import(source, target)
            code_root = _safe_relative(project_root, target) or "."
            if plan.conflicts:
                attempted_conflicts[code_root] = plan.conflicts
                continue
            mutation = _apply_import(plan, target)
            try:
                if not _is_reproflow_root(target):
                    raise BootstrapError(
                        "BOOTSTRAP_VALIDATION_FAILED",
                        "Imported files do not satisfy the ReproFlow fingerprint.",
                        allowed_next_actions=["RECOVER_BOOTSTRAP"],
                    )
                artifacts = _write_bootstrap_artifacts(
                    project_root,
                    code_root=code_root,
                    bootstrap_mode="TEMPLATE_IMPORT",
                    repo_url=repo_url,
                    ref=ref,
                    resolved_commit=resolved_commit,
                    preserved_paths=plan.preserved_paths,
                )
            except Exception:
                _rollback_import(mutation)
                raise
            return {
                "accepted": True,
                "action": "BOOTSTRAP_REPROFLOW",
                "codebase_status": "REPROFLOW_PRESENT",
                "code_root": code_root,
                "bootstrap_mode": "TEMPLATE_IMPORT",
                "source": {
                    "repository": _display_repo_url(repo_url),
                    "requested_ref": ref,
                    "resolved_commit": resolved_commit,
                },
                "preserved_paths": sorted(plan.preserved_paths),
                "identical_paths": sorted(plan.identical_paths),
                "artifacts": artifacts,
                "allowed_next_actions": [
                    "READ_REPROFLOW_CONTRACT",
                    "RUN_DATASET_DOCTOR",
                ],
            }

    violations = [
        f"{code_root}: {conflict}"
        for code_root, conflicts in attempted_conflicts.items()
        for conflict in conflicts
    ]
    raise BootstrapError(
        "BOOTSTRAP_CONFLICT",
        "ReproFlow cannot be imported without overwriting existing files.",
        violations=violations,
        allowed_next_actions=["PROFILE_EXISTING_CODEBASE", "RESOLVE_FILE_CONFLICTS"],
    )


def validate_codebase(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    violations: list[str] = []
    state_path = project_root / STATE_PATH
    profile_path = project_root / PROFILE_PATH
    state: dict[str, Any] = {}
    if not state_path.is_file():
        violations.append(f"Missing {STATE_PATH.as_posix()}")
    else:
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            violations.append(f"Invalid bootstrap state JSON: {exc}")
        if not isinstance(state, dict):
            violations.append("Bootstrap state must be a JSON object.")
            state = {}
    if not profile_path.is_file():
        violations.append(f"Missing {PROFILE_PATH.as_posix()}")

    code_root_value = str(state.get("code_root", "")) if state else ""
    code_root = project_root
    if code_root_value and code_root_value != ".":
        try:
            code_root = _safe_destination(project_root, code_root_value)
        except BootstrapError as exc:
            violations.extend(exc.violations)
    if state and state.get("framework") != "REPROFLOW":
        violations.append("Bootstrap state framework must be REPROFLOW.")
    if state and not _is_reproflow_root(code_root):
        violations.append(
            "ReproFlow fingerprint is incomplete at the recorded code root."
        )
    bootstrap_mode = str(state.get("bootstrap_mode", "")).strip() if state else ""
    if state and bootstrap_mode not in {
        "DIRECT_CLONE",
        "TEMPLATE_IMPORT",
        "ADOPT_EXISTING",
    }:
        violations.append("Bootstrap state has an unsupported bootstrap_mode.")
    raw_source = state.get("source", {}) if state else {}
    source = raw_source if isinstance(raw_source, dict) else {}
    if state and not isinstance(raw_source, dict):
        violations.append("Bootstrap state source must be a JSON object.")
    repository = str(source.get("repository", "")).strip()
    requested_ref = str(source.get("requested_ref", "")).strip()
    resolved_commit = str(source.get("resolved_commit", "")).strip()
    if state and not repository:
        violations.append("Bootstrap state is missing source.repository.")
    if state and not requested_ref:
        violations.append("Bootstrap state is missing source.requested_ref.")
    if state and bootstrap_mode in {"DIRECT_CLONE", "TEMPLATE_IMPORT"}:
        if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", resolved_commit):
            violations.append(
                "Bootstrap source.resolved_commit must be a 40- or 64-character "
                "hex Git commit."
            )
    elif state and bootstrap_mode == "ADOPT_EXISTING":
        if resolved_commit != "UNVERSIONED" and not re.fullmatch(
            r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}",
            resolved_commit,
        ):
            violations.append(
                "Adopted source.resolved_commit must be UNVERSIONED or a valid "
                "Git commit."
            )
    elif state and not resolved_commit:
        violations.append("Bootstrap state is missing source.resolved_commit.")

    if state and bootstrap_mode == "DIRECT_CLONE":
        try:
            actual_commit = _run_git(["rev-parse", "HEAD"], cwd=code_root)
        except BootstrapError as exc:
            violations.append(
                f"Cannot verify the direct-clone Git HEAD: {exc.message}"
            )
        else:
            if actual_commit.lower() != resolved_commit.lower():
                violations.append(
                    "Recorded source.resolved_commit does not match direct-clone "
                    "Git HEAD."
                )

    return {
        "accepted": not violations,
        "action": "VALIDATE_CODEBASE",
        "codebase_status": "REPROFLOW_PRESENT" if not violations else "INVALID",
        "code_root": code_root_value or None,
        "violations": violations,
        "allowed_next_actions": (
            ["RUN_DATASET_DOCTOR"] if not violations else ["RECOVER_CODEBASE_BOOTSTRAP"]
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a project and bootstrap ReproFlow only when code is absent."
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Root of the user's research project.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect", help="Inspect whether runnable code already exists.")
    bootstrap = commands.add_parser(
        "bootstrap",
        help="Bootstrap or adopt ReproFlow without overwriting existing code.",
    )
    bootstrap.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    bootstrap.add_argument("--ref", default=DEFAULT_REF)
    bootstrap.add_argument(
        "--destination",
        default="auto",
        help="Relative code root or 'auto' (default: root, then codebase/ fallback).",
    )
    commands.add_parser(
        "validate",
        help="Validate bootstrap provenance, profile, and ReproFlow fingerprint.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    project_root = Path(args.project_root)
    try:
        if args.command == "inspect":
            result = inspect_codebase(project_root)
        elif args.command == "bootstrap":
            result = bootstrap_reproflow(
                project_root,
                repo_url=args.repo_url,
                ref=args.ref,
                destination=args.destination,
            )
        else:
            result = validate_codebase(project_root)
    except BootstrapError as exc:
        result = {
            "accepted": False,
            "error_code": exc.code,
            "message": exc.message,
            "violations": exc.violations,
            "allowed_next_actions": exc.allowed_next_actions,
        }
    except Exception as exc:  # pragma: no cover - last-resort machine-readable failure
        result = {
            "accepted": False,
            "error_code": "UNEXPECTED_ERROR",
            "message": f"{type(exc).__name__}: {exc}",
            "violations": ["Unexpected bootstrap failure; no override is authorized."],
            "allowed_next_actions": ["DIAGNOSE_BOOTSTRAP"],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("accepted") else 2


if __name__ == "__main__":
    raise SystemExit(main())
