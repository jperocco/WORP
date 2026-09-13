#!/usr/bin/env python3
"""
WOOKIEE TRANSACTION TIMING SURGERY V0.1

Question:
Can we explain the small set of transaction-linked disagreements from the
previous temporal audit by transaction timing/week semantics?

Scope:
- Wookiee completed seasons only (2023-2025)
- Sleeper matchup ownership + completed transactions
- NO WoRP, waiver boundary, Captura, offseason, BRFFZAP2

Outputs:
- all clean directional checks
- only disagreements
"""

import csv, json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

CURRENT_LEAGUE_ID = "1317417394439741440"
OUT_ALL = Path("wookiee_transaction_timing_checks_v0_1.csv")
OUT_BAD = Path("wookiee_transaction_timing_disagreements_v0_1.csv")

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent":"WoRPLab/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def league(lid):
    return get_json(f"https://api.sleeper.app/v1/league/{lid}")

def matchups(lid,w):
    return get_json(f"https://api.sleeper.app/v1/league/{lid}/matchups/{w}")

def transactions(lid,w):
    return get_json(f"https://api.sleeper.app/v1/league/{lid}/transactions/{w}")

def owner_map(rows):
    out={}
    for r in rows or []:
        rid=r.get("roster_id")
        for pid in (r.get("players") or []):
            out[str(pid)] = rid
    return out

def iso_ms(x):
    if x is None:
        return ""
    try:
        return datetime.fromtimestamp(int(x)/1000, tz=timezone.utc).isoformat()
    except Exception:
        return str(x)

# lineage, completed only
lineage=[]
seen=set()
lid=CURRENT_LEAGUE_ID
while lid and lid!="0" and lid not in seen:
    seen.add(lid)
    lg=league(lid)
    if str(lg.get("status"))=="complete":
        lineage.append((int(lg["season"]),str(lid)))
    lid=str(lg.get("previous_league_id") or "")
lineage.sort()

checks=[]

for season,lid in lineage:
    maps={w:owner_map(matchups(lid,w)) for w in range(1,19)}

    for txw in range(2,18):  # both adjacent weeks available
        for tx in transactions(lid,txw) or []:
            if str(tx.get("status") or "")!="complete":
                continue

            adds={str(k):v for k,v in (tx.get("adds") or {}).items()}
            drops={str(k):v for k,v in (tx.get("drops") or {}).items()}
            touched=set(adds)|set(drops)

            for pid in touched:
                before=maps[txw-1].get(pid)
                same=maps[txw].get(pid)
                after=maps[txw+1].get(pid)
                add_to=adds.get(pid)
                drop_from=drops.get(pid)

                consistent=True
                reasons=[]

                if drop_from is not None:
                    if before is not None and str(before)!=str(drop_from):
                        consistent=False
                        reasons.append("W-1 owner != drop_from")
                    if after is not None and str(after)==str(drop_from):
                        consistent=False
                        reasons.append("W+1 still owned by drop_from")

                if add_to is not None:
                    if after is not None and str(after)!=str(add_to):
                        consistent=False
                        reasons.append("W+1 owner != add_to")

                settings=tx.get("settings") or {}
                checks.append({
                    "season":season,
                    "transaction_week":txw,
                    "transaction_type":tx.get("type"),
                    "transaction_id":tx.get("transaction_id"),
                    "status_updated_ms":tx.get("status_updated"),
                    "status_updated_utc":iso_ms(tx.get("status_updated")),
                    "created_ms":tx.get("created"),
                    "created_utc":iso_ms(tx.get("created")),
                    "player_id":pid,
                    "drop_from":drop_from,
                    "add_to":add_to,
                    "owner_w_minus_1":before,
                    "owner_w":same,
                    "owner_w_plus_1":after,
                    "waiver_bid":settings.get("waiver_bid",""),
                    "consistent":consistent,
                    "reason":"; ".join(reasons),
                })

bad=[r for r in checks if not r["consistent"]]

if checks:
    with OUT_ALL.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(checks[0]))
        w.writeheader(); w.writerows(checks)
if bad:
    with OUT_BAD.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(bad[0]))
        w.writeheader(); w.writerows(bad)

print("="*118)
print("WOOKIEE TRANSACTION TIMING SURGERY V0.1")
print("="*118)
print("Completed seasons only. Goal: inspect the disagreements, not build the economic model.")
print()
print(f"Clean adjacent-week checks: {len(checks)}")
print(f"Consistent: {len(checks)-len(bad)}/{len(checks)} ({100*(len(checks)-len(bad))/len(checks):.1f}%)")
print(f"Disagreements: {len(bad)}")
print()

print("DISAGREEMENTS")
print("-"*118)
for r in bad:
    print(
        f"{r['season']} W{r['transaction_week']:02d} | {str(r['transaction_type']):<10} | "
        f"player={r['player_id']} | W-1={r['owner_w_minus_1']} -> W={r['owner_w']} -> W+1={r['owner_w_plus_1']} | "
        f"drop={r['drop_from']} add={r['add_to']} | "
        f"updated={r['status_updated_utc']} | {r['reason']}"
    )

print()
print("PATTERN SUMMARY")
print("-"*118)
patterns={}
for r in bad:
    key=(str(r["transaction_type"]),r["reason"])
    patterns[key]=patterns.get(key,0)+1
for (typ,reason),n in sorted(patterns.items(), key=lambda x:(-x[1],x[0])):
    print(f"{n:>3} | {typ:<10} | {reason}")

print()
print("DECISION RULE")
print("-"*118)
print("Do NOT auto-PASS from this script alone.")
print("If disagreements cluster around same-week transaction ordering/timing while W+1 reflects the completed move,")
print("we can define a conservative ownership convention using the prior preserved snapshot.")
print("If disagreements show later/final-state contamination across adjacent weeks, PARK/KILL matchup.players.")
print()
print(f"Saved: {OUT_ALL}")
print(f"Saved: {OUT_BAD if bad else '(no disagreement file; zero disagreements)'}")
