#!/usr/bin/env python3
"""Initialize a minimal research-record workspace without overwriting content."""

from __future__ import annotations

import argparse
from pathlib import Path


PAPER_INDEX = "# Paper log\n\n| Record | Date | Kind | Title | Current |\n|---|---|---|---|---|\n"
EXPERIMENT_INDEX = "# Experiment log\n\n| Experiment | Runs | Question |\n|---|---:|---|\n"


def write_once(path: Path, content: str, created: list[Path], preserved: list[Path]) -> None:
    if path.exists():
        preserved.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(path)


def expected_paths(project_root: Path) -> tuple[list[Path], list[Path]]:
    records = project_root / "research-records"
    files = [
        records / "project.md",
        records / "paper-log" / "index.md",
        records / "experiment-log" / "index.md",
    ]
    directories = [
        records / "paper-log" / "entries",
        records / "experiment-log" / "experiments",
    ]
    return files, directories


def conflicts(project_root: Path) -> list[str]:
    files, directories = expected_paths(project_root)
    problems = [f"expected a regular file: {path}" for path in files if path.exists() and not path.is_file()]
    problems.extend(f"expected a directory: {path}" for path in directories if path.exists() and not path.is_dir())
    return problems


def initialize(args: argparse.Namespace) -> tuple[list[Path], list[Path]]:
    records = args.project_root / "research-records"
    created: list[Path] = []
    preserved: list[Path] = []
    project = f"""# {args.title.strip()}

- Research question: {args.question.strip()}
- Research line: {args.research_line}
- Current stage: {args.stage.strip()}
- Immediate milestone: {args.milestone.strip()}
- Known material locations: {args.locations.strip() or 'None recorded'}

## Working note

Keep this profile short. Put research history in `paper-log/` and concrete analysis
or experiment runs in `experiment-log/`.
"""
    write_once(records / "project.md", project, created, preserved)
    (records / "paper-log" / "entries").mkdir(parents=True, exist_ok=True)
    (records / "experiment-log" / "experiments").mkdir(parents=True, exist_ok=True)
    write_once(records / "paper-log" / "index.md", PAPER_INDEX, created, preserved)
    write_once(records / "experiment-log" / "index.md", EXPERIMENT_INDEX, created, preserved)
    return created, preserved


def validate(project_root: Path) -> int:
    files, directories = expected_paths(project_root)
    problems = [f"missing or not a regular file: {path}" for path in files if not path.is_file()]
    problems.extend(f"missing or not a directory: {path}" for path in directories if not path.is_dir())
    for problem in problems:
        print(f"ERROR: {problem}")
    if not problems:
        print("OK: minimal research workspace is complete")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--title")
    parser.add_argument("--question")
    parser.add_argument("--research-line", choices=("empirical", "cds", "mixed", "not-yet-decided"))
    parser.add_argument("--stage")
    parser.add_argument("--milestone")
    parser.add_argument("--locations", default="")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if args.validate:
        return validate(args.project_root)
    missing = [name for name in ("title", "question", "research_line", "stage", "milestone") if not getattr(args, name)]
    if missing:
        parser.error("initialization requires: " + ", ".join("--" + name.replace("_", "-") for name in missing))
    preflight = conflicts(args.project_root)
    if preflight:
        for problem in preflight:
            print(f"ERROR: {problem}")
        return 1
    created, preserved = initialize(args)
    for path in created:
        print(f"CREATED: {path}")
    for path in preserved:
        print(f"PRESERVED: {path}")
    return validate(args.project_root)


if __name__ == "__main__":
    raise SystemExit(main())
