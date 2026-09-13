#!/usr/bin/env python3
"""
WOOKIEE FREE -> CAPTURABILITY TEMPORAL AUDIT V0.2

Refinement of V0.1:
- V0.1 treated ANY same-week transaction as AMBIGUOUS.
- V0.2 uses transaction timestamps and game timestamps where available.
- A same-week drop BEFORE the player's game supports CAPTURABLE.
- A same-week drop AFTER the player's game supports NOT_CAPTURABLE.
- If game timing cannot be established, remain AMBIGUOUS.
- If no relevant drop exists before production, the player is CAPTURABLE
  (consistent with being continuously free).

This audit is about ex-ante availability, not whether a manager should have
started the player or whether an acquisition would have succeeded under a
specific FAAB/waiver priority mechanism.

STOP RULE:
AMBIGUOUS > 4% of positive-WoRP FREE player-weeks => STOP.
"""

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

WORP = Path("wookiee_2023_2025_weekly_worp.csv")

LEAGUES = {
    2023: "950220100039311360",
    2024: "1050961255520923648",
    2025: "1182581249532833792",
}

STOP_RATE = 0.04


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "WoRPLab/0.2.6"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def to_dt(value):
    if value is None:
        return None
    try:
        x = float(value)
        if x > 10_000_000_000:
            x /= 1000
        return datetime.fromtimestamp(x, tz=timezone.utc)
    except Exception:
        return None


def pid(x):
    return str(x) if x is not None else None


def tx_players(tx):
    ids = set()
    for key in ("adds", "drops"):
        obj = tx.get(key) or {}
        if isinstance(obj, dict):
            ids.update(pid(x) for x in obj.keys())
        elif isinstance(obj, list):
            ids.update(pid(x) for x in obj)
    return {x for x in ids if x is not None}


def get_transactions(league_id, week):
    raw = get_json(
        f"https://api.sleeper.app/v1/league/{league_id}/transactions/{week}"
    )
    return raw if isinstance(raw, list) else []


def get_matchups(league_id, week):
    raw = get_json(
        f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}"
    )
    return raw if isinstance(raw, list) else []


def get_games_for_week(season, week):
    """
    Sleeper NFL state endpoint is used where available.

    The endpoint can expose game_id/team/opponent context but does not always
    expose a universal kickoff timestamp. We therefore also inspect NFL game
    metadata from Sleeper when available and retain AMBIGUOUS if no reliable
    game timestamp can be established.
    """
    candidates = [
        f"https://api.sleeper.com/schedule/nfl/{season}/{week}",
        f"https://api.sleeper.com/games/nfl/{season}/{week}",
    ]

    for url in candidates:
        try:
            raw = get_json(url)
            if isinstance(raw, list) and raw:
                return raw
            if isinstance(raw, dict) and raw:
                return raw
        except Exception:
            pass

    return []


def extract_game_times(raw_games):
    """
    Build a team -> kickoff mapping where possible.

    Sleeper schedule schemas have varied over time, so this deliberately
    accepts several common timestamp/team field names rather than assuming
    one schema.
    """
    team_time = {}

    records = raw_games if isinstance(raw_games, list) else []
    if isinstance(raw_games, dict):
        records = raw_games.get("games") or raw_games.get("data") or []

    for g in records:
        if not isinstance(g, dict):
            continue

        ts = None
        for key in (
            "start_time",
            "startTime",
            "kickoff",
            "kickoff_time",
            "scheduled",
            "game_start",
        ):
            if g.get(key) is not None:
                ts = to_dt(g.get(key))
                if ts:
                    break

        if not ts:
            continue

        teams = []
        for key in ("home_team", "away_team", "home", "away"):
            val = g.get(key)
            if isinstance(val, str):
                teams.append(val)
        for key in ("home_team_abbr", "away_team_abbr"):
            val = g.get(key)
            if isinstance(val, str):
                teams.append(val)

        for team in teams:
            team_time[str(team).upper()] = ts

    return team_time


