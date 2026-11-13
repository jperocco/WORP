#!/usr/bin/env python3
import json, urllib.request
from pathlib import Path
import pandas as pd

WORP = Path("wookiee_2023_2025_weekly_worp.csv")
LEAGUES = {
    2023:"950220100039311360",
    2024:"1050961255520923648",
    2025:"1182581249532833792",
}
POS = {"QB","RB","WR","TE"}

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"WoRPLab/0.2.3"})
    with urllib.request.urlopen(req,timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def parse(raw):
    if isinstance(raw,dict):
        return [(str(pid), st or {}) for pid,st in raw.items()]
    out=[]
    for rec in raw or []:
        if not isinstance(rec,dict) or rec.get("player_id") is None: continue
        st=rec.get("stats")
        if st is None:
            st={k:v for k,v in rec.items() if k not in {"player_id","team","opponent","game_id"}}
        out.append((str(rec["player_id"]),st or {}))
    return out

def val(st,*keys):
    for k in keys:
        if k in st:
            try: return float(st.get(k) or 0)
            except: return 0.0
    return 0.0

print("="*100)
print("WOOKIEE INTERPOSITIONAL FREE VALUE + VOLUME AUDIT V0.2.3")
print("="*100)

w=pd.read_csv(WORP)
w["player_id"]=w["player_id"].astype(str)
w=w[w.season.isin(LEAGUES)&w.week.between(1,18)&w.position.isin(POS)].copy()
print("WoRP rows:",len(w))

# Same Sleeper weekly stats source / same Sleeper player_id namespace used to build the cache.
vol=[]
for season in LEAGUES:
    for week in range(1,19):
        raw=get_json(f"https://api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular")
        for pid,st in parse(raw):
            vol.append({
                "season":season,"week":week,"player_id":pid,
                "carries":val(st,"rush_att","rushing_attempts","carries"),
                "targets":val(st,"rec_tgt","targets"),
                "receptions":val(st,"rec","receptions"),
                "pass_attempts":val(st,"pass_att","passing_attempts","attempts"),
                "rush_yards":val(st,"rush_yd","rushing_yards"),
                "rec_yards":val(st,"rec_yd","receiving_yards"),
                "pass_yards":val(st,"pass_yd","passing_yards"),
                "rush_tds":val(st,"rush_td","rushing_tds"),
                "rec_tds":val(st,"rec_td","receiving_tds"),
                "pass_tds":val(st,"pass_td","passing_tds"),
            })
v=pd.DataFrame(vol).drop_duplicates(["season","week","player_id"])

m=w.merge(v,on=["season","week","player_id"],how="left",indicator=True)
active=pd.to_numeric(m.fantasy_points,errors="coerce").fillna(0)!=0
active_rate=((m._merge=="both")&active).sum()/max(1,active.sum())
positive=pd.to_numeric(m.weekly_worp,errors="coerce").fillna(0)>0
pos_rate=((m._merge=="both")&positive).sum()/max(1,positive.sum())
print(f"Same-source join, nonzero FP: {100*active_rate:.2f}%")
print(f"Same-source join, positive WoRP: {100*pos_rate:.2f}%")

missing_positive=m[positive&(m._merge!="both")]
missing_pct=len(missing_positive)/max(1,positive.sum())
if missing_pct>=.04:
    print(f"GATILHO 4%: {100*missing_pct:.2f}% positive-WoRP rows missing. STOP.")
    print(missing_positive[["season","week","player_id","player_name","position","fantasy_points","weekly_worp"]]
          .sort_values("weekly_worp",ascending=False).head(20).to_string(index=False))
    raise SystemExit(2)

# Ownership snapshots.
owned={}
for season,lid in LEAGUES.items():
    for week in range(1,19):
        rows=get_json(f"https://api.sleeper.app/v1/league/{lid}/matchups/{week}")
        ids=set()
        for r in rows:
            ids.update(str(x) for x in (r.get("players") or []) if x is not None)
        owned[(season,week)]=ids

m["ownership_state"]=[
    "ROSTERED" if pid in owned[(int(s),int(week))] else "FREE"
    for s,week,pid in zip(m.season,m.week,m.player_id)
]
for c in ["carries","targets","receptions","pass_attempts","rush_yards","rec_yards",
          "pass_yards","rush_tds","rec_tds","pass_tds"]:
    m[c]=pd.to_numeric(m[c],errors="coerce").fillna(0)

m["volume"]=0.0
m.loc[m.position=="QB","volume"]=m.pass_attempts+m.carries
m.loc[m.position=="RB","volume"]=m.carries+m.targets
m.loc[m.position.isin(["WR","TE"]),"volume"]=m.targets
m["volume_metric"]=m.position.map({
    "QB":"pass attempts + carries","RB":"carries + targets","WR":"targets","TE":"targets"
})
m["total_tds"]=m.rush_tds+m.rec_tds+m.pass_tds
m["scrimmage_yards"]=m.rush_yards+m.rec_yards

print("\nFREE POOL — POSITIVE WoRP + SAME-WEEK VOLUME")
print("-"*100)
summary=[]
for p in ["QB","RB","WR","TE"]:
    x=m[(m.position==p)&(m.ownership_state=="FREE")&(m.weekly_worp>0)].copy()
    if x.empty: continue
    total=x.weekly_worp.sum()
    med=x.volume.median(); p75=x.volume.quantile(.75)
    low=x.loc[x.volume<med,"weekly_worp"].sum()/total
    high=x.loc[x.volume>=p75,"weekly_worp"].sum()/total
    summary.append([p,len(x),total,med,p75,low,high])
    print(f"{p}: n={len(x):4d} | +Free WoRP={total:7.3f} | volume med={med:5.1f} P75={p75:5.1f} | "
          f"WoRP <med vol={100*low:5.1f}% | WoRP >=P75 vol={100*high:5.1f}%")

pd.DataFrame(summary,columns=[
    "position","positive_free_player_weeks","positive_free_worp","median_volume","p75_volume",
    "worp_share_below_median_volume","worp_share_at_or_above_p75_volume"
]).to_csv("wookiee_interpositional_free_value_volume_by_position_v0_2_3.csv",index=False)

# Human review: top 15 per position, no automated "diagnosable" label.
cols=["season","week","player_id","player_name","position","fantasy_points","weekly_worp",
      "volume","volume_metric","carries","targets","receptions","pass_attempts",
      "scrimmage_yards","pass_yards","total_tds"]
cases=[]
for p in ["QB","RB","WR","TE"]:
    cases.append(m[(m.position==p)&(m.ownership_state=="FREE")&(m.weekly_worp>0)]
                 .sort_values("weekly_worp",ascending=False).head(15)[cols])
cases=pd.concat(cases,ignore_index=True)
cases.to_csv("wookiee_interpositional_free_value_human_cases_v0_2_3.csv",index=False)
m.to_csv("wookiee_interpositional_free_value_volume_detail_v0_2_3.csv",index=False)

print("\nTOP 5 FREE CASES PER POSITION")
for p in ["QB","RB","WR","TE"]:
    x=cases[cases.position==p].head(5)
    print("\n"+p)
    print(x[["season","week","player_name","fantasy_points","weekly_worp","volume","total_tds"]].to_string(index=False))

print("\nPASS: same Sleeper identity/source used for WoRP cache and volume.")
print("STOP HERE: same-week volume != ex-ante diagnosability.")
