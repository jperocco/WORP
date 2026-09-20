# Choose roster composition by earlier manual-policy capture — completed

## Question and fixed comparison

Does choosing positional counts from earlier simulated manual-lineup results improve later manual capture over the previously fixed perfect-opportunity composition rule?

Both rules use the same profile-selection model, available complete positional rank blocks, league scoring, 256 synthetic rosters and three seeds. Two pre-game lineup policies use prior three- or five-week mean fantasy points. All complete feasible roster compositions are evaluated within each capacity. Selection minimizes worst earlier-window regret in signed capture, then mean regret and lexical counts. W8–11 is tested after selecting from W4–7; W12–15 follows selection from W4–7/W8–11. Future data never choose counts or rescue unavailable compositions.

The incumbent is not a current product recommendation: it is the preceding research rule choosing counts by positive hindsight opportunity. This test evaluates changing the research objective, not whether either allocator beats actual dynasty managers.

## Results

- 18 league-seasons, two bench depths, two test windows and two lineup policies: **144 planned cases**.
- **131 evaluated**; four lack training profile supply and nine selected compositions lack simulated profile support later. No test-informed replacement was made.
- All 131 evaluated cases have matched incumbent results under the same lineup policy.
- **46 improvements, 71 deteriorations, 14 numerical ties** versus the incumbent. These are correlated scenario comparisons, not independent matches or an accuracy rate.
- The unweighted mean case difference is −0.020170 in four-week summed signed WoRP capture; league-weighted group results are below. These units are not actual victories or calibrated joint team win probabilities.

| Group | Bench | 3-week policy: mean league difference | 5-week policy: mean league difference |
|---|---:|---:|---:|
| 1QB | 5 | −0.037472 | −0.027222 |
| 1QB | 12 | +0.017383 | +0.002171 |
| SF/1TE | 5 | −0.034952 | −0.044042 |
| SF/1TE | 12 | −0.025321 | +0.002265 |
| SF/2TE | 5 | −0.016910 | −0.026448 |
| SF/2TE | 12 | −0.022354 | −0.014257 |

Comparisons average test windows within each league-season first, then league-seasons equally. Supports vary; see `summary.csv` for fold counts and league ranges. Every group includes league-level variation. No significance or economic-materiality threshold was invented after seeing the results.

## Decision

**Do not adopt this objective change as the roster recommender.** It shows no consistent advantage over the incumbent under the tested model and policies. This rejects the proposed deployment of this particular variant; it does not prove manual-aware optimization can never help, validate the incumbent, or invalidate the frozen Scoring Core and QB/RB optionality research.

Do not convert the newly selected counts to user-facing quotas, and do not continue tuning a threshold simply to make this variant pass. The specific authorized comparison is complete. App, engine, historical Core and Lineup Economics remain unchanged.

## Method limits retained

This is retrospective research on previously explored seasons, not untouched prospective validation. Profile holdings are hypothetical rank-block samples, acquisitions are unconstrained by market cost, and the simple manual policies omit historical injury/bye information. Missing stats assume zero fantasy points and use the engine's positional zero-point WoRP; starters' negative production counts, bench negatives do not. Composition selection uses only earlier outcomes but this does not remove development-level selection bias. No names are exposed in reports.

## Validation and reproduction

Three focused tests pass: optimized evaluation equals direct legal-lineup calculation, future results cannot select a composition, and future supply failure cannot trigger reselection. An additional numerical cross-check reproduces all 138 prior manual-policy case results with maximum absolute discrepancy 8.9e-16.

```bash
python3 -m unittest test_manual_composition
python3 worp_manual_composition_comparison.py
```

Inputs are the previously documented caches, fixed manifest and prior manual-capture results. `protocol.json`, `fold_results.csv`, `paired_comparison.csv`, `summary.csv` and code hashes are committed. Full per-league composition surfaces regenerate locally as `surface_<league_id>.csv`; they are not committed. The checks compare identical inputs, not independent predictive validity.
