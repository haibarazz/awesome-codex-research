from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import bootstrap_codebase as bootstrap_module  # noqa: E402
from bootstrap_codebase import (  # noqa: E402
    BootstrapError,
    bootstrap_reproflow,
    inspect_codebase,
    validate_codebase,
)


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


@pytest.fixture()
def reproflow_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "upstream"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=main")
    (repo / "main.py").write_text("print('reproflow')\n", encoding="utf-8")
    (repo / "scripts").mkdir()
    (repo / "scripts/doctor.py").write_text("print('doctor')\n", encoding="utf-8")
    (repo / "reproflow").mkdir()
    (repo / "reproflow/__init__.py").write_text("", encoding="utf-8")
    (repo / "configs").mkdir()
    (repo / "configs/config.yaml").write_text("device: cpu\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs/architecture.md").write_text("# Architecture\n", encoding="utf-8")
    (repo / "dataset").mkdir()
    (repo / "dataset/sample.csv").write_text("x,y\n1,0\n", encoding="utf-8")
    (repo / "AGENTS.md").write_text("# ReproFlow contract\n", encoding="utf-8")
    (repo / "README.md").write_text("# ReproFlow\n", encoding="utf-8")
    (repo / ".gitignore").write_text("result/\ncheckpoints/\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(
        repo,
        "-c",
        "user.name=AutoResearch Test",
        "-c",
        "user.email=autoresearch@example.invalid",
        "commit",
        "-m",
        "fixture",
    )
    return repo, _git(repo, "rev-parse", "HEAD")


def test_inspect_ignores_data_and_embedded_skill(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "dataset").mkdir()
    (project / "dataset/data.csv").write_text("x,y\n1,0\n", encoding="utf-8")
    (project / "autoresearch").mkdir()
    (project / "autoresearch/SKILL.md").write_text("# Skill\n", encoding="utf-8")
    assert inspect_codebase(project)["codebase_status"] == "NO_CODE"


