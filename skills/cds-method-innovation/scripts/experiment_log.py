#!/usr/bin/env python3
"""Create and validate a minimal backend-neutral experiment log."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

EXP_RE = re.compile(r"^EXP-(\d{4})$")
RUN_RE = re.compile(r"^RUN-(\d{4})\.md$")
OUTCOMES = ("completed", "failed", "null", "abandoned", "partial")


def ensure_root(root: Path) -> None:
    (root / "experiments").mkdir(parents=True, exist_ok=True)
    if not (root / "index.md").exists():
        (root / "index.md").write_text("# Experiment log\n\n| Experiment | Runs | Question |\n|---|---:|---|\n", encoding="utf-8")


def experiment_dirs(root: Path) -> list[Path]:
    return sorted(path for path in (root / "experiments").glob("EXP-*") if path.is_dir() and EXP_RE.match(path.name))


def next_exp(root: Path) -> str:
    numbers = [int(EXP_RE.match(path.name).group(1)) for path in experiment_dirs(root)]
    return f"EXP-{max(numbers, default=0) + 1:04d}"


def all_runs(root: Path) -> list[Path]:
    return sorted(path for path in (root / "experiments").glob("EXP-*/runs/RUN-*.md") if RUN_RE.match(path.name))


def next_run(root: Path) -> str:
    numbers = [int(RUN_RE.match(path.name).group(1)) for path in all_runs(root)]
    return f"RUN-{max(numbers, default=0) + 1:04d}"


def new_experiment(root: Path, args: argparse.Namespace) -> Path:
    ensure_root(root)
    exp_id = next_exp(root)
    folder = root / "experiments" / exp_id
    (folder / "runs").mkdir(parents=True)
    text = f"""# {exp_id} — {args.title.strip()}

- Created: {date.today().isoformat()}
- Question or hypothesis: {args.question.strip()}
- Comparison: {args.comparison.strip()}
- Primary estimand or metric: {args.primary_metric.strip()}
- Decision logic: {args.decision_logic.strip()}

## Constraints or threats

{args.constraints.strip()}
"""
    (folder / "overview.md").write_text(text, encoding="utf-8")
    rebuild(root)
    return folder / "overview.md"


def add_run(root: Path, args: argparse.Namespace) -> Path:
    ensure_root(root)
    exp_dir = root / "experiments" / args.experiment
    if not (exp_dir / "overview.md").is_file():
        raise SystemExit(f"experiment not found: {args.experiment}")
    (exp_dir / "runs").mkdir(exist_ok=True)
    run_id = next_run(root)
    path = exp_dir / "runs" / f"{run_id}.md"
    text = f"""# {run_id} — {args.title.strip()}

- Experiment: {args.experiment}
- Date: {date.today().isoformat()}
- Outcome: {args.outcome}
- Execution location: {args.execution.strip() or 'Not recorded'}
- External run or job ID: {args.external_id.strip() or 'None'}
- Artifact paths: {args.artifacts.strip() or 'None recorded'}

## What changed

{args.changed.strip()}

## Data, sample, or split

{args.data.strip()}

## Configuration or specification

{args.configuration.strip()}

## Observed results

{args.results.strip()}

## Interpretation and limitations

{args.interpretation.strip()}

## Next step

{args.next_step.strip()}
"""
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text)
    rebuild(root)
    return path


def overview_question(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^- Question or hypothesis: (.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else "MISSING"


def table_cell(value: str) -> str:
    return value.replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def rebuild(root: Path) -> None:
    ensure_root(root)
    rows = []
    for exp_dir in experiment_dirs(root):
        overview = exp_dir / "overview.md"
        question = overview_question(overview) if overview.exists() else "MISSING"
        count = len(list((exp_dir / "runs").glob("RUN-*.md"))) if (exp_dir / "runs").exists() else 0
        rows.append(f"| [{exp_dir.name}](experiments/{exp_dir.name}/overview.md) | {count} | {table_cell(question)} |")
    body = "# Experiment log\n\n| Experiment | Runs | Question |\n|---|---:|---|\n"
    (root / "index.md").write_text(body + "\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")


def validate(root: Path) -> int:
    problems = []
    seen_runs = set()
    if not (root / "index.md").is_file():
        problems.append("missing index.md")
    if not (root / "experiments").is_dir():
        problems.append("missing or not a directory: experiments")
    for exp_dir in experiment_dirs(root):
        overview = exp_dir / "overview.md"
        if not overview.is_file():
            problems.append(f"{exp_dir.name}: missing overview.md")
        if not (exp_dir / "runs").is_dir():
            problems.append(f"{exp_dir.name}: missing or not a directory: runs")
        for path in (exp_dir / "runs").glob("RUN-*.md") if (exp_dir / "runs").exists() else []:
            if path.name in seen_runs:
                problems.append(f"duplicate run ID: {path.name}")
            seen_runs.add(path.name)
            text = path.read_text(encoding="utf-8")
            for heading in ("## What changed", "## Data, sample, or split", "## Configuration or specification", "## Observed results", "## Interpretation and limitations", "## Next step"):
                if heading not in text:
                    problems.append(f"{path.name}: missing {heading}")
    for problem in problems:
        print(f"ERROR: {problem}")
    if not problems:
        print(f"OK: {len(experiment_dirs(root))} experiment(s), {len(seen_runs)} run(s) validated")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("research-records/experiment-log"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    exp = sub.add_parser("new-experiment")
    for flag in ("title", "question", "comparison", "primary_metric", "decision_logic", "constraints"):
        exp.add_argument(f"--{flag.replace('_', '-')}", dest=flag, required=True)
    run = sub.add_parser("add-run")
    run.add_argument("experiment")
    run.add_argument("--title", required=True)
    run.add_argument("--outcome", choices=OUTCOMES, required=True)
    for flag in ("changed", "data", "configuration", "results", "interpretation", "next_step"):
        run.add_argument(f"--{flag.replace('_', '-')}", dest=flag, required=True)
    run.add_argument("--execution", default="")
    run.add_argument("--external-id", default="")
    run.add_argument("--artifacts", default="")
    sub.add_parser("rebuild")
    sub.add_parser("validate")
    args = parser.parse_args()
    if args.command == "init":
        ensure_root(args.root); print(args.root)
    elif args.command == "new-experiment":
        print(new_experiment(args.root, args))
    elif args.command == "add-run":
        print(add_run(args.root, args))
    elif args.command == "rebuild":
        rebuild(args.root); print(args.root / "index.md")
    else:
        return validate(args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
