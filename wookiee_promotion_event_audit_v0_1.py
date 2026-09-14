#!/usr/bin/env python3
"""
Wookiee Promotion Event Audit V0.1

Purpose
-------
Exploratory audit for fluid roster-state transitions.

This version does NOT claim to observe true NFL role-change events such as injuries,
depth-chart promotions, or starter announcements. The existing validated local data
contains player-week WoRP and lineup states, but no historical injury/depth-chart/news
feed. Therefore V0.1 detects *utilization/performance promotions* ex post and measures
how strongly they resemble the proposed NON-SCORING -> SCORING/STARTER transition.

Key principle
-------------
Do not hard-code one binary promotion threshold yet. Instead create a continuous
before/after transition table and summarize the largest changes by position.

Input
-----
wookiee_ex_ante_lineup_player_week_v0_6.csv

Outputs
-------
wookiee_promotion_event_player_week_v0_1.csv
wookiee_promotion_event_position_summary_v0_1.csv
wookiee_promotion_event_top_cases_v0_1.csv

Method
------
For each season x roster x player:
- PRE window: up to 4 immediately prior rostered weeks.
- POST window: current week + next 2 rostered weeks.
- require contiguous NFL weeks inside each window where possible;
- compute REAL start rate, ORACLE start rate, mean WoRP and positive-WoRP share;
- compute deltas POST - PRE.

The resulting metrics describe an ex-post transition. They are not yet proof that the
transition was identifiable before kickoff, nor that it was caused by a true NFL role
change. That requires a later historical availability/role feed.
"""

from pathlib import Path
import numpy as np
import pandas as pd

INPUT = Path("wookiee_ex_ante_lineup_player_week_v0_6.csv")
OUT_DETAIL = Path("wookiee_promotion_event_player_week_v0_1.csv")
OUT_POS = Path("wookiee_promotion_event_position_summary_v0_1.csv")
OUT_TOP = Path("wookiee_promotion_event_top_cases_v0_1.csv")

PRE_WEEKS = 4
POST_WEEKS = 3


def contiguous_window(g: pd.DataFrame, idx: int, before: int, after: int):
    """Return pre and post slices constrained to same player/roster/season rows.

    Windows are based on observed rostered rows. Additional flags record whether the
    NFL week numbers are contiguous, so later analysis can distinguish stable ownership
    from interrupted roster presence.
    """
    pre = g.iloc[max(0, idx - before):idx].copy()
    post = g.iloc[idx:min(len(g), idx + after)].copy()
    return pre, post


def rate_bool(s: pd.Series):
    if len(s) == 0:
        return np.nan
    return float(pd.Series(s).astype(bool).mean())


def mean_num(s: pd.Series):
    if len(s) == 0:
        return np.nan
    return float(pd.to_numeric(s, errors="coerce").mean())


def pos_share(s: pd.Series):
    if len(s) == 0:
        return np.nan
    x = pd.to_numeric(s, errors="coerce")
    return float((x > 0).mean())


def weeks_contiguous(df: pd.DataFrame):
    if len(df) <= 1:
        return True
    w = df["week"].astype(int).to_numpy()
    return bool(np.all(np.diff(w) == 1))


