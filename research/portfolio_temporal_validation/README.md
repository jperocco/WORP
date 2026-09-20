# Chronological portfolio-rule validation

Completed the authorized next test across the fixed 18 league-season manifest (2023–2025), 1QB/Superflex/2TE cases, league-native scoring, and bench capacities five and twelve. The engine is unchanged.

## Frozen procedure

Use the preceding three weeks to rank profiles and the existing rank-block sampling model. Three seeds, 256 simulated rosters per composition. For W8–11, choose counts from W4–7 only; for W12–15, choose from W4–7 and W8–11. Choose the completely supported composition minimizing the largest training opportunity gap, then mean training gap, then positional-count lexical order for deterministic ties. Test scores never select the composition. If the selected composition loses profile support at test time, record failure; never select a replacement using test outcomes.

`protocol.json` was written before this run's calculations. Some seasons/windows were already examined during development, so this is retrospective chronological validation of the implementation, **not a pristine independent holdout or prospective validation**. The prior-owned pool, short-history rank blocks, hypothetical availability, and hindsight legal-lineup ceiling remain modeling assumptions. Scoring context is historical realized native WoRP, not a forecast of future replacement/scoring distributions. Acquisition costs and manual lineup capture are not modeled.

## Coverage

72 planned league-season/bench/test-window cases:

- 69 evaluated (95.83% execution coverage, not an accuracy or success rate).
- Two have insufficient training profile supply: 2025 league 1180224010881282048, 14T 1QB, capacity 21. This league's actual active capacity is 19; the twelve-bench scenario is hypothetical and cannot be filled under the sampled profile supply.
- One chosen composition loses supply: 2023 league 918960870980501504, ten-team SF/1TE, capacity 22, W8–11. The training choice 4QB/6RB/8WR/4TE is recorded without a future-informed replacement.

All 69 evaluated cases have the planned complete training windows and seeds. Missing cases remain in `fold_results.csv`; aggregate performance tables cover evaluable cases only and must not hide coverage failures.

## Future-window opportunity gaps

Gap is the difference between the best hindsight composition in each test sample and the composition chosen from earlier windows. Units are four-week sums of positive weekly WoRP opportunity, **not observed wins or joint win probabilities**. Within each league-season, average folds; then weight league-seasons equally for each group.

| Group | Bench | Evaluated cases | Mean league gap | Worst test-window mean gap |
|---|---:|---:|---:|---:|
| 1QB | 5 | 12 | 0.072694 | 0.172961 |
| 1QB | 12 | 10 | 0.047125 | 0.135484 |
| SF/1TE | 5 | 12 | 0.063094 | 0.239202 |
| SF/1TE | 12 | 11 | 0.047755 | 0.124675 |
| SF/2TE | 5 | 12 | 0.053965 | 0.199094 |
| SF/2TE | 12 | 12 | 0.051688 | 0.184765 |

No pass/fail performance threshold was invented after seeing these numbers. This quantifies chronological opportunity loss under the model; it does not establish acceptable product regret or advantage over practical roster-building alternatives. Repeated franchise histories and seeds are not independent validation observations.

In the previously discussed 2025 12T case, selected counts change with information available at the decision date:

| Capacity | Future window | Earlier-data choice QB/RB/WR/TE |
|---|---|---|
| 15 | W8–11 | 3 / 3 / 6 / 3 |
| 15 | W12–15 | 3 / 4 / 5 / 3 |
| 22 | W8–11 | 5 / 6 / 8 / 3 |
| 22 | W12–15 | 4 / 6 / 9 / 3 |

These are test outputs, not recommendations for the user's current league. All totals match the scenario capacity exactly. They illustrate why an all-window retrospective winner cannot be deployed as if known earlier.

## Product decision

The fixed-rule chronological test is complete and results are preserved. It does not authorize automatic app quotas: supply failures remain, model-selection history prevents claiming a clean untouched test, and acquisition/capture assumptions remain. No change to Engine V0.2.1, Core V0.24/V0.32 or Lineup Economics. App remains V0.9.4.6.

## Reproduce

```bash
python3 -m unittest test_portfolio_temporal_validation test_positional_portfolio_simulation test_portfolio_sensitivity
python3 worp_portfolio_temporal_validation.py
```

Eight tests pass, including adversarial future-score changes that cannot affect training selection, missing future supply that cannot trigger reselection, and empty training data. Inputs come from the committed manifest and previously documented cache; individual run surfaces regenerate under `runs/`. Results, protocol and provenance are committed alongside this document.
