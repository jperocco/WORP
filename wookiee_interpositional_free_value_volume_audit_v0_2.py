#!/usr/bin/env python3
"""
WOOKIEE INTERPOSITIONAL FREE VALUE + VOLUME AUDIT V0.2

First-pass descriptive audit only.
Question:
When realized weekly WoRP appeared in Wookiee's FREE pool, was it accompanied
by meaningful same-week opportunity/volume, or was it mostly scoring spike?

NO ex-ante diagnosability classification.
NO offseason.
NO FAAB.
NO Captura.
NO frozen-engine math changes.

Inputs expected in current folder:
- wookiee_2023_2025_weekly_worp.csv
- weekly ownership is fetched from Sleeper matchup snapshots
- weekly NFL stats are loaded through the project's existing nflverse_loader.py
"""

from pathlib import Path
from collections import defaultdict
from statistics import mean, median
import csv, json, urllib.request
import pandas as pd

WORP_FILE = Path("wookiee_2023_2025_weekly_worp.csv")
LEAGUES = {
    2023: "950220100039311360",
    2024: "1050961255520923648",
    2025: "1182581249532833792",
}
POSITIONS = {"QB","RB","WR","TE"}

def api_json(url):
    req = urllib.request.Request(url, headers={"User-Agent":"WoRPLab/0.2"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def detect(df, names, required=True):
    lower = {str(c).lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    if required:
        raise RuntimeError(f"Missing one of {names}. Columns: {list(df.columns)}")
    return None

def num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

def load_weekly_stats(seasons):
    # Use the project's already-installed nflverse path rather than inventing a new data source.
    import nflverse_loader as nl

    candidates = [
        "load_weekly_data",
        "load_weekly",
        "load_player_stats",
        "load_weekly_stats",
    ]
    last = None
    for name in candidates:
        fn = getattr(nl, name, None)
        if not callable(fn):
            continue
        for arg in (list(seasons), tuple(seasons)):
            try:
                out = fn(arg)
                if isinstance(out, pd.DataFrame):
                    return out.copy()
            except Exception as e:
                last = e
        # Some loaders accept one season at a time.
        frames = []
        try:
            for s in seasons:
                x = fn(s)
                if not isinstance(x, pd.DataFrame):
                    raise TypeError
                frames.append(x)
            if frames:
                return pd.concat(frames, ignore_index=True)
        except Exception as e:
            last = e

    # nflreadpy fallback, already part of the WoRP project stack.
    try:
        import nflreadpy as nfl
        for name in ("load_player_stats", "load_weekly_data"):
            fn = getattr(nfl, name, None)
            if callable(fn):
                out = fn(list(seasons))
                if hasattr(out, "to_pandas"):
                    out = out.to_pandas()
                if isinstance(out, pd.DataFrame):
                    return out.copy()
    except Exception as e:
        last = e

    raise RuntimeError(
        "Could not load weekly NFL stats using the existing project loader. "
        f"Last error: {last}"
    )

if not WORP_FILE.exists():
    raise SystemExit(f"Missing {WORP_FILE}")

worp = pd.read_csv(WORP_FILE)
sc = detect(worp, ["season","year"])
wc = detect(worp, ["week"])
pc = detect(worp, ["position","pos"])
ic = detect(worp, ["player_id","sleeper_id","playerid","id"])
woc = detect(worp, ["weekly_worp","worp"])
fpc = detect(worp, ["fantasy_points","fantasy_points_ppr","points","fp"], required=False)
nc = detect(worp, ["player_name","full_name","name","player"], required=False)

worp = worp.rename(columns={sc:"season",wc:"week",pc:"position",ic:"player_id",woc:"weekly_worp"})
if fpc: worp = worp.rename(columns={fpc:"wookiee_fp"})
if nc: worp = worp.rename(columns={nc:"player_name"})
worp["season"] = pd.to_numeric(worp["season"], errors="coerce")
worp["week"] = pd.to_numeric(worp["week"], errors="coerce")
worp["player_id"] = worp["player_id"].astype(str)
worp["position"] = worp["position"].astype(str).str.upper()
worp = worp[
    worp["season"].isin(LEAGUES) &
    worp["week"].between(1,18) &
    worp["position"].isin(POSITIONS)
].copy()
worp["season"] = worp["season"].astype(int)
worp["week"] = worp["week"].astype(int)

print("="*120)
print("WOOKIEE INTERPOSITIONAL FREE VALUE + VOLUME AUDIT V0.2")
print("="*120)
print(f"WoRP rows loaded: {len(worp)}")

# Ownership snapshots.
owned = {}
for season,lid in LEAGUES.items():
    for week in range(1,19):
        rows = api_json(f"https://api.sleeper.app/v1/league/{lid}/matchups/{week}")
        ids = set()
        for r in rows:
            ids.update(str(x) for x in (r.get("players") or []) if x is not None)
        owned[(season,week)] = ids

worp["ownership_state"] = [
    "ROSTERED" if pid in owned[(s,w)] else "FREE"
    for s,w,pid in zip(worp.season,worp.week,worp.player_id)
]

# Weekly stats.
stats = load_weekly_stats([2023,2024,2025])
ss = detect(stats, ["season","year"])
sw = detect(stats, ["week"])
sid = detect(stats, ["player_id","sleeper_id","playerid","id"], required=False)
sname = detect(stats, ["player_name","full_name","name","player_display_name"], required=False)
spos = detect(stats, ["position","pos"], required=False)

stats = stats.rename(columns={ss:"season",sw:"week"})
stats["season"] = pd.to_numeric(stats["season"], errors="coerce")
stats["week"] = pd.to_numeric(stats["week"], errors="coerce")
stats = stats[stats["season"].isin(LEAGUES) & stats["week"].between(1,18)].copy()
stats["season"] = stats["season"].astype(int)
stats["week"] = stats["week"].astype(int)

# We strongly prefer exact player_id. If namespaces do not match, STOP instead of fuzzy-name guessing.
if sid is None:
    raise RuntimeError("Weekly stats have no player_id column. STOP: no fuzzy-name join allowed.")
stats = stats.rename(columns={sid:"player_id"})
stats["player_id"] = stats["player_id"].astype(str)

# Volume columns: detect only what actually exists.
col = {}
for key,names in {
    "carries":["carries","rushing_attempts","rush_attempts"],
    "targets":["targets"],
    "receptions":["receptions"],
    "pass_attempts":["attempts","passing_attempts","pass_attempts"],
    "rush_yards":["rushing_yards","rush_yards"],
    "rec_yards":["receiving_yards","rec_yards"],
    "pass_yards":["passing_yards","pass_yards"],
    "pass_tds":["passing_tds","pass_tds"],
    "rush_tds":["rushing_tds","rush_tds"],
    "rec_tds":["receiving_tds","rec_tds"],
}.items():
    c = detect(stats, names, required=False)
    if c:
        col[key] = c

keep = ["season","week","player_id"] + list(dict.fromkeys(col.values()))
stats2 = stats[keep].copy()
rename = {v:k for k,v in col.items()}
stats2 = stats2.rename(columns=rename)
for k in col:
    stats2[k] = num(stats2[k])

# Deduplicate defensively.
agg = {k:"sum" for k in col}
stats2 = stats2.groupby(["season","week","player_id"], as_index=False).agg(agg)

m = worp.merge(stats2, on=["season","week","player_id"], how="left", indicator=True)
match_rate = (m["_merge"]=="both").mean()
print(f"Weekly NFL-stat join: {(m['_merge']=='both').sum()}/{len(m)} = {100*match_rate:.1f}%")
if match_rate < .90:
    print("FAIL: weekly stats join below 90%. STOP — likely ID/schema mismatch.")
    raise SystemExit(2)
m = m.drop(columns="_merge")

for k in ["carries","targets","receptions","pass_attempts","rush_yards","rec_yards","pass_yards",
          "pass_tds","rush_tds","rec_tds"]:
    if k not in m:
        m[k] = 0.0
    else:
        m[k] = num(m[k])

m["opportunities"] = m["carries"] + m["targets"]
m["yards_from_scrimmage"] = m["rush_yards"] + m["rec_yards"]
m["total_tds"] = m["pass_tds"] + m["rush_tds"] + m["rec_tds"]

# Position-appropriate same-week volume measure.
m["volume"] = 0.0
m["volume_label"] = ""
for idx,r in m.iterrows():
    if r.position == "QB":
        m.at[idx,"volume"] = r.pass_attempts + r.carries
        m.at[idx,"volume_label"] = "pass attempts + carries"
    elif r.position == "RB":
        m.at[idx,"volume"] = r.carries + r.targets
        m.at[idx,"volume_label"] = "carries + targets"
    else:
        m.at[idx,"volume"] = r.targets
        m.at[idx,"volume_label"] = "targets"

# Save full joined table.
detail_out = "wookiee_interpositional_free_value_volume_detail_v0_2.csv"
m.to_csv(detail_out, index=False)

print()
print("FREE-POOL VOLUME MAP")
print("-"*120)
print("These are descriptive same-week results. Volume-backed != ex-ante diagnosable.")
print()

rows_out = []
for pos in ["QB","RB","WR","TE"]:
    x = m[(m.position==pos) & (m.ownership_state=="FREE")].copy()
    xp = x[x.weekly_worp > 0].copy()
    if len(xp)==0:
        continue
    q50 = xp.volume.median()
    q75 = xp.volume.quantile(.75)
    total_pos = xp.weekly_worp.sum()
    hi = xp[xp.volume >= q75]
    lo = xp[xp.volume < q50]
    rows_out.append({
        "position":pos,
        "free_positive_player_weeks":len(xp),
        "positive_free_worp":total_pos,
        "median_volume":q50,
        "p75_volume":q75,
        "worp_share_at_or_above_p75_volume": hi.weekly_worp.sum()/total_pos if total_pos else 0,
        "worp_share_below_median_volume": lo.weekly_worp.sum()/total_pos if total_pos else 0,
    })
    print(
        f"{pos}: positive free weeks={len(xp):4d} | positive Free WoRP={total_pos:8.3f} | "
        f"volume median={q50:5.1f} P75={q75:5.1f} | "
        f"WoRP from >=P75 volume={100*hi.weekly_worp.sum()/total_pos:5.1f}% | "
        f"WoRP from <median volume={100*lo.weekly_worp.sum()/total_pos:5.1f}%"
    )

pd.DataFrame(rows_out).to_csv("wookiee_interpositional_free_value_volume_by_position_v0_2.csv", index=False)

# Human-review cases: highest-impact positive FREE WoRP, with FP if already present,
# plus volume and TD/yard context. Do not label diagnosability.
case_cols = ["season","week","player_id"]
if "player_name" in m: case_cols.append("player_name")
case_cols += ["position","weekly_worp"]
if "wookiee_fp" in m: case_cols.append("wookiee_fp")
case_cols += [
    "volume","volume_label","carries","targets","receptions","pass_attempts",
    "yards_from_scrimmage","pass_yards","total_tds"
]
cases = (
    m[(m.ownership_state=="FREE") & (m.weekly_worp>0)]
    .sort_values("weekly_worp", ascending=False)
    [case_cols]
    .head(120)
)
cases.to_csv("wookiee_interpositional_free_value_human_cases_v0_2.csv", index=False)

print()
print("TOP 10 POSITIVE FREE WoRP CASES — FOR HUMAN CONTEXT, NOT AUTOMATIC DIAGNOSIS")
print("-"*120)
show = ["season","week"]
if "player_name" in cases: show.append("player_name")
else: show.append("player_id")
show += ["position","weekly_worp","volume","volume_label","total_tds"]
print(cases[show].head(10).to_string(index=False))

print()
print("DECISION GATE")
print("-"*120)
print("PASS if:")
print("  1) weekly NFL-stat join is coherent;")
print("  2) QB/RB/WR/TE show interpretable Free WoRP + same-week volume structure;")
print("  3) the high-impact case list is small enough for selective human diagnosis.")
print()
print("Do NOT infer ex-ante diagnosability from same-week volume.")
print("Do NOT infer fungibility/Captura/acquisition cost yet.")
print()
print("Saved:")
print("  " + detail_out)
print("  wookiee_interpositional_free_value_volume_by_position_v0_2.csv")
print("  wookiee_interpositional_free_value_human_cases_v0_2.csv")
