#!/usr/bin/env python3
"""Validate the local Codex skills/plugin catalog without external services."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(errors, f"{path.relative_to(ROOT)}: invalid JSON ({exc})")
        return None


def validate_skill(skill_dir: Path, errors: list[str]) -> None:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        fail(errors, f"{skill_dir.relative_to(ROOT)}: missing SKILL.md")
        return
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(errors, f"{skill_file.relative_to(ROOT)}: missing YAML frontmatter")
        return
    end = text.find("\n---", 4)
    if end == -1:
        fail(errors, f"{skill_file.relative_to(ROOT)}: unterminated YAML frontmatter")
        return
    frontmatter = text[4:end]
    fields = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name or not description:
        fail(errors, f"{skill_file.relative_to(ROOT)}: name and description are required")
    if name != skill_dir.name:
        fail(errors, f"{skill_file.relative_to(ROOT)}: name {name!r} does not match directory")


def validate_plugin(plugin_dir: Path, errors: list[str]) -> None:
    manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
    manifest = load_json(manifest_path, errors)
    if not isinstance(manifest, dict):
        return
    name = manifest.get("name")
    if name != plugin_dir.name:
        fail(errors, f"{manifest_path.relative_to(ROOT)}: name does not match directory")
    if not manifest.get("version") or not manifest.get("description"):
        fail(errors, f"{manifest_path.relative_to(ROOT)}: version and description are required")
    skills_root = plugin_dir / "skills"
    if manifest.get("skills") and not skills_root.is_dir():
        fail(errors, f"{plugin_dir.relative_to(ROOT)}: manifest declares skills/ but it is missing")
    if skills_root.is_dir():
        for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            validate_skill(skill_dir, errors)
    mcp_path = plugin_dir / ".mcp.json"
    if manifest.get("mcpServers") and not mcp_path.is_file():
        fail(errors, f"{plugin_dir.relative_to(ROOT)}: manifest declares .mcp.json but it is missing")
    if mcp_path.is_file():
        load_json(mcp_path, errors)


def main() -> int:
    errors: list[str] = []
    marketplace_path = ROOT / ".agents" / "plugins" / "marketplace.json"
    marketplace = load_json(marketplace_path, errors)
    if isinstance(marketplace, dict):
        for entry in marketplace.get("plugins", []):
            name = entry.get("name") if isinstance(entry, dict) else None
            source = entry.get("source", {}) if isinstance(entry, dict) else {}
            path = source.get("path") if isinstance(source, dict) else None
            if not name or not path:
                fail(errors, f"{marketplace_path.relative_to(ROOT)}: malformed plugin entry")
                continue
            plugin_dir = (marketplace_path.parent.parent.parent / path).resolve()
            if not plugin_dir.is_dir():
                fail(errors, f"{marketplace_path.relative_to(ROOT)}: missing plugin path {path}")
            elif plugin_dir.name != name:
                fail(errors, f"{marketplace_path.relative_to(ROOT)}: entry name/path mismatch")
    plugins_root = ROOT / "plugins"
    for plugin_dir in sorted(path for path in plugins_root.iterdir() if path.is_dir()):
        validate_plugin(plugin_dir, errors)
    for skill_dir in sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir()):
        validate_skill(skill_dir, errors)
    if errors:
        print("Repository validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

