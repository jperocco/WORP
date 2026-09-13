import os
import pandas as pd
import numpy as np

from worp_engine import LeagueSettings, calculate_season_worp
from nflverse_loader import load_nflverse_player_weeks


SEASONS = list(range(2016, 2026))
BANDS = [3, 6, 9]
N_SIMS = 8000
SEED = 7

SETTINGS = LeagueSettings(
    teams=12,
    qb=1,
    rb=2,
    wr=3,
    te=2,
    flex=2,
    superflex=1,
    ppr=0.5,
    te_premium=1.0,
)

KEY_2025_PLAYERS = [
    "Trey McBride",
    "Christian McCaffrey",
    "Josh Allen",
    "Bijan Robinson",
    "Jonathan Taylor",
    "Drake Maye",
    "Matthew Stafford",
    "Jahmyr Gibbs",
    "Trevor Lawrence",
    "Puka Nacua",
    "Kyle Pitts",
    "Travis Kelce",
]


def add_ranks(df):
    out = df.copy()
    out["overall_rank_band"] = (
        out.groupby(["replacement_band", "season"])["worp"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    out["pos_rank_band"] = (
        out.groupby(["replacement_band", "season", "position"])["worp"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    return out


def player_key(df):
    if "player_id" in df.columns:
        return ["season", "player_id"]
    return ["season", "player_name", "position"]


def spearman_rank(a, b):
    # pandas corr(method="spearman") does not require scipy.
    return a.corr(b, method="spearman")


print("=" * 110)
print("WoRP LAB — MARCO 4: REPLACEMENT BAND SENSITIVITY")
print("Bands: 3 vs 6 vs 9 | Official format | 2016-2025 | empirical Monte Carlo")
print("=" * 110)

all_rankings = []
all_weekly = []

for season in SEASONS:
    print(f"\nLoading {season} once...")
    season_df = load_nflverse_player_weeks([season], SETTINGS)

    for band in BANDS:
        print(f"  Running season={season} replacement_band={band}...")
        weekly, ranking = calculate_season_worp(
            season_df,
            SETTINGS,
            replacement_band=band,
            n_sims=N_SIMS,
            seed=SEED,
        )

        weekly = weekly.copy()
        ranking = ranking.copy()
        weekly["replacement_band"] = band
        ranking["replacement_band"] = band

        all_weekly.append(weekly)
        all_rankings.append(ranking)

rankings = pd.concat(all_rankings, ignore_index=True)
weekly = pd.concat(all_weekly, ignore_index=True)

rankings = add_ranks(rankings)

rankings.to_csv("worp_2016_2025_band_sensitivity_rankings.csv", index=False)
weekly.to_csv("worp_2016_2025_band_sensitivity_weekly.csv", index=False)

print("\nSaved:")
print("  worp_2016_2025_band_sensitivity_rankings.csv")
print("  worp_2016_2025_band_sensitivity_weekly.csv")


# -----------------------------------------------------------------------------
# 1. CONTROL REGRESSION: BAND 6 SHOULD MATCH FROZEN HISTORICAL RUN
# -----------------------------------------------------------------------------

print("\n" + "=" * 110)
print("1. BAND 6 CONTROL REGRESSION")
print("=" * 110)

control_path = "worp_2016_2025_rankings.csv"

if os.path.exists(control_path):
    control = pd.read_csv(control_path)
    b6 = rankings[rankings["replacement_band"] == 6].copy()

    keys = player_key(control)
    cols = keys + ["worp"]

    c = control[cols].rename(columns={"worp": "worp_control"})
    n = b6[cols].rename(columns={"worp": "worp_band6"})

    merged = c.merge(n, on=keys, how="inner")
    merged["abs_diff"] = (merged["worp_control"] - merged["worp_band6"]).abs()

    missing_control = len(c) - len(merged)
    missing_new = len(n) - len(merged)
    max_diff = merged["abs_diff"].max() if len(merged) else np.nan

    print(f"Matched rows: {len(merged)}")
    print(f"Missing from new band-6 run: {missing_control}")
    print(f"Extra/unmatched new band-6 rows: {missing_new}")
    print(f"Max absolute WoRP difference: {max_diff:.12f}")

    if missing_control == 0 and missing_new == 0 and max_diff < 1e-9:
        print("PASS: band=6 exactly reproduces frozen historical rankings.")
    elif max_diff < 1e-6 and missing_control == 0 and missing_new == 0:
        print("PASS (floating tolerance): band=6 reproduces frozen historical rankings.")
    else:
        print("WARNING: band=6 does NOT exactly reproduce the frozen control. Investigate before interpreting sensitivity.")
else:
    print(f"SKIP: {control_path} not found. Sensitivity still runs, but exact frozen regression was not checked.")


# -----------------------------------------------------------------------------
# 2. OVERALL DISTRIBUTION BY BAND
# -----------------------------------------------------------------------------

print("\n" + "=" * 110)
print("2. FULL-WINDOW WoRP DISTRIBUTION BY BAND")
print("=" * 110)

dist = (
    rankings.groupby(["replacement_band", "position"])["worp"]
    .agg(["count", "mean", "median", "max"])
    .round(4)
)
print(dist.to_string())


# -----------------------------------------------------------------------------
# 3. RANK CORRELATION VS BAND 6
# -----------------------------------------------------------------------------

print("\n" + "=" * 110)
print("3. YEAR-BY-YEAR RANK STABILITY VS BAND 6")
print("=" * 110)

corr_rows = []

for season in SEASONS:
    base = rankings[
        (rankings["season"] == season) &
        (rankings["replacement_band"] == 6)
    ].copy()

    keys = player_key(base)

    for band in [3, 9]:
        other = rankings[
            (rankings["season"] == season) &
            (rankings["replacement_band"] == band)
        ].copy()

        m = base[keys + ["worp", "overall_rank_band"]].merge(
            other[keys + ["worp", "overall_rank_band"]],
            on=keys,
            suffixes=("_b6", f"_b{band}")
        )

        corr_rows.append({
            "season": season,
            "band": band,
            "matched_players": len(m),
            "worp_spearman": spearman_rank(m["worp_b6"], m[f"worp_b{band}"]),
            "rank_spearman": spearman_rank(
                m["overall_rank_band_b6"],
                m[f"overall_rank_band_b{band}"]
            ),
            "median_abs_worp_delta": (m[f"worp_b{band}"] - m["worp_b6"]).abs().median(),
            "max_abs_worp_delta": (m[f"worp_b{band}"] - m["worp_b6"]).abs().max(),
        })

corr_df = pd.DataFrame(corr_rows)
print(corr_df.round(5).to_string(index=False))

print("\nFull-window summary:")
print(
    corr_df.groupby("band")
    .agg(
        mean_worp_spearman=("worp_spearman", "mean"),
        min_worp_spearman=("worp_spearman", "min"),
        mean_rank_spearman=("rank_spearman", "mean"),
        min_rank_spearman=("rank_spearman", "min"),
        median_of_median_abs_delta=("median_abs_worp_delta", "median"),
        max_abs_delta=("max_abs_worp_delta", "max"),
    )
    .round(5)
    .to_string()
)


# -----------------------------------------------------------------------------
# 4. TOP-24 OVERLAP VS BAND 6
# -----------------------------------------------------------------------------

print("\n" + "=" * 110)
print("4. TOP-24 OVERLAP VS BAND 6")
print("=" * 110)

overlap_rows = []

for season in SEASONS:
    base = rankings[
        (rankings["season"] == season) &
        (rankings["replacement_band"] == 6)
    ].nsmallest(24, "overall_rank_band")

    key_cols = ["player_name", "position"]
    base_set = set(map(tuple, base[key_cols].values.tolist()))

    for band in [3, 9]:
        other = rankings[
            (rankings["season"] == season) &
            (rankings["replacement_band"] == band)
        ].nsmallest(24, "overall_rank_band")

        other_set = set(map(tuple, other[key_cols].values.tolist()))
        overlap = len(base_set & other_set)

        overlap_rows.append({
            "season": season,
            "band": band,
            "top24_overlap": overlap,
            "top24_overlap_pct": overlap / 24,
        })

overlap_df = pd.DataFrame(overlap_rows)
print(overlap_df.to_string(index=False))
print("\nAverage overlap:")
print(
    overlap_df.groupby("band")[["top24_overlap", "top24_overlap_pct"]]
    .mean()
    .round(4)
    .to_string()
)


# -----------------------------------------------------------------------------
# 5. POSITIONAL LEADERS BY YEAR / BAND
# -----------------------------------------------------------------------------

print("\n" + "=" * 110)
print("5. POSITIONAL LEADERS BY YEAR / BAND")
print("=" * 110)

leaders = (
    rankings.sort_values(
        ["replacement_band", "season", "position", "worp"],
        ascending=[True, True, True, False]
    )
    .groupby(["replacement_band", "season", "position"], as_index=False)
    .first()
)

print(
    leaders[
        ["replacement_band", "season", "position", "player_name", "worp", "overall_rank_band"]
    ].to_string(index=False)
)


# -----------------------------------------------------------------------------
# 6. 2025 KEY SIGNALS
# -----------------------------------------------------------------------------

print("\n" + "=" * 110)
print("6. 2025 KEY SIGNALS")
print("=" * 110)

key25 = rankings[
    (rankings["season"] == 2025) &
    (rankings["player_name"].isin(KEY_2025_PLAYERS))
][
    [
        "replacement_band",
        "player_name",
        "position",
        "worp",
        "overall_rank_band",
        "pos_rank_band",
        "porp",
        "avg_replacement_points",
    ]
].sort_values(["player_name", "replacement_band"])

print(key25.round(4).to_string(index=False))


# -----------------------------------------------------------------------------
# 7. 2025 TOP 15 BY BAND
# -----------------------------------------------------------------------------

print("\n" + "=" * 110)
print("7. 2025 TOP 15 BY BAND")
print("=" * 110)

for band in BANDS:
    x = rankings[
        (rankings["season"] == 2025) &
        (rankings["replacement_band"] == band)
    ].nsmallest(15, "overall_rank_band")

    print(f"\nBAND {band}")
    print(
        x[
            ["overall_rank_band", "player_name", "position", "worp", "porp", "avg_replacement_points"]
        ].round(4).to_string(index=False)
    )


# -----------------------------------------------------------------------------
# 8. HISTORICAL TOP 25 BY BAND
# -----------------------------------------------------------------------------

print("\n" + "=" * 110)
print("8. HISTORICAL TOP 25 SEASONS BY BAND")
print("=" * 110)

for band in BANDS:
    x = rankings[rankings["replacement_band"] == band].nlargest(25, "worp")
    print(f"\nBAND {band}")
    print(
        x[
            ["season", "player_name", "position", "games", "worp", "overall_rank_band"]
        ].round(4).to_string(index=False)
    )


# -----------------------------------------------------------------------------
# 9. PLAYER-LEVEL DELTAS VS BAND 6
# -----------------------------------------------------------------------------

print("\n" + "=" * 110)
print("9. LARGEST PLAYER-LEVEL WoRP DELTAS VS BAND 6")
print("=" * 110)

base = rankings[rankings["replacement_band"] == 6].copy()
keys = player_key(base)

for band in [3, 9]:
    other = rankings[rankings["replacement_band"] == band].copy()

    m = base[keys + ["player_name", "position", "worp"]].merge(
        other[keys + ["worp"]],
        on=keys,
        suffixes=("_b6", f"_b{band}")
    )
    m["delta"] = m[f"worp_b{band}"] - m["worp_b6"]
    m["abs_delta"] = m["delta"].abs()

    print(f"\nBAND {band} vs 6 — largest absolute deltas")
    print(
        m.nlargest(20, "abs_delta")[
            ["season", "player_name", "position", "worp_b6", f"worp_b{band}", "delta", "abs_delta"]
        ].round(5).to_string(index=False)
    )


# -----------------------------------------------------------------------------
# 10. SIMPLE GATE SUMMARY
# -----------------------------------------------------------------------------

print("\n" + "=" * 110)
print("10. MARCO 4 DIAGNOSTIC GATE")
print("=" * 110)

summary = (
    corr_df.groupby("band")
    .agg(
        min_spearman=("worp_spearman", "min"),
        mean_spearman=("worp_spearman", "mean"),
        max_abs_worp_delta=("max_abs_worp_delta", "max"),
    )
    .join(
        overlap_df.groupby("band").agg(
            mean_top24_overlap=("top24_overlap", "mean"),
            min_top24_overlap=("top24_overlap", "min"),
        )
    )
)

print(summary.round(5).to_string())

print("\nInterpretation guide:")
print("- Strong robustness: rank correlations stay very high and Top-24 overlap remains high.")
print("- Some WoRP movement is expected: changing the replacement band changes replacement points by design.")
print("- A major reversal in positional hierarchy, historical leaders, or key 2025 signals is a yellow/red flag.")
print("- Do NOT change the frozen engine solely because one player's exact WoRP moves.")
print("- Band 6 remains the control; this script tests whether conclusions survive reasonable bands 3 and 9.")

print("\nMarco 4 replacement-band sensitivity run complete.")
