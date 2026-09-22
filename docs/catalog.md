# Capability catalog

## Plugins

| Name | Type | Version | Source | License | Local changes |
| --- | --- | --- | --- | --- | --- |
| `autodl-remote` | Codex plugin with two skills and an MCP server | `0.9.0+codex.20260715093031` | [haibarazz/AutoDL-Remote](https://github.com/haibarazz/AutoDL-Remote) | MIT | None at import time |

The AutoDL Remote bundle was copied from the installed Codex plugin cache as a
complete directory, preserving `.codex-plugin/plugin.json`, `.claude-plugin/`,
`.mcp.json`, the CLI wrapper, example configuration, MCP server, README, and
both bundled skills. Its two cache copies were compared before import and the
imported tree was checked with `diff -qr`.

## Standalone skills

| Name | Type | Source | Local changes |
| --- | --- | --- | --- |
| `intent-aligner` | Codex standalone skill with `agents/openai.yaml` | Local Codex skill at import time | None at import time |
| `auto-exp` | Codex standalone skill with experiment references | `/Users/Zhuanz/Documents/code/互联网医院/auto-exp/skills/auto-exp` | None at import time |

Add standalone skills only when they are not owned by a plugin already present
in this repository.

## Naming and provenance rules

- Use lowercase hyphenated names for new skills and plugins.
- Preserve upstream licenses and attribution.
- Record the exact upstream version or commit whenever available.
- Clearly distinguish an unchanged vendored bundle from a locally adapted one.
