"""Small unit-style check for the V0.1.1 REG-only rule without network access."""
import pandas as pd
from worp_engine import LeagueSettings, score_nflverse_weekly


def apply_reg_rule(df: pd.DataFrame) -> pd.DataFrame:
    if "season_type" not in df.columns:
        raise ValueError("missing season_type")
    season_type = df["season_type"].astype(str).str.upper().str.strip()
    return df.loc[season_type.eq("REG")].copy()


raw = pd.DataFrame(
    {
        "season": [2025, 2025, 2025],
        "week": [18, 19, 22],
        "season_type": ["REG", "POST", "POST"],
        "player_id": ["x", "x", "x"],
        "player_name": ["Test QB"] * 3,
        "position": ["QB"] * 3,
        "passing_yards": [250, 300, 350],
        "passing_tds": [2, 3, 4],
    }
)
filtered = apply_reg_rule(raw)
assert filtered["week"].tolist() == [18]
pts = score_nflverse_weekly(filtered, LeagueSettings())
assert len(pts) == 1
print("PASS: REG-only filter excludes postseason rows")
