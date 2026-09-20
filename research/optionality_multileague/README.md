# Joint QB/RB optionality diagnostic

This is a research diagnostic, not a deployed positional allocator. The app remains V0.9.4.6.

## Question

With the same eight or nine optionality places, what changes when one RB place is exchanged for one QB place? Each paired comparison uses the same historical roster, observation week, baseline, option pool and four-week outcome window.

## Sample and calculation

- Eighteen league-seasons selected before looking at outcomes from the user's 326 league-season inventory entries in 2023–2025. Six observations each in 1QB, Superflex with one TE, and Superflex with two or more TEs. These are broad reporting groups, not exact-format equivalence classes or independent league franchises.
- Within each season/group, select the first league by team count and league ID, then a different team count when available. This is a reproducible convenience sample, not random population sampling.
- Exact Sleeper scoring, frozen WoRP engine, 2,500 engine simulations with seed 7. Historical data from 2023–2025 only.
- Freeze ownership at the preceding week. Options must also have been held in the two preceding snapshots and have no actual or positive-WoRP hindsight lineup use in the preceding three to five weeks.
- Keep other offensive players as the common baseline. Compare random nested QB/RB subsets, 64 coupled draws, over the next four weeks. Maximum legal lineups account for FLEX and Superflex competition jointly. Draws are not independent observed rosters.
- Eight/nine-option portfolios must fit within starting-plus-bench capacity together with the baseline. Compare adjacent QB/RB splits only when both can be formed from the same owned pool.
- Report four-week positive-WoRP opportunity gain and descriptive probabilities of reaching 0.25, 0.50 or 0.75 gain. These probes are not new membership thresholds. Results are hindsight opportunities, not realized capture rates.
- Summaries give each represented league-season equal weight. Different pairs can have different support; their means cannot be ranked as an all-roster optimum.

## Limits that affect interpretation

The baseline is defined by prior use, not by a jointly validated V0.32 Scoring Core tuple. This study does not establish a full QB/RB/WR/TE roster allocation. Low-use WR/TE options are not allocated. Ownership snapshots do not separate IR/taxi availability, and prospective acquisition, retention and transaction feasibility are not modeled. Capacity is checked for the hypothetical portfolio, but historical ownership does not prove an executable active-roster policy. Windows overlap and league histories may repeat across years. Small simulation error does not fix sparse real support.

## Reproduce

From the repository root:

```bash
python3 -m unittest test_optionality_multileague
python3 worp_optionality_multileague.py --out research/optionality_multileague --cache research/optionality_multileague/cache --draws 64
```

The committed selection manifest fixes the sample on replay. To select a new sample, use a separate output directory after generating the inventory with `sleeper_user_league_discovery_v0_14.py`. Raw public Sleeper downloads and native weekly calculations are cached locally; those raw caches are not committed. A replay that downloads revised upstream data may differ.

## Completed results

All 18 league-seasons completed without reported failures: 2,544 roster-week cohorts, 500 adjacent-allocation comparisons drawn from 150 distinct roster-week cohorts. The 500 rows are not 500 independent cases. Eight-option pools fit in 217 cohorts; nine-option pools fit in 104, with overlap between those groups.

The specific exchange from two QB options to three QB options gives:

| Format group | Exchange | Paired roster-weeks | League-seasons | Seasons represented | Mean four-week opportunity delta | Change in probability of gain >=0.50 |
|---|---|---:|---:|---:|---:|---:|
| SF, one TE | 2QB+6RB → 3QB+5RB | 19 | 3 | 2 | −0.006398 | −0.379 percentage points |
| SF, two TEs | 2QB+6RB → 3QB+5RB | 36 | 5 | 3 | −0.024851 | −0.276 percentage points |
| SF, one TE | 2QB+7RB → 3QB+6RB | 9 | 2 | 2 | +0.001615 | −1.094 percentage points |
| SF, two TEs | 2QB+7RB → 3QB+6RB | 8 | 2 | 2 | +0.013545 | +2.930 percentage points |

Positive delta favors the additional QB; negative delta favors retaining the RB. Units are summed positive weekly WoRP opportunity over four weeks, not observed wins, a relative percentage improvement, or a calibrated joint team win probability. The frozen engine's individual probability differences are not additive team probabilities.

For eight options, every represented league-season in these two-QB versus three-QB comparisons favors retaining the RB on the mean opportunity measure. For nine options, signs vary between represented league-seasons, and support is much smaller. Neither comparison establishes the globally best allocation. The corresponding two-QB comparisons have no common support in the sampled 1QB cohorts.

**Decision:** the completed diagnostic supplies numerical comparisons but does not validate a full-roster quota. In particular, it cannot justify publishing 5QB/10RB/6WR/3TE or another exact default. Sparse owned-pool support and the baseline/acquisition limitations above remain material. Do not interpret tiny mean differences or their signs as a proven product recommendation.