def main():
    if not INPUT.exists():
        raise SystemExit(f"Missing input: {INPUT}")

    df = pd.read_csv(INPUT)
    required = {
        "season", "week", "roster_id", "player_id", "player_name", "position",
        "weekly_worp", "real_started", "oracle_started",
        "prior_st_worp_per_week", "prior_l3_worp_per_week", "prior_rows_observed",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    df = df.sort_values(["season", "roster_id", "player_id", "week"]).reset_index(drop=True)

    rows = []
    key_cols = ["season", "roster_id", "player_id"]

    for (season, roster_id, player_id), g in df.groupby(key_cols, sort=False):
        g = g.sort_values("week").reset_index(drop=True)
        for i, r in g.iterrows():
            pre, post = contiguous_window(g, i, PRE_WEEKS, POST_WEEKS)

            # We need some baseline history and at least 2 post observations to call the
            # row useful for transition analysis, but preserve every row in detail.
            pre_real = rate_bool(pre["real_started"])
            post_real = rate_bool(post["real_started"])
            pre_oracle = rate_bool(pre["oracle_started"])
            post_oracle = rate_bool(post["oracle_started"])
            pre_worp = mean_num(pre["weekly_worp"])
            post_worp = mean_num(post["weekly_worp"])
            pre_pos = pos_share(pre["weekly_worp"])
            post_pos = pos_share(post["weekly_worp"])

            row = {
                "season": int(season),
                "week": int(r["week"]),
                "roster_id": roster_id,
                "player_id": player_id,
                "player_name": r["player_name"],
                "position": r["position"],
                "weekly_worp": r["weekly_worp"],
                "real_started": bool(r["real_started"]),
                "oracle_started": bool(r["oracle_started"]),
                "prior_st_worp_per_week": r["prior_st_worp_per_week"],
                "prior_l3_worp_per_week": r["prior_l3_worp_per_week"],
                "prior_rows_observed": r["prior_rows_observed"],
                "pre_n": len(pre),
                "post_n": len(post),
                "pre_contiguous": weeks_contiguous(pre),
                "post_contiguous": weeks_contiguous(post),
                "pre_real_start_rate": pre_real,
                "post_real_start_rate": post_real,
                "delta_real_start_rate": post_real - pre_real if pd.notna(pre_real) and pd.notna(post_real) else np.nan,
                "pre_oracle_start_rate": pre_oracle,
                "post_oracle_start_rate": post_oracle,
                "delta_oracle_start_rate": post_oracle - pre_oracle if pd.notna(pre_oracle) and pd.notna(post_oracle) else np.nan,
                "pre_mean_worp": pre_worp,
                "post_mean_worp": post_worp,
                "delta_mean_worp": post_worp - pre_worp if pd.notna(pre_worp) and pd.notna(post_worp) else np.nan,
                "pre_positive_worp_share": pre_pos,
                "post_positive_worp_share": post_pos,
                "delta_positive_worp_share": post_pos - pre_pos if pd.notna(pre_pos) and pd.notna(post_pos) else np.nan,
            }

            # Continuous exploratory score. No semantic class is assigned from it.
            components = []
            for v in [row["delta_oracle_start_rate"], row["delta_real_start_rate"], row["delta_positive_worp_share"]]:
                if pd.notna(v):
                    components.append(v)
            if pd.notna(row["delta_mean_worp"]):
                # Scale WoRP delta conservatively so it does not dominate start-rate changes.
                components.append(np.tanh(row["delta_mean_worp"]))
            row["promotion_score_expost"] = float(np.mean(components)) if components else np.nan

            row["analysis_eligible"] = bool(len(pre) >= 2 and len(post) >= 2)
            rows.append(row)

    out = pd.DataFrame(rows)
    out.to_csv(OUT_DETAIL, index=False)

    eligible = out[out["analysis_eligible"]].copy()

    # Position-level descriptive summary only. No claim that higher score = better roster strategy.
    pos = (
        eligible.groupby("position")
        .agg(
            rows=("player_id", "size"),
            players=("player_id", "nunique"),
            mean_delta_real_start=("delta_real_start_rate", "mean"),
            mean_delta_oracle_start=("delta_oracle_start_rate", "mean"),
            mean_delta_worp=("delta_mean_worp", "mean"),
            mean_delta_positive_share=("delta_positive_worp_share", "mean"),
            median_promotion_score=("promotion_score_expost", "median"),
            p90_promotion_score=("promotion_score_expost", lambda s: s.quantile(0.90)),
        )
        .reset_index()
        .sort_values("position")
    )
    pos.to_csv(OUT_POS, index=False)

    # Human-review cases: largest continuous transitions, requiring stronger history windows.
    top = (
        eligible[(eligible["pre_n"] >= 3) & (eligible["post_n"] >= 3)]
        .sort_values(["promotion_score_expost", "delta_mean_worp"], ascending=False)
        .head(100)
    )
    top.to_csv(OUT_TOP, index=False)

    print("Wookiee Promotion Event Audit V0.1")
    print("==================================")
    print(f"input rows: {len(df):,}")
    print(f"detail rows: {len(out):,}")
    print(f"analysis-eligible rows: {len(eligible):,}")
    print("\nPOSITION SUMMARY")
    print(pos.round(4).to_string(index=False))

    print("\nTOP 20 EX-POST TRANSITIONS")
    show_cols = [
        "season", "week", "player_name", "position", "roster_id",
        "pre_real_start_rate", "post_real_start_rate",
        "pre_oracle_start_rate", "post_oracle_start_rate",
        "pre_mean_worp", "post_mean_worp", "promotion_score_expost",
    ]
    print(top[show_cols].head(20).round(4).to_string(index=False))

    print("\nGUARDRAIL")
    print("V0.1 detects ex-post utilization/performance transitions only.")
    print("It does NOT yet prove historical injury/depth-chart/role-change events or ex-ante identifiability.")
    print(f"\nWrote: {OUT_DETAIL}")
    print(f"Wrote: {OUT_POS}")
    print(f"Wrote: {OUT_TOP}")


if __name__ == "__main__":
    main()
