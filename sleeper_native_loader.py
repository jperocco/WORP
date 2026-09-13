import json
import urllib.request
from collections import defaultdict

API_V1 = "https://api.sleeper.app/v1"
WEEKLY_ENDPOINTS = (
    "https://api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular",
    "https://api.sleeper.app/v1/stats/nfl/regular/{season}/{week}",
)
POSITIONS = {"QB", "RB", "WR", "TE"}

def _get_json(url, timeout=30):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "WoRP-Lab-Sleeper-Native/0.5"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def _try_json(urls):
    last = None
    for url in urls:
        try:
            return _get_json(url), url
        except Exception as exc:
            last = exc
    raise RuntimeError(f"All Sleeper stats endpoint candidates failed. Last error: {last}")

def fetch_player_map():
    return _get_json(f"{API_V1}/players/nfl")

def normalize_stats_payload(payload):
    """
    Normalize Sleeper weekly stats to:
        {player_id: stat_dict}
    """
    out = {}

    if isinstance(payload, dict):
        source = []
        for key, value in payload.items():
            if isinstance(value, dict):
                row = dict(value)
                row.setdefault("player_id", key)
                source.append(row)
    elif isinstance(payload, list):
        source = payload
    else:
        source = []

    for row in source:
        if not isinstance(row, dict):
            continue

        player = row.get("player") or {}
        pid = row.get("player_id") or player.get("player_id")
        if pid is None:
            continue

        stats = row.get("stats")
        if stats is None:
            stats = {
                k: v for k, v in row.items()
                if k not in {
                    "player_id", "player", "team", "position",
                    "season", "week", "category", "game_id",
                }
            }

        if isinstance(stats, dict):
            out[str(pid)] = stats

    return out

def score_stats_exact(stats, scoring_settings):
    """
    Canonical Sleeper-native scoring contract validated by the 3-year audit:
        fantasy_points = Σ stats[key] * scoring_settings[key]

    No nflverse translation layer and no aliases.
    """
    total = 0.0
    for key, raw_weight in (scoring_settings or {}).items():
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            continue

        if weight == 0:
            continue

        try:
            value = float(stats.get(key, 0.0) or 0.0)
        except (TypeError, ValueError):
            value = 0.0

        total += value * weight

    return round(total, 6)

def fetch_week_stats(season, week):
    urls = [
        template.format(season=int(season), week=int(week))
        for template in WEEKLY_ENDPOINTS
    ]
    payload, endpoint = _try_json(urls)
    return normalize_stats_payload(payload), endpoint

def load_sleeper_player_weeks(
    seasons,
    scoring_settings,
    weeks=range(1, 19),
    player_map=None,
):
    """
    Return the minimal weekly dataframe contract consumed by WoRP Engine V0.2.1:
        season, season_type, week, player_id, player_name, position, fantasy_points

    Only QB/RB/WR/TE are included.
    """
    import pandas as pd

    if player_map is None:
        player_map = fetch_player_map()

    rows = []
    endpoint_log = {}

    for season in seasons:
        endpoint_log[int(season)] = []

        for week in weeks:
            week_stats, endpoint = fetch_week_stats(season, week)
            endpoint_log[int(season)].append(endpoint)

            for pid, stats in week_stats.items():
                p = player_map.get(pid, {}) if isinstance(player_map, dict) else {}
                position = p.get("position")
                if position not in POSITIONS:
                    continue

                full_name = (
                    p.get("full_name")
                    or " ".join(
                        part for part in [p.get("first_name"), p.get("last_name")]
                        if part
                    ).strip()
                    or pid
                )

                rows.append({
                    "season": int(season),
                    "season_type": "REG",
                    "week": int(week),
                    "player_id": str(pid),
                    "player_name": full_name,
                    "position": position,
                    "fantasy_points": score_stats_exact(stats, scoring_settings),
                })

    df = pd.DataFrame(rows)

    if df.empty:
        raise RuntimeError("Sleeper weekly loader returned no QB/RB/WR/TE rows.")

    # Defensive de-duplication: one row per player-season-week.
    df = (
        df.sort_values(["season", "week", "position", "player_id"])
          .drop_duplicates(["season", "week", "player_id"], keep="last")
          .reset_index(drop=True)
    )

    return df, endpoint_log

def validate_weekly_contract(df):
    required = {
        "season", "season_type", "week", "player_id",
        "player_name", "position", "fantasy_points",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Sleeper weekly dataframe missing required columns: {sorted(missing)}")

    if not set(df["position"].dropna().unique()).issubset(POSITIONS):
        raise ValueError("Unexpected position found in Sleeper weekly dataframe.")

    if not set(df["season_type"].dropna().unique()).issubset({"REG"}):
        raise ValueError("Non-REG rows found in Sleeper weekly dataframe.")

    if df.duplicated(["season", "week", "player_id"]).any():
        raise ValueError("Duplicate player-season-week rows found.")

    return True
