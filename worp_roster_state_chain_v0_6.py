#!/usr/bin/env python3
"""WoRP Lab — Roster State Chain V0.6

Tests the corrected roster-construction mechanism:
LINEUP <- SCORING BENCH <- NON-SCORING ROSTER <- FREE NON-SCORING.

The FREE player is NOT required to produce WoRP. This audit asks whether a
manager's roster already contains positive-WoRP bench production that can move
into the lineup, while FREE replenishes the Non-Scoring tail.

State definitions are empirical weekly states:
STARTED = in Sleeper starters.
BENCHED_SCORING = rostered, not started, weekly WoRP > 0.
ROSTERED_NON_SCORING = rostered, not started, weekly WoRP <= 0.
FREE = not on any league roster. FREE is measured as supply only, not scored.

This is Wookiee behavioral research, not universal product logic.
"""
import json, urllib.request
from pathlib import Path
import pandas as pd

WORP=Path("wookiee_2023_2025_weekly_worp.csv")
LEAGUES={2023:"950220100039311360",2024:"1050961255520923648",2025:"1182581249532833792"}
POSITIONS=["QB","RB","WR","TE"]

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"WoRPLab/0.6"})
    with urllib.request.urlopen(req,timeout=90) as r:return json.loads(r.read().decode("utf-8"))

def snapshot(league_id,week):
    rows=get_json(f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}") or []
    out=[]
    for r in rows:
        rid=r.get("roster_id")
        starters={str(x) for x in (r.get("starters") or []) if x is not None and str(x)!="0"}
        players={str(x) for x in (r.get("players") or []) if x is not None}
        for p in players:
            out.append({"roster_id":rid,"player_id":p,"started":p in starters})
    return pd.DataFrame(out)

def main():
    if not WORP.exists():raise FileNotFoundError(WORP)
    w=pd.read_csv(WORP);w["player_id"]=w.player_id.astype(str)
    w=w[w.season.isin(LEAGUES)&w.position.isin(POSITIONS)&w.week.between(1,18)].copy()
    w["weekly_worp"]=pd.to_numeric(w.weekly_worp,errors="coerce").fillna(0.0)
    ident=w[["season","player_id","player_name","position"]].drop_duplicates(["season","player_id"])
    rows=[]
    for season,lid in LEAGUES.items():
        for week in range(1,19):
            snap=snapshot(lid,week)
            if snap.empty:continue
            ww=w[(w.season==season)&(w.week==week)][["player_id","player_name","position","weekly_worp"]]
            z=snap.merge(ww,on="player_id",how="left")
            z["weekly_worp"]=z.weekly_worp.fillna(0.0)
            z["position"]=z.position.fillna("UNKNOWN")
            z=z[z.position.isin(POSITIONS)].copy()
            z["state"]="ROSTERED_NON_SCORING"
            z.loc[z.started,"state"]="STARTED"
            z.loc[(~z.started)&z.weekly_worp.gt(0),"state"]="BENCHED_SCORING"

            owned=set(snap.player_id)
            free=ident[(ident.season==season)&(~ident.player_id.isin(owned))]
            free_counts=free.groupby("position").size().to_dict()

            for (rid,pos),g in z.groupby(["roster_id","position"]):
                bs=g[g.state.eq("BENCHED_SCORING")]
                ns=g[g.state.eq("ROSTERED_NON_SCORING")]
                st=g[g.state.eq("STARTED")]
                rows.append({"season":season,"week":week,"roster_id":rid,"position":pos,
                    "started_n":len(st),"started_positive_worp":st.loc[st.weekly_worp.gt(0),"weekly_worp"].sum(),
                    "benched_scoring_n":len(bs),"benched_scoring_worp":bs.weekly_worp.sum(),
                    "rostered_non_scoring_n":len(ns),"free_pool_n":int(free_counts.get(pos,0)),
                    "has_scoring_bench":len(bs)>0})
    d=pd.DataFrame(rows)
    s=d.groupby("position",as_index=False).agg(
        roster_weeks=("roster_id","count"),
        share_roster_weeks_with_scoring_bench=("has_scoring_bench","mean"),
        median_benched_scoring_n=("benched_scoring_n","median"),
        mean_benched_scoring_n=("benched_scoring_n","mean"),
        median_benched_scoring_worp=("benched_scoring_worp","median"),
        mean_benched_scoring_worp=("benched_scoring_worp","mean"),
        median_rostered_non_scoring_n=("rostered_non_scoring_n","median"),
        median_free_pool_n=("free_pool_n","median"))
    d.to_csv("worp_roster_state_chain_detail_v0_6.csv",index=False)
    s.to_csv("worp_roster_state_chain_summary_v0_6.csv",index=False)
    print("="*115);print("WORP ROSTER STATE CHAIN V0.6");print("="*115)
    print(s.to_string(index=False))
    print("\nIMPORTANT: FREE WoRP is deliberately absent. FREE replenishes Non-Scoring; it is not required to score.")
    print("NEXT: measure actual week-to-week promotions BENCH->START and NON-SCORING->SCORING, then test whether roster depth absorbs lineup demand.")
if __name__=="__main__":main()
