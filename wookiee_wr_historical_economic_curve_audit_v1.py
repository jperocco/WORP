#!/usr/bin/env python3
"""
WOOKIEE WR HISTORICAL ECONOMIC CURVE AUDIT V1

Question:
Does the realized-WoRP curve shape found in 2023-2025 survive over a longer
historical window when the CURRENT Wookiee lineup/scoring is applied?

Specifically:
  - Is the top of the WR curve consistently steep?
  - Does marginal realized WoRP compress through the middle?
  - Does a broad low-marginal-value tail emerge around WR55/60+?

IMPORTANT:
- This tests realized value structure only.
- It does NOT test identification, Captura, waiver replacement, fungibility,
  market value, trades, or roster construction.
- Current Wookiee rules are applied retrospectively to historical NFL stats.
- No automatic "threshold" is declared.

Requires in same folder:
  worp_engine.py

Uses Sleeper weekly stats and current Wookiee league settings.
"""

import json
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd

from worp_engine import LeagueSettings, compute_worp

LEAGUE_ID = "1317417394439741440"
SEASONS = list(range(2018, 2026))
N_SIMS = 8000
SEED = 7
BAND_SIZE = 6

OUT_RANKINGS = Path("wookiee_wr_historical_economic_rankings_2018_2025.csv")
OUT_PROFILE = Path("wookiee_wr_historical_economic_rank_profile_2018_2025.csv")
OUT_YEAR = Path("wookiee_wr_historical_economic_year_checks_2018_2025.csv")

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "WoRPLab/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def sleeper_week(season, week):
    return get_json(f"https://api.sleeper.app/v1/stats/nfl/regular/{season}/{week}")

def normalize_week(raw):
    rows = []
    if isinstance(raw, dict):
        iterator = raw.items()
        for pid, payload in iterator:
            if isinstance(payload, dict) and "stats" in payload and isinstance(payload["stats"], dict):
                stats = payload["stats"]
            elif isinstance(payload, dict):
                stats = payload
            else:
                continue
            row = {"player_id": str(pid)}
            row.update(stats)
            rows.append(row)
    elif isinstance(raw, list):
        for payload in raw:
            if not isinstance(payload, dict):
                continue
            pid = payload.get("player_id")
            if pid is None:
                continue
            stats = payload.get("stats", {})
            if not isinstance(stats, dict):
                continue
            row = {"player_id": str(pid)}
            row.update(stats)
            rows.append(row)
    return pd.DataFrame(rows)

def fantasy_points(df, scoring):
    total = np.zeros(len(df), dtype=float)
    for key, weight in scoring.items():
        if not weight:
            continue
        if key in df.columns:
            total += pd.to_numeric(df[key], errors="coerce").fillna(0).to_numpy() * float(weight)
    return total

def parse_settings(roster_positions):
    fixed = {"QB":0, "RB":0, "WR":0, "TE":0}
    flex = 0
    sf = 0
    for p in roster_positions:
        p = str(p).upper()
        if p in fixed:
            fixed[p] += 1
        elif p == "FLEX":
            flex += 1
        elif p in ("SUPER_FLEX", "SUPERFLEX"):
            sf += 1
    return fixed, flex, sf

league = get_json(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}")
scoring = {k: float(v) for k,v in league["scoring_settings"].items() if float(v) != 0}
fixed, flex, sf = parse_settings(league["roster_positions"])

print("="*110)
print("WOOKIEE WR HISTORICAL ECONOMIC CURVE AUDIT V1")
print("="*110)
print(f"League: {league.get('name')}")
print(f"Current lineup applied retrospectively: {fixed} + {flex} FLEX + {sf} SF")
print(f"Historical seasons: {SEASONS[0]}-{SEASONS[-1]}")
print("This is realized-value structure only. flatness != fungibility.")
print()

players = get_json("https://api.sleeper.app/v1/players/nfl")
meta = {}
for pid, p in players.items():
    if not isinstance(p, dict):
        continue
    pos = str(p.get("position") or "").upper()
    if pos in {"QB","RB","WR","TE"}:
        meta[str(pid)] = {
            "player_name": p.get("full_name") or p.get("first_name","") + " " + p.get("last_name",""),
            "position": pos
        }

# Build LeagueSettings using the same constructor pattern as the frozen project.
# Try common signatures defensively.
try:
    settings = LeagueSettings(
        teams=12,
        fixed_slots=fixed,
        flex_slots=flex,
        superflex_slots=sf,
        replacement_band=BAND_SIZE,
    )
except TypeError:
    try:
        settings = LeagueSettings(
            n_teams=12,
            fixed_slots=fixed,
            flex_slots=flex,
            superflex_slots=sf,
            replacement_band=BAND_SIZE,
        )
    except TypeError:
        # Match known frozen-engine field naming if dataclass exposes it.
        import inspect
        sig = inspect.signature(LeagueSettings)
        print("LeagueSettings signature:", sig)
        raise

all_rankings = []

