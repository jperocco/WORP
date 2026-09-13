#!/usr/bin/env python3
"""
WOOKIEE IN-SEASON ROSTER HISTORY AUDIT V0.1

Purpose:
Validate whether Sleeper preserves enough historical week-by-week roster state
for the Wookiee Moves league lineage to support a later waiver-boundary study.

This script DOES NOT:
- calculate WoRP
- infer Captura
- infer waiver/FAAB cost
- analyze offseason
- declare any positional threshold

PASS question:
Can we reliably recover, for completed regular-season weeks, the players owned
by all 12 rosters using that week's Sleeper matchup snapshot?

Outputs only an audit CSV if successful.
"""

import csv
import json
import urllib.request
from collections import Counter
from pathlib import Path

CURRENT_LEAGUE_ID = "1317417394439741440"
EXPECTED_TEAMS = 12
MAX_LINEAGE = 20
OUT = Path("wookiee_inseason_roster_history_audit_v0_1.csv")

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "WoRPLab/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def league_obj(league_id):
    return get_json(f"https://api.sleeper.app/v1/league/{league_id}")

def matchups(league_id, week):
    return get_json(f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}")

print("=" * 108)
print("WOOKIEE IN-SEASON ROSTER HISTORY AUDIT V0.1")
print("=" * 108)
print("Question: can we recover week-by-week owned-player state before building a waiver-boundary model?")
print("Scope: IN-SEASON only. No WoRP, Captura, FAAB/cost, or offseason inference.")
print()

# 1) Follow Sleeper league lineage backwards.
lineage = []
seen = set()
lid = CURRENT_LEAGUE_ID

for _ in range(MAX_LINEAGE):
    if not lid or lid == "0" or lid in seen:
        break
    seen.add(lid)
    lg = league_obj(lid)
    lineage.append({
        "league_id": str(lid),
        "season": str(lg.get("season", "")),
        "name": lg.get("name", ""),
        "status": lg.get("status", ""),
        "previous_league_id": str(lg.get("previous_league_id") or ""),
    })
    lid = str(lg.get("previous_league_id") or "")

lineage = sorted(lineage, key=lambda x: x["season"])

print("1. LEAGUE LINEAGE")
print("-" * 108)
for x in lineage:
    print(
        f"{x['season'] or '?'} | {x['name']} | league_id={x['league_id']} | "
        f"status={x['status']} | previous={x['previous_league_id'] or 'none'}"
    )
print()

# 2) Audit matchup snapshots for weeks that actually return data.
audit = []

print("2. WEEKLY MATCHUP SNAPSHOT AUDIT")
print("-" * 108)

for x in lineage:
    season = x["season"]
    league_id = x["league_id"]
    found_weeks = 0

    # NFL regular seasons are <=18 weeks in this window. Probe 1..18;
    # empty endpoint response means no preserved matchup snapshot for that week.
    for week in range(1, 19):
        rows = matchups(league_id, week)
        if not rows:
            continue

        found_weeks += 1
        roster_ids = [r.get("roster_id") for r in rows if r.get("roster_id") is not None]
        unique_rosters = len(set(roster_ids))

        player_lists = []
        missing_players_field = 0
        empty_players = 0
        for r in rows:
            p = r.get("players")
            if p is None:
                missing_players_field += 1
                continue
            if not isinstance(p, list):
                missing_players_field += 1
                continue
            if len(p) == 0:
                empty_players += 1
            player_lists.append([str(pid) for pid in p if pid is not None])

        all_owned = [pid for plist in player_lists for pid in plist]
        duplicate_owned_ids = sum(v - 1 for v in Counter(all_owned).values() if v > 1)

        counts = [len(p) for p in player_lists]
        min_owned = min(counts) if counts else 0
        max_owned = max(counts) if counts else 0
        total_owned = len(all_owned)

        pass_week = (
            len(rows) == EXPECTED_TEAMS
            and unique_rosters == EXPECTED_TEAMS
            and missing_players_field == 0
            and empty_players == 0
            and duplicate_owned_ids == 0
        )

        audit.append({
            "season": season,
            "league_id": league_id,
            "week": week,
            "matchup_rows": len(rows),
            "unique_rosters": unique_rosters,
            "missing_players_field": missing_players_field,
            "empty_players_lists": empty_players,
            "total_owned_player_ids": total_owned,
            "min_owned_per_roster": min_owned,
            "max_owned_per_roster": max_owned,
            "duplicate_owned_ids_across_rosters": duplicate_owned_ids,
            "structural_pass": pass_week,
        })

    print(f"{season}: preserved matchup weeks found = {found_weeks}")

print()

if audit:
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(audit[0].keys()))
        w.writeheader()
        w.writerows(audit)

# 3) Summary / gate.
print("3. STRUCTURAL SUMMARY")
print("-" * 108)

if not audit:
    print("FAIL: no historical matchup snapshots were recovered.")
    print("Decision: STOP. Do not build waiver-boundary logic from this source.")
else:
    by_season = {}
    for r in audit:
        by_season.setdefault(r["season"], []).append(r)

    total = len(audit)
    passed = sum(bool(r["structural_pass"]) for r in audit)
    print(f"Audited weekly snapshots: {total}")
    print(f"Structural PASS snapshots: {passed}/{total}")
    print()

    for season in sorted(by_season):
        rs = by_season[season]
        p = sum(bool(r["structural_pass"]) for r in rs)
        weeks = [r["week"] for r in rs]
        min_owned = min(r["min_owned_per_roster"] for r in rs)
        max_owned = max(r["max_owned_per_roster"] for r in rs)
        print(
            f"{season}: weeks {min(weeks)}-{max(weeks)} | snapshots={len(rs)} | "
            f"PASS={p}/{len(rs)} | owned/roster observed range={min_owned}-{max_owned}"
        )

    print()
    print("4. DECISION GATE")
    print("-" * 108)
    if passed == total:
        print("ADVANCE: Sleeper matchup snapshots are structurally usable for an in-season ownership history.")
        print("NEXT (not done here): add player positions and define the PRE-WEEK timing convention before")
        print("crossing rostered/free status with realized WoRP.")
    else:
        print("PARK: at least one recovered snapshot failed structural integrity.")
        print("Inspect failed rows in the CSV before any waiver-boundary analysis.")

    print()
    print(f"Saved: {OUT}")

print()
print("CRITICAL: a matchup snapshot being structurally valid does NOT yet prove its exact temporal")
print("meaning relative to waivers, lineup lock, or Sunday results. That timing must be validated next.")
