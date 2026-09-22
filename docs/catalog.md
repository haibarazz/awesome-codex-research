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
| `review-comment-decomposer` | Codex standalone skill with revision planning references and a LaTeX response template | Local build `2026-09-22` | `/Users/Zhuanz/.codex/skills/review-comment-decomposer` | Mixed: local original content, MIT reference material, and a CC BY 4.0 template; see provenance | None at import time |
| `research-literature-review` | CDS literature-positioning skill with two-stream prompts and dialogue-map examples | Local build `2026-09-22` | `/Volumes/haibara/Haibara/research/research-literature-review` | Not declared in the source folder | Functional files copied unchanged; `.DS_Store` omitted |
| `autoresearch` | Autonomous ML research skill with Runtime, schemas, tests, bilingual workflow pages, and a golden run | Source commit `dee5413646a14122a6277110eda88a3fed69dec0` | `/Volumes/haibara/Haibara/research/02-autoresearch/autoresearch` | Not declared in the source folder | Test caches and Python bytecode omitted; golden-run PDF fixtures repaired; one machine-specific corpus path generalized |
| `cds-method-innovation` | Standalone baseline-first CDS method-innovation workflow with staged guidance, templates, and research-record scripts | Local build `2026-09-22` | `/Volumes/haibara/Haibara/research/cds-method-innovation` | No license declared for the assembled folder or its direct local source packages; see audit below | None at import time; all 20 source files copied unchanged |

The `academic-paper-polisher` source tree was copied without modification. Its
93 files match the supplied distributable archive at
[`dist/academic-paper-polisher.skill`](../dist/academic-paper-polisher.skill).
The archive SHA-256 is
`f80dfaeb1cf6b48407daa1c720fb0f10687dc919348cef2675b8b111925b1938`.

The `review-comment-decomposer` source tree was copied without modification.
Its provenance is recorded in
[`skills/review-comment-decomposer/references/provenance.md`](../skills/review-comment-decomposer/references/provenance.md).
The imported version contains the locally rewritten revision-planning guide and
does not contain the previously referenced unlicensed pipeline excerpt.

The `autoresearch` import preserves its fictional golden run. Its three paper
files are locally repaired, parseable one-page PDF fixtures visibly marked as
synthetic test artifacts rather than scholarly full text. A regression test
covers their PDF structure. The imported package passes its complete test suite
plus the document-routing and bilingual-workflow checks.

The `cds-method-innovation` import is self-contained and does not require the
separate source skills named in its provenance notes. Its project initializer,
paper log, and experiment log use only the Python standard library; each script
was exercised in a temporary synthetic workspace before import.

Its bundled [`sources.md`](../skills/cds-method-innovation/references/sources.md)
identifies seven direct development sources. They were local working-tree
snapshots on `2026-09-22`; repository HEAD
`dee5413646a14122a6277110eda88a3fed69dec0` is recorded only as surrounding
repository context because some source directories were modified or untracked.

| Direct development source | Local source directory | Snapshot state | Package-level license |
| --- | --- | --- | --- |
| `research-project-init` | `/Volumes/haibara/Haibara/research/lab-skills/02-research-tools/01-project-records/research-project-init/skill/research-project-init` | Modified working tree | Not declared |
| `cds-research-direction-discovery` | `/Volumes/haibara/Haibara/research/lab-skills/03-cds-baseline-first/cds-research-direction-discovery/skill/cds-research-direction-discovery` | Untracked working tree | Not declared |
| `cds-baseline-and-benchmark` | `/Volumes/haibara/Haibara/research/lab-skills/03-cds-baseline-first/cds-baseline-and-benchmark/skill/cds-baseline-and-benchmark` | Untracked working tree | Not declared |
| `cds-innovation-grill` | `/Volumes/haibara/Haibara/research/lab-skills/03-cds-baseline-first/cds-innovation-grill/skill/cds-innovation-grill` | Untracked working tree | Not declared |
| `cds-research-design` | `/Volumes/haibara/Haibara/research/lab-skills/01-research-workflow/03-research-design/cds-research-design/skill/cds-research-design` | Modified working tree | Not declared |
| `research-paper-log` | `/Volumes/haibara/Haibara/research/lab-skills/02-research-tools/01-project-records/research-paper-log/skill/research-paper-log` | Modified working tree | Not declared |
| `research-experiment-log` | `/Volumes/haibara/Haibara/research/lab-skills/02-research-tools/01-project-records/research-experiment-log/skill/research-experiment-log` | Modified working tree | Not declared |

Those development packages contain their own upstream reference collections and
license notes in the research workspace, but those collections are not runtime
dependencies and are not copied into this repository. No redistribution license
is inferred for the assembled Skill beyond what its source explicitly declares.

Add standalone skills only when they are not owned by a plugin already present
in this repository.

## Naming and provenance rules

- Use lowercase hyphenated names for new skills and plugins.
- Preserve upstream licenses and attribution.
- Record the exact upstream version or commit whenever available.
- Clearly distinguish an unchanged vendored bundle from a locally adapted one.
