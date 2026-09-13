#!/usr/bin/env python3
"""
WOOKIEE EX-ANTE IDENTIFIABILITY AUDIT V0.1

Question:
Among positive-WoRP player-weeks already classified as FREE + CAPTURABLE,
how much had observable usage BEFORE the production week?

Critical rule:
NO current-week targets/carries/points are used to define identifiability.
Features are lagged: previous 1 week and previous 3 available regular-season weeks.

This is descriptive. V0.1 deliberately does NOT invent a "good waiver" cutoff.

Outputs:
- wookiee_ex_ante_identifiability_detail_v0_1.csv
- wookiee_ex_ante_identifiability_summary_v0_1.csv
- wookiee_ex_ante_identifiability_position_v0_1.csv
- wookiee_ex_ante_identifiability_signal_bands_v0_1.csv
- wookiee_ex_ante_identifiability_human_cases_v0_1.csv
"""

import json
import urllib.request
from pathlib import Path
import pandas as pd
import numpy as np

CAP = Path("wookiee_free_capturability_temporal_detail_v0_2.csv")
STOP_RATE = 0.04
SEASONS = [2023, 2024, 2025]


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "WoRPLab/0.2.7"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_stats(raw):
    if isinstance(raw, dict):
        return [(str(pid), st or {}) for pid, st in raw.items()]
    out = []
    for rec in raw or []:
        if not isinstance(rec, dict) or rec.get("player_id") is None:
            continue
        st = rec.get("stats")
        if st is None:
            st = {k: v for k, v in rec.items()
                  if k not in {"player_id", "team", "opponent", "game_id"}}
        out.append((str(rec["player_id"]), st or {}))
    return out


def val(st, *keys):
    for k in keys:
        if k in st:
            try:
                return float(st.get(k) or 0)
            except Exception:
                return 0.0
    return 0.0


