import pandas as pd

from worp_engine import LeagueSettings, calculate_season_worp
from nflverse_loader import load_nflverse_player_weeks


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

SEASONS = list(range(2016, 2026))

all_rankings = []
all_weekly = []

for season in SEASONS:
    print("\n" + "=" * 90)
    print(f"SEASON {season}")
    print("=" * 90)

    df = load_nflverse_player_weeks([season], SETTINGS)

    weekly, ranking = calculate_season_worp(
        df,
        SETTINGS,
        replacement_band=6,
        n_sims=8000,
        seed=7,
    )

    ranking = ranking.copy()
    ranking["season"] = season

    weekly = weekly.copy()
    weekly["season"] = season

    all_rankings.append(ranking)
    all_weekly.append(weekly)

    print(
        ranking[
            [
                "overall_rank",
                "player_name",
                "position",
                "games",
                "fantasy_points",
                "worp",
                "avg_replacement_points",
                "avg_replacement_effective_rank",
                "avg_replacement_win_prob",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


rankings = pd.concat(all_rankings, ignore_index=True)
weekly = pd.concat(all_weekly, ignore_index=True)

rankings.to_csv("worp_2016_2025_rankings.csv", index=False)
weekly.to_csv("worp_2016_2025_weekly.csv", index=False)


print("\n\n" + "=" * 90)
print("TOP 25 HISTORICAL SEASONS BY WoRP")
print("=" * 90)

print(
    rankings[
        [
            "season",
            "player_name",
            "position",
            "games",
            "fantasy_points",
            "worp",
            "overall_rank",
        ]
    ]
    .sort_values("worp", ascending=False)
    .head(25)
    .to_string(index=False)
)


print("\n\n" + "=" * 90)
print("TOP WoRP BY POSITION")
print("=" * 90)

for pos in ["QB", "RB", "WR", "TE"]:
    x = (
        rankings[rankings["position"] == pos]
        .sort_values("worp", ascending=False)
        .head(10)
    )

    print(f"\n{pos}")
    print(
        x[
            [
                "season",
                "player_name",
                "games",
                "fantasy_points",
                "worp",
            ]
        ].to_string(index=False)
    )


print("\n\n" + "=" * 90)
print("YEARLY POSITION LEADER")
print("=" * 90)

for season in SEASONS:
    x = rankings[rankings["season"] == season]

    print(f"\n{season}")

    for pos in ["QB", "RB", "WR", "TE"]:
        p = (
            x[x["position"] == pos]
            .sort_values("worp", ascending=False)
            .head(1)
        )

        if len(p):
            row = p.iloc[0]
            print(
                f"{pos}: {row['player_name']} "
                f"| WoRP {row['worp']:.3f} "
                f"| Overall #{int(row['overall_rank'])}"
            )


print("\nSaved worp_2016_2025_rankings.csv and worp_2016_2025_weekly.csv")
