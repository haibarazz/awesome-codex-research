# Research Experiment Log · Volume 001

## E001 · Frequency-aware weighting replacement

- Hypothesis: Frequency-aware weighting improves AUC by more than 0.5 pp.
- Change: Replace only the example-weighting component.
- Result: `NORMAL_EARLY_STOP` / `SUPPORTED`; {"auc": 0.812}
- Interpretation: The weighting replacement improved AUC and supports the predicted direction.
- Decision: Promote provisionally, then pivot to the loss bottleneck.
- Evidence: `logs/runs/E001/A01.jsonl`
