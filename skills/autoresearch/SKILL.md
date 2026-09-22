---
name: autoresearch
description: Run rigorous end-to-end autonomous ML and AI research after a user provides a dataset, target, and research budget. Use when AutoResearch must inspect or safely bootstrap a missing codebase with ReproFlow, align and freeze the research brief, then independently analyze literature, reproduce methods, run and repair experiments, promote research bases, and continue until the performance target is reached or the preregistered budget is exhausted, while remaining reproducible and avoiding pseudo-innovation.
---

# AutoResearch

Use this project-local skill when the user wants to provide a dataset and research target, complete one startup alignment, and then delegate the entire research process to AI. After the Research Brief is frozen, the AI runs the evidence-producing research loop without intermediate human approval except at the contract's narrowly defined `HUMAN_REVIEW_REQUIRED` gates, until it reaches the target or exhausts the preregistered budget. It covers research topic selection and literature mechanisms, but it does not cover writing the final paper.

## Mandatory First Read

Read [references/research_contract.md](references/research_contract.md) before planning or running any experiment. It is the only Markdown resource marked `activation.level: ALWAYS`. Together with this `SKILL.md`, it forms the complete always-on instruction surface.

For a visual map of the complete lifecycle, open [workflow.zh.html](workflow.zh.html) or [workflow.en.html](workflow.en.html). The two pages are synchronized navigation and package-maturity views; they help route the workflow but do not override the Research Contract.

If this skill conflicts with a project-specific Benchmark or an explicit user decision, stop and surface the conflict. Never silently rewrite the Benchmark to accommodate a candidate.

Before the first execution, browse [`examples/golden-run/`](examples/golden-run/) to understand the expected artifact shapes.

## Activation Router

At every transition:

1. infer exactly one current Phase from the frozen contracts and project artifacts;
2. consider only `PHASE` documents whose `activation.phases` includes that Phase;
3. among those documents, read only files whose `read_when` matches the immediate action;
4. read `ON_DEMAND` files only while generating, updating, or validating their artifact;
5. complete the current action and its exit checks before selecting the next Phase.

| Phase | Immediate purpose | Primary resource |
|---|---|---|
| `BOOTSTRAP` | inspect or bootstrap code; inspect data; freeze Brief, Benchmark, and initial anchors | [governance_and_autonomy.md](references/governance_and_autonomy.md) |
| `LITERATURE_RESEARCH` | run a question-driven search and recover transferable mechanisms | [paper_reproduction_and_innovation.md](references/paper_reproduction_and_innovation.md) |
| `CANDIDATE_DESIGN` | create and review one-hypothesis candidates | [candidate_priority_rules.md](references/candidate_priority_rules.md) |
| `EXPERIMENT_EXECUTION` | preregister, run, monitor, and close one experiment | [experiment_playbook.md](references/experiment_playbook.md) |
| `RESULT_ROUTING` | update roles, route the result, refresh Frontier, and select one next action | [research_graph_controller.md](prompts/research_graph_controller.md) |
| `STAGE_REFLECTION` | perform first-principles reflection and route review | [stage_reflection.md](prompts/stage_reflection.md) |
| `TERMINATION` | produce the final reached/not-reached handoff | [governance_and_autonomy.md](references/governance_and_autonomy.md) |
| `HUMAN_REVIEW` | freeze work for one of the three approved suspension reasons | [governance_and_autonomy.md](references/governance_and_autonomy.md) |

At `BOOTSTRAP_FROZEN`, `LITERATURE_COMPLETED`, `CANDIDATES_READY`, `EXPERIMENT_FINISHED`, or `STAGE_SUMMARY_COMPLETED`, read and execute [research_graph_controller.md](prompts/research_graph_controller.md). Do not keep it loaded while an experiment is merely running.

## Codebase Bootstrap Boundary

At the start of a new workspace, before dataset profiling, run:

```bash
python3 <skill>/scripts/bootstrap_codebase.py \
  --project-root <research-project> inspect
```

