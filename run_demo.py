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

if __name__ == "__main__":
    season = 2025
    print("WoRP Lab V0.2.1 — empirical win model, REG only")
    print("Loading nflverse weekly stats...", season)
    df = load_nflverse_player_weeks([season], SETTINGS)
    weekly, ranking = calculate_season_worp(
        df,
        SETTINGS,
        replacement_band=6,
        n_sims=8000,
        seed=7,
    )
    print("\nTop 30 by WoRP")
    print(ranking.head(30).to_string(index=False))
    ranking.to_csv(f"worp_{season}_ranking.csv", index=False)
    weekly.to_csv(f"worp_{season}_weekly.csv", index=False)
    print(f"\nSaved worp_{season}_ranking.csv and worp_{season}_weekly.csv")
