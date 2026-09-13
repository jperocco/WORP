#!/usr/bin/env python3
"""
WOOKIEE EX-ANTE SIGNAL DENOMINATOR AUDIT V0.1

Purpose
-------
Test whether prior usage actually discriminates NEXT-WEEK positive WoRP among
players who were FREE before the target week.

Unlike the prior audit, this includes BOTH:
- successes: FREE players who produce positive WoRP next week
- failures: FREE players with the same prior-signal bands who do not

No current-week information is used to define the signal.

Signal bands are carried forward unchanged from Ex-Ante Identifiability V0.1:
QB: HIGH >=35, MID >=25, LOW >0
RB: HIGH >=15, MID >=8, LOW >0
WR/TE: HIGH >=7, MID >=4, LOW >0
using max(previous-week opportunity, previous-3-week mean opportunity).

This is still descriptive. It does NOT declare a waiver threshold.
"""

import json
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd

WORP = Path("wookiee_2023_2025_weekly_worp.csv")
LEAGUES = {
    2023: "950220100039311360",
    2024: "1050961255520923648",
    2025: "1182581249532833792",
}
POSITIONS = {"QB", "RB", "WR", "TE"}
STOP_RATE = 0.04


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "WoRPLab/0.2.8"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_stats(raw):
    if isinstance(raw, dict):
        return [(str(pid), st or {}) for pid, st in raw.items()]
    out = []
    for rec in raw or []:
        if isinstance(rec, dict) and rec.get("player_id") is not None:
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


def observed_free(league_id, week):
    matchups = get_json(
        f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}"
    )
    owned = set()
    for row in matchups or []:
        for x in row.get("players") or []:
            owned.add(str(x))
    return owned


def band(row):
    if not row["has_prior_sample"]:
        return "NO_PRIOR_SAMPLE"
    a = row["prev1_opportunity"]
    b = row["prev3_opportunity_mean"]
    best = max(0 if pd.isna(a) else a, 0 if pd.isna(b) else b)
    p = row["position"]

    if p == "QB":
        if best >= 35: return "HIGH_PRIOR_USAGE"
        if best >= 25: return "MID_PRIOR_USAGE"
    elif p == "RB":
        if best >= 15: return "HIGH_PRIOR_USAGE"
        if best >= 8: return "MID_PRIOR_USAGE"
    else:
        if best >= 7: return "HIGH_PRIOR_USAGE"
        if best >= 4: return "MID_PRIOR_USAGE"

    if best > 0: return "LOW_PRIOR_USAGE"
    return "ZERO_PRIOR_USAGE"


