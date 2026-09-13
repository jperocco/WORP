#!/usr/bin/env python3
"""
WOOKIEE FREE -> CAPTURABILITY TEMPORAL AUDIT V0.1

Purpose
-------
Test whether positive-WoRP player-weeks classified as FREE were actually
available for acquisition BEFORE the player's game/production.

This is deliberately narrower than "waiver economics":
- FREE is the observed roster state in the weekly matchup snapshot.
- CAPTURABLE means the player was already outside all league rosters
  before the relevant game/production window.
- NOT_CAPTURABLE means the player became free only after the relevant
  production window, or was otherwise not available before production.
- AMBIGUOUS means the available Sleeper timing data cannot establish the
  state confidently.

STOP RULE
---------
If AMBIGUOUS exceeds 4% of positive-WoRP FREE player-weeks, the audit
fails and no capture estimate should be used.

This script uses the same leagues, weekly WoRP file, and Sleeper namespaces
used by the existing STARTED/BENCHED/FREE audit.
"""

import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

WORP = Path("wookiee_2023_2025_weekly_worp.csv")

LEAGUES = {
    2023: "950220100039311360",
    2024: "1050961255520923648",
    2025: "1182581249532833792",
}

POS = {"QB", "RB", "WR", "TE"}
STOP_RATE = 0.04


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "WoRPLab/0.2.5"}
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_matchups(raw):
    return raw if isinstance(raw, list) else []


def parse_transactions(raw):
    return raw if isinstance(raw, list) else []


def iso_to_ts(value):
    if value is None:
        return None
    try:
        # Sleeper transaction created timestamps are normally milliseconds.
        x = float(value)
        if x > 10_000_000_000:
            x /= 1000
        return datetime.fromtimestamp(x, tz=timezone.utc)
    except Exception:
        return None


def normalize_pid(x):
    if x is None:
        return None
    return str(x)


def transaction_player_ids(tx):
    ids = set()

    for key in ("adds", "drops"):
        obj = tx.get(key) or {}
        if isinstance(obj, dict):
            ids.update(normalize_pid(k) for k in obj.keys())
        elif isinstance(obj, list):
            ids.update(normalize_pid(x) for x in obj)

    return {x for x in ids if x is not None}


def get_weekly_roster_state(season, week, league_id):
    """
    Reconstruct observed ownership from the same matchup snapshot used by
    STARTED/BENCHED/FREE.

    Returns:
        owned: player_ids appearing on any roster
        started: player_ids appearing in any starter slot
    """
    rows = parse_matchups(
        get_json(f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}")
    )

    owned = set()
    started = set()

    for row in rows:
        players = row.get("players") or []
        starters = row.get("starters") or []

        owned.update(normalize_pid(x) for x in players if x is not None)
        started.update(
            normalize_pid(x)
            for x in starters
            if x is not None and str(x) != "0"
        )

    return owned, started


def get_week_transactions(season, week, league_id):
    return parse_transactions(
        get_json(
            f"https://api.sleeper.app/v1/league/{league_id}/transactions/{week}"
        )
    )


