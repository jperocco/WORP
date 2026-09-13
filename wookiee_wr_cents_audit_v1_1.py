#!/usr/bin/env python3
"""
WOOKIEE WR "CENTAVOS" AUDIT V1.1

Question:
Where on the WR curve do differences in realized WoRP still matter materially,
and where do they become small enough that exact rank distinctions add little?

IMPORTANT:
- This tests REALIZED VALUE FLATNESS only.
- It does NOT test identification, Captura, waiver replacement, fungibility,
  market value, trades, or roster construction.
- flatness != fungibility

Input:
  wookiee_wr_season_week_player_metrics.csv
produced by the validated Wookiee-native 2023-2025 audit.

No WoRP engine rerun is needed.
"""

from pathlib import Path
import math
import numpy as np
import pandas as pd

INPUT = Path("wookiee_wr_season_week_player_metrics.csv")
OUT_PROFILE = Path("wookiee_wr_cents_rank_profile.csv")
OUT_WINDOWS = Path("wookiee_wr_cents_windows.csv")
OUT_ANCHORS = Path("wookiee_wr_cents_anchor_costs.csv")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing {INPUT}. Run this script in the folder containing the cached "
        "Wookiee player-metrics CSV from Natural Tiers Audit V1."
    )

df = pd.read_csv(INPUT)

# Robust column detection.
pos_col = next((c for c in ["position", "pos"] if c in df.columns), None)
rank_col = next((c for c in ["pos_rank", "position_rank", "rank"] if c in df.columns), None)
worp_col = next((c for c in ["season_worp", "worp"] if c in df.columns), None)
season_col = next((c for c in ["season", "year"] if c in df.columns), None)

missing = [
    name for name, col in [
        ("pos_rank", rank_col),
        ("season_worp", worp_col), ("season", season_col)
    ] if col is None
]
if missing:
    raise ValueError(f"Required columns not found: {missing}\nColumns: {list(df.columns)}")

# The Natural Tiers cache is already WR-only and therefore may not contain
# a position column. If position exists, filter defensively; otherwise use
# the cache as-is.
if pos_col is not None:
    wr = df[df[pos_col].astype(str).str.upper().eq("WR")].copy()
else:
    wr = df.copy()
wr[rank_col] = pd.to_numeric(wr[rank_col], errors="coerce")
wr[worp_col] = pd.to_numeric(wr[worp_col], errors="coerce")
wr = wr.dropna(subset=[rank_col, worp_col])
wr[rank_col] = wr[rank_col].astype(int)

# Rank-level historical profile: equal weight per season-rank observation.
profile = (
    wr.groupby(rank_col)
      .agg(seasons=(season_col, "nunique"),
           mean_worp=(worp_col, "mean"),
           median_worp=(worp_col, "median"),
           sd_worp=(worp_col, "std"))
      .reset_index()
      .rename(columns={rank_col: "pos_rank"})
      .sort_values("pos_rank")
)
profile.to_csv(OUT_PROFILE, index=False)

# ---------------------------------------------------------------------
# Economic-magnitude view
# ---------------------------------------------------------------------
# We intentionally do NOT invent a universal "materiality = X WoRP" cutoff.
# Instead, show the actual realized WoRP cost of moving right by 3/6/12/18 ranks.
# This lets us see when rank precision becomes "cents" without smuggling in
# an arbitrary economic threshold.
lookup = profile.set_index("pos_rank")["mean_worp"].to_dict()

rows = []
for r in range(1, 91):
    if r not in lookup:
        continue
    for step in [3, 6, 12, 18]:
        r2 = r + step
        if r2 in lookup:
            rows.append({
                "start_rank": r,
                "end_rank": r2,
                "rank_gap": step,
                "start_mean_worp": lookup[r],
                "end_mean_worp": lookup[r2],
                "worp_cost": lookup[r] - lookup[r2],
                "worp_cost_per_rank": (lookup[r] - lookup[r2]) / step,
            })
windows = pd.DataFrame(rows)
windows.to_csv(OUT_WINDOWS, index=False)

# Anchors chosen BEFORE seeing this script's output because they correspond to
# the region already under discussion, not because they optimize a result.
anchors = [1, 8, 12, 20, 24, 30, 36, 40, 42, 45, 48, 50, 54, 55, 60, 66, 72, 78, 84, 90]
anchor_rows = []
for a in anchors:
    if a not in lookup:
        continue
    for b in anchors:
        if b <= a or b not in lookup:
            continue
        if (a, b) in [(1,8),(8,20),(20,40),(30,40),(30,50),(36,48),
                      (40,50),(40,55),(42,54),(45,54),(48,60),(50,60),
                      (55,60),(55,72),(60,72),(60,84),(60,90),(72,90)]:
            anchor_rows.append({
                "from_rank": a,
                "to_rank": b,
                "from_mean_worp": lookup[a],
                "to_mean_worp": lookup[b],
                "realized_worp_difference": lookup[a] - lookup[b],
            })
anchors_df = pd.DataFrame(anchor_rows)
anchors_df.to_csv(OUT_ANCHORS, index=False)

