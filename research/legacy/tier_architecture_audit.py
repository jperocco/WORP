from pathlib import Path
import pandas as pd
import numpy as np

FILE = Path("worp_2016_2025_rankings.csv")
TEAMS = 12
SEASONS = range(2016, 2026)
SPOT_COUNTS = range(4, 9)

if not FILE.exists():
    raise SystemExit(f"ERRO: não encontrei {FILE.name} na pasta atual.")

df = pd.read_csv(FILE)
need = {"season", "position", "worp"}
missing = need - set(df.columns)
if missing:
    raise SystemExit(f"ERRO: CSV sem colunas necessárias: {sorted(missing)}")

wr = df[(df["position"] == "WR") & (df["season"].isin(SEASONS))].copy()

# Prefer frozen positional rank if present; otherwise calculate from season WoRP.
if "pos_rank" not in wr.columns:
    wr["pos_rank"] = (
        wr.groupby("season")["worp"]
          .rank(method="first", ascending=False)
          .astype(int)
    )

# 12-team roster-relative tier: ranks 1-12 = WR1*, 13-24 = WR2*, etc.
wr["roster_tier"] = ((wr["pos_rank"] - 1) // TEAMS + 1).astype(int)

tier = (
    wr.groupby(["season", "roster_tier"])
      .agg(
          mean_worp=("worp", "mean"),
          median_worp=("worp", "median"),
          min_worp=("worp", "min"),
          max_worp=("worp", "max"),
          n=("worp", "size"),
      )
      .reset_index()
)

# We intentionally do NOT define waiver yet.
# First gate: quantify the structural value curve of WR1*, WR2*, WR3*...
summary = (
    tier.groupby("roster_tier")
        .agg(
            seasons=("season", "nunique"),
            avg_tier_mean_worp=("mean_worp", "mean"),
            median_tier_mean_worp=("mean_worp", "median"),
            avg_tier_median_worp=("median_worp", "mean"),
        )
        .reset_index()
)

summary["marginal_drop_vs_prev"] = (
    summary["avg_tier_mean_worp"].shift(1) - summary["avg_tier_mean_worp"]
)

print("=" * 82)
print("WR TIER ARCHITECTURE AUDIT — PROVOCAÇÃO / NÃO ALTERA O ENGINE")
print("12 teams | 2016-2025 | tiers defined by 12-player rank bands")
print("=" * 82)

print("\n1. HISTORICAL WR TIER CURVE")
print(summary.head(10).to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print("\n2. YEAR-BY-YEAR MEAN WoRP — WR1* TO WR8*")
pivot = tier[tier["roster_tier"].between(1, 8)].pivot(
    index="season", columns="roster_tier", values="mean_worp"
)
pivot.columns = [f"WR{int(c)}*" for c in pivot.columns]
print(pivot.to_string(float_format=lambda x: f"{x:.4f}"))

print("\n3. WITHIN WR1* — HOW DIFFERENT ARE WR1 AND WR12?")
top = wr[wr["pos_rank"].between(1, 12)].copy()
inside = (
    top.groupby("pos_rank")["worp"]
       .agg(["mean", "median", "min", "max", "count"])
       .reset_index()
)
print(inside.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

wr1 = inside.loc[inside["pos_rank"] == 1, "mean"].iloc[0]
wr12 = inside.loc[inside["pos_rank"] == 12, "mean"].iloc[0]
print(f"\nMean WR1 minus mean WR12: {wr1 - wr12:.4f} WoRP")
print(f"WR12 retains {100 * wr12 / wr1:.1f}% of WR1 mean WoRP" if wr1 else "")

print("\n4. ARCHITECTURE SETUP — 4 TO 8 WR ROSTER SPOTS")
print("We are NOT declaring a winner yet because waiver availability is not defined.")
print("This table shows exactly how many replacement/waiver spots Strategy A would require.")
rows = []
for spots in SPOT_COUNTS:
    rows.append({
        "WR roster spots": spots,
        "A: WR1* assets": min(3, spots),
        "A: waiver spots": max(0, spots - 3),
        "B: WR1* assets": 1,
        "B: WR3* assets": max(0, spots - 1),
    })
print(pd.DataFrame(rows).to_string(index=False))

tier.to_csv("wr_tier_by_season.csv", index=False)
summary.to_csv("wr_tier_summary.csv", index=False)
inside.to_csv("wr1_within_tier.csv", index=False)

print("\nSaved:")
print("  wr_tier_by_season.csv")
print("  wr_tier_summary.csv")
print("  wr1_within_tier.csv")
print("\nGATE:")
print("First inspect the tier curve and WR1*-internal spread.")
print("Only after that do we define a realistic waiver pool and run A vs B.")
