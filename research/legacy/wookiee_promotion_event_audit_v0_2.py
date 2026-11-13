#!/usr/bin/env python3
"""
Wookiee Promotion Event Audit V0.2

Purpose
-------
Refine V0.1 by separating high ex-post transitions that look like:

1) ESTABLISHED RE-ENTRY / RETURN
   A player already demonstrated meaningful lineup occupancy before the event and then
   returned to strong use. This includes many injury/suspension-return shapes.

2) EMERGENCE CANDIDATE
   A player had enough observable prior history in the sample but little prior lineup
   occupancy, then experienced a large utilization/performance jump.

3) HISTORY INSUFFICIENT
   We do not have enough prior player-week history to tell whether the event is a true
   contingent promotion or merely the return of an already-established asset.

This is still NOT a historical injury/depth-chart/news audit. Classification is based
only on player-week history available in our validated WoRP/lineup dataset.

Input
-----
wookiee_promotion_event_player_week_v0_1.csv
wookiee_ex_ante_lineup_player_week_v0_6.csv

Outputs
-------
wookiee_promotion_event_player_week_v0_2.csv
wookiee_promotion_event_event_summary_v0_2.csv
wookiee_promotion_event_emergence_cases_v0_2.csv

Key guardrail
-------------
A high V0.1 promotion score is not automatically contingent optionality. V0.2 tries to
remove obvious established-player re-entry contamination before we study NON-SCORING
-> SCORING/STARTER behavior.
"""

from pathlib import Path
import numpy as np
import pandas as pd

V01 = Path("wookiee_promotion_event_player_week_v0_1.csv")
BASE = Path("wookiee_ex_ante_lineup_player_week_v0_6.csv")
OUT_DETAIL = Path("wookiee_promotion_event_player_week_v0_2.csv")
OUT_SUMMARY = Path("wookiee_promotion_event_event_summary_v0_2.csv")
OUT_EMERGENCE = Path("wookiee_promotion_event_emergence_cases_v0_2.csv")

# These are deliberately conservative research gates, not product thresholds.
MIN_PRIOR_PLAYER_WEEKS = 6
ESTABLISHED_REAL_START_RATE = 0.50
ESTABLISHED_ORACLE_START_RATE = 0.50
LOW_PRIOR_REAL_START_RATE = 0.25
LOW_PRIOR_ORACLE_START_RATE = 0.25
MIN_EVENT_SCORE_FOR_REVIEW = 0.20


def safe_bool(s):
    if s.dtype == bool:
        return s
    return s.astype(str).str.lower().isin(["true", "1", "yes"])


