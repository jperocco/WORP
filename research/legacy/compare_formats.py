import pandas as pd

from worp_engine import LeagueSettings, calculate_season_worp
from nflverse_loader import load_nflverse_player_weeks


FORMATS = {
    "A_1QB_Start8": LeagueSettings(
        teams=12,
        qb=1,
        rb=2,
        wr=2,
        te=1,
        flex=2,
        superflex=0,
        ppr=0.5,
        te_premium=0.0,
    ),
    "B_1QB_Start11": LeagueSettings(
        teams=12,
        qb=1,
        rb=2,
        wr=3,
        te=1,
        flex=4,
        superflex=0,
        ppr=0.5,
        te_premium=0.0,
    ),
    "C_SF_1TE": LeagueSettings(
        teams=12,
        qb=1,
        rb=2,
        wr=3,
        te=1,
        flex=3,
        superflex=1,
        ppr=0.5,
        te_premium=0.0,
    ),
    "D_SF_2TE_TEP": LeagueSettings(
        teams=12,
        qb=1,
        rb=2,
        wr=3,
        te=2,
        flex=2,
        superflex=1,
        ppr=0.5,
        te_premium=1.0,
    ),
}


season = 2025
all_rankings = []

for format_name, settings in FORMATS.items():
    print("\n" + "=" * 90)
    print(format_name)
    print("=" * 90)

    df = load_nflverse_player_weeks([season], settings)

    weekly, ranking = calculate_season_worp(
        df,
        settings,
        replacement_band=6,
        n_sims=8000,
        seed=7,
    )

    ranking = ranking.copy()
    ranking["format"] = format_name
    all_rankings.append(ranking)

    print(
        ranking[
            [
                "overall_rank",
                "player_name",
                "position",
                "games",
                "fantasy_points",
                "worp",
            ]
        ]
        .head(15)
        .to_string(index=False)
    )


combined = pd.concat(all_rankings, ignore_index=True)

combined.to_csv("worp_2025_format_comparison.csv", index=False)


players = [
    "Trey McBride",
    "Christian McCaffrey",
    "Josh Allen",
    "Bijan Robinson",
    "Drake Maye",
    "Puka Nacua",
    "Jaxon Smith-Njigba",
    "Kyle Pitts",
    "Travis Kelce",
]

focus = combined[combined["player_name"].isin(players)].copy()

worp_table = focus.pivot(
    index=["player_name", "position"],
    columns="format",
    values="worp",
)

rank_table = focus.pivot(
    index=["player_name", "position"],
    columns="format",
    values="overall_rank",
)

print("\n\n" + "=" * 90)
print("SELECTED PLAYERS — WoRP")
print("=" * 90)
print(worp_table.round(3).to_string())

print("\n\n" + "=" * 90)
print("SELECTED PLAYERS — OVERALL RANK")
print("=" * 90)
print(rank_table.to_string())


print("\n\n" + "=" * 90)
print("TOP PLAYER BY POSITION / FORMAT")
print("=" * 90)

for format_name in FORMATS:
    x = combined[combined["format"] == format_name]

    print(f"\n{format_name}")

    for pos in ["QB", "RB", "WR", "TE"]:
        p = x[x["position"] == pos].sort_values("worp", ascending=False).head(1)

        if len(p):
            row = p.iloc[0]
            print(
                f"{pos}: {row['player_name']} "
                f"| WoRP {row['worp']:.3f} "
                f"| Overall #{int(row['overall_rank'])}"
            )


print("\nSaved worp_2025_format_comparison.csv")
