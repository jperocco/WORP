import pandas as pd
import numpy as np

df = pd.read_csv("worp_2016_2025_relevant_universe.csv")

POSITIONS = ["QB", "RB", "WR", "TE"]

# Avoid unstable ratios when PORP is very close to zero.
x = df[df["porp"] > 1.0].copy()
x["worp_per_porp"] = x["worp"] / x["porp"]

print("=" * 100)
print("PORP -> WoRP CONVERSION AUDIT")
print("=" * 100)

print("\n1. FULL 2016-2025 RELEVANT UNIVERSE")
print("-" * 100)

for pos in POSITIONS:
    p = x[x["position"] == pos]
    print(
        f"{pos}: n={len(p):4d} | "
        f"mean PORP={p['porp'].mean():7.2f} | "
        f"median PORP={p['porp'].median():7.2f} | "
        f"mean WoRP={p['worp'].mean():.3f} | "
        f"median WoRP={p['worp'].median():.3f} | "
        f"mean WoRP/PORP={p['worp_per_porp'].mean():.5f} | "
        f"median={p['worp_per_porp'].median():.5f}"
    )

print("\n" + "=" * 100)
print("2. YEAR-BY-YEAR MEDIAN WoRP/PORP")
print("=" * 100)

table = (
    x.groupby(["season", "position"])["worp_per_porp"]
    .median()
    .unstack()
    .reindex(columns=POSITIONS)
)
print(table.round(5).to_string())

print("\n" + "=" * 100)
print("3. YEAR-BY-YEAR MEDIAN PORP")
print("=" * 100)

table = (
    x.groupby(["season", "position"])["porp"]
    .median()
    .unstack()
    .reindex(columns=POSITIONS)
)
print(table.round(2).to_string())

print("\n" + "=" * 100)
print("4. WoRP/PORP BY PORP BUCKET")
print("=" * 100)

x["porp_bucket"] = pd.cut(
    x["porp"],
    bins=[1, 25, 50, 100, 150, 250, np.inf],
    labels=["1-25", "25-50", "50-100", "100-150", "150-250", "250+"],
    include_lowest=True,
)

bucket = (
    x.groupby(["porp_bucket", "position"], observed=True)
    .agg(
        n=("worp", "size"),
        median_porp=("porp", "median"),
        median_worp=("worp", "median"),
        median_conversion=("worp_per_porp", "median"),
    )
    .reset_index()
)

for bucket_name in bucket["porp_bucket"].unique():
    print(f"\nPORP {bucket_name}")
    b = bucket[bucket["porp_bucket"] == bucket_name]
    for _, row in b.iterrows():
        print(
            f"{row['position']}: "
            f"n={int(row['n']):3d} | "
            f"PORP={row['median_porp']:7.2f} | "
            f"WoRP={row['median_worp']:.3f} | "
            f"WoRP/PORP={row['median_conversion']:.5f}"
        )

print("\n" + "=" * 100)
print("5. HIGH-VALUE PLAYERS — PORP >= 100")
print("=" * 100)

elite = x[x["porp"] >= 100]

for pos in POSITIONS:
    p = elite[elite["position"] == pos]
    if len(p):
        print(
            f"{pos}: n={len(p):3d} | "
            f"median PORP={p['porp'].median():.2f} | "
            f"median WoRP={p['worp'].median():.3f} | "
            f"median WoRP/PORP={p['worp_per_porp'].median():.5f}"
        )

print("\n" + "=" * 100)
print("6. EXTREME CONVERSION RATIOS")
print("=" * 100)

cols = [
    "season",
    "player_name",
    "position",
    "porp",
    "worp",
    "worp_per_porp",
]

print("\nHIGHEST")
print(
    x.sort_values("worp_per_porp", ascending=False)[cols]
    .head(15)
    .to_string(index=False)
)

print("\nLOWEST")
print(
    x.sort_values("worp_per_porp")[cols]
    .head(15)
    .to_string(index=False)
)

print("\nPORP -> WoRP conversion audit complete.")
