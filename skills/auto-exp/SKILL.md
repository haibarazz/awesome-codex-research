---
name: auto-exp
description: Plan, execute, monitor, verify, compare, and document reproducible machine-learning experiments. Use when an AI agent is asked to design an experiment contract, implement or launch a training/evaluation run, monitor local or remote jobs, audit artifacts and metrics, maintain experiment logs or leaderboards, diagnose a failed run, or decide whether to continue, stop, retry, or archive an experiment.
---

# Auto Exp

Treat every experiment as a scientific contract followed by an auditable execution, not as an isolated training command.

## Independence

Remain execution-tool agnostic. Do not require, import, bundle, or assume any remote-execution plugin. Use whatever local or remote tools are available in the current environment after reading their own instructions. This skill defines experiment policy, lifecycle, evidence, and logging only.

Do not let tool availability change the scientific contract. Tool actions never imply permission to stop jobs, delete artifacts, overwrite results, spend additional compute, or shut down infrastructure.

## Scope Gate

Execute only the lifecycle stages required and authorized by the current request or an explicit project convention. A request to inspect, audit, monitor, compare, or diagnose is read-only unless it separately authorizes smoke runs, launches, source edits, retries, synchronization, cleanup, or shutdown.

## Reference Routing

- Read [references/ml_experiment_playbook.md](references/ml_experiment_playbook.md) before planning, launching, tuning, stopping, comparing, or reviewing experiments.
- Read [references/pre_run_checklist.md](references/pre_run_checklist.md) immediately before launching a smoke run, training run, evaluation run, or tuning sweep. Complete the checklist using concrete values rather than generic confirmations.
- Read [references/experiment_log_template.md](references/experiment_log_template.md) when creating or updating an experiment log, failure record, cleanup record, leaderboard, phase summary, or next-volume handoff.

## Core Workflow

1. **Inspect context.** Read the closest project instructions, existing experiment logs, active configs, current baseline, data release, and available execution tools. Verify mutable facts from artifacts rather than memory.
2. **Lock the contract.** State the hypothesis, change layer, single intended variable, dataset and split semantics, baseline, training protocol, selection protocol, evaluation protocol, metrics, stopping rule, output location, and authorization boundary.
3. **Run the authorized preflight.** Check paths, dependencies, sample counts, labels, leakage, truncation or shape limits, resource estimates, and output collisions. Run a smoke test only when the current request or project convention authorizes execution.
4. **Execute without drift when requested.** Make reusable code and configuration traceable in the project before execution. Launch with explicit run identity and metadata. Do not silently alter the contract after launch.
5. **Monitor proportionately.** Inspect progress, loss, learning rate, resource use, NaN/Inf, out-of-memory errors, tracebacks, disk pressure, and process state. Normal monitoring is read-only. Apply recovery only after diagnosing the complete error and preserving evidence.
6. **Verify completion.** Confirm process exit, expected row counts, metric files, predictions, histories, configs, audits, fingerprints, finite values, and declared selection/evaluation semantics. A filename alone is not proof.
7. **Record the decision.** Write settings, complete results, comparison to the fixed baseline, caveats, failure causes, and the next decision. Record `selection_exposure` and `evaluation_independence` as separate fields.
8. **Close safely.** Sync only required artifacts, preserve provenance, and perform destructive cleanup or infrastructure shutdown only with the required explicit authorization.

## Required Reasoning

- Distinguish information gain from architecture gain. When new information is activated, measure a simple integration baseline before attributing gains to a complex model.
- Distinguish fixed-epoch training, early stopping, tuning, model selection, and final evaluation. These are project choices, not universal defaults.
- Distinguish selection exposure from evaluation independence. Record `selection_exposure` as the ways a split influenced epochs, checkpoints, thresholds, hyperparameters, or go/no-go decisions; independently record `evaluation_independence` as `independent` or `non-independent`, with a reason.
- Prefer one scientifically meaningful change per comparison. If multiple changes are unavoidable, say that attribution is confounded.
- Record failed and stopped runs. An unrecorded failure will be repeated.
- Never present static checks, a smoke run, or a running process as a completed experiment.

## Stop Conditions

Stop and request user input when the next action would change the scientific contract, consume materially more resources than agreed, overwrite or delete evidence, terminate a healthy run without a preregistered rule, or require unavailable credentials or permissions.

When blocked by an implementation error, preserve the traceback and run metadata and diagnose the root cause. Make source changes or launch a retry only when the current request or project convention authorizes them. Record every authorized retry as a distinct attempt.
