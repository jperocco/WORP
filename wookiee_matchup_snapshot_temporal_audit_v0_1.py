#!/usr/bin/env python3
"""
WOOKIEE MATCHUP SNAPSHOT TEMPORAL AUDIT V0.1

Question:
Does Sleeper /matchups/{week} preserve historical ownership state, or can
its `players` field be contaminated by a later/current roster state?

Method:
1) Follow Wookiee league lineage.
2) Pull weekly matchup `players` sets.
3) Pull weekly transactions.
4) Find add/drop/trade ownership changes.
5) For each moved player, compare ownership in adjacent matchup weeks.
6) Also measure how much each roster's matchup-player set actually changes
   week-to-week. If every week looks like the same final roster, that is a red flag.

NO WoRP. NO waiver boundary. NO Captura.
"""

import csv
import json
import urllib.request
from collections import defaultdict
from pathlib import Path

CURRENT_LEAGUE_ID = "1317417394439741440"
MAX_LINEAGE = 20
OUT_EVENTS = Path("wookiee_matchup_temporal_events_v0_1.csv")
OUT_WEEKS = Path("wookiee_matchup_temporal_week_changes_v0_1.csv")

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "WoRPLab/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def league_obj(lid):
    return get_json(f"https://api.sleeper.app/v1/league/{lid}")

def matchups(lid, week):
    return get_json(f"https://api.sleeper.app/v1/league/{lid}/matchups/{week}")

def transactions(lid, week):
    return get_json(f"https://api.sleeper.app/v1/league/{lid}/transactions/{week}")

def matchup_owner_map(rows):
    owner = {}
    roster_sets = {}
    for r in rows or []:
        rid = r.get("roster_id")
        ps = r.get("players")
        if rid is None or not isinstance(ps, list):
            continue
        s = {str(p) for p in ps if p is not None}
        roster_sets[int(rid)] = s
        for pid in s:
            owner[pid] = int(rid)
    return owner, roster_sets

# lineage
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
        "season": int(lg.get("season")),
        "status": str(lg.get("status") or ""),
        "name": str(lg.get("name") or ""),
    })
    lid = str(lg.get("previous_league_id") or "")
lineage.sort(key=lambda x: x["season"])

print("="*112)
print("WOOKIEE MATCHUP SNAPSHOT TEMPORAL AUDIT V0.1")
print("="*112)
print("Question: is matchup.players a true historical ownership snapshot?")
print("No WoRP / waiver boundary / Captura.")
print()

event_rows = []
week_rows = []

for lg in lineage:
    season = lg["season"]
    lid = lg["league_id"]

    # Completed seasons are the main evidence. Current season is retained only
    # as a diagnostic, since future-week responses were already suspicious.
    maps = {}
    sets = {}
    for week in range(1, 19):
        rows = matchups(lid, week)
        om, rs = matchup_owner_map(rows)
        maps[week] = om
        sets[week] = rs

    # Week-to-week roster-set changes.
    for week in range(2, 19):
        prev = sets.get(week-1, {})
        cur = sets.get(week, {})
        common = sorted(set(prev) & set(cur))
        changed_rosters = 0
        total_added = 0
        total_removed = 0
        for rid in common:
            added = cur[rid] - prev[rid]
            removed = prev[rid] - cur[rid]
            if added or removed:
                changed_rosters += 1
            total_added += len(added)
            total_removed += len(removed)
        week_rows.append({
            "season": season,
            "status": lg["status"],
            "from_week": week-1,
            "to_week": week,
            "common_rosters": len(common),
            "changed_rosters": changed_rosters,
            "added_player_memberships": total_added,
            "removed_player_memberships": total_removed,
        })

    # Transaction-linked ownership changes.
    for tx_week in range(1, 19):
        txs = transactions(lid, tx_week) or []
        for tx in txs:
            status = str(tx.get("status") or "")
            if status != "complete":
                continue

            txid = str(tx.get("transaction_id") or "")
            ttype = str(tx.get("type") or "")
            adds = tx.get("adds") or {}
            drops = tx.get("drops") or {}

            touched = set(str(p) for p in adds.keys()) | set(str(p) for p in drops.keys())
            for pid in touched:
                add_to = adds.get(pid)
                drop_from = drops.get(pid)

                # Compare matchup ownership around the transaction week.
                # We do NOT assume tx_week maps perfectly to pre/post state;
                # the pattern itself is what we are auditing.
                before_week = tx_week - 1 if tx_week > 1 else None
                after_week = tx_week + 1 if tx_week < 18 else None

                owner_before = maps.get(before_week, {}).get(pid) if before_week else None
                owner_txweek = maps.get(tx_week, {}).get(pid)
                owner_after = maps.get(after_week, {}).get(pid) if after_week else None

                event_rows.append({
                    "season": season,
                    "league_status": lg["status"],
                    "transaction_week": tx_week,
                    "transaction_id": txid,
                    "transaction_type": ttype,
                    "player_id": pid,
                    "drop_from_roster": drop_from,
                    "add_to_roster": add_to,
                    "owner_matchup_week_before": owner_before,
                    "owner_matchup_tx_week": owner_txweek,
                    "owner_matchup_week_after": owner_after,
                })

