#!/usr/bin/env python3
"""
WOOKIEE INTERPOSITIONAL FREE VALUE AUDIT V0.1

Question:
In Wookiee 2023-2025, how much realized weekly WoRP came from players who were
already rostered versus players who were free in that week's Sleeper ownership snapshot?

Scope:
- In-season only
- QB / RB / WR / TE
- Uses existing wookiee_2023_2025_weekly_worp.csv
- Uses Sleeper matchup.players as the validated weekly ownership snapshot
- Excludes the known ambiguous transaction cases if the disagreement CSV is present
- NO Captura
- NO offseason
- NO FAAB/acquisition-price modeling yet

Important:
This is a first economic map, not a final "optimal roster construction" answer.
"""

import csv
import json
import urllib.request
from pathlib import Path
from collections import defaultdict
from statistics import median, mean

WORP_CSV = Path("wookiee_2023_2025_weekly_worp.csv")
AMBIG_CSV = Path("wookiee_transaction_timing_disagreements_v0_1.csv")

LEAGUES = {
    2023: "950220100039311360",
    2024: "1050961255520923648",
    2025: "1182581249532833792",
}

OUT_DETAIL = Path("wookiee_interpositional_free_value_detail_v0_1.csv")
OUT_POSITION = Path("wookiee_interpositional_free_value_by_position_v0_1.csv")
OUT_WEEK = Path("wookiee_interpositional_free_value_by_week_v0_1.csv")

POSITIONS = {"QB", "RB", "WR", "TE"}

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "WoRPLab/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def matchups(lid, week):
    return get_json(f"https://api.sleeper.app/v1/league/{lid}/matchups/{week}")

def matchup_owned_ids(rows):
    owned = set()
    for r in rows or []:
        for pid in (r.get("players") or []):
            if pid is not None:
                owned.add(str(pid))
    return owned

def detect_col(cols, candidates, label):
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    raise RuntimeError(f"Could not detect {label} column. Columns found: {cols}")

def fnum(x):
    try:
        return float(x)
    except Exception:
        return None

if not WORP_CSV.exists():
    raise SystemExit(f"Missing required file: {WORP_CSV}")

with WORP_CSV.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    cols = reader.fieldnames or []

season_col = detect_col(cols, ["season", "year"], "season")
week_col = detect_col(cols, ["week"], "week")
pos_col = detect_col(cols, ["position", "pos"], "position")
worp_col = detect_col(cols, ["worp", "weekly_worp"], "WoRP")
pid_col = detect_col(
    cols,
    ["player_id", "sleeper_id", "playerid", "id"],
    "player id"
)

name_col = None
for cand in ["player_name", "full_name", "name", "player"]:
    if cand in cols:
        name_col = cand
        break

print("=" * 116)
print("WOOKIEE INTERPOSITIONAL FREE VALUE AUDIT V0.1")
print("=" * 116)
print("Question: how much realized weekly WoRP was rostered vs free, by position?")
print("Scope: 2023-2025 in-season only. No Captura / offseason / FAAB.")
print()
print("Detected columns:")
print(f"  season={season_col} | week={week_col} | position={pos_col} | player_id={pid_col} | worp={worp_col}")
print(f"  player_name={name_col or '(not present)'}")
print()