# Local 12-rank cost, summarized by broad zones. These zones are descriptive
# reporting windows only, NOT tiers.
w12 = windows[windows["rank_gap"].eq(12)].copy()
zones = [(1,20), (21,35), (30,50), (36,55), (41,60), (55,72), (60,78)]
zone_rows = []
for lo, hi in zones:
    z = w12[w12["start_rank"].between(lo, hi)]
    if len(z):
        zone_rows.append({
            "start_rank_zone": f"WR{lo}-WR{hi}",
            "n_comparisons": len(z),
            "median_12rank_worp_cost": z["worp_cost"].median(),
            "mean_12rank_worp_cost": z["worp_cost"].mean(),
            "min_12rank_worp_cost": z["worp_cost"].min(),
            "max_12rank_worp_cost": z["worp_cost"].max(),
        })
zone_df = pd.DataFrame(zone_rows)

# Year-by-year sanity check for selected comparisons.
pairs = [(1,8),(8,20),(20,40),(30,40),(30,50),(36,48),
         (40,50),(40,55),(45,54),(48,60),(55,72),(60,72)]
year_rows = []
for season, g in wr.groupby(season_col):
    d = g.groupby(rank_col)[worp_col].mean().to_dict()
    for a,b in pairs:
        if a in d and b in d:
            year_rows.append({
                "season": season,
                "from_rank": a,
                "to_rank": b,
                "worp_difference": d[a] - d[b]
            })
year_df = pd.DataFrame(year_rows)

print("=" * 110)
print('WOOKIEE WR "CENTAVOS" AUDIT V1.1')
print("=" * 110)
print("Question: where do exact WR-rank differences still carry meaningful realized WoRP?")
print("This is NOT an identification/Captura/fungibility test.")
print("flatness != fungibility")
print()
print(f"WR player-seasons: {len(wr):,}")
print(f"Seasons: {sorted(wr[season_col].unique().tolist())}")
print(f"Rank profile: WR{profile.pos_rank.min()}-WR{profile.pos_rank.max()}")
print()

print("=" * 110)
print("1. SELECTED RANK PROFILE — REALIZED SEASON WoRP")
print("=" * 110)
sel = profile[profile["pos_rank"].isin(anchors)][["pos_rank","seasons","mean_worp","median_worp"]].copy()
sel["rank"] = "WR" + sel["pos_rank"].astype(str)
print(sel[["rank","seasons","mean_worp","median_worp"]].to_string(
    index=False,
    formatters={"mean_worp":"{:.3f}".format, "median_worp":"{:.3f}".format}
))

print()
print("=" * 110)
print("2. PRE-SPECIFIED ANCHOR DIFFERENCES")
print("=" * 110)
if len(anchors_df):
    show = anchors_df.copy()
    show["comparison"] = "WR" + show["from_rank"].astype(str) + " -> WR" + show["to_rank"].astype(str)
    print(show[["comparison","from_mean_worp","to_mean_worp","realized_worp_difference"]].to_string(
        index=False,
        formatters={
            "from_mean_worp":"{:.3f}".format,
            "to_mean_worp":"{:.3f}".format,
            "realized_worp_difference":"{:+.3f}".format
        }
    ))

print()
print("=" * 110)
print("3. 12-RANK MARGINAL COST BY DESCRIPTIVE ZONE")
print("=" * 110)
print("These are reporting windows, NOT natural tiers.")
print(zone_df.to_string(
    index=False,
    formatters={
        "median_12rank_worp_cost":"{:.3f}".format,
        "mean_12rank_worp_cost":"{:.3f}".format,
        "min_12rank_worp_cost":"{:.3f}".format,
        "max_12rank_worp_cost":"{:.3f}".format,
    }
))

print()
print("=" * 110)
print("4. YEAR-BY-YEAR SANITY CHECK")
print("=" * 110)
if len(year_df):
    piv = year_df.pivot_table(
        index=["from_rank","to_rank"], columns="season",
        values="worp_difference", aggfunc="mean"
    ).reset_index()
    piv.insert(0, "comparison", "WR" + piv["from_rank"].astype(str) + " -> WR" + piv["to_rank"].astype(str))
    piv = piv.drop(columns=["from_rank","to_rank"])
    for c in piv.columns[1:]:
        piv[c] = piv[c].map(lambda x: f"{x:+.3f}" if pd.notna(x) else "")
    print(piv.to_string(index=False))

print()
print("=" * 110)
print("5. INTERPRETATION GATE")
print("=" * 110)
print("""
DO NOT let this script auto-declare a universal threshold.

Read the output in this order:
1) Is the realized WoRP cost large on the left side of the curve?
2) Does that cost materially compress as rank moves right?
3) In WR30-WR50, are we already discussing small realized differences?
4) Does WR55/WR60 onward become flatter still?
5) Are those patterns reasonably consistent across 2023, 2024 and 2025?

Possible decision:
- ADVANCE: clear compression in economic magnitude, with a broad flat-value region.
- PARK: differences decline smoothly but no useful economic regime emerges.
- KILL discrete tiers: exact breakpoint labels add precision without useful magnitude.

CRITICAL:
Even if WR30-WR50 is flat in realized WoRP, DO NOT call it fungible.
Identification difficulty / Captura remains untested and may be the entire story in that range.
""")

print("Saved:")
for p in [OUT_PROFILE, OUT_WINDOWS, OUT_ANCHORS]:
    print(f"  {p}")
