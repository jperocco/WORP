# Positional roster scenarios — first modeled calculation

Authorized next step following [the Scott Connor update](../../WORP_UPDATE_SCOTT_CONNOR_2026-09-20.md). Engine V0.2.1 remains unchanged. These are synthetic positional rosters, not reconstructions of historical active rosters and not recommended quotas.

## Model

For each window, use players owned anywhere in that league in the preceding week's snapshot as the profile pool. Group by position, rank on the preceding three weeks' signed native WoRP, randomize ties, and divide into blocks the size of the league's team count. Each simulated roster samples one profile from each successive block. Increasing positional depth adds the next profile; it never swaps identities based on future outcomes. This is an explicit representative rank-band model, not a simulated draft or a market-price budget.

Enumerate all compositions within available complete positional blocks, respecting mandatory positional minima and exactly filling starting-plus-bench capacity. In each future week, find the legal lineup maximizing positive WoRP opportunity. Use identical sampled holdings across compositions, so positional competition through FLEX/SF is evaluated jointly. Sum four weekly opportunities. Evaluate three disjoint windows beginning weeks 4, 8 and 12. The historical settings and native engine outputs are those in the prior multi-league manifest/cache.

This objective is a hindsight opportunity ceiling. It is not actual manual-lineup capture, an expected-win forecast or an additive joint win probability. Rank ordering uses earlier data; choosing a composition by its reported future maximum would still be hindsight selection. The table below must not be used as a prospective recommendation.

## Results: 2025, 12 teams, 10 starters

Starting slots: QB / RB / RB / WR / WR / WR / TE / FLEX / FLEX / SF. The reference league has 27 active places; the modeled scenarios deliberately change bench depth to 5 and 12, producing capacities 15 and 22. All other league inputs are held fixed within this comparison.

Window-specific maxima with 256 sampled rosters per composition:

| Window | Total 15: QB/RB/WR/TE | Total 22: QB/RB/WR/TE |
|---|---|---|
| Weeks 4–7 | 3 / 3 / 6 / 3 | 5 / 6 / 8 / 3 |
| Weeks 8–11 | 3 / 4 / 5 / 3 | 3 / 8 / 8 / 3 |
| Weeks 12–15 | 3 / 4 / 5 / 3 | 4 / 6 / 9 / 3 |

The surface contains 109–140 feasible compositions per window/capacity. The 64-draw run is retained alongside the 256-draw sensitivity run. At week 12 the maximizing composition changes with draw count, exposing sampling sensitivity. There is no chosen universal optimum or invented equivalence threshold.

An additional 2024 case also completed with 256 draws: 12 teams, **11** starting slots, capacities 16 and 23. It has an additional FLEX compared with the 2025 case and its own scoring settings. It is a separate scenario, not a controlled year-over-year replication. Output is under `season2024/`.

## What this establishes

- Capacity changes produce complete numerical rosters; all positional counts sum exactly to the scenario capacity.
- Positional depth competes for the same legal starting vacancies.
- Weekly profile identity is retained, avoiding switching between future winners inside one roster place.
- The maximizing composition depends on window, settings and simulation sample.

## What remains unvalidated

Profile ordering from only three preceding weeks is not structural dynasty quality. Profiles may include historical reserve/taxi players and are deliberately treated as hypothetically available; no historical active membership or acquisition feasibility is asserted. Taking one player from each positional rank block gives every scenario a common selection rule, **not equal acquisition cost**. More WRs in this full-roster model is not evidence overturning prior low-use QB/RB optionality findings: the baselines and selection mechanisms differ.

The frozen Core envelope is not re-estimated or forced into these scenarios. A whole-roster scenario maximum cannot be used to overwrite it or label specific players Scoring/Non-Scoring. Best-ball-style opportunity capture is optimistic for manual lineup leagues. No app behavior changed and no quotas are deployed.

## Files and reproduction

Each run stores assumptions, all composition/window results, aggregate summaries, and window maxima. Aggregate summaries flag compositions not supported in all three windows; these cannot be compared as if support were identical. Input cache hashes are preserved by the preceding multi-league audit; this run's provenance additionally hashes its code and native input files.

```bash
python3 -m unittest test_positional_portfolio_simulation
python3 worp_positional_portfolio_simulation.py
python3 worp_positional_portfolio_simulation.py --draws 256 --out research/positional_portfolio_simulation/draws256
python3 worp_positional_portfolio_simulation.py --league-id 1045730844721270784 --draws 256 --out research/positional_portfolio_simulation/season2024
```

Four tests pass: capacity/supply, prior-data rank blocks, joint FLEX competition, and non-decreasing opportunity when adding a profile.
