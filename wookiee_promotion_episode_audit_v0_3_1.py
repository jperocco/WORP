#!/usr/bin/env python3
"""
Wookiee Promotion Episode Audit V0.3.1

Bug-fix refinement of V0.3.

Why this exists
---------------
V0.3 forced the active span to begin on the first trigger week. But the V0.1/V0.2
trigger is based on a forward-looking POST window (current week + next 2 rostered
weeks). Therefore a valid transition can be detected one or two weeks BEFORE the
player first becomes REAL-started or ORACLE-selected. That produced artificial
active_duration_weeks == 0 rows and understated episode WoRP/capture.

V0.3.1 keeps the same episode collapse but aligns the measured episode to the first
observed active week inside the trigger detection horizon.

Guardrails
----------
- Still an ex-post utilization/performance episode detector, not a validated NFL role
  change or ex-ante signal.
- Captured WoRP = positive WoRP only from weeks actually started.
- No promotion probability is calculated yet.
"""

from pathlib import Path
import numpy as np
import pandas as pd

EVENTS = Path("wookiee_promotion_event_player_week_v0_2.csv")
BASE = Path("wookiee_ex_ante_lineup_player_week_v0_6.csv")
OUT_DETAIL = Path("wookiee_promotion_episode_detail_v0_3_1.csv")
OUT_POS = Path("wookiee_promotion_episode_position_summary_v0_3_1.csv")
OUT_TOP = Path("wookiee_promotion_episode_top_cases_v0_3_1.csv")

TARGET_CLASS = "EMERGENCE_CANDIDATE"
POST_LOOKAHEAD_WEEKS = 2  # V0.1 POST = current + next 2 weeks


