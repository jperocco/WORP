# Positional portfolio sensitivity — completed modeled comparison

Same 2025 league case as the initial simulation: 12 teams, QB/2RB/3WR/TE/2FLEX/SF, exact native scoring from manifest league 1180084795436826624. Scenarios change bench capacity to five or twelve (15 or 22 total places). The actual reference league has 27 active places; these are explicit hypothetical capacities.

## What changed

Compared selection rankings based on the preceding three weeks, preceding five weeks, and season-to-date. Each uses only weeks before the evaluation window. Three random seeds (7000, 17000, 27000), 256 synthetic rosters per composition, future windows W4–7, W8–11 and W12–15. The same holdings are coupled across capacity/composition alternatives within each run.

Week 4 has only three preceding weeks, so all three lookback settings coincide. The summary removes those duplicates, leaving 21 scenario/window/seed cases per fully supported composition. These are **not 21 independent leagues or historical samples**; all reuse one league-season. Require complete support before comparing compositions.

For each case, measure the absolute opportunity gap to its own best composition. Sort fully supported compositions by the largest such gap, then mean gap. This is a transparent minimax diagnostic, not a new threshold for Scoring Core or a proof of optimality. No difference is automatically declared material.

## Results

| Active total | QB | RB | WR | TE | Mean gap | Largest gap |
|---|---:|---:|---:|---:|---:|---:|
| 15 | 3 | 4 | 5 | 3 | 0.025752 | 0.103860 |
| 22 | 4 | 7 | 8 | 3 | 0.032900 | 0.073459 |
| 22 | 4 | 6 | 9 | 3 | 0.032923 | 0.075257 |
| 22 | 4 | 6 | 8 | 4 | 0.031567 | 0.077997 |

Gaps are sums of positive weekly WoRP opportunity over four weeks. They are not actual victories, joint win probabilities, or relative percentages. The three 22-place examples differ little on these diagnostics; the mean and worst-case criteria also do not select the same row. Preserve alternatives instead of asserting a uniquely required division.

The 15-place row is the smallest worst-case-gap composition under these tested assumptions. It does not establish that every 15-place league should use it. All displayed rows fill their own capacity exactly. Independently taking their positional extrema would not produce an approved roster.

## Interpretation and boundaries

This step completes the initial ranking-window/sampling sensitivity check. It provides numerical candidate compositions and their trade-offs in this one modeled format, not a deployed full-roster recommendation. The original rank-block selection policy, hypothetical acquisition availability, historical-only evaluation, and hindsight optimal lineup objective remain. The selection family itself is still restricted: changing only its lookback is not testing all plausible roster-building policies.

A composition selected after evaluating these windows has not been validated prospectively. Sampling more rosters does not add independent historical seasons. No published Core envelope, engine calculation or app behavior is changed. Existing QB/RB low-use optionality evidence is not overwritten by this different whole-roster experiment.

## Reproduce

```bash
python3 -m unittest test_positional_portfolio_simulation test_portfolio_sensitivity
python3 worp_portfolio_sensitivity.py
```

Inputs are the prior multi-league cache and fixed manifest. `all_scenarios.csv` retains all runs, including duplicated early lookbacks for audit; `robustness_surface.csv` is deduplicated and labels full support; `shortlist.csv` contains five examples per capacity, not five validated recommendations. The runner regenerates individual run folders. Five tests pass, including duplicate-case handling and exclusion of incomplete support. `provenance.json` records code hashes and execution settings.