def main():
    print("=" * 110)
    print("WOOKIEE EX-ANTE SIGNAL DENOMINATOR AUDIT V0.1")
    print("=" * 110)

    w = pd.read_csv(WORP)
    w["player_id"] = w["player_id"].astype(str)
    w = w[w.position.isin(POSITIONS) & w.season.isin(LEAGUES)].copy()

    # Weekly usage universe.
    rows = []
    for season in LEAGUES:
        for week in range(1, 19):
            raw = get_json(
                f"https://api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular"
            )
            for player_id, st in parse_stats(raw):
                rows.append({
                    "season": season,
                    "week": week,
                    "player_id": player_id,
                    "targets": val(st, "rec_tgt", "targets"),
                    "carries": val(st, "rush_att", "rushing_attempts", "carries"),
                    "pass_attempts": val(st, "pass_att", "passing_attempts", "attempts"),
                })

    hist = pd.DataFrame(rows).drop_duplicates(["season", "week", "player_id"])

    # Position/name map from WoRP source.
    ident = w[["season", "player_id", "player_name", "position"]].drop_duplicates(
        ["season", "player_id"]
    )
    hist = hist.merge(ident, on=["season", "player_id"], how="inner")

    hist["opportunity"] = np.where(
        hist.position.eq("QB"),
        hist.pass_attempts + hist.carries,
        np.where(hist.position.eq("RB"),
                 hist.carries + hist.targets,
                 hist.targets)
    )

    hist = hist.sort_values(["season", "player_id", "week"]).copy()
    g = hist.groupby(["season", "player_id"], sort=False)

    hist["prev1_opportunity"] = g["opportunity"].shift(1)
    hist["prev3_opportunity_mean"] = g["opportunity"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    )
    hist["prior_weeks_observed"] = g["week"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).count()
    )
    hist["has_prior_sample"] = hist.prior_weeks_observed.fillna(0).gt(0)
    hist["prior_signal_band"] = hist.apply(band, axis=1)

    # Target-week WoRP outcome. Missing WoRP row = zero realized WoRP.
    outcome = w[[
        "season", "week", "player_id", "weekly_worp", "fantasy_points"
    ]].drop_duplicates(["season", "week", "player_id"])

    u = hist.merge(
        outcome,
        on=["season", "week", "player_id"],
        how="left"
    )
    u["weekly_worp"] = pd.to_numeric(u.weekly_worp, errors="coerce").fillna(0)
    u["fantasy_points"] = pd.to_numeric(u.fantasy_points, errors="coerce").fillna(0)

    # IMPORTANT: denominator = players observed FREE in the target-week matchup snapshot.
    owned_cache = {}
    free_mask = []

    for row in u.itertuples(index=False):
        key = (int(row.season), int(row.week))
        if key not in owned_cache:
            owned_cache[key] = observed_free(LEAGUES[key[0]], key[1])
        free_mask.append(str(row.player_id) not in owned_cache[key])

    u = u[np.array(free_mask)].copy()

    # Week 1 cannot have within-season prior sample and is not useful for this audit.
    u = u[u.week >= 2].copy()

    u["positive_worp"] = u.weekly_worp > 0
    u["midplus_signal"] = u.prior_signal_band.isin(
        ["MID_PRIOR_USAGE", "HIGH_PRIOR_USAGE"]
    )

    no_sample_rate = (~u.has_prior_sample).mean()

    print(f"FREE target player-weeks        : {len(u)}")
    print(f"Positive-WoRP successes         : {int(u.positive_worp.sum())}")
    print(f"Non-positive failures           : {int((~u.positive_worp).sum())}")
    print(f"No-prior-sample rate            : {no_sample_rate:.2%}")

    order = [
        "ZERO_PRIOR_USAGE", "LOW_PRIOR_USAGE",
        "MID_PRIOR_USAGE", "HIGH_PRIOR_USAGE", "NO_PRIOR_SAMPLE"
    ]

    rows = []
    for b in order:
        x = u[u.prior_signal_band == b]
        successes = int(x.positive_worp.sum())
        total = len(x)
        positive_worp_sum = x.loc[x.positive_worp, "weekly_worp"].sum()
        rows.append({
            "prior_signal_band": b,
            "free_player_weeks": total,
            "positive_worp_cases": successes,
            "hit_rate": successes / total if total else np.nan,
            "positive_worp_sum": positive_worp_sum,
            "worp_per_free_player_week": positive_worp_sum / total if total else np.nan,
            "mean_positive_worp_when_hit": (
                x.loc[x.positive_worp, "weekly_worp"].mean()
                if successes else np.nan
            ),
        })

    summary = pd.DataFrame(rows)

    print("\nSIGNAL DENOMINATORS")
    print("-" * 110)
    print(summary.to_string(
        index=False,
        formatters={
            "hit_rate": "{:.2%}".format,
            "positive_worp_sum": "{:.4f}".format,
            "worp_per_free_player_week": "{:.5f}".format,
            "mean_positive_worp_when_hit": "{:.4f}".format,
        }
    ))

    # Position-specific denominators.
    pos_rows = []
    for p in ["QB", "RB", "WR", "TE"]:
        p0 = u[u.position == p]
        for b in order:
            x = p0[p0.prior_signal_band == b]
            n = len(x)
            hits = int(x.positive_worp.sum())
            pos_rows.append({
                "position": p,
                "prior_signal_band": b,
                "free_player_weeks": n,
                "positive_worp_cases": hits,
                "hit_rate": hits / n if n else np.nan,
                "positive_worp_sum": x.loc[x.positive_worp, "weekly_worp"].sum(),
                "worp_per_free_player_week": (
                    x.loc[x.positive_worp, "weekly_worp"].sum() / n
                    if n else np.nan
                ),
            })

    pos = pd.DataFrame(pos_rows)

    print("\nPOSITION × SIGNAL DENOMINATORS")
    print("-" * 110)
    print(pos.to_string(
        index=False,
        formatters={
            "hit_rate": "{:.2%}".format,
            "positive_worp_sum": "{:.4f}".format,
            "worp_per_free_player_week": "{:.5f}".format,
        }
    ))

    # Compact discrimination comparison.
    clean = u[u.has_prior_sample].copy()
    midplus = clean.midplus_signal
    lowminus = ~midplus

    def metrics(mask):
        x = clean[mask]
        n = len(x)
        hits = int(x.positive_worp.sum())
        worp = x.loc[x.positive_worp, "weekly_worp"].sum()
        return n, hits, hits/n if n else np.nan, worp/n if n else np.nan

    mn, mh, mhr, mw = metrics(midplus)
    ln, lh, lhr, lw = metrics(lowminus)

    discrim = pd.DataFrame([{
        "midplus_free_player_weeks": mn,
        "midplus_hits": mh,
        "midplus_hit_rate": mhr,
        "midplus_worp_per_free_week": mw,
        "zero_low_free_player_weeks": ln,
        "zero_low_hits": lh,
        "zero_low_hit_rate": lhr,
        "zero_low_worp_per_free_week": lw,
        "hit_rate_lift_midplus_vs_zero_low": (
            mhr / lhr if lhr and not pd.isna(lhr) else np.nan
        ),
        "worp_rate_lift_midplus_vs_zero_low": (
            mw / lw if lw and not pd.isna(lw) else np.nan
        ),
    }])

    print("\nDISCRIMINATION")
    print("-" * 110)
    print(discrim.to_string(
        index=False,
        formatters={
            "midplus_hit_rate": "{:.2%}".format,
            "midplus_worp_per_free_week": "{:.5f}".format,
            "zero_low_hit_rate": "{:.2%}".format,
            "zero_low_worp_per_free_week": "{:.5f}".format,
            "hit_rate_lift_midplus_vs_zero_low": "{:.2f}x".format,
            "worp_rate_lift_midplus_vs_zero_low": "{:.2f}x".format,
        }
    ))

    # Save cases for inspection, including failures.
    u.to_csv("wookiee_ex_ante_signal_denominator_detail_v0_1.csv", index=False)
    summary.to_csv("wookiee_ex_ante_signal_denominator_summary_v0_1.csv", index=False)
    pos.to_csv("wookiee_ex_ante_signal_denominator_position_v0_1.csv", index=False)
    discrim.to_csv("wookiee_ex_ante_signal_denominator_discrimination_v0_1.csv", index=False)

    human = u[u.has_prior_sample].sort_values(
        ["midplus_signal", "weekly_worp"], ascending=[False, False]
    ).head(100)
    human[[
        "season", "week", "player_name", "position",
        "prior_signal_band", "prev1_opportunity", "prev3_opportunity_mean",
        "positive_worp", "weekly_worp", "fantasy_points"
    ]].to_csv("wookiee_ex_ante_signal_denominator_human_cases_v0_1.csv", index=False)

    if no_sample_rate > STOP_RATE:
        print("\nSTOP: NO_PRIOR_SAMPLE > 4%.")
        print("Do NOT interpret discrimination estimates.")
        raise SystemExit(2)

    print("\nPASS: NO_PRIOR_SAMPLE <= 4%.")
    print("The denominator comparison is usable descriptively.")
    print("INTERPRETATION STOP:")
    print("Signal lift is evidence of discrimination, NOT yet a waiver-value cutoff.")
    print("Roster acquisition cost, competition, persistence and lineup realization remain separate.")


if __name__ == "__main__":
    main()
