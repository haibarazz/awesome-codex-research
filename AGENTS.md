# Repository instructions

## Scope

This repository is a personal catalog and packaging workspace for Codex-based
research workflows. It may contain both standalone Agent Skills and installable
Codex plugins.

## Organization

- Put standalone skills under `skills/<skill-name>/` with a required `SKILL.md`.
- Put bundled plugins under `plugins/<plugin-name>/` with a required
  `.codex-plugin/plugin.json`.
- Keep plugin-local skills, MCP configuration, scripts, and assets inside the
  plugin that owns them.
- Register repo-local plugins in `.agents/plugins/marketplace.json`.
- Record upstream source, version, license, and local modifications in
  `docs/catalog.md` or a plugin-local provenance file.

## Safety

- Never commit passwords, API keys, SSH private keys, account files, or remote
  project bindings.
- Do not silently rewrite vendored upstream skills or plugins. Preserve their
  entrypoints and document any local adaptation.
- Validate manifests and skill frontmatter with `python3 scripts/validate_repository.py`
  before committing.

