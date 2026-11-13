#!/usr/bin/env python3
"""
Wookiee Promotion × Roster Context Audit V0.5

Purpose
-------
Join V0.4 low-use exposure / promotion events to the manager's PRE-WEEK roster context.
The goal is to test the QB1 + QB1 + QB1 principle empirically: a promoted asset's
sporting value is not enough; its lineup value depends on the economically relevant
competition for the league's eligible starting slots.

This audit deliberately avoids player names/ranks as semantic classes. Context is
relative within the roster and week.

Important guardrails
--------------------
- Context uses only PRE-WEEK signals already present in V0.6 (prior season-to-date and
  prior-L3 WoRP/week). Target-week WoRP/start outcomes never define context.
- Eligible-slot capacity is inferred from actual V0.6 real lineup position counts per
  roster-week. Because V0.6 does not preserve the slot label used for each starter, this
  is a conservative position-capacity proxy, NOT a full FLEX/SF assignment model.
- We therefore report BOTH same-position competition and observed max real-start
  capacity. Do not interpret this as final legal-slot modeling.
- A promotion is not automatically captured. Captured WoRP remains positive WoRP from
  weeks actually STARTED.
- Non-Scoring remains a proxy, not a validated semantic label.
- WoRP is sporting value, not market/trade price.

Inputs
------
wookiee_ex_ante_lineup_player_week_v0_6.csv
wookiee_non_scoring_exposure_player_week_v0_4.csv

Outputs
-------
wookiee_promotion_roster_context_event_v0_5.csv
wookiee_promotion_roster_context_summary_v0_5.csv
wookiee_promotion_roster_context_validation_v0_5.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path("wookiee_ex_ante_lineup_player_week_v0_6.csv")
EXPOSURE = Path("wookiee_non_scoring_exposure_player_week_v0_4.csv")
OUT_EVENT = Path("wookiee_promotion_roster_context_event_v0_5.csv")
OUT_SUM = Path("wookiee_promotion_roster_context_summary_v0_5.csv")
OUT_VAL = Path("wookiee_promotion_roster_context_validation_v0_5.csv")


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

    need = {"prior_st_worp_per_week", "prior_l3_worp_per_week"}
    miss = sorted(need - set(b.columns))
    if miss:
        raise SystemExit(f"Base missing pre-week signal columns: {miss}")
    if "promotion_episode_trigger" not in x.columns:
        raise SystemExit("Exposure file missing promotion_episode_trigger")

    x["promotion_episode_trigger"] = as_bool(x["promotion_episode_trigger"])
    ev = x[x["promotion_episode_trigger"]].copy()
    if ev.empty:
        raise SystemExit("No promotion triggers in V0.4 exposure file")

    keys = ["season", "week", "roster_id", "player_id"]
    b = b.sort_values(keys).drop_duplicates(keys, keep="last").copy()
    b = b[b["position"].isin(["QB", "RB", "WR", "TE"])].copy()

    # Observed position capacity: maximum number of players of a position actually
    # started by this roster in any week of the same season. This captures the league's
    # realized ability to deploy that position without inventing fixed QB/RB/WR names.
    started_counts = (
        b[b["real_started"]]
        .groupby(["season", "roster_id", "week", "position"])
        .size().rename("n").reset_index()
    )
    capacity = (
        started_counts.groupby(["season", "roster_id", "position"])["n"]
        .max().rename("observed_max_real_start_capacity").reset_index()
    )

    # Build relative pre-week roster context for every event.
    out = []
    for _, e in ev.iterrows():
        mask = (
            (b["season"] == e["season"]) &
            (b["week"] == e["week"]) &
            (b["roster_id"] == e["roster_id"])
        )
        r = b[mask].copy()
        same = r[r["position"] == e["position"]].copy()
        me = same[same["player_id"].astype(str) == str(e["player_id"])]
        if me.empty:
            continue
        me = me.iloc[0]

        caprow = capacity[
            (capacity["season"] == e["season"]) &
            (capacity["roster_id"] == e["roster_id"]) &
            (capacity["position"] == e["position"])
        ]
        cap = int(caprow.iloc[0]["observed_max_real_start_capacity"]) if len(caprow) else 0

        signal = "prior_l3_worp_per_week"
        same[signal] = pd.to_numeric(same[signal], errors="coerce").fillna(0.0)
        my_sig = float(pd.to_numeric(pd.Series([me[signal]]), errors="coerce").fillna(0).iloc[0])

        # Relative competition, not named tiers: how many same-position roster assets
        # enter the week with a stronger recent WoRP signal than the promoted asset?
        stronger = int((same[signal] > my_sig + 1e-12).sum())
        tied_or_stronger = int((same[signal] >= my_sig - 1e-12).sum()) - 1
        same_n = int(len(same))

        # Capacity pressure >0 means more stronger/equal competitors than observed
        # deployable same-position capacity. This is a diagnostic, not final legal slot
        # assignment because FLEX/SF eligibility is not explicit in this player-week CSV.
        stronger_plus_self = stronger + 1
        pressure_ratio = safe_div(stronger_plus_self, cap) if cap else np.nan
        likely_same_pos_room = bool(cap > stronger) if cap else False

        row = {
            "season": e["season"], "week": e["week"], "roster_id": e["roster_id"],
            "player_id": e["player_id"], "player_name": e.get("player_name", ""),
            "position": e["position"], "episode_id": e.get("episode_id", np.nan),
            "observed_max_real_start_capacity": cap,
            "same_position_rostered": same_n,
            "preweek_player_l3_worp_pg": my_sig,
            "same_position_stronger_l3_assets": stronger,
            "same_position_tied_or_stronger_l3_assets_ex_self": tied_or_stronger,
            "relative_capacity_pressure": pressure_ratio,
            "same_position_room_proxy": likely_same_pos_room,
            "positive_worp_produced": e.get("positive_worp_produced", np.nan),
            "captured_positive_worp": e.get("captured_positive_worp", np.nan),
            "active_duration_weeks": e.get("active_duration_weeks", np.nan),
        }
        produced = pd.to_numeric(pd.Series([row["positive_worp_produced"]]), errors="coerce").fillna(0).iloc[0]
        captured = pd.to_numeric(pd.Series([row["captured_positive_worp"]]), errors="coerce").fillna(0).iloc[0]
        row["capture_share_of_positive_worp"] = safe_div(captured, produced) if produced > 0 else np.nan
        out.append(row)

    d = pd.DataFrame(out)
    if d.empty:
        raise SystemExit("No event rows matched roster context")
    d.to_csv(OUT_EVENT, index=False)

    # Compare events with apparent same-position room vs events facing stronger-player
    # congestion. This is the direct first test of the QB1+QB1+QB1 intuition.
    d["context_bucket"] = np.where(
        d["same_position_room_proxy"],
        "ROOM_WITHIN_OBSERVED_POSITION_CAPACITY",
        "BLOCKED_BY_STRONGER_POSITION_COMPETITION_PROXY",
    )

    rows = []
    for (position, bucket), z in d.groupby(["position", "context_bucket"]):
        produced = pd.to_numeric(z["positive_worp_produced"], errors="coerce").fillna(0)
        captured = pd.to_numeric(z["captured_positive_worp"], errors="coerce").fillna(0)
        rows.append({
            "position": position,
            "context_bucket": bucket,
            "events": len(z),
            "mean_observed_capacity": z["observed_max_real_start_capacity"].mean(),
            "mean_stronger_same_pos_assets": z["same_position_stronger_l3_assets"].mean(),
            "mean_positive_worp_produced": produced.mean(),
            "mean_positive_worp_captured": captured.mean(),
            "aggregate_capture_share": safe_div(captured.sum(), produced.sum()),
            "events_with_any_capture": int((captured > 0).sum()),
            "any_capture_rate": float((captured > 0).mean()),
        })
    s = pd.DataFrame(rows).sort_values(["position", "context_bucket"])
    s.to_csv(OUT_SUM, index=False)

    # Validation / coverage diagnostics.
    val = pd.DataFrame([{
        "v04_promotion_events": int(len(ev)),
        "matched_context_events": int(len(d)),
        "match_rate": safe_div(len(d), len(ev)),
        "zero_capacity_events": int((d["observed_max_real_start_capacity"] <= 0).sum()),
        "null_capture_share_events": int(d["capture_share_of_positive_worp"].isna().sum()),
        "room_proxy_events": int(d["same_position_room_proxy"].sum()),
        "competition_proxy_events": int((~d["same_position_room_proxy"]).sum()),
    }])
    val.to_csv(OUT_VAL, index=False)

    print("Wookiee Promotion × Roster Context Audit V0.5")
    print("=============================================")
    print("Question: after a low-use asset promotes, does relative roster competition help explain whether its WoRP is captured?")
    print(f"V0.4 promotion events: {len(ev)}")
    print(f"Matched to pre-week roster context: {len(d)} ({safe_div(len(d), len(ev)):.1%})")
    print("\nCONTEXT SUMMARY")
    print(s.round(4).to_string(index=False))
    print("\nVALIDATION")
    print(val.round(4).to_string(index=False))
    print("\nGUARDRAILS")
    print("- No player name/rank is used to assign Starter/Scoring/Non-Scoring state.")
    print("- Context is relative to roster peers using PRE-WEEK L3 WoRP signal.")
    print("- observed_max_real_start_capacity is a realized position-capacity proxy, NOT final FLEX/SF legal-slot modeling.")
    print("- QB1+QB1+QB1 remains a competition/capacity problem; a third strong QB is not automatically Non-Scoring.")
    print("- Promotion and production do not imply capture; capture requires actual STARTED weeks.")
    print("- Do not rank positions from this audit alone.")
    print(f"\nWrote: {OUT_EVENT}")
    print(f"Wrote: {OUT_SUM}")
    print(f"Wrote: {OUT_VAL}")


if __name__ == "__main__":
    main()
