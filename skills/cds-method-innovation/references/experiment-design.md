# Computational Research Design

## 本阶段目标

Turn a selected research question into a clear experiment plan that another researcher could inspect and run.

The goal is not to produce a long checklist. The goal is to answer three questions:

1. What exactly is the paper trying to show?
2. What experiment would distinguish that claim from the strongest rival explanation?
3. Would the comparison still be fair if the result favored the new method?

If important information is missing, ask focused questions. Do not invent datasets, compute, labels, checkpoints, licenses, or results.

If the user is still deciding what to study, say that experiment design is premature and ask them to choose the research question first.

## 1. Start from the claim

In a baseline-first workflow, begin with the selected candidate, measured baseline
results and unresolved innovation-review questions. Read those artifacts directly;
no other Skill or approval status is required. If the comparison suite has not been
run, label baseline assumptions as unverified and separate baseline establishment
from candidate validation. Do not call an unrun design a verified improvement.

Record which baseline failure motivated the candidate, the candidate's mechanism
change, and a prediction that distinguishes it from the strongest rival. A review
decision to test the idea is not proof of novelty.

Write the main claim in one sentence. Then answer:

- **Scope:** Which task, data, model class, setting, or population does it cover?
- **Strongest rival:** What else could explain the expected improvement?
- **Falsifier:** What result would make the claim fail or need narrowing?
- **Minimum evidence:** What is the smallest fair experiment that would support it?
- **Stronger evidence:** What additional result would justify a broader claim?

Use the claim type to choose the evidence:

| Claim | Minimum evidence | Stronger evidence |
| --- | --- | --- |
| Beats prior methods | Strong tuned baselines, same splits, comparable compute | Several datasets or tasks, matched tuning, uncertainty reporting |
| A mechanism causes the gain | An ablation tied to that mechanism | A diagnostic or intervention that rules out the strongest rival |
| Scales better | More than one meaningful scale under one protocol | A consistent trend with compute, memory, and failures reported |
| Is robust | A relevant stress test or out-of-domain split | Several shifts with error analysis and explicit failure boundaries |
| Is useful in practice | A task-relevant metric under a realistic constraint | Deployment-like evaluation with cost and risk analysis |
| Reproduces a prior result | A faithful implementation and fair attempt | Explains where the prior result holds, fails, or needs qualification |

Do not treat a leaderboard win as evidence for mechanism, generalization, efficiency, or real-world value unless those claims have their own experiments.

## 2. Separate planned and exploratory evidence

Before finalizing the design, ask whether anyone has already inspected outcomes, test results, or favorable slices.

If results have been seen:

1. List what was inspected and when.
2. Record which claims, metrics, thresholds, slices, hyperparameters, or stopping choices changed afterward.
3. Mark evidence as **planned**, **exploratory**, or **invalid for the stated claim**.
4. Treat any test split used for tuning or selection as consumed for confirmation.
5. Write a locked follow-up protocol using untouched data when possible. If no credible confirmation data remain, keep the conclusion exploratory.

Do not describe a decision made after seeing results as preregistered or confirmatory.
Before results are available, lock or preregister the main comparisons, exclusion rules, and analysis plan when practical.

## 3. Define the task, data, and split

Explain what the benchmark is meant to test and what it does not test.

Before results are visible, decide:

- dataset version and inclusion rules;
- train, validation, and test construction;
- the unit that must stay together across splits, such as a user, patient, source document, video, site, or time period;
- preprocessing and augmentation;
- model-selection data and the final evaluation data;
- known coverage gaps or contamination risks.

Check for duplicate examples, source-family overlap, target leakage, preprocessing leakage, retrieval leakage, and test-set tuning.

List nuisance factors such as batch, time, machine, site, or annotator. Randomize or block run order when one of them could align with the method being compared.

If related observations share a source, split at the source level. Repeated measurements from one source are not independent evidence merely because there are many rows.

Record the assignment or treatment unit, the measurement unit, and the independent analysis unit. When observations are repeated or nested within a user, patient, site, document, or annotator, respect that structure through unit-level aggregation, a matched analysis, cluster-aware uncertainty, or an appropriate multilevel model.

## 4. Choose fair baselines

Include three kinds of comparison when relevant:

1. the closest technical ancestor;
2. a strong current method;
3. a simple diagnostic control that can expose a shortcut.

Make the comparison auditable:

| Fairness question | What to record |
| --- | --- |
| Were the same data used? | Splits, preprocessing, augmentation, and external data |
| Was tuning comparable? | Search space, number of trials, early stopping, and selection metric |
| Was compute comparable? | Hardware, wall time, memory, floating-point operations (FLOPs), or another suitable budget |
| Was implementation credible? | Official code, checkpoint source, reimplementation, and library defaults |
| Was model selection fair? | Validation metric and checkpoint-selection rule |

A missing or under-tuned baseline is a limitation, not evidence that the new method is better. If a strong baseline cannot be run, state the concrete reason, such as unavailable code, task incompatibility, compute, licensing, or safety.

## 5. Design ablations that answer why

