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

| Name | Type | Version | Source | License | Local changes |
| --- | --- | --- | --- | --- | --- |
| `intent-aligner` | Codex standalone skill with `agents/openai.yaml` | Import snapshot `2026-09-21` | Local Codex skill at import time | Not declared in the imported skill | None at import time |
| `auto-exp` | Codex standalone skill with experiment references | Import snapshot `2026-09-21` | `/Users/Zhuanz/Documents/code/互联网医院/auto-exp/skills/auto-exp` | Not declared in the imported skill | None at import time |
| `academic-paper-polisher` | Codex standalone skill with UI metadata, writing references, scripts, and venue templates | Local build `2026-09-21` | `/Users/Zhuanz/.codex/skills/academic-paper-polisher` | No top-level license declared; bundled reference skills retain their own license metadata | None at import time |

The `academic-paper-polisher` source tree was copied without modification. Its
93 files match the supplied distributable archive at
[`dist/academic-paper-polisher.skill`](../dist/academic-paper-polisher.skill).
The archive SHA-256 is
`f80dfaeb1cf6b48407daa1c720fb0f10687dc919348cef2675b8b111925b1938`.

Add standalone skills only when they are not owned by a plugin already present
in this repository.

## Naming and provenance rules

- Use lowercase hyphenated names for new skills and plugins.
- Preserve upstream licenses and attribution.
- Record the exact upstream version or commit whenever available.
- Clearly distinguish an unchanged vendored bundle from a locally adapted one.
