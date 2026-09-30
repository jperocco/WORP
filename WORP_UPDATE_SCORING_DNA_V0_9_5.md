# WoRP Lab — Scoring DNA (UI V0.9.5)

## Delivered

Added **QB Scoring DNA** to Structural Insights, between Lineup Share and
Roster Construction.

It is a league-specific, historical explainer of the scoring sources that
separate the top 12 qualifying QB seasons from QB13–QB28 in each selected
three-year window. Qualifying seasons require eight or more games.

The panel reports the average PPG separation attributable to:

- Passing TDs
- Passing volume
- Rushing
- Turnovers & sacks
- Bonuses
- Other scoring, where applicable

## Contract

- Uses only Sleeper's historical stat totals re-scored by the selected league's
  current scoring settings.
- Uses no player names, projections, Monte Carlo output, or WoRP values.
- Does not alter the frozen WoRP engine or Roster Construction research.
- It explains where the scoring advantage came from; it is not a player
  recommendation, a projection, or an archetype label.

## Validation

- Syntax compilation passed for `app_v0_9_5.py` and the Sleeper loader.
- Synthetic deterministic test passed for tier separation and component ranking.
- Component scoring test passed against the canonical Sleeper `stat × setting`
  contract.
