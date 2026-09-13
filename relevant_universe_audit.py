import pandas as pd

df = pd.read_csv("worp_2016_2025_rankings.csv")

POSITIONS = ["QB", "RB", "WR", "TE"]

# A player is considered economically relevant if his positional rank
# is no worse than the average end of the replacement pool.
relevant = df[
    df["pos_rank"] <= df["avg_replacement_pool_end"]
].copy()

print("=" * 100)
print("RELEVANT PLAYER UNIVERSE — STARTERS + REPLACEMENT BAND")
print("=" * 100)

print("\nFULL 2016-2025 SAMPLE")

for pos in POSITIONS:
    x = relevant[relevant["position"] == pos]

    print(
        f"{pos}: n={len(x):4d} | "
        f"mean WoRP={x['worp'].mean():.3f} | "
        f"median={x['worp'].median():.3f} | "
        f"positive={(x['worp'] > 0).mean() * 100:.1f}%"
    )


print("\n" + "=" * 100)
print("YEAR-BY-YEAR MEDIAN WoRP — RELEVANT UNIVERSE")
print("=" * 100)

median_table = (
    relevant.groupby(["season", "position"])["worp"]
    .median()
    .unstack()
    .reindex(columns=POSITIONS)
)

print(median_table.round(3).to_string())


print("\n" + "=" * 100)
print("YEAR-BY-YEAR MEAN WoRP — RELEVANT UNIVERSE")
print("=" * 100)

mean_table = (
    relevant.groupby(["season", "position"])["worp"]
    .mean()
    .unstack()
    .reindex(columns=POSITIONS)
)

print(mean_table.round(3).to_string())


print("\n" + "=" * 100)
print("POSITIVE WoRP RATE — RELEVANT UNIVERSE")
print("=" * 100)

for pos in POSITIONS:
    x = relevant[relevant["position"] == pos]
    positive = (x["worp"] > 0).sum()

    print(
        f"{pos}: {positive}/{len(x)} "
        f"({positive / len(x) * 100:.1f}%)"
    )


print("\n" + "=" * 100)
print("TOP-24 COMPOSITION BY SEASON")
print("=" * 100)

for season in sorted(relevant["season"].unique()):
    x = relevant[
        relevant["season"] == season
    ].sort_values("worp", ascending=False).head(24)

    counts = (
        x["position"]
        .value_counts()
        .reindex(POSITIONS, fill_value=0)
    )

    print(
        f"{season}: "
        + " | ".join(
            f"{p} {int(counts[p]):2d}"
            for p in POSITIONS
        )
    )


print("\n" + "=" * 100)
print("AVERAGE POSITION RANK OF LAST RELEVANT PLAYER")
print("=" * 100)

for season in sorted(relevant["season"].unique()):
    x = relevant[relevant["season"] == season]

    pieces = []

    for pos in POSITIONS:
        p = x[x["position"] == pos]

        if len(p):
            pieces.append(
                f"{pos} {int(p['pos_rank'].max())}"
            )

    print(f"{season}: " + " | ".join(pieces))


print("\n" + "=" * 100)
print("BOTTOM OF RELEVANT UNIVERSE — 2025")
print("=" * 100)

x = relevant[relevant["season"] == 2025]

for pos in POSITIONS:
    p = (
        x[x["position"] == pos]
        .sort_values("pos_rank")
        .tail(8)
    )

    print(f"\n{pos}")
    print(
        p[
            [
                "player_name",
                "pos_rank",
                "worp",
                "avg_replacement_effective_rank",
                "avg_replacement_pool_end",
            ]
        ].to_string(index=False)
    )


relevant.to_csv(
    "worp_2016_2025_relevant_universe.csv",
    index=False
)

print("\nSaved worp_2016_2025_relevant_universe.csv")