An ablation should change one meaningful factor while holding the rest fixed.

For every mechanism claim, specify:

- the component or assumption being tested;
- what remains fixed;
- what the focal mechanism predicts;
- what the strongest rival predicts;
- how each possible outcome changes the claim.

If an ablation changes architecture, data, objective, and compute together, call it a bundle comparison. It cannot isolate one mechanism.

Use compute-matched controls when extra training, parameters, data, or prompt search could explain the gain.

## 6. Add only claim-relevant robustness checks

Choose robustness tests from the actual boundary of the claim. Relevant dimensions may include:

- random seeds or repeated runs;
- datasets or domains;
- distribution shifts;
- model sizes;
- hyperparameters;
- prompt variants;
- deployment constraints;
- alternative but defensible metrics.

Do not add a large robustness grid by habit. Explain what threat each test probes.

Treat a favorable slice discovered after seeing results as exploratory, not as planned confirmation.

## 7. Plan metrics, uncertainty, and stopping

Define every headline metric before running the experiment. State what it measures, its direction, aggregation, and limitations.

Choose seeds and repeat counts from expected variability, cost, and claim risk. There is no universal seed count.

When randomness can change the conclusion, report a spread or interval rather than a single best run. Preserve and disclose every failed run. Predefine failure categories and their analysis: report method-attributable failures as a separate failure rate and include them in the task metric when that metric permits; handle infrastructure faults, corrupted inputs, and evaluator failures under a written retry or exclusion rule rather than automatically mixing them into the performance mean.

Decide in advance:

- how checkpoints are selected;
- when training stops;
- which metric controls selection;
- how paired comparisons are formed;
- how multiple headline comparisons are handled.

Never tune on the test set or choose the reported metric because it looks favorable.

## 8. Check resources, reproducibility, and responsible use

Estimate the full cost of the proposed method and all required baselines, tuning, repeats, ablations, and robustness checks.

Record enough detail for another researcher to understand the experiment:

- software and important versions;
- data and checkpoint sources;
- training and evaluation commands;
- hyperparameters and seed protocol;
- hardware, training time, inference cost, and storage;
- expected outputs and known nondeterminism;
- code and data availability.

State privacy, consent, licensing, safety, bias, or access limits when they affect what may be run or released. A justified limitation is better than pretending every artifact can be made public.

For human evaluation, conditionally record:

- the rating task, annotator instructions, recruitment or qualifications, and any blinding;
- repeated annotation, aggregation, agreement, and quality-control rules;
- consent, payment, privacy, and institutional review or ethics status when applicable.

## 9. Extra check for information-systems or design-science claims

Use this check only when the claim concerns information systems (IS), people or organizations interacting with technology, or an artifact built to solve a practical problem.

If the work claims organizational or human value, connect the technical task to the real phenomenon:

```text
real-world construct -> observable proxy or label -> computational task
-> metric -> claimed practical consequence
```

Explain where this chain is weak. A better benchmark score does not by itself prove organizational impact.

For a design-science contribution—research that builds an artifact to solve a class of problems—plan an evaluation that demonstrates utility for a real problem. “We built it and it ran” is not sufficient evidence.

## Worked example: is the objective better, or did it just use more compute?

A paper claims that a new self-supervised objective improves representation quality.

A weak experiment trains the new objective longer than the baseline and reports one favorable seed. That result cannot isolate the objective.

A stronger design does the following:

1. Hold architecture, data, preprocessing, and total pretraining compute fixed.
2. Change only the objective.
3. Tune both methods under the same budget.
4. Evaluate on the same held-out split.
5. Repeat across enough seeds to show the gain is not a lucky run.
6. Report error bars and failed runs.

If the gain disappears after compute matching, narrow the claim. The experiment may show that the full training recipe works, but not that the objective caused the improvement.

## Deliverable

Write one readable Markdown experiment plan. Use [实验方案模板](../assets/experiment-design-brief-template.md) if helpful.

The plan should contain:

1. evidence timing and planned, exploratory, or invalid labels;
2. research question and claims;
3. strongest rivals and falsifiers;
4. datasets, versions, and splits;
5. proposed method and fair baselines;
6. ablations and robustness checks;
7. metrics, seeds, uncertainty, and stopping;
8. compute and reproducibility details;
9. risks, limitations, and conclusions the experiment cannot support.

End with a short list of unresolved decisions. Do not fill missing information with guesses.

For a delegated baseline-first workflow, link any existing direction record and
record the planned comparison before execution. If no record tool or log exists,
use a comparison section in the plan; a separate record is not a prerequisite.
For discussion-only requests, return this section as a draft without writing files.
The current
coding/training tools then implement and run the plan within the requested scope;
design alone is not execution. For implementation, follow [execution-and-feedback.md](execution-and-feedback.md) within this same Skill. Record every run and failure, then return
the actual results to diagnosis or candidate review. If baseline results generated
the hypothesis, preserve their exploratory role and reserve independent evidence
for confirmation. Log selection, rejection or reframing when the results change
the direction; do not silently replace the original hypothesis.
