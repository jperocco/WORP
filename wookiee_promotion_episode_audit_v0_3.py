#!/usr/bin/env python3
"""
Wookiee Promotion Episode Audit V0.3

Purpose
-------
Collapse consecutive V0.2 EMERGENCE_CANDIDATE trigger rows into discrete promotion
*episodes* and measure what happened after the trigger.

This fixes a key V0.2 problem: one underlying transition can create multiple weekly
rows (for example W16 + W17). V0.3 counts the episode once.

Important guardrails
--------------------
- This is still an ex-post utilization/performance episode detector, NOT a validated
  historical NFL injury/depth-chart/news event feed.
- "Captured WoRP" means positive WoRP from weeks the player was ACTUALLY STARTED.
  Rostered production on the bench is NOT captured.
- ORACLE is used only to describe ex-post lineup-worthiness, never ex-ante knowledge.
- V0.3 does NOT yet estimate promotion probability per Non-Scoring player-week. The
  denominator requires a defensible time-local Non-Scoring state definition first.

Inputs
------
wookiee_promotion_event_player_week_v0_2.csv
wookiee_ex_ante_lineup_player_week_v0_6.csv

Outputs
-------
wookiee_promotion_episode_detail_v0_3.csv
wookiee_promotion_episode_position_summary_v0_3.csv
wookiee_promotion_episode_top_cases_v0_3.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd

EVENTS = Path("wookiee_promotion_event_player_week_v0_2.csv")
BASE = Path("wookiee_ex_ante_lineup_player_week_v0_6.csv")
OUT_DETAIL = Path("wookiee_promotion_episode_detail_v0_3.csv")
OUT_POS = Path("wookiee_promotion_episode_position_summary_v0_3.csv")
OUT_TOP = Path("wookiee_promotion_episode_top_cases_v0_3.csv")

TARGET_CLASS = "EMERGENCE_CANDIDATE"


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

    need_ev = {
        "season", "week", "roster_id", "player_id", "player_name", "position",
        "event_prior_state_class", "review_worthy", "promotion_score_expost",
        "prior_player_weeks_all_sample", "prior_career_real_start_rate",
        "prior_career_oracle_start_rate",
    }
    need_base = {
        "season", "week", "roster_id", "player_id", "player_name", "position",
        "weekly_worp", "real_started", "oracle_started",
    }
    miss = sorted(need_ev - set(ev.columns))
    if miss:
        raise SystemExit(f"V0.2 missing columns: {miss}")
    miss = sorted(need_base - set(base.columns))
    if miss:
        raise SystemExit(f"Base missing columns: {miss}")

    ev["review_worthy"] = as_bool(ev["review_worthy"])
    base["real_started"] = as_bool(base["real_started"])
    base["oracle_started"] = as_bool(base["oracle_started"])
    for d in [ev, base]:
        d["season"] = pd.to_numeric(d["season"], errors="coerce").astype("Int64")
        d["week"] = pd.to_numeric(d["week"], errors="coerce").astype("Int64")

    triggers = ev[
        ev["review_worthy"]
        & (ev["event_prior_state_class"] == TARGET_CLASS)
    ].copy()
    triggers = triggers.sort_values(
        ["season", "roster_id", "player_id", "week"]
    ).reset_index(drop=True)

    if triggers.empty:
        raise SystemExit("No review-worthy EMERGENCE_CANDIDATE rows found.")

    # Build episode IDs by collapsing consecutive trigger weeks for the same
    # season x roster x player. A gap > 1 starts a new episode.
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
        start_week = int(g["week"].min())
        trigger_end_week = int(g["week"].max())

        # Same player + same roster + same season after episode start.
        p = base[
            (base["season"] == season)
            & (base["roster_id"] == roster_id)
            & (base["player_id"] == player_id)
            & (base["week"] >= start_week)
        ].copy().sort_values("week")

        # Keep one observation per NFL week if source duplication exists.
        p = p.drop_duplicates(subset=["season", "week", "roster_id", "player_id"], keep="last")

        # Promotion utilization span: consecutive rostered weeks beginning at the
        # trigger in which the player was either actually started OR Oracle-selected.
        # Stop at the first observed rostered week where neither condition is true,
        # or at a week gap. This is an ex-post persistence measure, not role news.
        active_rows = []
        expected_week = start_week
        for _, r in p.iterrows():
            w = int(r["week"])
            if w != expected_week:
                break
            active = bool(r["real_started"]) or bool(r["oracle_started"])
            if not active:
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
            "episode_start_week": start_week,
            "trigger_end_week": trigger_end_week,
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
        ["season", "episode_start_week", "position", "player_name"]
    ).reset_index(drop=True)

    # Flag repeat episodes for the same player in the available sample. This does not
    # resolve historical contamination, but makes it visible instead of silently
    # counting every episode as a fresh contingent asset discovery.
    out["player_episode_number_in_sample"] = (
        out.sort_values(["player_id", "season", "episode_start_week"])
        .groupby("player_id")
        .cumcount()
        + 1
    )
    out["first_episode_for_player_in_sample"] = out["player_episode_number_in_sample"] == 1

    out.to_csv(OUT_DETAIL, index=False)

    pos = (
        out.groupby("position")
        .agg(
            episodes=("player_id", "size"),
            unique_players=("player_id", "nunique"),
            median_active_duration=("active_duration_weeks", "median"),
            mean_active_duration=("active_duration_weeks", "mean"),
            median_positive_worp_produced=("positive_worp_produced", "median"),
            mean_positive_worp_produced=("positive_worp_produced", "mean"),
            median_captured_positive_worp=("captured_positive_worp", "median"),
            mean_captured_positive_worp=("captured_positive_worp", "mean"),
            mean_uncaptured_positive_worp=("uncaptured_positive_worp", "mean"),
            median_capture_rate=("capture_rate_of_positive_worp", "median"),
            mean_capture_rate=("capture_rate_of_positive_worp", "mean"),
        )
        .reset_index()
        .sort_values("position")
    )
    pos.to_csv(OUT_POS, index=False)

    top = out.sort_values(
        ["positive_worp_produced", "active_duration_weeks", "max_trigger_score"],
        ascending=False,
    ).head(100)
    top.to_csv(OUT_TOP, index=False)

    print("Wookiee Promotion Episode Audit V0.3")
    print("====================================")
    print(f"V0.2 emergence trigger rows: {len(triggers):,}")
    print(f"collapsed promotion episodes: {len(out):,}")
    print(f"duplicate trigger rows removed by episode collapse: {len(triggers)-len(out):,}")

    print("\nPOSITION SUMMARY")
    print(pos.round(4).to_string(index=False))

    print("\nTOP 30 EPISODES BY POSITIVE WORP PRODUCED")
    show = [
        "season", "episode_start_week", "player_name", "position", "trigger_rows",
        "active_duration_weeks", "real_start_weeks", "oracle_start_weeks",
        "positive_worp_produced", "captured_positive_worp",
        "uncaptured_positive_worp", "capture_rate_of_positive_worp",
        "player_episode_number_in_sample",
    ]
    print(top[show].head(30).round(4).to_string(index=False))

    print("\nGUARDRAILS")
    print("- Episodes are ex-post utilization/performance shapes, not validated NFL role-change events.")
    print("- Captured WoRP counts only positive WoRP from weeks the player was actually started.")
    print("- No promotion-rate denominator is reported yet; Non-Scoring player-weeks are not yet classified.")
    print("- Repeat episodes remain flagged because incomplete historical context can still contaminate emergence classification.")

    print(f"\nWrote: {OUT_DETAIL}")
    print(f"Wrote: {OUT_POS}")
    print(f"Wrote: {OUT_TOP}")


if __name__ == "__main__":
    main()