def as_bool(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s
    return s.astype(str).str.lower().isin(["true", "1", "yes"])


def safe_div(a, b):
    return float(a / b) if b and pd.notna(b) else np.nan


def main():
    for p in [EVENTS, BASE]:
        if not p.exists():
            raise SystemExit(f"Missing input: {p}")

    ev = pd.read_csv(EVENTS)
    base = pd.read_csv(BASE)

    ev["review_worthy"] = as_bool(ev["review_worthy"])
    base["real_started"] = as_bool(base["real_started"])
    base["oracle_started"] = as_bool(base["oracle_started"])
    for d in [ev, base]:
        d["season"] = pd.to_numeric(d["season"], errors="coerce").astype("Int64")
        d["week"] = pd.to_numeric(d["week"], errors="coerce").astype("Int64")

    triggers = ev[
        ev["review_worthy"]
        & (ev["event_prior_state_class"] == TARGET_CLASS)
    ].copy().sort_values(["season", "roster_id", "player_id", "week"])

    if triggers.empty:
        raise SystemExit("No review-worthy EMERGENCE_CANDIDATE rows found.")

    grp_cols = ["season", "roster_id", "player_id"]
    triggers["prev_week"] = triggers.groupby(grp_cols)["week"].shift(1)
    triggers["new_episode"] = (
        triggers["prev_week"].isna()
        | ((triggers["week"] - triggers["prev_week"]) > 1)
    )
    triggers["episode_seq"] = triggers.groupby(grp_cols)["new_episode"].cumsum().astype(int)

    episodes = []
    for (season, roster_id, player_id, episode_seq), g in triggers.groupby(
        grp_cols + ["episode_seq"], sort=False
    ):
        g = g.sort_values("week")
        trigger_start_week = int(g["week"].min())
        trigger_end_week = int(g["week"].max())
        onset_search_end = trigger_end_week + POST_LOOKAHEAD_WEEKS

        p = base[
            (base["season"] == season)
            & (base["roster_id"] == roster_id)
            & (base["player_id"] == player_id)
            & (base["week"] >= trigger_start_week)
        ].copy().sort_values("week")
        p = p.drop_duplicates(
            subset=["season", "week", "roster_id", "player_id"], keep="last"
        )

        # Find first REAL/ORACLE active week within the same detection horizon that
        # caused the trigger. This fixes the V0.3 anchor bug without widening the event.
        onset_candidates = p[
            (p["week"] <= onset_search_end)
            & (p["real_started"] | p["oracle_started"])
        ]

        if onset_candidates.empty:
            active = pd.DataFrame(columns=p.columns)
            active_start_week = np.nan
            onset_lag_weeks = np.nan
        else:
            active_start_week = int(onset_candidates.iloc[0]["week"])
            onset_lag_weeks = active_start_week - trigger_start_week

            # Measure contiguous active span beginning at the true first active week.
            active_rows = []
            expected_week = active_start_week
            for _, r in p[p["week"] >= active_start_week].iterrows():
                w = int(r["week"])
                if w != expected_week:
                    break
                if not (bool(r["real_started"]) or bool(r["oracle_started"])):
                    break
                active_rows.append(r)
                expected_week += 1
            active = pd.DataFrame(active_rows)

        if active.empty:
            active_duration = 0
            active_end_week = np.nan
            positive_worp_produced = 0.0
            captured_positive_worp = 0.0
            oracle_positive_worp = 0.0
            real_start_weeks = 0
            oracle_start_weeks = 0
            positive_worp_weeks = 0
        else:
            w = pd.to_numeric(active["weekly_worp"], errors="coerce").fillna(0.0)
            pos = w.clip(lower=0.0)
            real_mask = active["real_started"].astype(bool).to_numpy()
            oracle_mask = active["oracle_started"].astype(bool).to_numpy()
            active_duration = int(len(active))
            active_end_week = int(active["week"].max())
            positive_worp_produced = float(pos.sum())
            captured_positive_worp = float(pos.to_numpy()[real_mask].sum())
            oracle_positive_worp = float(pos.to_numpy()[oracle_mask].sum())
            real_start_weeks = int(real_mask.sum())
            oracle_start_weeks = int(oracle_mask.sum())
            positive_worp_weeks = int((w > 0).sum())

        uncaptured_positive_worp = max(0.0, positive_worp_produced - captured_positive_worp)

        episodes.append({
            "season": int(season),
            "roster_id": roster_id,
            "player_id": player_id,
            "player_name": g.iloc[0]["player_name"],
            "position": g.iloc[0]["position"],
            "episode_seq": int(episode_seq),
            "trigger_start_week": trigger_start_week,
            "trigger_end_week": trigger_end_week,
            "active_start_week": active_start_week,
            "onset_lag_weeks": onset_lag_weeks,
            "trigger_rows": int(len(g)),
            "max_trigger_score": float(pd.to_numeric(g["promotion_score_expost"], errors="coerce").max()),
            "mean_trigger_score": float(pd.to_numeric(g["promotion_score_expost"], errors="coerce").mean()),
            "prior_player_weeks_all_sample": int(pd.to_numeric(g.iloc[0]["prior_player_weeks_all_sample"], errors="coerce")),
            "prior_career_real_start_rate": float(g.iloc[0]["prior_career_real_start_rate"]),
            "prior_career_oracle_start_rate": float(g.iloc[0]["prior_career_oracle_start_rate"]),
            "active_duration_weeks": active_duration,
            "active_end_week": active_end_week,
            "real_start_weeks": real_start_weeks,
            "oracle_start_weeks": oracle_start_weeks,
            "positive_worp_weeks": positive_worp_weeks,
            "positive_worp_produced": positive_worp_produced,
            "captured_positive_worp": captured_positive_worp,
            "uncaptured_positive_worp": uncaptured_positive_worp,
            "oracle_positive_worp": oracle_positive_worp,
            "capture_rate_of_positive_worp": safe_div(captured_positive_worp, positive_worp_produced),
            "real_start_share_active_span": safe_div(real_start_weeks, active_duration),
            "oracle_start_share_active_span": safe_div(oracle_start_weeks, active_duration),
        })

    out = pd.DataFrame(episodes).sort_values(
        ["season", "trigger_start_week", "position", "player_name"]
    ).reset_index(drop=True)

    order = out.sort_values(["player_id", "season", "trigger_start_week"]).index
    numbering = pd.Series(index=out.index, dtype="int64")
    numbering.loc[order] = (
        out.loc[order].groupby("player_id").cumcount() + 1
    ).to_numpy()
    out["player_episode_number_in_sample"] = numbering.astype(int)
    out["first_episode_for_player_in_sample"] = out["player_episode_number_in_sample"] == 1
    out["active_episode_found"] = out["active_duration_weeks"] > 0

    out.to_csv(OUT_DETAIL, index=False)

    pos = (
        out.groupby("position")
        .agg(
            episodes=("player_id", "size"),
            active_episodes=("active_episode_found", "sum"),
            unique_players=("player_id", "nunique"),
            median_onset_lag=("onset_lag_weeks", "median"),
            median_active_duration=("active_duration_weeks", "median"),
            mean_active_duration=("active_duration_weeks", "mean"),
            mean_positive_worp_produced=("positive_worp_produced", "mean"),
            mean_captured_positive_worp=("captured_positive_worp", "mean"),
            mean_uncaptured_positive_worp=("uncaptured_positive_worp", "mean"),
            median_capture_rate=("capture_rate_of_positive_worp", "median"),
            mean_capture_rate=("capture_rate_of_positive_worp", "mean"),
        )
        .reset_index()
        .sort_values("position")
    )
    pos["active_episode_rate"] = pos["active_episodes"] / pos["episodes"]
    pos.to_csv(OUT_POS, index=False)

    top = out.sort_values(
        ["positive_worp_produced", "active_duration_weeks", "max_trigger_score"],
        ascending=False,
    ).head(100)
    top.to_csv(OUT_TOP, index=False)

    print("Wookiee Promotion Episode Audit V0.3.1")
    print("======================================")
    print(f"V0.2 emergence trigger rows: {len(triggers):,}")
    print(f"collapsed promotion episodes: {len(out):,}")
    print(f"active episodes after onset alignment: {int(out['active_episode_found'].sum()):,}/{len(out):,}")
    print(f"zero-duration episodes remaining: {int((out['active_duration_weeks'] == 0).sum()):,}")
    print("\nPOSITION SUMMARY")
    print(pos.round(4).to_string(index=False))

    print("\nTOP 30 EPISODES BY POSITIVE WORP PRODUCED")
    show = [
        "season", "trigger_start_week", "active_start_week", "onset_lag_weeks",
        "player_name", "position", "trigger_rows", "active_duration_weeks",
        "real_start_weeks", "oracle_start_weeks", "positive_worp_produced",
        "captured_positive_worp", "uncaptured_positive_worp",
        "capture_rate_of_positive_worp", "player_episode_number_in_sample",
    ]
    print(top[show].head(30).round(4).to_string(index=False))

    print("\nGUARDRAILS")
    print("- Trigger week and active onset are now distinct.")
    print("- Episodes remain ex-post shapes, not validated NFL role-change events.")
    print("- Captured WoRP counts only positive WoRP from weeks actually started.")
    print("- Promotion-rate denominator remains intentionally deferred.")

    print(f"\nWrote: {OUT_DETAIL}")
    print(f"Wrote: {OUT_POS}")
    print(f"Wrote: {OUT_TOP}")


if __name__ == "__main__":
    main()
