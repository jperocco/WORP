#!/usr/bin/env python3
"""WORP LAB — MARGINAL CAPTURABLE CURVE PREFLIGHT V0.4.1

Fixes V0.4 outcome leakage: temporal detail contains only positive-WoRP FREE
cases. It may diagnose timing among positive cases, but cannot gate the full
candidate denominator. Wookiee remains a behavioral preflight, not product logic.
"""
import pandas as pd
from pathlib import Path

RANKINGS=Path("wookiee_2023_2025_rankings_worp.csv")
FREE_SIGNAL=Path("wookiee_ex_ante_signal_denominator_detail_v0_1.csv")
TEMPORAL=Path("wookiee_free_capturability_temporal_detail_v0_2.csv")
POSITIONS=["QB","RB","WR","TE"]
RANK_WINDOWS=[(1,8),(9,16),(17,24),(25,32),(33,40),(41,50),(51,60),(61,72),(73,90),(91,120)]
SIGNAL_OK={"MID_PRIOR_USAGE","HIGH_PRIOR_USAGE"}

def pick_col(df,candidates):
    for c in candidates:
        if c in df.columns:return c
    raise KeyError(f"None of columns found: {candidates}; available={list(df.columns)}")

def main():
    for p in (RANKINGS,FREE_SIGNAL,TEMPORAL):
        if not p.exists():raise FileNotFoundError(p)
    r=pd.read_csv(RANKINGS); f=pd.read_csv(FREE_SIGNAL); t=pd.read_csv(TEMPORAL)
    for df in (r,f,t):
        if "player_id" in df.columns:df["player_id"]=df["player_id"].astype(str)
    rank_col=pick_col(r,["position_rank","pos_rank","rank"])
    season_worp_col=pick_col(r,["season_worp","total_worp","worp","weekly_worp"])

    # Full ex-ante denominator: observed FREE target-week players, successes + failures.
    x=f[f.prior_signal_band.isin(SIGNAL_OK)].copy()
    x["weekly_worp"]=pd.to_numeric(x.weekly_worp,errors="coerce").fillna(0.0)
    t["weekly_worp"]=pd.to_numeric(t.weekly_worp,errors="coerce").fillna(0.0)

    alt_rows=[]
    for (season,position),g in x.groupby(["season","position"]):
        weekly_best=g.groupby("week").weekly_worp.max()
        tp=t[(t.season==season)&(t.position==position)]
        tn=len(tp); tc=int(tp.capturability.eq("CAPTURABLE").sum()) if tn else 0
        alt_rows.append({"season":int(season),"position":position,
            "eligible_free_player_weeks":len(g),"eligible_free_unique_players":g.player_id.nunique(),
            "eligible_free_positive_cases":int(g.weekly_worp.gt(0).sum()),
            "eligible_free_positive_rate":g.weekly_worp.gt(0).mean(),
            "eligible_free_worp_per_exposure":g.weekly_worp.mean(),
            "optimistic_weekly_best_free_worp_mean":weekly_best.mean(),
            "optimistic_weekly_best_free_worp_median":weekly_best.median(),
            "weeks_with_eligible_free":weekly_best.size,
            "positive_free_temporal_cases":tn,"positive_free_temporal_capturable":tc,
            "positive_free_temporal_capturable_rate":tc/tn if tn else float("nan")})
    alt=pd.DataFrame(alt_rows)

    r[rank_col]=pd.to_numeric(r[rank_col],errors="coerce")
    r[season_worp_col]=pd.to_numeric(r[season_worp_col],errors="coerce")
    secured_rows=[]
    for (season,position),g in r[r.position.isin(POSITIONS)].groupby(["season","position"]):
        for lo,hi in RANK_WINDOWS:
            q=g[g[rank_col].between(lo,hi)]
            if q.empty:continue
            secured_rows.append({"season":int(season),"position":position,"rank_lo":lo,"rank_hi":hi,
                "secured_rank_band":f"{position}{lo}-{position}{hi}","secured_players":len(q),
                "secured_median_season_worp":q[season_worp_col].median(),
                "secured_mean_season_worp":q[season_worp_col].mean()})
    out=pd.DataFrame(secured_rows).merge(alt,on=["season","position"],how="left")
    out["preflight_only"]=True; out["delta_status"]="NOT_COMPUTED_UNITS_MISMATCH"
    summary=alt.groupby("position",as_index=False).agg(
        seasons=("season","nunique"),eligible_free_player_weeks=("eligible_free_player_weeks","sum"),
        median_unique_free_players=("eligible_free_unique_players","median"),
        median_positive_rate=("eligible_free_positive_rate","median"),
        median_worp_per_exposure=("eligible_free_worp_per_exposure","median"),
        median_optimistic_weekly_best=("optimistic_weekly_best_free_worp_mean","median"),
        median_weeks_with_eligible_free=("weeks_with_eligible_free","median"),
        median_positive_temporal_capturable_rate=("positive_free_temporal_capturable_rate","median"))
    out.to_csv("worp_marginal_capturable_curve_preflight_v0_4.csv",index=False)
    summary.to_csv("worp_marginal_capturable_curve_preflight_summary_v0_4.csv",index=False)
    print("="*108);print("MARGINAL CAPTURABLE CURVE PREFLIGHT V0.4.1 — OUTCOME LEAKAGE FIXED");print("="*108)
    print(summary.to_string(index=False))
    if summary.median_positive_rate.eq(1.0).all():
        print("\nSTOP: all positional median hit rates remain 100%; denominator still looks contaminated.");raise SystemExit(2)
    print("\nPASS: successes and failures coexist in the ex-ante FREE denominator.")
    print("Temporal audit is diagnostic only because its source universe is positive-WoRP cases.")
    print("GUARDRAIL: no marginal delta yet — secured and FREE sides remain on different horizons.")
    print("NEXT: normalize both sides to a common forward horizon, then estimate marginal WoRP.")
if __name__=="__main__":main()
