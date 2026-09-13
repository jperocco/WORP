import pandas as pd

df = pd.read_csv("worp_2016_2025_rankings.csv")

POSITIONS = ["QB", "RB", "WR", "TE"]

print("=" * 100)
print("1. POSITION REPRESENTATION BY SEASON")
print("=" * 100)

for season in sorted(df["season"].unique()):
    x = df[df["season"] == season].sort_values("worp", ascending=False)

    print(f"\n{season}")
    for cutoff in [12, 24, 50]:
        counts = (
            x.head(cutoff)["position"]
            .value_counts()
            .reindex(POSITIONS, fill_value=0)
        )
        print(
            f"Top {cutoff:>2}: "
            + " | ".join(f"{p} {int(counts[p]):>2}" for p in POSITIONS)
        )


print("\n" + "=" * 100)
print("2. YEARLY POSITION WoRP — MAX / MEDIAN")
print("=" * 100)

rows = []

for season in sorted(df["season"].unique()):
    for pos in POSITIONS:
        x = df[(df["season"] == season) & (df["position"] == pos)]

        rows.append(
            {
                "season": season,
                "position": pos,
                "max_worp": x["worp"].max(),
                "median_worp": x["worp"].median(),
            }
        )

summary = pd.DataFrame(rows)

print(
    summary.pivot(
        index="season",
        columns="position",
        values="max_worp"
    ).round(3).to_string()
)

print("\nMEDIAN WoRP")
print(
    summary.pivot(
        index="season",
        columns="position",
        values="median_worp"
    ).round(3).to_string()
)


print("\n" + "=" * 100)
print("3. REPLACEMENT EFFECTIVE RANK BY SEASON / POSITION")
print("=" * 100)

replacement = (
    df.groupby(["season", "position"])["avg_replacement_effective_rank"]
    .median()
    .unstack()
    .reindex(columns=POSITIONS)
)

print(replacement.round(2).to_string())


print("\n" + "=" * 100)
print("4. REPLACEMENT POINTS BY SEASON / POSITION")
print("=" * 100)

replacement_points = (
    df.groupby(["season", "position"])["avg_replacement_points"]
    .median()
    .unstack()
    .reindex(columns=POSITIONS)
)

print(replacement_points.round(2).to_string())


print("\n" + "=" * 100)
print("5. TOP-50 POSITION SHARE — FULL 2016-2025 WINDOW")
print("=" * 100)

top50_rows = []

for season in sorted(df["season"].unique()):
    x = df[df["season"] == season].sort_values("worp", ascending=False).head(50)
    top50_rows.append(x)

top50 = pd.concat(top50_rows)

counts = top50["position"].value_counts().reindex(POSITIONS, fill_value=0)
shares = counts / len(top50)

for pos in POSITIONS:
    print(
        f"{pos}: {int(counts[pos])} / {len(top50)} "
        f"({shares[pos] * 100:.1f}%)"
    )


print("\n" + "=" * 100)
print("6. NEGATIVE WoRP RATE")
print("=" * 100)

for pos in POSITIONS:
    x = df[df["position"] == pos]
    rate = (x["worp"] < 0).mean()
    print(f"{pos}: {rate * 100:.1f}% ({(x['worp'] < 0).sum()} / {len(x)})")


print("\nStructural audit complete.")
