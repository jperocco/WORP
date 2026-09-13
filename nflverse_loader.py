from __future__ import annotations
import pandas as pd
from worp_engine import LeagueSettings, score_nflverse_weekly


def load_nflverse_player_weeks(seasons, settings: LeagueSettings) -> pd.DataFrame:
    """Load nflverse weekly player stats through nflreadpy and normalize for WoRP Lab."""
    try:
        import nflreadpy as nfl
    except ImportError as exc:
        raise RuntimeError("Install dependencies first: pip install -r requirements.txt") from exc

    raw = nfl.load_player_stats(list(seasons), summary_level="week")
    df = raw.to_pandas() if hasattr(raw, "to_pandas") else pd.DataFrame(raw)

    # Common nflverse naming fallbacks.
    rename = {}
    if "player_display_name" in df.columns:
        rename["player_display_name"] = "player_name"
    elif "player_name" not in df.columns and "player" in df.columns:
        rename["player"] = "player_name"
    if "player_id" not in df.columns and "player_id" not in rename:
        for candidate in ["gsis_id", "player_gsis_id"]:
            if candidate in df.columns:
                rename[candidate] = "player_id"
                break
    df = df.rename(columns=rename)

    # WoRP Lab V0.1.1: regular-season only. nflverse weekly player stats
    # include postseason rows using the same season/week fields, so filtering by
    # week number alone is not robust. Require and use season_type explicitly.
    if "season_type" not in df.columns:
        raise ValueError(
            "nflverse weekly data is missing season_type; cannot safely exclude postseason rows"
        )
    season_type = df["season_type"].astype(str).str.upper().str.strip()
    df = df.loc[season_type.eq("REG")].copy()

    required_identity = ["season", "week", "player_id", "player_name", "position"]
    missing = [c for c in required_identity if c not in df.columns]
    if missing:
        raise ValueError(f"nflverse data missing expected identity columns: {missing}")

    df["fantasy_points"] = score_nflverse_weekly(df, settings)
    keep = required_identity + ["fantasy_points"]
    if "team" in df.columns:
        keep.insert(5, "team")
    return df[keep].copy()
