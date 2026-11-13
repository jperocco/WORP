#!/usr/bin/env python3
"""
Wookiee Non-Scoring Exposure Audit V0.4

Purpose
-------
Construct a conservative, time-local exposure denominator for the fluid-roster-state
research: rostered player-weeks that look like plausible NON-SCORING inventory before
that week's games, then measure how often those exposures lead into a V0.3.1 promotion
episode.

This is deliberately a PROXY audit, not a validated semantic classification of every
roster spot. The current dataset does not contain historical injury/depth-chart/news or
market valuation.

Core guardrails
---------------
- State is defined only from information available before the target week.
- Target-week weekly_worp, real_started and oracle_started are outcomes, never inputs to
  the pre-week exposure classification.
- A player-week is not called Non-Scoring merely because the player was benched that
  week. We require evidence of low recent/prior lineup use.
- Promotion episodes remain ex-post utilization/performance shapes, not validated NFL
  role-change events.
- Rates are descriptive proxy rates. They must not yet be presented as the true
  probability that a Non-Scoring asset promotes.
- WoRP remains sporting value, not trade/market appreciation.

Inputs
------
wookiee_ex_ante_lineup_player_week_v0_6.csv
wookiee_promotion_episode_detail_v0_3_1.csv

Outputs
-------
wookiee_non_scoring_exposure_player_week_v0_4.csv
wookiee_non_scoring_exposure_position_summary_v0_4.csv
wookiee_non_scoring_exposure_sensitivity_v0_4.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path("wookiee_ex_ante_lineup_player_week_v0_6.csv")
EPISODES = Path("wookiee_promotion_episode_detail_v0_3_1.csv")
OUT_DETAIL = Path("wookiee_non_scoring_exposure_player_week_v0_4.csv")
OUT_POS = Path("wookiee_non_scoring_exposure_position_summary_v0_4.csv")
OUT_SENS = Path("wookiee_non_scoring_exposure_sensitivity_v0_4.csv")

LOOKBACKS = [3, 5, 8]
PRIMARY_LOOKBACK = 5


def as_bool(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s
    return s.astype(str).str.lower().isin(["true", "1", "yes"])


def safe_div(a, b):
    return float(a / b) if b and pd.notna(b) else np.nan


def main():
    for p in [BASE, EPISODES]:
        if not p.exists():
            raise SystemExit(f"Missing input: {p}")

    b = pd.read_csv(BASE)
    ep = pd.read_csv(EPISODES)

    need_b = {
        "season", "week", "roster_id", "player_id", "player_name", "position",
        "prior_rows_observed", "real_started", "oracle_started",
    }
    need_ep = {
        "season", "roster_id", "player_id", "player_name", "position",
        "trigger_start_week", "active_start_week", "active_duration_weeks",
        "positive_worp_produced", "captured_positive_worp",
    }
    miss = sorted(need_b - set(b.columns))
    if miss:
        raise SystemExit(f"Base missing columns: {miss}")
    miss = sorted(need_ep - set(ep.columns))
    if miss:
        raise SystemExit(f"Episodes missing columns: {miss}")

    b["real_started"] = as_bool(b["real_started"])
    b["oracle_started"] = as_bool(b["oracle_started"])
    for d in [b, ep]:
        d["season"] = pd.to_numeric(d["season"], errors="coerce").astype("Int64")
        d["week"] = pd.to_numeric(d.get("week"), errors="coerce").astype("Int64") if "week" in d.columns else None

    keys = ["season", "week", "roster_id", "player_id"]
    b = b.sort_values(keys).drop_duplicates(keys, keep="last").copy()
    b = b[b["position"].isin(["QB", "RB", "WR", "TE"])].copy()

    gcols = ["season", "roster_id", "player_id"]
    b = b.sort_values(gcols + ["week"]).reset_index(drop=True)

    for lb in LOOKBACKS:
        b[f"prior_real_starts_l{lb}"] = (
            b.groupby(gcols)["real_started"]
             .transform(lambda s: s.astype(int).shift(1).rolling(lb, min_periods=1).sum())
        )
        b[f"prior_oracle_starts_l{lb}"] = (
            b.groupby(gcols)["oracle_started"]
             .transform(lambda s: s.astype(int).shift(1).rolling(lb, min_periods=1).sum())
        )
        b[f"prior_obs_l{lb}"] = (
            b.groupby(gcols)["week"]
             .transform(lambda s: s.shift(1).rolling(lb, min_periods=1).count())
        )
        b[f"non_scoring_proxy_l{lb}"] = (
            (b[f"prior_obs_l{lb}"] >= 2)
            & (b[f"prior_real_starts_l{lb}"] == 0)
            & (b[f"prior_oracle_starts_l{lb}"] == 0)
        )

    ep = ep.copy()
    ep["trigger_start_week"] = pd.to_numeric(ep["trigger_start_week"], errors="coerce").astype("Int64")
    ep["active_start_week"] = pd.to_numeric(ep["active_start_week"], errors="coerce").astype("Int64")
    ep = ep.reset_index(drop=True)
    ep["episode_id"] = np.arange(1, len(ep) + 1)

    ecols = [
        "season", "roster_id", "player_id", "trigger_start_week", "active_start_week",
        "episode_id", "active_duration_weeks", "positive_worp_produced",
        "captured_positive_worp",
    ]
    em = ep[ecols].rename(columns={"trigger_start_week": "week"})
    b = b.merge(em, on=["season", "roster_id", "player_id", "week"], how="left")
    b["promotion_episode_trigger"] = b["episode_id"].notna()

    primary = f"non_scoring_proxy_l{PRIMARY_LOOKBACK}"
    detail = b[b[primary]].copy()
    detail.to_csv(OUT_DETAIL, index=False)

    rows = []
    for position_name, x in detail.groupby("position"):
        triggers = x[x["promotion_episode_trigger"]]
        rows.append({
            "position": position_name,
            "non_scoring_proxy_player_weeks": int(len(x)),
            "unique_players_exposed": int(x["player_id"].nunique()),
            "promotion_episode_triggers": int(triggers["promotion_episode_trigger"].sum()),
            "unique_players_promoted": int(triggers["player_id"].nunique()),
            "proxy_promotion_rate_per_player_week": safe_div(triggers["promotion_episode_trigger"].sum(), len(x)),
            "mean_episode_positive_worp_when_promoted": float(pd.to_numeric(triggers["positive_worp_produced"], errors="coerce").mean()) if len(triggers) else np.nan,
            "mean_episode_captured_worp_when_promoted": float(pd.to_numeric(triggers["captured_positive_worp"], errors="coerce").mean()) if len(triggers) else np.nan,
            "total_episode_positive_worp_from_promotions": float(pd.to_numeric(triggers["positive_worp_produced"], errors="coerce").fillna(0).sum()),
            "total_episode_captured_worp_from_promotions": float(pd.to_numeric(triggers["captured_positive_worp"], errors="coerce").fillna(0).sum()),
            "produced_worp_per_100_exposure_weeks": 100.0 * safe_div(pd.to_numeric(triggers["positive_worp_produced"], errors="coerce").fillna(0).sum(), len(x)),
            "captured_worp_per_100_exposure_weeks": 100.0 * safe_div(pd.to_numeric(triggers["captured_positive_worp"], errors="coerce").fillna(0).sum(), len(x)),
        })
    pos_summary = pd.DataFrame(rows).sort_values("position")
    pos_summary.to_csv(OUT_POS, index=False)

    sens_rows = []
    for lb in LOOKBACKS:
        flag = f"non_scoring_proxy_l{lb}"
        for position_name, x in b[b[flag]].groupby("position"):
            n = len(x)
            trig = int(x["promotion_episode_trigger"].sum())
            sens_rows.append({
                "lookback_weeks": lb,
                "position": position_name,
                "exposure_player_weeks": n,
                "promotion_episode_triggers": trig,
                "proxy_promotion_rate_per_player_week": safe_div(trig, n),
            })
    sens = pd.DataFrame(sens_rows).sort_values(["lookback_weeks", "position"])
    sens.to_csv(OUT_SENS, index=False)

    total_exposure = int(len(detail))
    total_triggers = int(detail["promotion_episode_trigger"].sum())
    all_episode_count = int(len(ep))
    matched_episode_ids = set(detail.loc[detail["promotion_episode_trigger"], "episode_id"].dropna().astype(int))

    print("Wookiee Non-Scoring Exposure Audit V0.4")
    print("========================================")
    print(f"Primary proxy lookback: {PRIMARY_LOOKBACK} weeks")
    print("Definition: >=2 prior observations, 0 REAL starts and 0 ORACLE selections in prior lookback")
    print(f"Non-Scoring proxy player-weeks: {total_exposure:,}")
    print(f"Promotion episode triggers from proxy state: {total_triggers:,}")
    print(f"Proxy promotion rate / player-week: {safe_div(total_triggers, total_exposure):.4%}" if total_exposure else "Proxy promotion rate / player-week: n/a")
    print(f"V0.3.1 episodes matched to primary proxy: {len(matched_episode_ids):,}/{all_episode_count:,}")

    print("\nPOSITION SUMMARY — PRIMARY PROXY")
    print(pos_summary.round(4).to_string(index=False))

    print("\nSENSITIVITY — LOOKBACK 3/5/8")
    print(sens.round(5).to_string(index=False))

    print("\nINTERPRETATION GUARDRAILS")
    print("- This is a conservative time-local Non-Scoring PROXY, not a validated roster-state label.")
    print("- Target-week production/start outcomes are excluded from the exposure definition.")
    print("- Promotion rates are descriptive proxy rates; do not call them true promotion probabilities yet.")
    print("- Produced WoRP and captured WoRP remain separate; bench production is not captured.")
    print("- Market/trade appreciation is not measured by this audit.")

    print(f"\nWrote: {OUT_DETAIL}")
    print(f"Wrote: {OUT_POS}")
    print(f"Wrote: {OUT_SENS}")


if __name__ == "__main__":
    main()