print("1. WEEK-TO-WEEK ROSTER CHANGE SIGNAL")
print("-"*112)
for lg in lineage:
    s = lg["season"]
    rs = [r for r in week_rows if r["season"] == s]
    transitions = len(rs)
    nonzero = sum(r["changed_rosters"] > 0 for r in rs)
    total_changes = sum(r["added_player_memberships"] + r["removed_player_memberships"] for r in rs)
    print(
        f"{s} ({lg['status']}): transitions={transitions} | "
        f"transitions with roster changes={nonzero}/{transitions} | "
        f"total membership changes={total_changes}"
    )

# Evaluate transaction-linked directional consistency for completed seasons.
# Strong event = explicit add and/or drop with adjacent weeks available.
completed = [r for r in event_rows if r["league_status"] == "complete"]
directional = []
for r in completed:
    before = r["owner_matchup_week_before"]
    after = r["owner_matchup_week_after"]
    add_to = r["add_to_roster"]
    drop_from = r["drop_from_roster"]

    # Require both adjacent weeks for a clean temporal check.
    if r["transaction_week"] <= 1 or r["transaction_week"] >= 18:
        continue

    evidence = False
    consistent = True

    if drop_from is not None:
        evidence = True
        if before is not None and str(before) != str(drop_from):
            # Could be transaction timing/week semantics; flag rather than assume.
            consistent = False
        if after is not None and str(after) == str(drop_from):
            consistent = False

    if add_to is not None:
        evidence = True
        if after is not None and str(after) != str(add_to):
            consistent = False

    if evidence:
        directional.append((r, consistent))

print()
print("2. TRANSACTION-LINKED TEMPORAL CHECK")
print("-"*112)
print(f"Completed-season touched-player events: {len(completed)}")
print(f"Clean adjacent-week directional checks: {len(directional)}")
if directional:
    ok = sum(c for _, c in directional)
    print(f"Directionally consistent: {ok}/{len(directional)} ({100*ok/len(directional):.1f}%)")
else:
    ok = 0
    print("Directionally consistent: n/a")

# Show a compact sample of events where ownership visibly changes.
visible = []
for r in completed:
    b, a = r["owner_matchup_week_before"], r["owner_matchup_week_after"]
    if b != a and (b is not None or a is not None):
        visible.append(r)

print()
print("3. SAMPLE OF VISIBLE OWNERSHIP CHANGES")
print("-"*112)
for r in visible[:20]:
    print(
        f"{r['season']} W{r['transaction_week']:02d} | {r['transaction_type']:<7} | "
        f"player={r['player_id']} | matchup owner W-1={r['owner_matchup_week_before']} "
        f"-> W={r['owner_matchup_tx_week']} -> W+1={r['owner_matchup_week_after']} | "
        f"drop={r['drop_from_roster']} add={r['add_to_roster']}"
    )
if not visible:
    print("No visible adjacent-week ownership changes found.")

# Save.
if event_rows:
    with OUT_EVENTS.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(event_rows[0].keys()))
        w.writeheader()
        w.writerows(event_rows)

if week_rows:
    with OUT_WEEKS.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(week_rows[0].keys()))
        w.writeheader()
        w.writerows(week_rows)

print()
print("4. DECISION GATE")
print("-"*112)

completed_week_rows = [r for r in week_rows if any(l["season"] == r["season"] and l["status"] == "complete" for l in lineage)]
nonzero_completed = sum(r["changed_rosters"] > 0 for r in completed_week_rows)

if completed_week_rows and nonzero_completed == 0:
    print("KILL SOURCE: completed seasons show no week-to-week roster movement.")
    print("matchup.players behaves like a static/final roster representation.")
elif directional and (ok / len(directional)) >= 0.90:
    print("ADVANCE: matchup.players shows historical movement and >=90% directional agreement with transactions.")
    print("NEXT: inspect timing convention more precisely before labeling a snapshot PRE-WEEK.")
elif directional and (ok / len(directional)) >= 0.70:
    print("PARK: historical movement exists, but transaction/week timing semantics need reconciliation.")
    print("Do NOT build waiver boundary yet.")
else:
    print("PARK/KILL: insufficient clean temporal agreement.")
    print("Prefer reconstructing ownership from transactions rather than trusting matchup.players.")

print()
print("Saved:")
print(f"  {OUT_EVENTS}")
print(f"  {OUT_WEEKS}")