for season in SEASONS:
    print(f"Season {season}")
    week_frames = []
    for week in range(1, 19):
        raw = sleeper_week(season, week)
        w = normalize_week(raw)
        if w.empty:
            continue
        w["season"] = season
        w["week"] = week
        w["player_id"] = w["player_id"].astype(str)
        w["position"] = w["player_id"].map(lambda x: meta.get(x, {}).get("position"))
        w["player_name"] = w["player_id"].map(lambda x: meta.get(x, {}).get("player_name"))
        w = w[w["position"].isin(["QB","RB","WR","TE"])].copy()
        w["fantasy_points"] = fantasy_points(w, scoring)
        week_frames.append(w[["season","week","player_id","player_name","position","fantasy_points"]])
        print(f"  Week {week:2d}: {len(w):4d} rows")
    if not week_frames:
        print("  No usable data; skipping.")
        continue
    season_df = pd.concat(week_frames, ignore_index=True)

    print("  Running frozen WoRP engine...")
    # Frozen engine expected to return weekly and rankings.
    result = compute_worp(season_df, settings, n_sims=N_SIMS, seed=SEED)
    if isinstance(result, tuple) and len(result) == 2:
        weekly, rankings = result
    elif isinstance(result, dict):
        weekly = result.get("weekly")
        rankings = result.get("rankings")
    else:
        raise TypeError(f"Unexpected compute_worp return type: {type(result)}")

    rankings = rankings.copy()
    if "season" not in rankings.columns:
        rankings["season"] = season
    all_rankings.append(rankings)

rankings = pd.concat(all_rankings, ignore_index=True)

# Robust column names
pos_col = "position" if "position" in rankings.columns else "pos"
worp_col = "worp" if "worp" in rankings.columns else "season_worp"
name_col = "player_name" if "player_name" in rankings.columns else None

wr = rankings[rankings[pos_col].astype(str).str.upper().eq("WR")].copy()
wr["pos_rank"] = wr.groupby("season")[worp_col].rank(method="first", ascending=False).astype(int)
wr.to_csv(OUT_RANKINGS, index=False)

profile = (
    wr[wr["pos_rank"].le(96)]
    .groupby("pos_rank")
    .agg(
        seasons=("season","nunique"),
        mean_worp=(worp_col,"mean"),
        median_worp=(worp_col,"median"),
        sd_worp=(worp_col,"std")
    )
    .reset_index()
    .sort_values("pos_rank")
)
profile.to_csv(OUT_PROFILE, index=False)
lookup = profile.set_index("pos_rank")["mean_worp"].to_dict()

anchors = [1,8,12,20,24,30,36,40,42,45,48,50,54,55,60,66,72,78,84,90]
pairs = [(1,8),(8,20),(20,40),(30,40),(30,50),(36,48),
         (40,50),(40,55),(42,54),(45,54),(48,60),(50,60),
         (55,60),(55,72),(60,72),(60,84),(60,90),(72,90)]

print()
print("="*110)
print("1. LONG-WINDOW SELECTED RANK PROFILE")
print("="*110)
for r in anchors:
    if r in lookup:
        row = profile[profile.pos_rank.eq(r)].iloc[0]
        print(f"WR{r:<2} | seasons={int(row.seasons)} | mean WoRP={row.mean_worp:+.3f} | median={row.median_worp:+.3f}")

print()
print("="*110)
print("2. LONG-WINDOW ANCHOR DIFFERENCES")
print("="*110)
for a,b in pairs:
    if a in lookup and b in lookup:
        print(f"WR{a:<2} -> WR{b:<2}: {lookup[a]-lookup[b]:+.3f} WoRP")

# 12-rank costs
rows = []
for r in range(1,79):
    if r in lookup and r+12 in lookup:
        rows.append({"start_rank":r, "cost12":lookup[r]-lookup[r+12]})
cost = pd.DataFrame(rows)
zones = [(1,20),(21,35),(30,50),(36,55),(41,60),(55,72),(60,78)]

print()
print("="*110)
print("3. 12-RANK MARGINAL COST — LONG WINDOW")
print("="*110)
for lo,hi in zones:
    z = cost[cost.start_rank.between(lo,hi)]
    if len(z):
        print(f"WR{lo}-WR{hi}: median={z.cost12.median():.3f} | mean={z.cost12.mean():.3f} | range={z.cost12.min():.3f}..{z.cost12.max():.3f}")

# Year-by-year selected pairs
yr = []
for season, g in wr.groupby("season"):
    d = g.set_index("pos_rank")[worp_col].to_dict()
    for a,b in pairs:
        if (a,b) in [(1,8),(8,20),(20,40),(30,50),(40,55),(45,54),(48,60),(55,72),(60,72)]:
            if a in d and b in d:
                yr.append({"season":season,"from_rank":a,"to_rank":b,"worp_difference":d[a]-d[b]})
year_df = pd.DataFrame(yr)
year_df.to_csv(OUT_YEAR, index=False)

print()
print("="*110)
print("4. YEAR-BY-YEAR STABILITY")
print("="*110)
piv = year_df.pivot_table(index=["from_rank","to_rank"], columns="season", values="worp_difference").reset_index()
for _, row in piv.iterrows():
    vals = []
    for s in SEASONS:
        v = row.get(s, np.nan)
        vals.append(f"{s}:{v:+.3f}" if pd.notna(v) else f"{s}:NA")
    print(f"WR{int(row.from_rank)} -> WR{int(row.to_rank)} | " + "  ".join(vals))

print()
print("="*110)
print("5. DECISION GATE")
print("="*110)
print("""
We are looking for SHAPE stability, not identical ranks or identical deltas.

ADVANCE if:
- top remains much steeper than middle in most seasons;
- marginal 12-rank cost generally compresses as rank moves right;
- WR55/60+ remains a distinctly low-marginal-value region across the long window.

PARK if:
- 2023-2025 shape was unusually specific to those seasons.

KILL a discrete boundary if:
- the broad compression survives but exact ~55/~60 boundary moves substantially.

DO NOT infer:
identification, Captura, fungibility, waiver replaceability, market/trade strategy,
or optimal roster construction.
""")
print("Saved:")
for p in [OUT_RANKINGS, OUT_PROFILE, OUT_YEAR]:
    print(f"  {p}")