# Known ambiguous transaction-week cases: discard only the exact focal player-week.
ambiguous = set()
if AMBIG_CSV.exists():
    with AMBIG_CSV.open(newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                ambiguous.add((int(r["season"]), int(r["transaction_week"]), str(r["player_id"])))
            except Exception:
                pass

# Pull weekly ownership snapshots.
owned_by_week = {}
for season, lid in LEAGUES.items():
    for week in range(1, 19):
        owned_by_week[(season, week)] = matchup_owned_ids(matchups(lid, week))

detail = []
eligible = 0
matched_id = 0
excluded_ambiguous = 0

for r in rows:
    try:
        season = int(float(r[season_col]))
        week = int(float(r[week_col]))
    except Exception:
        continue

    if season not in LEAGUES or not (1 <= week <= 18):
        continue

    pos = str(r[pos_col]).upper().strip()
    if pos not in POSITIONS:
        continue

    pid = str(r[pid_col]).strip()
    worp = fnum(r[worp_col])
    if not pid or worp is None:
        continue

    eligible += 1

    if (season, week, pid) in ambiguous:
        excluded_ambiguous += 1
        continue

    owned = owned_by_week[(season, week)]
    is_rostered = pid in owned
    if is_rostered:
        matched_id += 1

    detail.append({
        "season": season,
        "week": week,
        "player_id": pid,
        "player_name": r.get(name_col, "") if name_col else "",
        "position": pos,
        "worp": worp,
        "ownership_state": "ROSTERED" if is_rostered else "FREE",
    })

# A low rostered match rate would indicate an ID-namespace problem, not a football result.
rostered_rate = matched_id / max(1, len(detail))

print("JOIN / SOURCE GATE")
print("-" * 116)
print(f"Eligible weekly QB/RB/WR/TE rows: {eligible}")
print(f"Excluded known ambiguous player-weeks: {excluded_ambiguous}")
print(f"Rows analyzed: {len(detail)}")
print(f"Rows matching a Sleeper-owned player that week: {matched_id} ({100*rostered_rate:.1f}%)")
print()

# We expect many free players, so rostered rate need not be near 100%.
# But if absurdly low, player IDs probably do not share the Sleeper namespace.
if rostered_rate < 0.10:
    print("FAIL: <10% of weekly rows match Sleeper ownership.")
    print("Likely player-ID namespace mismatch. STOP before interpreting economics.")
    raise SystemExit(2)

# Save detail.
with OUT_DETAIL.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(detail[0].keys()))
    w.writeheader()
    w.writerows(detail)

# Summaries by position/state.
group = defaultdict(list)
for r in detail:
    group[(r["position"], r["ownership_state"])].append(r["worp"])

summary_rows = []
print("ECONOMIC MAP BY POSITION")
print("-" * 116)
print(f"{'POS':<4} {'STATE':<9} {'N':>7} {'MEAN WoRP':>12} {'MEDIAN':>12} {'POS WoRP%':>12} {'TOTAL WoRP':>12}")
for pos in ["QB","RB","WR","TE"]:
    for state in ["ROSTERED","FREE"]:
        xs = group.get((pos,state), [])
        if not xs:
            continue
        pos_pct = sum(x > 0 for x in xs) / len(xs)
        row = {
            "position": pos,
            "ownership_state": state,
            "n_player_weeks": len(xs),
            "mean_weekly_worp": mean(xs),
            "median_weekly_worp": median(xs),
            "positive_worp_pct": pos_pct,
            "total_worp": sum(xs),
        }
        summary_rows.append(row)
        print(
            f"{pos:<4} {state:<9} {len(xs):>7} "
            f"{mean(xs):>12.4f} {median(xs):>12.4f} {100*pos_pct:>11.1f}% {sum(xs):>12.3f}"
        )

with OUT_POSITION.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
    w.writeheader()
    w.writerows(summary_rows)

# Weekly "free value frontier": best free WoRP available by position each week.
week_summary = []
print()
print("BEST FREE WoRP AVAILABLE PER WEEK — DISTRIBUTION ACROSS 54 WEEKS")
print("-" * 116)
for pos in ["QB","RB","WR","TE"]:
    bests = []
    for season in LEAGUES:
        for week in range(1,19):
            xs = [
                r["worp"] for r in detail
                if r["season"] == season and r["week"] == week
                and r["position"] == pos and r["ownership_state"] == "FREE"
            ]
            if xs:
                bests.append(max(xs))
                week_summary.append({
                    "season": season,
                    "week": week,
                    "position": pos,
                    "best_free_worp": max(xs),
                })
    if bests:
        s = sorted(bests)
        p25 = s[max(0, int(0.25*(len(s)-1)))]
        p75 = s[max(0, int(0.75*(len(s)-1)))]
        print(
            f"{pos}: weeks={len(bests)} | median best-free={median(bests):.4f} | "
            f"mean={mean(bests):.4f} | P25={p25:.4f} | P75={p75:.4f} | max={max(bests):.4f}"
        )

with OUT_WEEK.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(week_summary[0].keys()))
    w.writeheader()
    w.writerows(week_summary)

print()
print("DECISION GATE")
print("-" * 116)
print("ADVANCE only if:")
print("  1) the ID/source gate is plausible; and")
print("  2) free-vs-rostered WoRP distributions show interpretable positional structure.")
print()
print("DO NOT conclude Captura, fungibility, offseason behavior, or acquisition cost from this audit.")
print()
print("Saved:")
print(f"  {OUT_DETAIL}")
print(f"  {OUT_POSITION}")
print(f"  {OUT_WEEK}")