- `REPROFLOW_PRESENT`: adopt it and validate its recorded code root.
- `EXISTING_CODE`: never clone or overwrite; create `CODEBASE_PROFILE.md` from [codebase_profile.md](templates/codebase_profile.md) and map the existing entrypoints.
- `NO_CODE`: run the same script with `bootstrap`. This automatically imports `haibarazz/ReproFlow`, records the resolved commit, and creates the Codebase Profile without another user approval.

Read [reproflow_code_contract.md](references/reproflow_code_contract.md) only while inspecting, bootstrapping, validating, or modifying the execution codebase. Codebase bootstrap precedes Graph initialization and never creates experimental evidence. Never treat a non-empty directory as proof that runnable project code exists.

## Runtime Boundary

Use [scripts/autoresearch_runtime.py](scripts/autoresearch_runtime.py) for every Graph or Experiment lifecycle mutation. Read [runtime_api.md](references/runtime_api.md) only when constructing or correcting a Runtime request.

```text
LLM research judgment
→ structured request
→ init / inspect / propose / start-run / finish-run / validate
→ accepted state or explicit violations
→ one next research action
```

- Begin every decision point and every crash recovery with `inspect`; resume only from its machine-owned `current_phase`, `last_trigger`, and `active_run`. Use `validate` after recovery, before handoff, or when artifacts disagree.
- Submit Literature, Candidate, Repair, Merge, Frontier, branch, role and Stage Summary changes through `propose`.
- Use `start-run` before launching a trainer. For every formal run, preregister the resolved config, metrics JSON, artifact manifest, and trainer-log paths; any positive `planned_max_cost` uses the unit frozen in the Brief. Use `finish-run` only after those artifacts exist; Runtime, not the LLM, reads the authoritative metrics before any scientific state changes.
- Never directly edit `EXPERIMENT_GRAPH.json`, `.autoresearch/runtime_state.json`, `EXPERIMENT_GRAPH.html`, or attempt boundary events.
- Never edit the `## Runtime Record` section of any Experiment Card; append research judgment only under `## Research Notes`.
- A rejected proposal is a constraint result. Follow `violations` and `allowed_next_actions`; do not bypass it by editing canonical files.

## Non-Negotiable Research Loop

For each Candidate, enforce:

```text
提出假设 → 预登记预测与证伪条件 → 修改 → 运行 → 指标与机制判断 → 保留/回滚/修复
```

- For ordinary experiments, classify the change relative to the current Research Base. Inside a Paper Repair Cycle, classify the local change relative to the Experimental Parent, while project value and promotion remain relative to the current Research Base.
- Change one primary hypothesis at a time.
- Reproduce useful paper methods on the target project dataset before calling downstream changes novel.
- Prefer component-level reproduction and replacement over branch accumulation.
- Keep the Anchor Baseline, Research Base, and Champion as distinct roles.
- Preserve failures and technical failures as different evidence classes.
- Do not promote a model solely because it beats a failed Experimental Parent.

## Resource Discipline

- `PHASE` means eligible in that Phase, not mandatory to load.
- Templates, record schemas, detailed rubrics, and structural specifications remain `ON_DEMAND`.
- Do not load raw trainer logs unless a specific diagnosis requires them.
- JSON Schema and Python enforce deterministic structure and state; Prompts and References remain authoritative for research judgment.

## Output Boundary

This skill may initialize and maintain project research artifacts, experiment records, literature and mechanism notes, candidate decisions, and stage summaries. It does not draft manuscript sections or claim publication novelty without literature evidence.

The autonomous research task has exactly two research-level terminal outcomes:

- `TARGET_REACHED`: the frozen performance target is achieved under the Benchmark and hard constraints.
- `TARGET_NOT_REACHED`: the preregistered research budget is exhausted before the target is achieved.

Intermediate experimental failures, paper-route failures, temporary lack of improvement, and ordinary technical failures must be repaired or routed around within the remaining budget; they are not additional research terminal outcomes.

`HUMAN_REVIEW_REQUIRED` is a temporary suspension state, not a terminal outcome. It is allowed only for fundamental data or evaluation invalidity, an external infrastructure or access blocker that remains after one bounded Recovery Cycle, or an explicit user request to pause or materially change a frozen contract.