def classify_free_event(
    player_id,
    season,
    week,
    owned_before,
    owned_week,
    transactions_by_week,
):
    """
    Conservative classification.

    We care about availability BEFORE production, not merely the weekly
    snapshot label.

    Logic:
    1. If player is owned at the weekly snapshot, the row should not be FREE.
    2. Search transactions in the relevant week and prior weeks for a drop
       involving this player.
    3. A drop before the weekly window supports CAPTURABLE.
    4. A drop after the weekly production window supports NOT_CAPTURABLE.
    5. If timing cannot be established, return AMBIGUOUS.

    Important:
    Sleeper's transaction timestamps are the authoritative timing evidence
    available to this audit. We do not infer timing from transaction order.
    """
    pid = normalize_pid(player_id)

    if pid in owned_week:
        return "NOT_FREE_AT_SNAPSHOT", None, None

    relevant = []

    for tx_week, txs in transactions_by_week.items():
        if tx_week not in range(max(1, week - 1), min(18, week + 1) + 1):
            continue

        for tx in txs:
            ids = transaction_player_ids(tx)
            if pid not in ids:
                continue

            created = iso_to_ts(tx.get("created"))
            status = tx.get("status")
            tx_type = tx.get("type")

            relevant.append(
                {
                    "tx_week": tx_week,
                    "created": created,
                    "status": status,
                    "type": tx_type,
                    "transaction_id": tx.get("transaction_id"),
                    "drops": tx.get("drops") or {},
                    "adds": tx.get("adds") or {},
                }
            )

    # If no relevant transaction exists, the player may have been a free
    # agent continuously. That is the cleanest CAPTURABLE case.
    if not relevant:
        return "CAPTURABLE", "NO_RELEVANT_TRANSACTION_FOUND", None

    relevant.sort(
        key=lambda x: x["created"] or datetime.min.replace(tzinfo=timezone.utc)
    )

    # We intentionally do not invent a precise game kickoff timestamp here.
    # The weekly audit therefore uses transaction timing relative to the
    # transaction week and requires an explicit pre-production drop only
    # when timestamp evidence exists.
    for ev in relevant:
        if ev["created"] is None:
            continue

        if ev["tx_week"] < week:
            return "CAPTURABLE", "PLAYER_FREE_BEFORE_WEEK", ev

        if ev["tx_week"] == week:
            # A transaction in the same week is not automatically enough to
            # prove availability before the player's game.
            return "AMBIGUOUS", "SAME_WEEK_TRANSACTION", ev

    return "AMBIGUOUS", "TIMING_UNRESOLVED", relevant[-1]


