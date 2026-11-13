#!/usr/bin/env python3
"""
WOOKIEE 9-CASE TRANSACTION CHAIN AUDIT V0.1

Question:
Are the 9 apparent temporal disagreements explained by additional completed
transactions involving the same player around the same week?

Scope:
- Only the 9 known cases from the previous audit
- Wookiee 2023-2025
- Pull ALL completed transactions for W-1, W, W+1
- Show same-player events chronologically
- Show matchup ownership W-1, W, W+1
- NO WoRP / waiver boundary / Captura / offseason
"""

import json
import urllib.request
from datetime import datetime, timezone

LEAGUES = {
    2023: "950220100039311360",
    2024: "1050961255520923648",
    2025: "1182581249532833792",
}

CASES = [
    (2023,17,"5122"),
    (2023,17,"11370"),
    (2023,17,"9490"),
    (2023,17,"5880"),
    (2023,17,"8254"),
    (2023,17,"6878"),
    (2024,8,"2133"),
    (2024,17,"3199"),
    (2025,6,"7535"),
]

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent":"WoRPLab/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def transactions(lid, week):
    return get_json(f"https://api.sleeper.app/v1/league/{lid}/transactions/{week}")

def matchups(lid, week):
    return get_json(f"https://api.sleeper.app/v1/league/{lid}/matchups/{week}")

def owner(rows, pid):
    hits=[]
    for r in rows or []:
        if pid in {str(x) for x in (r.get("players") or [])}:
            hits.append(r.get("roster_id"))
    return hits[0] if len(hits)==1 else (hits if hits else None)

def ts(tx):
    x=tx.get("status_updated") or tx.get("created") or 0
    try: return int(x)
    except: return 0

def iso(x):
    if not x: return ""
    return datetime.fromtimestamp(int(x)/1000, tz=timezone.utc).isoformat()

print("="*124)
print("WOOKIEE 9-CASE TRANSACTION CHAIN AUDIT V0.1")
print("="*124)
print("Question: do additional same-player transactions explain the 9 apparent disagreements?")
print()

explained = 0
unresolved = 0

for season, focal_week, pid in CASES:
    lid=LEAGUES[season]
    own={}
    for w in range(max(1,focal_week-1), min(18,focal_week+1)+1):
        own[w]=owner(matchups(lid,w),pid)

    events=[]
    for w in range(max(1,focal_week-1), min(18,focal_week+1)+1):
        for tx in transactions(lid,w) or []:
            if str(tx.get("status") or "")!="complete":
                continue
            adds={str(k):v for k,v in (tx.get("adds") or {}).items()}
            drops={str(k):v for k,v in (tx.get("drops") or {}).items()}
            if pid not in adds and pid not in drops:
                continue
            events.append({
                "week":w,
                "type":str(tx.get("type") or ""),
                "id":str(tx.get("transaction_id") or ""),
                "add":adds.get(pid),
                "drop":drops.get(pid),
                "ms":ts(tx),
                "utc":iso(tx.get("status_updated") or tx.get("created")),
            })
    events.sort(key=lambda e:(e["ms"],e["week"],e["id"]))

    # The narrow question: is there >1 completed transaction for this player
    # in the ±1-week window? If yes, the previous one-event test was incomplete.
    multi = len(events) > 1
    if multi: explained += 1
    else: unresolved += 1

    print("-"*124)
    print(
        f"{season} focal W{focal_week:02d} | player={pid} | "
        f"matchup ownership: W-1={own.get(focal_week-1)} -> W={own.get(focal_week)} -> W+1={own.get(focal_week+1)}"
    )
    print(f"same-player completed transactions in ±1 week: {len(events)}")
    for e in events:
        print(
            f"  W{e['week']:02d} | {e['type']:<10} | {e['utc']} | "
            f"drop={e['drop']} add={e['add']} | tx={e['id']}"
        )
    print("  classification:", "EXPLAINABLE BY MULTIPLE EVENTS" if multi else "STILL NEEDS EXPLANATION")

print()
print("="*124)
print("SUMMARY")
print("="*124)
print(f"Cases with multiple same-player events in ±1 week: {explained}/9")
print(f"Cases still single-event/unresolved: {unresolved}/9")
print()
print("DECISION:")
if unresolved == 0:
    print("PASS CANDIDATE: all 9 prior disagreements were artifacts of evaluating transactions in isolation.")
    print("We can close source auditing after interpreting the event chains.")
else:
    print("NOT YET PASS: at least one disagreement remains unexplained by another nearby same-player transaction.")
    print("Do not build waiver economics until those remaining cases are interpreted.")
