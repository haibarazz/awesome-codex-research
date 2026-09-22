"""Safe filesystem operations for canonical AutoResearch artifacts."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterator

from .constants import (
    GRAPH_FILENAME,
    RUNTIME_DIRECTORY,
    RUNTIME_LOCK_FILENAME,
    RUNTIME_STATE_FILENAME,
)


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_project_root(project_root: str | Path) -> Path:
    root = Path(project_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Project root does not exist or is not a directory: {root}")
    return root


def resolve_project_path(
    root: Path,
    value: str,
    *,
    must_exist: bool = False,
    allow_directory: bool = True,
) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Artifact path must be a non-empty string")
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"Artifact path escapes project root: {value}") from error
    if must_exist and not resolved.exists():
        raise ValueError(f"Required artifact does not exist: {value}")
    if must_exist and not allow_directory and not resolved.is_file():
        raise ValueError(f"Required artifact is not a file: {value}")
    return resolved


def relative_project_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        directory_descriptor = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def atomic_write_json(path: Path, data: Any) -> None:
    atomic_write_text(path, canonical_json(data))


@contextlib.contextmanager
def project_lock(root: Path) -> Iterator[None]:
    lock_path = root / RUNTIME_DIRECTORY / RUNTIME_LOCK_FILENAME
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def graph_path(root: Path) -> Path:
    return root / GRAPH_FILENAME


def state_path(root: Path) -> Path:
    return root / RUNTIME_DIRECTORY / RUNTIME_STATE_FILENAME


def load_project(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    graph_file = graph_path(root)
    runtime_file = state_path(root)
    if not graph_file.exists() or not runtime_file.exists():
        raise FileNotFoundError(
            "AutoResearch project is not initialized; run the init command first"
        )
    return read_json(graph_file), read_json(runtime_file)


def append_jsonl_atomic(path: Path, event: dict[str, Any]) -> None:
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    line = json.dumps(event, ensure_ascii=False, sort_keys=True)
    atomic_write_text(path, f"{previous}{line}\n")
