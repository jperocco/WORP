# WoRP Lab V0.2

Research engine for **Wins over Replacement Player** in custom fantasy-football formats.

## What changed in V0.2

V0.2 replaces the provisional Normal/50-50 win model from V0.1.x with an **empirical Monte Carlo win model**.

For each NFL week and league format, the engine:

1. builds a starter-level player pool from the real weekly scoring environment;
2. calculates a dynamic positional replacement baseline;
3. simulates complete fantasy-team scores under the requested lineup settings;
4. for each position, simulates the rest of a roster while leaving one eligible slot empty;
5. fills that slot with either the positional replacement score or the player's real weekly score;
6. evaluates both teams against the same empirical opponent-score distribution;
7. calculates:

`Weekly WoRP = P(win with player) - P(win with replacement)`

The replacement team is **not forced to a 50% win probability**.

## Current test format

- 12 teams
- 1 QB
- 2 RB
- 3 WR
- 2 TE
- 2 FLEX
- 1 Superflex
- 0.5 PPR
- +1.0 TE premium

## Important status

This is still a research build. The empirical win model is now testable, but the exact definition of replacement level remains under audit. Do not treat rankings as production-grade yet.

## Install

Python 3.10+ is required. Python 3.12 is recommended.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Tests

```bash
python test_synthetic.py
python test_empirical_win_model.py
python test_regular_season_filter.py
```

## Real 2025 demo

```bash
python run_demo.py
```

Outputs:

- `worp_2025_ranking.csv`
- `worp_2025_weekly.csv`

The weekly file includes `win_prob_replacement`, `win_prob_player`, `weekly_worp`, `win_model`, and empirical opponent-score diagnostics.

## V0.2.1 — replacement transparency patch

V0.2.1 does **not** change WoRP mathematics. It makes the replacement baseline auditable.
For each position/week it now records:

- `starter_cutoff_rank`: number/rank of players in the aggregate starter pool.
- `replacement_pool_start`: first rank in the replacement band.
- `replacement_pool_end`: last rank actually present in the replacement band.
- `replacement_effective_rank`: midpoint rank of that band (the rank analogue of the median baseline).
- `replacement_points`: median fantasy points of the replacement band (unchanged from V0.2).

`replacement_rank` is retained as a backward-compatible alias for `replacement_pool_start`; it should not be interpreted as the effective replacement rank.

Season outputs additionally expose averages of all four transparency rank fields. The empirical win model, starter allocation, replacement-band scoring, REG-only filter, and WoRP formula are unchanged.