def main():
    for p in [V01, BASE]:
        if not p.exists():
            raise SystemExit(f"Missing input: {p}")

    ev = pd.read_csv(V01)
    base = pd.read_csv(BASE)

    needed_ev = {
        "season", "week", "roster_id", "player_id", "player_name", "position",
        "analysis_eligible", "promotion_score_expost", "delta_real_start_rate",
        "delta_oracle_start_rate", "delta_mean_worp", "pre_real_start_rate",
        "post_real_start_rate", "pre_oracle_start_rate", "post_oracle_start_rate",
        "pre_mean_worp", "post_mean_worp",
    }
    needed_base = {
        "season", "week", "roster_id", "player_id", "player_name", "position",
        "weekly_worp", "real_started", "oracle_started",
    }
    miss = sorted(needed_ev - set(ev.columns))
    if miss:
        raise SystemExit(f"V0.1 missing columns: {miss}")
    miss = sorted(needed_base - set(base.columns))
    if miss:
        raise SystemExit(f"Base missing columns: {miss}")

    base = base.copy()
    base["real_started"] = safe_bool(base["real_started"])
    base["oracle_started"] = safe_bool(base["oracle_started"])
    base["season"] = pd.to_numeric(base["season"], errors="coerce").astype("Int64")
    base["week"] = pd.to_numeric(base["week"], errors="coerce").astype("Int64")

    # Build prior history across the entire available sample, independent of roster.
    # For each event row, only weeks strictly before the event are allowed.
    hist_rows = []
    base = base.sort_values(["player_id", "season", "week", "roster_id"]).reset_index(drop=True)

    for _, r in ev.iterrows():
        pid = r["player_id"]
        season = int(r["season"])
        week = int(r["week"])

        h = base[
            (base["player_id"] == pid)
            & (
                (base["season"] < season)
                | ((base["season"] == season) & (base["week"] < week))
            )
        ].copy()

        # Deduplicate player-season-week if the player changed rosters in the source.
        if not h.empty:
            h = h.sort_values(["season", "week", "roster_id"]).drop_duplicates(
                subset=["player_id", "season", "week"], keep="last"
            )

        n = len(h)
        real_rate = float(h["real_started"].mean()) if n else np.nan
        oracle_rate = float(h["oracle_started"].mean()) if n else np.nan
        mean_worp = float(pd.to_numeric(h["weekly_worp"], errors="coerce").mean()) if n else np.nan
        positive_rate = float((pd.to_numeric(h["weekly_worp"], errors="coerce") > 0).mean()) if n else np.nan
        prior_seasons = int(h["season"].nunique()) if n else 0

        hist_rows.append({
            "prior_player_weeks_all_sample": n,
            "prior_player_seasons_all_sample": prior_seasons,
            "prior_career_real_start_rate": real_rate,
            "prior_career_oracle_start_rate": oracle_rate,
            "prior_career_mean_worp": mean_worp,
            "prior_career_positive_worp_rate": positive_rate,
        })

    hist = pd.DataFrame(hist_rows)
    out = pd.concat([ev.reset_index(drop=True), hist], axis=1)

    def classify(r):
        if not bool(r.get("analysis_eligible", False)):
            return "NOT_ANALYSIS_ELIGIBLE"

        n = int(r["prior_player_weeks_all_sample"] or 0)
        if n < MIN_PRIOR_PLAYER_WEEKS:
            return "HISTORY_INSUFFICIENT"

        rr = r["prior_career_real_start_rate"]
        oo = r["prior_career_oracle_start_rate"]

        if (pd.notna(rr) and rr >= ESTABLISHED_REAL_START_RATE) or (
            pd.notna(oo) and oo >= ESTABLISHED_ORACLE_START_RATE
        ):
            return "ESTABLISHED_REENTRY_CANDIDATE"

        if (pd.isna(rr) or rr <= LOW_PRIOR_REAL_START_RATE) and (
            pd.isna(oo) or oo <= LOW_PRIOR_ORACLE_START_RATE
        ):
            return "EMERGENCE_CANDIDATE"

        return "AMBIGUOUS_PRIOR_STATE"

    out["event_prior_state_class"] = out.apply(classify, axis=1)
    out["review_worthy"] = (
        out["analysis_eligible"].astype(bool)
        & (pd.to_numeric(out["promotion_score_expost"], errors="coerce") >= MIN_EVENT_SCORE_FOR_REVIEW)
    )

    out.to_csv(OUT_DETAIL, index=False)

    review = out[out["review_worthy"]].copy()
    summary = (
        review.groupby(["event_prior_state_class", "position"])
        .agg(
            events=("player_id", "size"),
            players=("player_id", "nunique"),
            median_score=("promotion_score_expost", "median"),
            mean_score=("promotion_score_expost", "mean"),
            mean_delta_real_start=("delta_real_start_rate", "mean"),
            mean_delta_oracle_start=("delta_oracle_start_rate", "mean"),
            mean_delta_worp=("delta_mean_worp", "mean"),
            median_prior_weeks=("prior_player_weeks_all_sample", "median"),
        )
        .reset_index()
        .sort_values(["event_prior_state_class", "events"], ascending=[True, False])
    )
    summary.to_csv(OUT_SUMMARY, index=False)

    emergence = (
        review[review["event_prior_state_class"] == "EMERGENCE_CANDIDATE"]
        .sort_values(["promotion_score_expost", "delta_mean_worp"], ascending=False)
        .head(100)
    )
    emergence.to_csv(OUT_EMERGENCE, index=False)

    print("Wookiee Promotion Event Audit V0.2")
    print("==================================")
    print(f"V0.1 rows: {len(ev):,}")
    print(f"review-worthy rows (score >= {MIN_EVENT_SCORE_FOR_REVIEW:.2f}): {len(review):,}")
    print("\nREVIEW-WORTHY EVENT CLASSES")
    counts = review["event_prior_state_class"].value_counts(dropna=False)
    print(counts.to_string())

    print("\nSUMMARY BY CLASS x POSITION")
    if summary.empty:
        print("(none)")
    else:
        print(summary.round(4).to_string(index=False))

    print("\nTOP 25 EMERGENCE CANDIDATES")
    show = [
        "season", "week", "player_name", "position", "roster_id",
        "prior_player_weeks_all_sample", "prior_career_real_start_rate",
        "prior_career_oracle_start_rate", "pre_real_start_rate", "post_real_start_rate",
        "pre_oracle_start_rate", "post_oracle_start_rate", "pre_mean_worp",
        "post_mean_worp", "promotion_score_expost",
    ]
    if emergence.empty:
        print("(none)")
    else:
        print(emergence[show].head(25).round(4).to_string(index=False))

    print("\nINTERPRETATION GUARDRAIL")
    print("ESTABLISHED_REENTRY_CANDIDATE is a historical-usage shape, not a proven injury return.")
    print("EMERGENCE_CANDIDATE is a low-prior-use transition shape, not yet a validated NFL role promotion.")
    print("HISTORY_INSUFFICIENT must remain unresolved rather than being forced into emergence/re-entry.")
    print(f"\nWrote: {OUT_DETAIL}")
    print(f"Wrote: {OUT_SUMMARY}")
    print(f"Wrote: {OUT_EMERGENCE}")


if __name__ == "__main__":
    main()
