#!/usr/bin/env python3
"""Create and validate a minimal, versioned Markdown paper log."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ENTRY_RE = re.compile(r"^PAPER-(\d{4})-v(\d{3})\.md$")
KINDS = ("idea", "decision", "writing", "meeting", "checkpoint", "other")


def ensure_root(root: Path) -> None:
    (root / "entries").mkdir(parents=True, exist_ok=True)
    index = root / "index.md"
    if not index.exists():
        index.write_text("# Paper log\n\n| Record | Date | Kind | Title | Current |\n|---|---|---|---|---|\n", encoding="utf-8")


def records(root: Path) -> list[tuple[int, int, Path]]:
    found = []
    for path in (root / "entries").glob("PAPER-*-v*.md"):
        match = ENTRY_RE.match(path.name)
        if match:
            found.append((int(match.group(1)), int(match.group(2)), path))
    return sorted(found)


def next_record_id(root: Path) -> int:
    existing = records(root)
    return max((number for number, _, _ in existing), default=0) + 1


def write_entry(path: Path, record_id: str, version: int, args: argparse.Namespace) -> None:
    related = args.related.strip() if args.related else "None recorded"
    text = f"""# {record_id} v{version:03d} — {args.title.strip()}

- Date: {date.today().isoformat()}
- Kind: {args.kind}
- Ownership: {args.ownership.strip()}
- Related files or sources: {related}

## What changed

{args.changed.strip()}

## Why it matters

{args.matters.strip()}

## Basis

{args.basis.strip()}

## Open question or next step

{args.next_step.strip()}
"""
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text)


def add(root: Path, args: argparse.Namespace) -> Path:
    ensure_root(root)
    number = next_record_id(root)
    record_id = f"PAPER-{number:04d}"
    path = root / "entries" / f"{record_id}-v001.md"
    write_entry(path, record_id, 1, args)
    rebuild(root)
    return path


def revise(root: Path, args: argparse.Namespace) -> Path:
    ensure_root(root)
    match = re.fullmatch(r"PAPER-(\d{4})", args.record_id)
    if not match:
        raise SystemExit("record ID must look like PAPER-0001")
    number = int(match.group(1))
    versions = [(version, path) for n, version, path in records(root) if n == number]
    if not versions:
        raise SystemExit(f"record not found: {args.record_id}")
    version = max(v for v, _ in versions) + 1
    path = root / "entries" / f"{args.record_id}-v{version:03d}.md"
    write_entry(path, args.record_id, version, args)
    rebuild(root)
    return path


def field(text: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}: (.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else "MISSING"


def table_cell(value: str) -> str:
    return value.replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def rebuild(root: Path) -> None:
    ensure_root(root)
    all_records = records(root)
    latest = {}
    for number, version, path in all_records:
        latest[number] = max(version, latest.get(number, 0))
    rows = []
    for number, version, path in all_records:
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].split(" — ", 1)[-1]
        current = "yes" if version == latest[number] else "superseded"
        rows.append(
            f"| [{path.stem}](entries/{path.name}) | {table_cell(field(text, 'Date'))} | "
            f"{table_cell(field(text, 'Kind'))} | {table_cell(title)} | {current} |"
        )
    body = "# Paper log\n\n| Record | Date | Kind | Title | Current |\n|---|---|---|---|---|\n"
    (root / "index.md").write_text(body + "\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")


def validate(root: Path) -> int:
    problems = []
    if not (root / "index.md").is_file():
        problems.append("missing index.md")
    if not (root / "entries").is_dir():
        problems.append("missing or not a directory: entries")
    for _, _, path in records(root):
        text = path.read_text(encoding="utf-8")
        for heading in ("## What changed", "## Why it matters", "## Basis", "## Open question or next step"):
            if heading not in text:
                problems.append(f"{path.name}: missing {heading}")
    for problem in problems:
        print(f"ERROR: {problem}")
    if not problems:
        print(f"OK: {len(records(root))} paper-log version(s) validated")
    return 1 if problems else 0


def content_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", required=True)
    parser.add_argument("--kind", choices=KINDS, required=True)
    parser.add_argument("--ownership", required=True)
    parser.add_argument("--changed", required=True)
    parser.add_argument("--matters", required=True)
    parser.add_argument("--basis", required=True)
    parser.add_argument("--next-step", required=True)
    parser.add_argument("--related", default="")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("research-records/paper-log"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    content_args(sub.add_parser("add"))
    revise_parser = sub.add_parser("revise")
    revise_parser.add_argument("record_id")
    content_args(revise_parser)
    sub.add_parser("rebuild")
    sub.add_parser("validate")
    args = parser.parse_args()
    if args.command == "init":
        ensure_root(args.root)
        print(args.root)
    elif args.command == "add":
        print(add(args.root, args))
    elif args.command == "revise":
        print(revise(args.root, args))
    elif args.command == "rebuild":
        rebuild(args.root)
        print(args.root / "index.md")
    else:
        return validate(args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
