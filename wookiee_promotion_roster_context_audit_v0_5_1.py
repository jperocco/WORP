#!/usr/bin/env python3
"""
Wookiee Promotion × Roster Context Audit V0.5.1

Purpose
-------
Refine V0.5 after the first binary ROOM/BLOCKED proxy proved too crude.

The V0.5 problem was conceptual, not just cosmetic: counting every same-position asset
with a numerically stronger pre-week L3 signal made almost every event look blocked.
That can violate the intended QB1 + QB1 + QB1 framework because the real question is
not "how many players are stronger?" but "where does this asset sit relative to the
roster's economically relevant starting-capacity cutoff?"

V0.5.1 therefore keeps the comparison continuous and relative:
- observed position capacity C = max number of that position actually started by the
  roster in any week of the season (still only a realized capacity proxy);
- order same-position assets by PRE-WEEK prior-L3 WoRP/week;
- find the C-th asset's signal (the same-position capacity cutoff);
- measure promoted asset's rank, slots beyond capacity, and signal distance to cutoff;
- do NOT impose a semantic threshold for "similar" or "far" yet;
- summarize capture by relative rank/cutoff-distance quantiles.

This directly preserves the QB1 + QB1 + QB1 intuition:
- third QB with two QB-capable slots and a tiny gap to QB2 = competitive/ambiguous;
- third QB with a large gap to QB2 = more plausibly optional depth;
- names and fixed QB ranks are irrelevant.

Guardrails
----------
- All context inputs are PRE-WEEK only.
- Target-week production/start outcomes are used only as downstream outcomes.
- observed position capacity is NOT final FLEX/SF legal-slot modeling.
- No fixed semantic cutoff is introduced in V0.5.1.
- WoRP capture requires actual STARTED weeks.

Inputs
------
wookiee_ex_ante_lineup_player_week_v0_6.csv
wookiee_non_scoring_exposure_player_week_v0_4.csv

Outputs
-------
wookiee_promotion_roster_context_event_v0_5_1.csv
wookiee_promotion_roster_context_quantile_summary_v0_5_1.csv
wookiee_promotion_roster_context_validation_v0_5_1.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path("wookiee_ex_ante_lineup_player_week_v0_6.csv")
EXPOSURE = Path("wookiee_non_scoring_exposure_player_week_v0_4.csv")
OUT_EVENT = Path("wookiee_promotion_roster_context_event_v0_5_1.csv")
OUT_SUM = Path("wookiee_promotion_roster_context_quantile_summary_v0_5_1.csv")
OUT_VAL = Path("wookiee_promotion_roster_context_validation_v0_5_1.csv")


def as_bool(s):
    if s.dtype == bool:
        return s
    return s.astype(str).str.lower().isin(["true", "1", "yes"])


def safe_div(a, b):
    return float(a / b) if b and pd.notna(b) else np.nan


def main():
    for p in [BASE, EXPOSURE]:
        if not p.exists():
            raise SystemExit(f"Missing input: {p}")

    b = pd.read_csv(BASE)
    x = pd.read_csv(EXPOSURE)

    for d in [b, x]:
        d["season"] = pd.to_numeric(d["season"], errors="coerce").astype("Int64")
        d["week"] = pd.to_numeric(d["week"], errors="coerce").astype("Int64")

    b["real_started"] = as_bool(b["real_started"])
    b["oracle_started"] = as_bool(b["oracle_started"])
    x["promotion_episode_trigger"] = as_bool(x["promotion_episode_trigger"])

    need_b = {
        "season", "week", "roster_id", "player_id", "player_name", "position",
        "real_started", "prior_l3_worp_per_week",
    }
    need_x = {
        "season", "week", "roster_id", "player_id", "player_name", "position",
        "promotion_episode_trigger", "positive_worp_produced", "captured_positive_worp",
        "active_duration_weeks",
    }
    miss = sorted(need_b - set(b.columns))
    if miss:
        raise SystemExit(f"Base missing columns: {miss}")
    miss = sorted(need_x - set(x.columns))
    if miss:
        raise SystemExit(f"Exposure missing columns: {miss}")

    ev = x[x["promotion_episode_trigger"]].copy()
    if ev.empty:
        raise SystemExit("No promotion triggers")

    keys = ["season", "week", "roster_id", "player_id"]
    b = b.sort_values(keys).drop_duplicates(keys, keep="last").copy()
    b = b[b["position"].isin(["QB", "RB", "WR", "TE"])].copy()

    started_counts = (
        b[b["real_started"]]
        .groupby(["season", "roster_id", "week", "position"])
        .size().rename("n").reset_index()
    )
    capacity = (
        started_counts.groupby(["season", "roster_id", "position"])["n"]
        .max().rename("observed_max_real_start_capacity").reset_index()
    )

    rows = []
    for _, e in ev.iterrows():
        roster_week = b[
            (b["season"] == e["season"])
            & (b["week"] == e["week"])
            & (b["roster_id"] == e["roster_id"])
            & (b["position"] == e["position"])
        ].copy()
        if roster_week.empty:
            continue

        roster_week["signal"] = pd.to_numeric(
            roster_week["prior_l3_worp_per_week"], errors="coerce"
        ).fillna(0.0)
        roster_week = roster_week.sort_values(
            ["signal", "player_id"], ascending=[False, True]
        ).reset_index(drop=True)
        roster_week["relative_rank"] = np.arange(1, len(roster_week) + 1)

        me = roster_week[roster_week["player_id"].astype(str) == str(e["player_id"])]
        if me.empty:
            continue
        me = me.iloc[0]

        caprow = capacity[
            (capacity["season"] == e["season"])
            & (capacity["roster_id"] == e["roster_id"])
            & (capacity["position"] == e["position"])
        ]
        cap = int(caprow.iloc[0]["observed_max_real_start_capacity"]) if len(caprow) else 0
        if cap <= 0:
            cutoff_signal = np.nan
        else:
            cutoff_idx = min(cap, len(roster_week)) - 1
            cutoff_signal = float(roster_week.iloc[cutoff_idx]["signal"])

        my_signal = float(me["signal"])
        my_rank = int(me["relative_rank"])
        slots_beyond = max(0, my_rank - cap) if cap > 0 else np.nan
        gap_to_cutoff = my_signal - cutoff_signal if pd.notna(cutoff_signal) else np.nan

        # A within-position normalized distance helps compare roster-weeks with different
        # signal scales. Keep it continuous; no semantic threshold is assigned.
        med = float(roster_week["signal"].median())
        mad = float((roster_week["signal"] - med).abs().median())
        scale = mad if mad > 1e-9 else float(roster_week["signal"].std(ddof=0))
        if not pd.notna(scale) or scale <= 1e-9:
            normalized_gap = 0.0 if pd.notna(gap_to_cutoff) else np.nan
        else:
            normalized_gap = float(gap_to_cutoff / scale)

        produced = float(pd.to_numeric(pd.Series([e["positive_worp_produced"]]), errors="coerce").fillna(0).iloc[0])
        captured = float(pd.to_numeric(pd.Series([e["captured_positive_worp"]]), errors="coerce").fillna(0).iloc[0])

        rows.append({
            "season": int(e["season"]),
            "week": int(e["week"]),
            "roster_id": e["roster_id"],
            "player_id": e["player_id"],
            "player_name": e.get("player_name", ""),
            "position": e["position"],
            "episode_id": e.get("episode_id", np.nan),
            "observed_max_real_start_capacity": cap,
            "same_position_rostered": int(len(roster_week)),
            "preweek_player_l3_worp_pg": my_signal,
            "relative_rank_same_position": my_rank,
            "slots_beyond_observed_capacity": slots_beyond,
            "capacity_cutoff_l3_worp_pg": cutoff_signal,
            "gap_to_capacity_cutoff": gap_to_cutoff,
            "normalized_gap_to_capacity_cutoff": normalized_gap,
            "positive_worp_produced": produced,
            "captured_positive_worp": captured,
            "capture_share_of_positive_worp": safe_div(captured, produced) if produced > 0 else np.nan,
            "active_duration_weeks": e.get("active_duration_weeks", np.nan),
        })

    d = pd.DataFrame(rows)
    if d.empty:
        raise SystemExit("No matched event rows")

    # Quantiles are descriptive only. They avoid inventing a universal cutoff for what
    # counts as economically similar to the starter-capacity frontier.
    d["gap_quantile_all"] = pd.qcut(
        d["normalized_gap_to_capacity_cutoff"].rank(method="first"),
        q=4,
        labels=["Q1_FAR_BELOW_CUTOFF", "Q2", "Q3", "Q4_AT_OR_ABOVE_CUTOFF"],
    )
    d.to_csv(OUT_EVENT, index=False)

    summaries = []
    for (pos, q), z in d.groupby(["position", "gap_quantile_all"], observed=True):
        prod = z["positive_worp_produced"].fillna(0)
        capd = z["captured_positive_worp"].fillna(0)
        summaries.append({
            "position": pos,
            "gap_quantile_all": str(q),
            "events": int(len(z)),
            "median_relative_rank": float(z["relative_rank_same_position"].median()),
            "median_slots_beyond_capacity": float(z["slots_beyond_observed_capacity"].median()),
            "median_normalized_gap_to_cutoff": float(z["normalized_gap_to_capacity_cutoff"].median()),
            "mean_positive_worp_produced": float(prod.mean()),
            "mean_positive_worp_captured": float(capd.mean()),
            "aggregate_capture_share": safe_div(capd.sum(), prod.sum()),
            "any_capture_rate": float((capd > 0).mean()),
        })
    s = pd.DataFrame(summaries).sort_values(["position", "gap_quantile_all"])
    s.to_csv(OUT_SUM, index=False)

    val = pd.DataFrame([{
        "promotion_events_input": int(len(ev)),
        "matched_events": int(len(d)),
        "match_rate": safe_div(len(d), len(ev)),
        "zero_capacity_events": int((d["observed_max_real_start_capacity"] <= 0).sum()),
        "events_rank_within_capacity": int((d["relative_rank_same_position"] <= d["observed_max_real_start_capacity"]).sum()),
        "events_rank_beyond_capacity": int((d["relative_rank_same_position"] > d["observed_max_real_start_capacity"]).sum()),
        "median_same_position_rostered": float(d["same_position_rostered"].median()),
        "median_observed_capacity": float(d["observed_max_real_start_capacity"].median()),
    }])
    val.to_csv(OUT_VAL, index=False)

    print("Wookiee Promotion × Roster Context Audit V0.5.1")
    print("===============================================")
    print("Refinement: replace crude stronger-count bucket with continuous rank + distance to the observed capacity cutoff.")
    print(f"Promotion events input: {len(ev)}")
    print(f"Matched events: {len(d)} ({safe_div(len(d), len(ev)):.1%})")
    print("\nVALIDATION")
    print(val.round(4).to_string(index=False))
    print("\nPOSITION × CUTOFF-DISTANCE QUARTILE")
    print(s.round(4).to_string(index=False))
    print("\nTOP 25 EVENTS CLOSEST TO / ABOVE CUTOFF")
    show = [
        "season", "week", "player_name", "position", "relative_rank_same_position",
        "observed_max_real_start_capacity", "slots_beyond_observed_capacity",
        "gap_to_capacity_cutoff", "normalized_gap_to_capacity_cutoff",
        "positive_worp_produced", "captured_positive_worp",
    ]
    print(d.sort_values("normalized_gap_to_capacity_cutoff", ascending=False)[show].head(25).round(4).to_string(index=False))
    print("\nGUARDRAILS")
    print("- No semantic similarity threshold is forced in V0.5.1.")
    print("- QB1+QB1+QB1 is represented as relative quality around a capacity frontier, not player names or fixed ranks.")
    print("- observed capacity is still a realized position-capacity proxy, not final slot-eligibility modeling.")
    print("- If capture does not vary coherently with cutoff distance, this proxy is not decision-useful and should STOP.")
    print(f"\nWrote: {OUT_EVENT}")
    print(f"Wrote: {OUT_SUM}")
    print(f"Wrote: {OUT_VAL}")


if __name__ == "__main__":
    main()
