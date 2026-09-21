# awesome-codex-research

Personal, inspectable Codex workflows for research and machine-learning work.

This repository is designed to hold two kinds of reusable capability:

- standalone skills, each with its own `SKILL.md`;
- installable Codex plugins, which can bundle skills, MCP servers, scripts, and
  other supporting assets.

## Current contents

The first bundled plugin is `autodl-remote`. It provides a local CLI and MCP
server for controlling AutoDL or SSH-backed research machines, including
explicit file transfer, detached jobs, run metadata, fleet operations, and
optional tmux monitoring.

See [the capability catalog](docs/catalog.md) for source and provenance details.

## Repository layout

```text
.
├── .agents/plugins/marketplace.json  # repo-local Codex plugin catalog
├── plugins/                          # installable plugin bundles
├── skills/                           # future standalone skills
├── docs/                             # catalog and contributor guidance
└── scripts/                          # repository validation helpers
```

## Validate locally

```bash
python3 scripts/validate_repository.py
```

The validator checks plugin manifests, marketplace entries, skill metadata,
and JSON configuration. It does not connect to AutoDL or execute remote jobs.

## Adding a capability

Keep the original entrypoint and resource layout intact. Add a catalog entry
with the upstream repository, version, license, import date, and whether local
changes were made. Do not place credentials or machine-specific bindings in
this repository.

