import os
import pandas as pd
import numpy as np

INPUT = "worp_2016_2025_rankings.csv"
OUTPUT = "worp_2016_2025_normalized.csv"

if not os.path.exists(INPUT):
    raise FileNotFoundError(
        f"{INPUT} not found. Put this script in the worp_lab_v0_2_1 folder."
    )

df = pd.read_csv(INPUT)

required = ["season", "player_name", "position", "games", "worp", "porp"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

x = df[df["games"] > 0].copy()

# Companion rate metrics. Raw season WoRP remains the canonical total-value metric.
x["worp_per_game"] = x["worp"] / x["games"]
x["porp_per_game"] = x["porp"] / x["games"]

# Era-neutral 17-game pace is presentation only, not a new WoRP definition.
x["worp_17g_pace"] = x["worp_per_game"] * 17
x["porp_17g_pace"] = x["porp_per_game"] * 17

# Ranking columns for historical comparison.
x["historical_worp_rank"] = x["worp"].rank(method="min", ascending=False).astype(int)
x["historical_worp_pg_rank"] = x["worp_per_game"].rank(method="min", ascending=False).astype(int)

x["season_worp_rank"] = (
    x.groupby("season")["worp"]
    .rank(method="min", ascending=False)
    .astype(int)
)
x["season_worp_pg_rank"] = (
    x.groupby("season")["worp_per_game"]
    .rank(method="min", ascending=False)
    .astype(int)
)

x["position_historical_worp_rank"] = (
    x.groupby("position")["worp"]
    .rank(method="min", ascending=False)
    .astype(int)
)
x["position_historical_worp_pg_rank"] = (
    x.groupby("position")["worp_per_game"]
    .rank(method="min", ascending=False)
    .astype(int)
)

x.to_csv(OUTPUT, index=False)

print("=" * 110)
print("WoRP LAB — MARCO 5: HISTORICAL NORMALIZATION")
print("Raw WoRP remains canonical | WoRP/game and 17-game pace are companion views")
print("=" * 110)

print(f"\nSaved {OUTPUT}")
print(f"Rows: {len(x)}")
print(f"Seasons: {int(x['season'].min())}-{int(x['season'].max())}")

print("\n" + "=" * 110)
print("1. HISTORICAL TOP 25 — RAW SEASON WoRP")
print("=" * 110)

cols = ["historical_worp_rank", "season", "player_name", "position", "games", "worp", "worp_per_game", "worp_17g_pace"]
print(
    x.nsmallest(25, "historical_worp_rank")[cols]
    .round({"worp": 4, "worp_per_game": 4, "worp_17g_pace": 4})
    .to_string(index=False)
)

print("\n" + "=" * 110)
print("2. HISTORICAL TOP 25 — WoRP PER GAME")
print("=" * 110)

cols = ["historical_worp_pg_rank", "season", "player_name", "position", "games", "worp", "worp_per_game", "worp_17g_pace"]
print(
    x.nsmallest(25, "historical_worp_pg_rank")[cols]
    .round({"worp": 4, "worp_per_game": 4, "worp_17g_pace": 4})
    .to_string(index=False)
)

print("\n" + "=" * 110)
print("3. HISTORICAL TOP 10 BY POSITION — WoRP/GAME")
print("=" * 110)

for pos in ["QB", "RB", "WR", "TE"]:
    p = x[x["position"] == pos].nsmallest(10, "position_historical_worp_pg_rank")
    print(f"\n{pos}")
    print(
        p[
            ["position_historical_worp_pg_rank", "season", "player_name", "games", "worp", "worp_per_game", "worp_17g_pace"]
        ]
        .round({"worp": 4, "worp_per_game": 4, "worp_17g_pace": 4})
        .to_string(index=False)
    )

print("\n" + "=" * 110)
print("4. RAW RANK vs PER-GAME RANK — BIGGEST MOVERS")
print("=" * 110)

# Restrict this diagnostic to substantial seasons so tiny samples do not dominate.
substantial = x[x["games"] >= 12].copy()
substantial["rank_delta_pg_minus_raw"] = (
    substantial["historical_worp_rank"] - substantial["historical_worp_pg_rank"]
)

print("\nBiggest risers when switching from raw WoRP to WoRP/game (12+ games):")
print(
    substantial.nlargest(20, "rank_delta_pg_minus_raw")[
        ["season", "player_name", "position", "games", "worp", "worp_per_game",
         "historical_worp_rank", "historical_worp_pg_rank", "rank_delta_pg_minus_raw"]
    ].round({"worp": 4, "worp_per_game": 4}).to_string(index=False)
)

print("\nBiggest fallers when switching from raw WoRP to WoRP/game (12+ games):")
print(
    substantial.nsmallest(20, "rank_delta_pg_minus_raw")[
        ["season", "player_name", "position", "games", "worp", "worp_per_game",
         "historical_worp_rank", "historical_worp_pg_rank", "rank_delta_pg_minus_raw"]
    ].round({"worp": 4, "worp_per_game": 4}).to_string(index=False)
)

print("\n" + "=" * 110)
print("5. ERA CHECK — TOP-50 REPRESENTATION")
print("=" * 110)

raw_top50 = x.nsmallest(50, "historical_worp_rank").copy()
pg_top50 = x.nsmallest(50, "historical_worp_pg_rank").copy()

def era(season):
    return "2016-2020 (16g era)" if season <= 2020 else "2021-2025 (17g era)"

raw_top50["era"] = raw_top50["season"].map(era)
pg_top50["era"] = pg_top50["season"].map(era)

era_table = pd.DataFrame({
    "raw_top50": raw_top50["era"].value_counts(),
    "per_game_top50": pg_top50["era"].value_counts(),
}).fillna(0).astype(int)

print(era_table.to_string())

print("\n" + "=" * 110)
print("6. YEARLY LEADERS — RAW vs WoRP/GAME")
print("=" * 110)

rows = []
for season in sorted(x["season"].unique()):
    s = x[x["season"] == season]
    raw = s.nlargest(1, "worp").iloc[0]
    pg = s.nlargest(1, "worp_per_game").iloc[0]
    rows.append({
        "season": season,
        "raw_leader": raw["player_name"],
        "raw_pos": raw["position"],
        "raw_games": int(raw["games"]),
        "raw_worp": raw["worp"],
        "pg_leader": pg["player_name"],
        "pg_pos": pg["position"],
        "pg_games": int(pg["games"]),
        "pg_worp_per_game": pg["worp_per_game"],
    })

leaders = pd.DataFrame(rows)
print(leaders.round({"raw_worp": 4, "pg_worp_per_game": 4}).to_string(index=False))

print("\n" + "=" * 110)
print("7. IMPORTANT HISTORICAL SEASONS")
print("=" * 110)

names = [
    "Patrick Mahomes",
    "Lamar Jackson",
    "Josh Allen",
    "Christian McCaffrey",
    "Travis Kelce",
    "Trey McBride",
    "Cooper Kupp",
    "David Johnson",
    "Todd Gurley",
]

key = x[x["player_name"].isin(names)].copy()
key = key[
    (key["worp"] >= 3.4) |
    (key["worp_per_game"] >= x["worp_per_game"].quantile(0.99))
]

print(
    key[
        ["season", "player_name", "position", "games", "worp", "worp_per_game",
         "worp_17g_pace", "historical_worp_rank", "historical_worp_pg_rank"]
    ]
    .sort_values("worp_per_game", ascending=False)
    .round({"worp": 4, "worp_per_game": 4, "worp_17g_pace": 4})
    .to_string(index=False)
)

print("\n" + "=" * 110)
print("8. NORMALIZATION GATE")
print("=" * 110)

raw16 = (raw_top50["season"] <= 2020).sum()
raw17 = (raw_top50["season"] >= 2021).sum()
pg16 = (pg_top50["season"] <= 2020).sum()
pg17 = (pg_top50["season"] >= 2021).sum()

print(f"Raw Top-50:      16-game era={raw16} | 17-game era={raw17}")
print(f"WoRP/game Top-50: 16-game era={pg16} | 17-game era={pg17}")

print("\nInterpretation:")
print("- Raw season WoRP measures total wins added over the season and remains canonical.")
print("- WoRP/game measures weekly dominance and is the preferred companion for cross-era comparisons.")
print("- 17-game pace is only a display normalization; do not sum or feed it back into the engine.")
print("- Players with very small game samples can rank highly per game, so UI should show games prominently.")
print("- For historical leaderboards, offer TOTAL and PER GAME views rather than replacing one with the other.")

print("\nMarco 5 historical normalization audit complete.")
