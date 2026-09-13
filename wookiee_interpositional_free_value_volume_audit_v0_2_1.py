#!/usr/bin/env python3
"""
WOOKIEE INTERPOSITIONAL FREE VALUE + VOLUME AUDIT V0.2.1
PATCH: Sleeper player_id -> Sleeper metadata gsis_id -> nflverse weekly player_id.
No fuzzy-name matching. No frozen WoRP math changes.
"""

import json, urllib.request
from pathlib import Path
import pandas as pd

WORP_FILE = Path("wookiee_2023_2025_weekly_worp.csv")
LEAGUES = {
    2023: "950220100039311360",
    2024: "1050961255520923648",
    2025: "1182581249532833792",
}
POSITIONS = {"QB","RB","WR","TE"}

def api_json(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent":"WoRPLab/0.2.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def detect(df, names, required=True):
    lower = {str(c).lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    if required:
        raise RuntimeError(f"Missing one of {names}. Columns: {list(df.columns)}")
    return None

def load_weekly_stats(seasons):
    import nflreadpy as nfl
    out = nfl.load_player_stats(list(seasons))
    if hasattr(out, "to_pandas"):
        out = out.to_pandas()
    return out.copy()

print("="*112)
print("WOOKIEE INTERPOSITIONAL FREE VALUE + VOLUME AUDIT V0.2.1")
print("="*112)

w = pd.read_csv(WORP_FILE)
w["player_id"] = w["player_id"].astype(str)
w["position"] = w["position"].astype(str).str.upper()
w = w[
    w["season"].isin(LEAGUES) &
    w["week"].between(1,18) &
    w["position"].isin(POSITIONS)
].copy()
print(f"WoRP rows: {len(w)}")

# 1) Exact Sleeper -> GSIS bridge from Sleeper's own player metadata.
print("Loading Sleeper player metadata...")
players = api_json("https://api.sleeper.app/v1/players/nfl")
bridge = {}
for sleeper_id, meta in players.items():
    gsis = (meta or {}).get("gsis_id")
    if gsis:
        bridge[str(sleeper_id)] = str(gsis)

w["gsis_id"] = w["player_id"].map(bridge)
bridge_rate = w["gsis_id"].notna().mean()
print(f"Sleeper -> GSIS bridge: {w['gsis_id'].notna().sum()}/{len(w)} = {100*bridge_rate:.1f}%")
if bridge_rate < .90:
    print("FAIL: bridge below 90%. STOP.")
    raise SystemExit(2)

# 2) Weekly ownership snapshot.
owned = {}
for season,lid in LEAGUES.items():
    for week in range(1,19):
        rows = api_json(f"https://api.sleeper.app/v1/league/{lid}/matchups/{week}")
        ids = set()
        for r in rows:
            ids.update(str(x) for x in (r.get("players") or []) if x is not None)
        owned[(season,week)] = ids

w["ownership_state"] = [
    "ROSTERED" if pid in owned[(int(s),int(week))] else "FREE"
    for s,week,pid in zip(w.season,w.week,w.player_id)
]

# 3) nflverse weekly volume.
stats = load_weekly_stats([2023,2024,2025])
sc = detect(stats, ["season"])
wc = detect(stats, ["week"])
ic = detect(stats, ["player_id"])
stats = stats.rename(columns={sc:"season",wc:"week",ic:"gsis_id"})
stats["gsis_id"] = stats["gsis_id"].astype(str)
stats = stats[stats["season"].isin(LEAGUES) & stats["week"].between(1,18)].copy()

aliases = {
    "carries": ["carries","rushing_attempts","rush_attempts"],
    "targets": ["targets"],
    "receptions": ["receptions"],
    "pass_attempts": ["attempts","passing_attempts","pass_attempts"],
    "rush_yards": ["rushing_yards","rush_yards"],
    "rec_yards": ["receiving_yards","rec_yards"],
    "pass_yards": ["passing_yards","pass_yards"],
    "pass_tds": ["passing_tds","pass_tds"],
    "rush_tds": ["rushing_tds","rush_tds"],
    "rec_tds": ["receiving_tds","rec_tds"],
}
found = {}
for out,names in aliases.items():
    c = detect(stats,names,required=False)
    if c: found[out]=c

keep = ["season","week","gsis_id"] + list(dict.fromkeys(found.values()))
s = stats[keep].rename(columns={v:k for k,v in found.items()}).copy()
for k in found:
    s[k] = pd.to_numeric(s[k], errors="coerce").fillna(0.0)
s = s.groupby(["season","week","gsis_id"],as_index=False).sum(numeric_only=True)

m = w.merge(s,on=["season","week","gsis_id"],how="left",indicator=True)
join_rate = (m["_merge"]=="both").mean()
print(f"GSIS weekly-stat join: {(m['_merge']=='both').sum()}/{len(m)} = {100*join_rate:.1f}%")

# Important: WoRP cache contains many zero/no-stat player-weeks. Measure join among actual scorers too.
active = pd.to_numeric(m["fantasy_points"],errors="coerce").fillna(0) != 0
active_join = ((m["_merge"]=="both") & active).sum()
active_n = active.sum()
active_rate = active_join/max(1,active_n)
print(f"Join among nonzero-FP rows: {active_join}/{active_n} = {100*active_rate:.1f}%")
if active_rate < .95:
    print("FAIL: active-player weekly-stat join below 95%. STOP before economics.")
    raise SystemExit(3)
m = m.drop(columns="_merge")

for k in aliases:
    if k not in m: m[k]=0.0
    m[k]=pd.to_numeric(m[k],errors="coerce").fillna(0.0)

m["opportunities"] = m["carries"] + m["targets"]
m["scrimmage_yards"] = m["rush_yards"] + m["rec_yards"]
m["total_tds"] = m["pass_tds"] + m["rush_tds"] + m["rec_tds"]

m["volume"] = 0.0
m.loc[m.position=="QB","volume"] = m["pass_attempts"] + m["carries"]
m.loc[m.position=="RB","volume"] = m["carries"] + m["targets"]
m.loc[m.position.isin(["WR","TE"]),"volume"] = m["targets"]

m["volume_metric"] = m["position"].map({
    "QB":"pass attempts + carries",
    "RB":"carries + targets",
    "WR":"targets",
    "TE":"targets",
})

m.to_csv("wookiee_interpositional_free_value_volume_detail_v0_2_1.csv",index=False)

print()
print("FREE POOL — POSITIVE WoRP + SAME-WEEK VOLUME")
print("-"*112)
summary=[]
for pos in ["QB","RB","WR","TE"]:
    x=m[(m.position==pos)&(m.ownership_state=="FREE")&(m.weekly_worp>0)].copy()
    if x.empty: continue
    total=x.weekly_worp.sum()
    med=x.volume.median()
    p75=x.volume.quantile(.75)
    low=x[x.volume<med].weekly_worp.sum()/total if total else 0
    high=x[x.volume>=p75].weekly_worp.sum()/total if total else 0
    summary.append([pos,len(x),total,med,p75,low,high])
    print(f"{pos}: n={len(x):4d} | +Free WoRP={total:7.3f} | volume med={med:5.1f} P75={p75:5.1f} | "
          f"WoRP <med volume={100*low:5.1f}% | WoRP >=P75 volume={100*high:5.1f}%")

pd.DataFrame(summary,columns=[
    "position","positive_free_player_weeks","positive_free_worp",
    "median_volume","p75_volume","worp_share_below_median_volume",
    "worp_share_at_or_above_p75_volume"
]).to_csv("wookiee_interpositional_free_value_volume_by_position_v0_2_1.csv",index=False)

# Impact cases, balanced by position: top 15 each rather than letting WR volume swamp the review.
case_cols=["season","week","player_id","player_name","position","fantasy_points","weekly_worp",
           "volume","volume_metric","carries","targets","receptions","pass_attempts",
           "scrimmage_yards","pass_yards","total_tds"]
cases=[]
for pos in ["QB","RB","WR","TE"]:
    x=(m[(m.position==pos)&(m.ownership_state=="FREE")&(m.weekly_worp>0)]
       .sort_values("weekly_worp",ascending=False).head(15))
    cases.append(x[case_cols])
cases=pd.concat(cases,ignore_index=True)
cases.to_csv("wookiee_interpositional_free_value_human_cases_v0_2_1.csv",index=False)

print()
print("TOP 5 FREE CASES PER POSITION")
print("-"*112)
for pos in ["QB","RB","WR","TE"]:
    x=cases[cases.position==pos].head(5)
    print(f"\n{pos}")
    print(x[["season","week","player_name","fantasy_points","weekly_worp","volume","volume_metric","total_tds"]].to_string(index=False))

print()
print("STOP HERE FOR INTERPRETATION.")
print("Same-week volume tells us whether production had workload behind it; it does NOT prove ex-ante diagnosability.")
print("Saved detail, positional summary, and 15 high-impact human-review cases per position.")
