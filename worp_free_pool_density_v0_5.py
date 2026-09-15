#!/usr/bin/env python3
"""WoRP Lab — FREE Pool Density V0.5

First clean test of the user's capture-volume insight.

At each Wookiee season/week snapshot:
1. Sleeper matchup rosters define OWNED players.
2. NFL WoRP universe minus OWNED defines the league's actual FREE pool.
3. Every FREE player's NEXT COMPLETE 4-WEEK WoRP is measured.
4. We describe the distribution/density of future WoRP available in that pool.

No player is selected with hindsight. No ex-ante signal is used yet. This stage
measures supply/density only. Identifiability is a later gate.

Wookiee is a behavioral reference case only. Product logic must later rerun the
same construction from each league's own Sleeper rosters/settings.
"""
import json, urllib.request
from pathlib import Path
import numpy as np
import pandas as pd

WORP=Path("wookiee_2023_2025_weekly_worp.csv")
LEAGUES={2023:"950220100039311360",2024:"1050961255520923648",2025:"1182581249532833792"}
POSITIONS=["QB","RB","WR","TE"]
HORIZON=4
# Descriptive probes, not semantic thresholds.
PROBES=[0.00,0.10,0.25,0.50,0.75]

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"WoRPLab/0.5"})
    with urllib.request.urlopen(req,timeout=90) as r:return json.loads(r.read().decode("utf-8"))

def owned(league_id,week):
    rows=get_json(f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}")
    return {str(p) for row in (rows or []) for p in (row.get("players") or [])}

def main():
    if not WORP.exists():raise FileNotFoundError(WORP)
    w=pd.read_csv(WORP)
    w["player_id"]=w.player_id.astype(str)
    w=w[w.position.isin(POSITIONS)&w.season.isin(LEAGUES)&w.week.between(1,18)].copy()
    w["weekly_worp"]=pd.to_numeric(w.weekly_worp,errors="coerce").fillna(0.0)

    # Complete NFL player-season identity universe from the WoRP source.
    ident=w[["season","player_id","player_name","position"]].drop_duplicates(["season","player_id"])
    outcome=w[["season","week","player_id","weekly_worp"]].drop_duplicates(["season","week","player_id"])

    rows=[]
    detail=[]
    for season,league_id in LEAGUES.items():
        for week in range(1,15): # weeks week+1 ... week+4 must fit through 18
            own=owned(league_id,week)
            base=ident[ident.season.eq(season)].copy()
            free=base[~base.player_id.isin(own)].copy()

            future=outcome[(outcome.season.eq(season))&outcome.week.between(week+1,week+HORIZON)]
            fw=future.groupby("player_id",as_index=False).weekly_worp.sum().rename(columns={"weekly_worp":"future4_worp"})
            free=free.merge(fw,on="player_id",how="left")
            free["future4_worp"]=free.future4_worp.fillna(0.0)
            free["season"]=season;free["snapshot_week"]=week
            detail.append(free)

            for pos in POSITIONS:
                g=free[free.position.eq(pos)]
                if g.empty:continue
                rec={"season":season,"snapshot_week":week,"position":pos,"free_pool_players":len(g),
                     "future4_mean":g.future4_worp.mean(),"future4_median":g.future4_worp.median(),
                     "future4_p75":g.future4_worp.quantile(.75),"future4_p90":g.future4_worp.quantile(.90),
                     "future4_p95":g.future4_worp.quantile(.95),"future4_max":g.future4_worp.max()}
                for q in PROBES:
                    n=int(g.future4_worp.ge(q).sum())
                    label=str(q).replace(".","p")
                    rec[f"n_ge_{label}"]=n
                    rec[f"share_ge_{label}"]=n/len(g)
                rows.append(rec)

    d=pd.concat(detail,ignore_index=True)
    s=pd.DataFrame(rows)
    summary=s.groupby("position",as_index=False).agg(
        snapshots=("snapshot_week","count"),
        median_free_pool=("free_pool_players","median"),
        median_future4_p75=("future4_p75","median"),
        median_future4_p90=("future4_p90","median"),
        median_future4_p95=("future4_p95","median"),
        median_n_ge_0p10=("n_ge_0p1","median"),
        median_n_ge_0p25=("n_ge_0p25","median"),
        median_n_ge_0p50=("n_ge_0p5","median"),
        median_n_ge_0p75=("n_ge_0p75","median"))

    d.to_csv("worp_free_pool_density_detail_v0_5.csv",index=False)
    s.to_csv("worp_free_pool_density_snapshot_v0_5.csv",index=False)
    summary.to_csv("worp_free_pool_density_summary_v0_5.csv",index=False)

    print("="*120);print("WORP FREE POOL DENSITY V0.5 — NEXT COMPLETE 4 WEEKS");print("="*120)
    print(summary.to_string(index=False))
    print("\nREADING RULES")
    print("- FREE = not on ANY Sleeper roster in that league at the snapshot.")
    print("- Counts measure number of available paths to future production, not our ability to identify the winner.")
    print("- .10/.25/.50/.75 are descriptive probes only; they are NOT roster cutlines.")
    print("- Next stage: compare this FREE distribution with rostered rank/band future4 WoRP on the SAME snapshots/horizon.")

if __name__=="__main__":main()
