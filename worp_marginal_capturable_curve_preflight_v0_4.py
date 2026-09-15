#!/usr/bin/env python3
"""
WORP LAB — MARGINAL CAPTURABLE CURVE PREFLIGHT V0.4

Purpose
-------
Establish the first empirical bridge from the league-native WoRP curve to
realistically obtainable alternatives WITHOUT turning .25/.50/.75 into
absolute roster thresholds.

This is intentionally a Wookiee behavioral preflight, not product logic.
League-native adaptability remains mandatory before any roster recommendation.

Core question
-------------
For each position and season, how much WoRP separates progressively better
season-rank regions from the WoRP that was actually observed FREE before a
week and had a legitimate prior-information signal?

Important limitations
---------------------
- FREE is observed from Sleeper matchup roster snapshots.
- Ex-ante signal uses only prior-week / prior-3-week opportunity.
- This script does NOT claim a waiver acquisition would succeed.
- It does NOT claim the FREE player would be selected into the lineup.
- It does NOT use .25/.50/.75 as semantic thresholds.
- Wookiee is a behavioral reference case only.

Outputs
-------
- worp_marginal_capturable_curve_preflight_v0_4.csv
- worp_marginal_capturable_curve_preflight_summary_v0_4.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path

RANKINGS = Path("wookiee_2023_2025_rankings_worp.csv")
FREE_SIGNAL = Path("wookiee_ex_ante_signal_denominator_detail_v0_1.csv")
TEMPORAL = Path("wookiee_free_capturability_temporal_detail_v0_2.csv")

POSITIONS = ["QB", "RB", "WR", "TE"]
RANK_WINDOWS = [(1, 8), (9, 16), (17, 24), (25, 32), (33, 40),
                (41, 50), (51, 60), (61, 72), (73, 90), (91, 120)]
SIGNAL_OK = {"MID_PRIOR_USAGE", "HIGH_PRIOR_USAGE"}


def pick_col(df, candidates, required=True):
    for c in candidates:
        if c in df.columns:
            return c
    if required:
        raise KeyError(f"None of columns found: {candidates}; available={list(df.columns)}")
    return None


def main():
    for p in (RANKINGS, FREE_SIGNAL, TEMPORAL):
        if not p.exists():
            raise FileNotFoundError(p)

    r = pd.read_csv(RANKINGS)
    f = pd.read_csv(FREE_SIGNAL)
    t = pd.read_csv(TEMPORAL)

    # Normalize identities.
    for df in (r, f, t):
        if "player_id" in df.columns:
            df["player_id"] = df["player_id"].astype(str)

    rank_col = pick_col(r, ["position_rank", "pos_rank", "rank"])
    season_worp_col = pick_col(r, ["season_worp", "total_worp", "worp", "weekly_worp"])

    # Build legitimate FREE alternatives: target-week FREE denominator + prior signal
    # + temporal availability compatible with capture.
    keys = ["season", "week", "player_id"]
    temporal_cols = keys + ["capturability"]
    x = f.merge(t[temporal_cols].drop_duplicates(keys), on=keys, how="left")
    x["capturability"] = x["capturability"].fillna("UNKNOWN")
    x["eligible_signal"] = x["prior_signal_band"].isin(SIGNAL_OK)
    x["eligible_temporal"] = x["capturability"].eq("CAPTURABLE")
    x["eligible_alternative"] = x["eligible_signal"] & x["eligible_temporal"]

    # Target-week WoRP is an outcome, used only to estimate realized payoff conditional
    # on an ex-ante eligible candidate. Candidate selection itself uses no target-week info.
    x["weekly_worp"] = pd.to_numeric(x["weekly_worp"], errors="coerce").fillna(0.0)

    alt_rows = []
    for (season, position), g in x.groupby(["season", "position"]):
        g = g[g.eligible_alternative].copy()
        if g.empty:
            continue

        # Two alternative baselines. Neither cherry-picks the eventual winner:
        # 1) exposure-weighted expectation per eligible FREE player-week;
        # 2) weekly best realized payoff among ex-ante eligible candidates — an explicit
        #    optimistic ceiling, NOT an attainable strategy.
        exposure_mean = g.weekly_worp.mean()
        positive_rate = g.weekly_worp.gt(0).mean()
        weekly_best = g.groupby("week").weekly_worp.max()

        alt_rows.append({
            "season": int(season),
            "position": position,
            "eligible_free_player_weeks": len(g),
            "eligible_free_unique_players": g.player_id.nunique(),
            "eligible_free_positive_rate": positive_rate,
            "eligible_free_worp_per_exposure": exposure_mean,
            "optimistic_weekly_best_free_worp_mean": weekly_best.mean(),
            "optimistic_weekly_best_free_worp_median": weekly_best.median(),
            "weeks_with_eligible_free": weekly_best.size,
        })

    alt = pd.DataFrame(alt_rows)

    # Secured side: use season-rank windows to avoid false single-rank precision.
    secured_rows = []
    r[rank_col] = pd.to_numeric(r[rank_col], errors="coerce")
    r[season_worp_col] = pd.to_numeric(r[season_worp_col], errors="coerce")

    for (season, position), g in r[r.position.isin(POSITIONS)].groupby(["season", "position"]):
        for lo, hi in RANK_WINDOWS:
            q = g[g[rank_col].between(lo, hi)].copy()
            if q.empty:
                continue
            secured_rows.append({
                "season": int(season),
                "position": position,
                "rank_lo": lo,
                "rank_hi": hi,
                "secured_rank_band": f"{position}{lo}-{position}{hi}",
                "secured_players": len(q),
                "secured_median_season_worp": q[season_worp_col].median(),
                "secured_mean_season_worp": q[season_worp_col].mean(),
            })

    secured = pd.DataFrame(secured_rows)
    out = secured.merge(alt, on=["season", "position"], how="left")

    # NOTE: units differ (season WoRP vs weekly FREE payoff), so DO NOT subtract them.
    # V0.4 preflight's job is to validate candidate supply and signal/temporal coverage.
    # A valid marginal delta requires converting both sides to a common horizon first.
    out["preflight_only"] = True
    out["delta_status"] = "NOT_COMPUTED_UNITS_MISMATCH"

    summary = alt.groupby("position", as_index=False).agg(
        seasons=("season", "nunique"),
        eligible_free_player_weeks=("eligible_free_player_weeks", "sum"),
        median_unique_free_players=("eligible_free_unique_players", "median"),
        median_positive_rate=("eligible_free_positive_rate", "median"),
        median_worp_per_exposure=("eligible_free_worp_per_exposure", "median"),
        median_optimistic_weekly_best=("optimistic_weekly_best_free_worp_mean", "median"),
        median_weeks_with_eligible_free=("weeks_with_eligible_free", "median"),
    )

    out.to_csv("worp_marginal_capturable_curve_preflight_v0_4.csv", index=False)
    summary.to_csv("worp_marginal_capturable_curve_preflight_summary_v0_4.csv", index=False)

    print("=" * 100)
    print("MARGINAL CAPTURABLE CURVE PREFLIGHT V0.4")
    print("=" * 100)
    print(summary.to_string(index=False))
    print("\nGUARDRAIL: no marginal delta computed yet because secured side is season-horizon")
    print("while FREE alternative payoff is target-week horizon. This is intentional.")
    print("NEXT: if supply/coverage is adequate, normalize both sides to a common forward horizon")
    print("before comparing marginal WoRP.")


if __name__ == "__main__":
    main()