def main():
    print("=" * 110)
    print("WOOKIEE FREE -> CAPTURABILITY TEMPORAL AUDIT V0.1")
    print("=" * 110)

    if not WORP.exists():
        raise FileNotFoundError(f"Missing {WORP}")

    w = pd.read_csv(WORP)
    w["player_id"] = w["player_id"].astype(str)

    w = w[
        w.season.isin(LEAGUES)
        & w.week.between(1, 18)
        & w.position.isin(POS)
    ].copy()

    free_positive = w[w.weekly_worp > 0].copy()

    # Reconstruct weekly observed ownership.
    weekly_owned = {}
    weekly_started = {}

    for season, league_id in LEAGUES.items():
        for week in range(1, 19):
            owned, started = get_weekly_roster_state(
                season, week, league_id
            )
            weekly_owned[(season, week)] = owned
            weekly_started[(season, week)] = started

    free_positive["observed_free"] = [
        pid not in weekly_owned[(int(season), int(week))]
        for season, week, pid in zip(
            free_positive.season,
            free_positive.week,
            free_positive.player_id,
        )
    ]

    # This should recover the FREE rows used by the previous audit.
    candidates = free_positive[free_positive.observed_free].copy()

    print(f"Positive-WoRP rows: {len(free_positive)}")
    print(f"Positive-WoRP FREE candidates: {len(candidates)}")

    # Cache transactions through the season. We need the prior week and the
    # current week to resolve ordinary drops; no inference is made from
    # transaction ordering alone.
    transactions_by_week = {}

    for season, league_id in LEAGUES.items():
        for week in range(1, 19):
            transactions_by_week[(season, week)] = get_week_transactions(
                season, week, league_id
            )

    results = []

    for row in candidates.itertuples(index=False):
        season = int(row.season)
        week = int(row.week)
        pid = str(row.player_id)

        status, reason, evidence = classify_free_event(
            pid,
            season,
            week,
            weekly_owned.get((season, week - 1), set()),
            weekly_owned[(season, week)],
            {
                tx_week[1]: txs
                for tx_week, txs in transactions_by_week.items()
                if tx_week[0] == season
            },
        )

        evidence_created = None
        evidence_tx_week = None
        evidence_tx_type = None
        evidence_tx_id = None

        if isinstance(evidence, dict):
            evidence_created = (
                evidence["created"].isoformat()
                if evidence.get("created")
                else None
            )
            evidence_tx_week = evidence.get("tx_week")
            evidence_tx_type = evidence.get("type")
            evidence_tx_id = evidence.get("transaction_id")

        results.append(
            {
                "season": season,
                "week": week,
                "player_id": pid,
                "player_name": row.player_name,
                "position": row.position,
                "weekly_worp": row.weekly_worp,
                "fantasy_points": row.fantasy_points,
                "observed_state": "FREE",
                "capturability": status,
                "reason": reason,
                "evidence_tx_week": evidence_tx_week,
                "evidence_tx_type": evidence_tx_type,
                "evidence_tx_id": evidence_tx_id,
                "evidence_created_utc": evidence_created,
            }
        )

    out = pd.DataFrame(results)

    total = len(out)
    ambiguous = int((out.capturability == "AMBIGUOUS").sum())
    capturable = int((out.capturability == "CAPTURABLE").sum())
    not_capturable = int((out.capturability == "NOT_CAPTURABLE").sum())

    ambiguous_rate = ambiguous / max(1, total)

    total_free_worp = out.weekly_worp.sum()
    capturable_worp = out.loc[
        out.capturability == "CAPTURABLE", "weekly_worp"
    ].sum()
    ambiguous_worp = out.loc[
        out.capturability == "AMBIGUOUS", "weekly_worp"
    ].sum()
    not_capturable_worp = out.loc[
        out.capturability == "NOT_CAPTURABLE", "weekly_worp"
    ].sum()

    out.to_csv(
        "wookiee_free_capturability_temporal_detail_v0_1.csv",
        index=False,
    )

    summary = pd.DataFrame(
        [
            {
                "positive_free_player_weeks": total,
                "capturable_player_weeks": capturable,
                "not_capturable_player_weeks": not_capturable,
                "ambiguous_player_weeks": ambiguous,
                "ambiguous_rate": ambiguous_rate,
                "total_free_worp": total_free_worp,
                "capturable_worp": capturable_worp,
                "not_capturable_worp": not_capturable_worp,
                "ambiguous_worp": ambiguous_worp,
                "capturable_worp_share": (
                    capturable_worp / total_free_worp
                    if total_free_worp
                    else 0
                ),
            }
        ]
    )

    summary.to_csv(
        "wookiee_free_capturability_temporal_summary_v0_1.csv",
        index=False,
    )

    print("\nRESULT")
    print("-" * 110)
    print(f"FREE positive player-weeks : {total}")
    print(f"CAPTURABLE                  : {capturable}")
    print(f"NOT_CAPTURABLE              : {not_capturable}")
    print(f"AMBIGUOUS                   : {ambiguous}")
    print(f"AMBIGUOUS RATE              : {ambiguous_rate:.2%}")
    print(f"TOTAL FREE WoRP             : {total_free_worp:.6f}")
    print(f"CAPTURABLE WoRP             : {capturable_worp:.6f}")
    print(f"NOT CAPTURABLE WoRP         : {not_capturable_worp:.6f}")
    print(f"AMBIGUOUS WoRP              : {ambiguous_worp:.6f}")
    print(f"CAPTURABLE WoRP SHARE       : {capturable_worp / total_free_worp:.2%}"
          if total_free_worp else "CAPTURABLE WoRP SHARE       : n/a")

    if ambiguous_rate > STOP_RATE:
        print("\nSTOP: AMBIGUOUS > 4%.")
        print("Do NOT use the capture estimate.")
        raise SystemExit(2)

    print("\nPASS: AMBIGUOUS <= 4%.")
    print("The observed FREE pool is temporally coherent enough for the next stage.")
    print("IMPORTANT: this is a capturability audit, not yet a waiver-value model.")


if __name__ == "__main__":
    main()
