# Four-position marginal roster opportunity — capacity audit

## Implemented scope

The accepted article review preserves Engine V0.2.1 and introduces no product floor-zero change. This diagnostic evaluates one additional QB, RB, WR or TE on the same prior-use baseline, against legal weekly lineups. Positive weekly WoRP is an opportunity ceiling only. It is not captured production, a calibrated joint win probability, or a prospective recommendation.

The candidate is held throughout a four-week window. Each prior-owned candidate in a position is evaluated separately and given equal weight; the algorithm does not choose the future best performer each week. FLEX and Superflex competition is recomputed for each addition. Paired comparisons share the same baseline and observation window. Pair supports differ and must not be pooled into a global position ranking.

This extends the existing cached 18 league-season diagnostic to all four positions and adds a conservative capacity screen: total preceding-snapshot ownership must not exceed starting-plus-bench capacity, and the baseline plus one option must fit. Snapshots exceeding capacity are excluded rather than silently counted as active-roster evidence. Even a snapshot below capacity does not establish that each candidate was active instead of IR/taxi.

## Actual results and decision

| Group | Observed roster-weeks | Passing capacity screen |
|---|---:|---:|
| 1QB | 888 | 56 |
| SF, one TE | 792 | 16 |
| SF, two TEs | 864 | 25 |
| Total | 2,544 | 97 |

Only 97/2,544 (3.81%) pass. Of these, 94 have at least one paired positional comparison, across seven league-seasons. There are 284 pair rows, not independent observations. The 276 position/cohort marginal rows include 150 with zero mean incremental gain under the diagnostic objective. This describes the screened sample only.

The screen strongly selects on roster circumstances and is not proof that excluded rosters were illegal: their snapshots can include reserve/taxi ownership. Existing sources do not identify historical active status sufficiently to interpret the results as an executable active-roster allocation policy.

**Relevance STOP:** coverage falls below the project's 4% discussion trigger. Do not further refine comparisons or publish positional quotas from this selected subset without agreeing the decision value of resolving historical active-roster availability. This is not a conclusion that optionality is unimportant, or that QB/RB evidence was invalidated. It identifies a data-to-product translation limit.

The baseline remains prior-use based, not a validated V0.32 joint core tuple. Low-use candidate selection consults only prior ownership/usage; outcomes are retrospective. Aggregate league-season summaries weight represented league-seasons equally. Windows overlap. Full-pool availability/acquisition and manual lineup capture are unmodeled. There is no automatic recommendation or app modification.

## Files and validation

- `support.csv`: all examined cohorts and capacity eligibility, including excluded cases.
- `marginal_detail.csv`: position-specific marginal results, no player names or IDs.
- `paired_detail.csv`, `paired_league_means.csv`, `paired_summary.csv`: matched comparisons and descriptive summaries.
- `worp_optionality_four_positions.py`: calculation; inputs are the frozen selection manifest and local historical caches from `research/optionality_multileague/`. That directory's provenance hashes identify the input cache.
- Ten tests pass across the new marginal calculation and the existing joint-allocation calculation, including blocked bench production, FLEX competition, Superflex eligibility and holding the same candidate across weeks.

Run from the repository root after preparing the documented multi-league cache:

```bash
python3 -m unittest test_optionality_four_positions test_optionality_multileague
python3 worp_optionality_four_positions.py
```

The engine, Scoring Core, Lineup Economics and app V0.9.4.6 remain unchanged.