def build_ownership(league_id, week):
    rows = get_matchups(league_id, week)
    owned = set()
    player_team = {}

    for row in rows:
        players = row.get("players") or []
        roster_id = row.get("roster_id")
        for x in players:
            p = pid(x)
            if p:
                owned.add(p)
                player_team[p] = roster_id

    return owned, player_team


def main():
    print("=" * 110)
    print("WOOKIEE FREE -> CAPTURABILITY TEMPORAL AUDIT V0.2")
    print("=" * 110)

    if not WORP.exists():
        raise FileNotFoundError(WORP)

    w = pd.read_csv(WORP)
    w["player_id"] = w["player_id"].astype(str)

    w = w[
        w.season.isin(LEAGUES)
        & w.week.between(1, 18)
        & w.weekly_worp.gt(0)
    ].copy()

    # Reconstruct observed FREE candidates.
    owned_cache = {}
    for season, league_id in LEAGUES.items():
        for week in range(1, 19):
            owned, player_team = build_ownership(league_id, week)
            owned_cache[(season, week)] = owned

    candidates = w[
        [
            pid(x) not in owned_cache[(int(s), int(week))]
            for s, week, x in zip(w.season, w.week, w.player_id)
        ]
    ].copy()

    print(f"Positive-WoRP rows: {len(w)}")
    print(f"Positive-WoRP FREE candidates: {len(candidates)}")

    # Cache transactions and schedule metadata.
    tx_cache = {}
    schedule_cache = {}

    for season, league_id in LEAGUES.items():
        for week in range(1, 19):
            tx_cache[(season, week)] = get_transactions(league_id, week)
            schedule_cache[(season, week)] = extract_game_times(
                get_games_for_week(season, week)
            )

    results = []

    for row in candidates.itertuples(index=False):
        season = int(row.season)
        week = int(row.week)
        player_id = pid(row.player_id)

        # Relevant transaction events for this player in current/prior week.
        events = []

        for tx_week in (max(1, week - 1), week):
            for tx in tx_cache[(season, tx_week)]:
                if player_id not in tx_players(tx):
                    continue

                created = to_dt(tx.get("created"))
                drops = {pid(x) for x in (tx.get("drops") or {}).keys()}
                adds = {pid(x) for x in (tx.get("adds") or {}).keys()}

                if isinstance(tx.get("drops"), list):
                    drops = {pid(x) for x in tx.get("drops")}
                if isinstance(tx.get("adds"), list):
                    adds = {pid(x) for x in tx.get("adds")}

                events.append(
                    {
                        "week": tx_week,
                        "created": created,
                        "type": tx.get("type"),
                        "transaction_id": tx.get("transaction_id"),
                        "is_drop": player_id in drops,
                        "is_add": player_id in adds,
                    }
                )

        drop_events = [
            x for x in events if x["is_drop"] and x["created"] is not None
        ]
        drop_events.sort(key=lambda x: x["created"])

        # No drop in the current/prior week: if already FREE at snapshot,
        # treat as continuously available unless evidence says otherwise.
        if not drop_events:
            classification = "CAPTURABLE"
            reason = "NO_RECENT_DROP_EVIDENCE"

        else:
            latest_drop = drop_events[-1]

            # A prior-week drop is clean evidence that the player was already
            # free before the target week.
            if latest_drop["week"] < week:
                classification = "CAPTURABLE"
                reason = "DROP_BEFORE_TARGET_WEEK"

            else:
                # Same-week transaction requires actual game timing.
                # The WoRP file may not carry team/game_id, so use schedule
                # metadata only if it can be mapped through a player team.
                game_time = None

                # Try common player/team fields in WoRP.
                team = None
                for attr in ("team", "team_abbr", "player_team"):
                    if hasattr(row, attr):
                        val = getattr(row, attr)
                        if isinstance(val, str) and val:
                            team = val.upper()
                            break

                if team:
                    game_time = schedule_cache[(season, week)].get(team)

                if game_time is None:
                    classification = "AMBIGUOUS"
                    reason = "SAME_WEEK_DROP_NO_RELIABLE_GAME_TIME"
                elif latest_drop["created"] < game_time:
                    classification = "CAPTURABLE"
                    reason = "DROP_BEFORE_PLAYER_GAME"
                else:
                    classification = "NOT_CAPTURABLE"
                    reason = "DROP_AFTER_PLAYER_GAME"

        results.append(
            {
                "season": season,
                "week": week,
                "player_id": player_id,
                "player_name": row.player_name,
                "position": row.position,
                "weekly_worp": row.weekly_worp,
                "fantasy_points": row.fantasy_points,
                "capturability": classification,
                "reason": reason,
                "latest_drop_week": (
                    drop_events[-1]["week"] if drop_events else None
                ),
                "latest_drop_created_utc": (
                    drop_events[-1]["created"].isoformat()
                    if drop_events
                    else None
                ),
                "latest_drop_transaction_id": (
                    drop_events[-1]["transaction_id"]
                    if drop_events
                    else None
                ),
            }
        )

    out = pd.DataFrame(results)

    total = len(out)
    cap = out.capturability.eq("CAPTURABLE")
    nocap = out.capturability.eq("NOT_CAPTURABLE")
    amb = out.capturability.eq("AMBIGUOUS")

    total_worp = out.weekly_worp.sum()
    cap_worp = out.loc[cap, "weekly_worp"].sum()
    nocap_worp = out.loc[nocap, "weekly_worp"].sum()
    amb_worp = out.loc[amb, "weekly_worp"].sum()

    summary = pd.DataFrame(
        [
            {
                "positive_free_player_weeks": total,
                "capturable_player_weeks": int(cap.sum()),
                "not_capturable_player_weeks": int(nocap.sum()),
                "ambiguous_player_weeks": int(amb.sum()),
                "ambiguous_rate": amb.mean() if total else 0,
                "total_free_worp": total_worp,
                "capturable_worp": cap_worp,
                "not_capturable_worp": nocap_worp,
                "ambiguous_worp": amb_worp,
                "capturable_worp_share": cap_worp / total_worp if total_worp else 0,
            }
        ]
    )

    out.to_csv(
        "wookiee_free_capturability_temporal_detail_v0_2.csv",
        index=False,
    )
    summary.to_csv(
        "wookiee_free_capturability_temporal_summary_v0_2.csv",
        index=False,
    )

    print("\nRESULT")
    print("-" * 110)
    print(f"FREE positive player-weeks : {total}")
    print(f"CAPTURABLE                  : {int(cap.sum())}")
    print(f"NOT_CAPTURABLE              : {int(nocap.sum())}")
    print(f"AMBIGUOUS                   : {int(amb.sum())}")
    print(f"AMBIGUOUS RATE              : {amb.mean():.2%}" if total else "AMBIGUOUS RATE: n/a")
    print(f"TOTAL FREE WoRP             : {total_worp:.6f}")
    print(f"CAPTURABLE WoRP             : {cap_worp:.6f}")
    print(f"NOT CAPTURABLE WoRP         : {nocap_worp:.6f}")
    print(f"AMBIGUOUS WoRP              : {amb_worp:.6f}")
    print(
        f"CAPTURABLE WoRP SHARE       : {cap_worp / total_worp:.2%}"
        if total_worp else
        "CAPTURABLE WoRP SHARE       : n/a"
    )

    if total and amb.mean() > STOP_RATE:
        print("\nSTOP: AMBIGUOUS > 4%.")
        raise SystemExit(2)

    print("\nPASS: AMBIGUOUS <= 4%.")
    print("This supports using the capturable estimate as the next-stage input.")


if __name__ == "__main__":
    main()