def main():
    print("=" * 110)
    print("WOOKIEE EX-ANTE IDENTIFIABILITY AUDIT V0.1")
    print("=" * 110)

    if not CAP.exists():
        raise FileNotFoundError(CAP)

    cap = pd.read_csv(CAP)
    cap["player_id"] = cap["player_id"].astype(str)
    cap = cap[
        (cap["capturability"] == "CAPTURABLE") &
        (cap["weekly_worp"] > 0)
    ].copy()

    # Load full weekly usage history so all signals can be lagged.
    rows = []
    for season in SEASONS:
        for week in range(1, 19):
            raw = get_json(
                f"https://api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular"
            )
            for player_id, st in parse_stats(raw):
                carries = val(st, "rush_att", "rushing_attempts", "carries")
                targets = val(st, "rec_tgt", "targets")
                pass_attempts = val(st, "pass_att", "passing_attempts", "attempts")
                rows.append({
                    "season": season,
                    "week": week,
                    "player_id": player_id,
                    "prev_fantasy_points_raw": val(
                        st, "pts_ppr", "fantasy_points_ppr", "fantasy_points"
                    ),
                    "targets": targets,
                    "carries": carries,
                    "pass_attempts": pass_attempts,
                    "receptions": val(st, "rec", "receptions"),
                    "scrimmage_yards": (
                        val(st, "rush_yd", "rushing_yards") +
                        val(st, "rec_yd", "receiving_yards")
                    ),
                    "total_tds": (
                        val(st, "rush_td", "rushing_tds") +
                        val(st, "rec_td", "receiving_tds") +
                        val(st, "pass_td", "passing_tds")
                    ),
                })

    hist = pd.DataFrame(rows)
    hist = hist.drop_duplicates(["season", "week", "player_id"])
    hist = hist.sort_values(["season", "player_id", "week"]).copy()

    # Attach position from target cases where possible.
    posmap = cap[["season", "player_id", "position"]].drop_duplicates(
        ["season", "player_id"]
    )
    hist = hist.merge(posmap, on=["season", "player_id"], how="left")

    hist["opportunity"] = np.where(
        hist.position.eq("QB"),
        hist.pass_attempts + hist.carries,
        np.where(
            hist.position.eq("RB"),
            hist.carries + hist.targets,
            hist.targets
        )
    )

    g = hist.groupby(["season", "player_id"], sort=False)

    # STRICTLY PRIOR-WEEK FEATURES.
    for col in ["opportunity", "targets", "carries", "receptions",
                "scrimmage_yards", "total_tds"]:
        hist[f"prev1_{col}"] = g[col].shift(1)
        hist[f"prev3_{col}_mean"] = g[col].transform(
            lambda s: s.shift(1).rolling(3, min_periods=1).mean()
        )
        hist[f"prev3_{col}_max"] = g[col].transform(
            lambda s: s.shift(1).rolling(3, min_periods=1).max()
        )

    hist["prior_weeks_observed"] = g["week"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).count()
    )

    feature_cols = [
        c for c in hist.columns
        if c.startswith("prev1_") or c.startswith("prev3_")
    ] + ["prior_weeks_observed"]

    m = cap.merge(
        hist[["season", "week", "player_id"] + feature_cols],
        on=["season", "week", "player_id"],
        how="left"
    )

    # Missing prior data is a real identifiability limitation, not silently zeroed.
    m["has_prior_observation"] = m["prior_weeks_observed"].fillna(0) > 0

    # Descriptive signal strength. These are NOT waiver thresholds.
    # They only partition prior opportunity into transparent bands.
    def signal_band(row):
        if not row["has_prior_observation"]:
            return "NO_PRIOR_SAMPLE"

        p = row["position"]
        p1 = row.get("prev1_opportunity", np.nan)
        p3 = row.get("prev3_opportunity_mean", np.nan)

        best = np.nanmax([p1, p3]) if not (pd.isna(p1) and pd.isna(p3)) else 0

        if p == "QB":
            if best >= 35: return "HIGH_PRIOR_USAGE"
            if best >= 25: return "MID_PRIOR_USAGE"
            if best > 0: return "LOW_PRIOR_USAGE"
            return "ZERO_PRIOR_USAGE"

        if p == "RB":
            if best >= 15: return "HIGH_PRIOR_USAGE"
            if best >= 8: return "MID_PRIOR_USAGE"
            if best > 0: return "LOW_PRIOR_USAGE"
            return "ZERO_PRIOR_USAGE"

        # WR / TE
        if best >= 7: return "HIGH_PRIOR_USAGE"
        if best >= 4: return "MID_PRIOR_USAGE"
        if best > 0: return "LOW_PRIOR_USAGE"
        return "ZERO_PRIOR_USAGE"

    m["prior_signal_band"] = m.apply(signal_band, axis=1)

    total_worp = m.weekly_worp.sum()
    no_sample = m.prior_signal_band.eq("NO_PRIOR_SAMPLE")
    unresolved_rate = no_sample.mean()

    print(f"Capturable positive player-weeks : {len(m)}")
    print(f"Capturable WoRP                 : {total_worp:.6f}")
    print(f"No-prior-sample cases           : {int(no_sample.sum())}")
    print(f"No-prior-sample rate            : {unresolved_rate:.2%}")

    bands = []
    order = [
        "ZERO_PRIOR_USAGE",
        "LOW_PRIOR_USAGE",
        "MID_PRIOR_USAGE",
        "HIGH_PRIOR_USAGE",
        "NO_PRIOR_SAMPLE",
    ]

    for band in order:
        x = m[m.prior_signal_band == band]
        bands.append({
            "prior_signal_band": band,
            "player_weeks": len(x),
            "player_week_share": len(x) / len(m) if len(m) else 0,
            "worp": x.weekly_worp.sum(),
            "worp_share": x.weekly_worp.sum() / total_worp if total_worp else 0,
            "median_worp": x.weekly_worp.median() if len(x) else np.nan,
            "median_prev1_opportunity": x.prev1_opportunity.median() if len(x) else np.nan,
            "median_prev3_opportunity": x.prev3_opportunity_mean.median() if len(x) else np.nan,
        })

    bands = pd.DataFrame(bands)

    print("\nPRIOR-USAGE SIGNAL BANDS")
    print("-" * 110)
    print(bands.to_string(
        index=False,
        formatters={
            "player_week_share": "{:.1%}".format,
            "worp": "{:.4f}".format,
            "worp_share": "{:.1%}".format,
            "median_worp": "{:.4f}".format,
            "median_prev1_opportunity": "{:.1f}".format,
            "median_prev3_opportunity": "{:.1f}".format,
        }
    ))

    # Position × signal.
    pos_rows = []
    for pos in ["QB", "RB", "WR", "TE"]:
        x0 = m[m.position == pos]
        if x0.empty:
            continue
        tw = x0.weekly_worp.sum()
        for band in order:
            x = x0[x0.prior_signal_band == band]
            pos_rows.append({
                "position": pos,
                "prior_signal_band": band,
                "player_weeks": len(x),
                "player_week_share": len(x) / len(x0),
                "worp": x.weekly_worp.sum(),
                "worp_share": x.weekly_worp.sum() / tw if tw else 0,
            })

    pos = pd.DataFrame(pos_rows)

    print("\nPOSITION × PRIOR SIGNAL")
    print("-" * 110)
    print(pos.to_string(
        index=False,
        formatters={
            "player_week_share": "{:.1%}".format,
            "worp": "{:.4f}".format,
            "worp_share": "{:.1%}".format,
        }
    ))

    # Continuity / acceleration view: did opportunity exist immediately before?
    observed = m[m.has_prior_observation].copy()
    observed["prev1_any_usage"] = observed.prev1_opportunity.fillna(0) > 0
    observed["prev1_midplus"] = observed.prior_signal_band.isin(
        ["MID_PRIOR_USAGE", "HIGH_PRIOR_USAGE"]
    )

    summary = pd.DataFrame([{
        "capturable_player_weeks": len(m),
        "capturable_worp": total_worp,
        "no_prior_sample_cases": int(no_sample.sum()),
        "no_prior_sample_rate": unresolved_rate,
        "prior_sample_cases": len(observed),
        "any_prev1_usage_case_share": observed.prev1_any_usage.mean() if len(observed) else np.nan,
        "midplus_prior_signal_case_share": observed.prev1_midplus.mean() if len(observed) else np.nan,
        "midplus_prior_signal_worp_share": (
            observed.loc[observed.prev1_midplus, "weekly_worp"].sum() / total_worp
            if total_worp else np.nan
        ),
    }])

    print("\nSUMMARY")
    print("-" * 110)
    print(summary.to_string(
        index=False,
        formatters={
            "capturable_worp": "{:.4f}".format,
            "no_prior_sample_rate": "{:.2%}".format,
            "any_prev1_usage_case_share": "{:.1%}".format,
            "midplus_prior_signal_case_share": "{:.1%}".format,
            "midplus_prior_signal_worp_share": "{:.1%}".format,
        }
    ))

    # Human inspection: biggest realized WoRP cases and what was visible beforehand.
    human = m.sort_values("weekly_worp", ascending=False).head(60).copy()
    human_cols = [
        "season", "week", "player_name", "position", "weekly_worp",
        "prior_signal_band", "prior_weeks_observed",
        "prev1_opportunity", "prev3_opportunity_mean",
        "prev1_targets", "prev3_targets_mean",
        "prev1_carries", "prev3_carries_mean",
        "prev1_scrimmage_yards", "prev3_scrimmage_yards_mean",
    ]

    human[human_cols].to_csv(
        "wookiee_ex_ante_identifiability_human_cases_v0_1.csv", index=False
    )
    m.to_csv("wookiee_ex_ante_identifiability_detail_v0_1.csv", index=False)
    summary.to_csv("wookiee_ex_ante_identifiability_summary_v0_1.csv", index=False)
    pos.to_csv("wookiee_ex_ante_identifiability_position_v0_1.csv", index=False)
    bands.to_csv("wookiee_ex_ante_identifiability_signal_bands_v0_1.csv", index=False)

    print("\nTOP 20 REALIZED WoRP CASES WITH PRIOR SIGNAL")
    print("-" * 110)
    print(human[human_cols].head(20).to_string(index=False))

    if unresolved_rate > STOP_RATE:
        print("\nSTOP: NO_PRIOR_SAMPLE > 4%.")
        print("Do NOT convert prior-signal bands into an identifiability estimate.")
        raise SystemExit(2)

    print("\nPASS: NO_PRIOR_SAMPLE <= 4%.")
    print("Descriptive ex-ante signal decomposition is usable.")
    print("INTERPRETATION STOP:")
    print("MID/HIGH prior usage is NOT yet a waiver-value threshold.")
    print("This audit only asks what opportunity was observable before the production week.")


if __name__ == "__main__":
    main()