def test_inspect_ignores_agent_infrastructure_and_finds_deep_code(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    for directory in (".agents", ".claude", ".codex", ".cursor"):
        infra = project / directory
        infra.mkdir()
        (infra / "helper.py").write_text("print('tooling')\n", encoding="utf-8")
    assert inspect_codebase(project)["codebase_status"] == "NO_CODE"

    deep_code = project / "packages/a/b/c/d/e/f/train.py"
    deep_code.parent.mkdir(parents=True)
    deep_code.write_text("print('training')\n", encoding="utf-8")
    inspection = inspect_codebase(project)
    assert inspection["codebase_status"] == "EXISTING_CODE"
    assert "packages/a/b/c/d/e/f/train.py" in inspection["evidence"]


def test_direct_clone_into_truly_empty_directory(
    tmp_path: Path,
    reproflow_repo: tuple[Path, str],
) -> None:
    upstream, commit = reproflow_repo
    project = tmp_path / "empty-project"
    project.mkdir()
    result = bootstrap_reproflow(
        project,
        repo_url=upstream.as_uri(),
        ref="main",
    )
    assert result["accepted"] is True
    assert result["bootstrap_mode"] == "DIRECT_CLONE"
    assert result["source"]["resolved_commit"] == commit
    assert (project / ".git").is_dir()
    assert (project / "CODEBASE_PROFILE.md").is_file()
    assert validate_codebase(project)["accepted"] is True


def test_invalid_source_leaves_empty_project_untouched(tmp_path: Path) -> None:
    invalid_repo = tmp_path / "invalid-upstream"
    invalid_repo.mkdir()
    _git(invalid_repo, "init", "--initial-branch=main")
    (invalid_repo / "README.md").write_text("# Not ReproFlow\n", encoding="utf-8")
    _git(invalid_repo, "add", ".")
    _git(
        invalid_repo,
        "-c",
        "user.name=AutoResearch Test",
        "-c",
        "user.email=autoresearch@example.invalid",
        "commit",
        "-m",
        "fixture",
    )
    project = tmp_path / "empty-project"
    project.mkdir()

    with pytest.raises(BootstrapError) as captured:
        bootstrap_reproflow(
            project,
            repo_url=invalid_repo.as_uri(),
            ref="main",
        )

    assert captured.value.code == "INVALID_REPROFLOW_SOURCE"
    assert list(project.iterdir()) == []


def test_import_into_existing_git_repo_preserves_user_files(
    tmp_path: Path,
    reproflow_repo: tuple[Path, str],
) -> None:
    upstream, commit = reproflow_repo
    project = tmp_path / "existing-git"
    project.mkdir()
    _git(project, "init", "--initial-branch=main")
    (project / "README.md").write_text("# User project\n", encoding="utf-8")
    (project / ".gitignore").write_text("private-data/\n", encoding="utf-8")
    (project / "dataset").mkdir()
    (project / "dataset/sample.csv").write_text("user,data\n", encoding="utf-8")

    result = bootstrap_reproflow(
        project,
        repo_url=upstream.as_uri(),
        ref="main",
    )

    assert result["bootstrap_mode"] == "TEMPLATE_IMPORT"
    assert result["code_root"] == "."
    assert result["source"]["resolved_commit"] == commit
    assert (project / "README.md").read_text(encoding="utf-8") == "# User project\n"
    assert (
        project / "dataset/sample.csv"
    ).read_text(encoding="utf-8") == "user,data\n"
    gitignore = (project / ".gitignore").read_text(encoding="utf-8")
    assert "private-data/" in gitignore
    assert "result/" in gitignore
    assert not (project / "codebase/.git").exists()
    assert validate_codebase(project)["accepted"] is True


def test_existing_code_forbids_bootstrap_without_mutation(
    tmp_path: Path,
    reproflow_repo: tuple[Path, str],
) -> None:
    upstream, _ = reproflow_repo
    project = tmp_path / "existing-code"
    project.mkdir()
    train = project / "train.py"
    train.write_text("print('user training')\n", encoding="utf-8")

    with pytest.raises(BootstrapError) as captured:
        bootstrap_reproflow(project, repo_url=upstream.as_uri(), ref="main")

    assert captured.value.code == "EXISTING_CODE_PRESENT"
    assert train.read_text(encoding="utf-8") == "print('user training')\n"
    assert not (project / ".autoresearch").exists()


def test_root_conflict_falls_back_to_codebase(
    tmp_path: Path,
    reproflow_repo: tuple[Path, str],
) -> None:
    upstream, _ = reproflow_repo
    project = tmp_path / "conflict"
    project.mkdir()
    (project / "AGENTS.md").write_text("# User rules\n", encoding="utf-8")

    result = bootstrap_reproflow(project, repo_url=upstream.as_uri(), ref="main")

    assert result["code_root"] == "codebase"
    assert (project / "AGENTS.md").read_text(encoding="utf-8") == "# User rules\n"
    assert (project / "codebase/AGENTS.md").is_file()
    assert not (project / "codebase/.git").exists()
    profile = (project / "CODEBASE_PROFILE.md").read_text(encoding="utf-8")
    assert (
        "`cd codebase && python scripts/doctor.py "
        "data=<dataset> model=<model> trainer=<trainer> metrics=default`"
        in profile
    )
    assert (
        "`cd codebase && python main.py "
        "data=<dataset> model=<model> trainer=<trainer> metrics=default`"
        in profile
    )
    assert "`cd codebase && python run_ml_benchmark.py data=<dataset>`" in profile
    assert validate_codebase(project)["accepted"] is True


def test_blocked_control_path_prevents_import_without_mutation(
    tmp_path: Path,
    reproflow_repo: tuple[Path, str],
) -> None:
    upstream, _ = reproflow_repo
    project = tmp_path / "blocked-control"
    project.mkdir()
    readme = project / "README.md"
    readme.write_text("# User project\n", encoding="utf-8")
    blocker = project / ".autoresearch"
    blocker.write_text("not a directory\n", encoding="utf-8")

    with pytest.raises(BootstrapError) as captured:
        bootstrap_reproflow(project, repo_url=upstream.as_uri(), ref="main")

    assert captured.value.code == "CONTROL_ARTIFACT_BLOCKED"
    assert readme.read_text(encoding="utf-8") == "# User project\n"
    assert blocker.read_text(encoding="utf-8") == "not a directory\n"
    assert sorted(path.name for path in project.iterdir()) == [
        ".autoresearch",
        "README.md",
    ]


def test_control_artifact_failure_rolls_back_imported_code(
    tmp_path: Path,
    reproflow_repo: tuple[Path, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upstream, _ = reproflow_repo
    project = tmp_path / "artifact-failure"
    project.mkdir()
    readme = project / "README.md"
    readme.write_text("# User project\n", encoding="utf-8")

    def fail_artifact_write(*args: object, **kwargs: object) -> dict[str, bool]:
        raise OSError("simulated artifact failure")

    monkeypatch.setattr(
        bootstrap_module,
        "_write_bootstrap_artifacts",
        fail_artifact_write,
    )
    with pytest.raises(OSError, match="simulated artifact failure"):
        bootstrap_reproflow(project, repo_url=upstream.as_uri(), ref="main")

    assert readme.read_text(encoding="utf-8") == "# User project\n"
    assert sorted(path.name for path in project.iterdir()) == ["README.md"]


def test_repeated_bootstrap_adopts_recorded_import(
    tmp_path: Path,
    reproflow_repo: tuple[Path, str],
) -> None:
    upstream, commit = reproflow_repo
    project = tmp_path / "repeat"
    project.mkdir()
    (project / "README.md").write_text("# User project\n", encoding="utf-8")
    first = bootstrap_reproflow(project, repo_url=upstream.as_uri(), ref="main")
    original_state = json.loads(
        (project / ".autoresearch/codebase_bootstrap.json").read_text(
            encoding="utf-8"
        )
    )
    second = bootstrap_reproflow(project, repo_url=upstream.as_uri(), ref="main")

    assert first["source"]["resolved_commit"] == commit
    assert second["action"] == "ADOPT_REPROFLOW"
    state = json.loads(
        (project / ".autoresearch/codebase_bootstrap.json").read_text(
            encoding="utf-8"
        )
    )
    assert state["source"]["resolved_commit"] == commit
    assert state["bootstrap_mode"] == original_state["bootstrap_mode"]
    assert state["created_at"] == original_state["created_at"]
    assert second["artifacts"]["state_created"] is False


def test_unversioned_existing_reproflow_is_adopted_without_clone(
    tmp_path: Path,
    reproflow_repo: tuple[Path, str],
) -> None:
    upstream, _ = reproflow_repo
    project = tmp_path / "manual-copy"
    shutil.copytree(upstream, project, ignore=shutil.ignore_patterns(".git"))

    result = bootstrap_reproflow(project)

    assert result["action"] == "ADOPT_REPROFLOW"
    assert result["source"]["resolved_commit"] == "UNVERSIONED"
    assert (project / "CODEBASE_PROFILE.md").is_file()
    assert validate_codebase(project)["accepted"] is True


def test_validate_rejects_missing_or_malformed_bootstrap_provenance(
    tmp_path: Path,
    reproflow_repo: tuple[Path, str],
) -> None:
    upstream, _ = reproflow_repo
    project = tmp_path / "invalid-provenance"
    project.mkdir()
    bootstrap_reproflow(project, repo_url=upstream.as_uri(), ref="main")
    state_path = project / ".autoresearch/codebase_bootstrap.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["source"] = {
        "repository": "",
        "requested_ref": "",
        "resolved_commit": "not-a-git-commit",
    }
    state_path.write_text(json.dumps(state), encoding="utf-8")

    result = validate_codebase(project)

    assert result["accepted"] is False
    assert "Bootstrap state is missing source.repository." in result["violations"]
    assert "Bootstrap state is missing source.requested_ref." in result["violations"]
    assert any(
        "40- or 64-character hex Git commit" in violation
        for violation in result["violations"]
    )


def test_validate_direct_clone_compares_recorded_commit_with_head(
    tmp_path: Path,
    reproflow_repo: tuple[Path, str],
) -> None:
    upstream, _ = reproflow_repo
    project = tmp_path / "head-mismatch"
    project.mkdir()
    bootstrap_reproflow(project, repo_url=upstream.as_uri(), ref="main")
    _git(
        project,
        "-c",
        "user.name=AutoResearch Test",
        "-c",
        "user.email=autoresearch@example.invalid",
        "commit",
        "--allow-empty",
        "-m",
        "local mutation",
    )

    result = validate_codebase(project)

    assert result["accepted"] is False
    assert any(
        "does not match direct-clone Git HEAD" in violation
        for violation in result["violations"]
    )


def test_cli_emits_machine_readable_json(
    tmp_path: Path,
    reproflow_repo: tuple[Path, str],
) -> None:
    upstream, _ = reproflow_repo
    project = tmp_path / "cli-project"
    project.mkdir()
    cli = SCRIPT_ROOT / "bootstrap_codebase.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(cli),
            "--project-root",
            str(project),
            "bootstrap",
            "--repo-url",
            upstream.as_uri(),
            "--ref",
            "main",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert payload["accepted"] is True
    assert payload["codebase_status"] == "REPROFLOW_PRESENT"
