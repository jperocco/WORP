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
print("WOOKIEE STARTED × BENCHED × FREE + VOLUME AUDIT V0.2.4")
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

# Actual weekly Sleeper state: STARTED / BENCHED / FREE.
# "STARTED" is observed lineup placement, NOT a retrospective claim that it was
# the correct/capturable decision.
owned={}
started={}
snapshot_audit=[]
for season,lid in LEAGUES.items():
    for week in range(1,19):
        rows=get_json(f"https://api.sleeper.app/v1/league/{lid}/matchups/{week}")
        owned_ids=set()
        starter_ids=set()
        roster_count=0
        for r in rows:
            roster_count += 1
            players={str(x) for x in (r.get("players") or []) if x is not None}
            starters={str(x) for x in (r.get("starters") or []) if x is not None and str(x)!="0"}
            owned_ids.update(players)
            starter_ids.update(starters)
        owned[(season,week)]=owned_ids
        started[(season,week)]=starter_ids
        snapshot_audit.append({
            "season":season,"week":week,"matchup_rows":roster_count,
            "owned_unique":len(owned_ids),"started_unique":len(starter_ids),
            "starters_not_owned":len(starter_ids-owned_ids)
        })

snap=pd.DataFrame(snapshot_audit)
bad_snap=snap[(snap["matchup_rows"]!=12)|(snap["starters_not_owned"]!=0)]
if len(bad_snap):
    print("\nFAIL: incoherent Sleeper lineup snapshots.")
    print(bad_snap.to_string(index=False))
    raise SystemExit(3)

def state_for(s,week,pid):
    key=(int(s),int(week))
    if pid in started[key]: return "STARTED"
    if pid in owned[key]: return "BENCHED"
    return "FREE"

m["roster_state"]=[
    state_for(s,week,pid)
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

print("\nSTARTED × BENCHED × FREE — POSITIVE WoRP + SAME-WEEK VOLUME")
print("-"*110)

# Classification coverage is deterministic for every WoRP row once snapshots are coherent.
assert m["roster_state"].isin(["STARTED","BENCHED","FREE"]).all()
print("Roster-state classification: 100.00%")

positive = m[m.weekly_worp > 0].copy()
states=["STARTED","BENCHED","FREE"]
positions=["QB","RB","WR","TE"]

rows=[]
for p in positions:
    ptotal=positive.loc[positive.position==p,"weekly_worp"].sum()
    for state in states:
        x=positive[(positive.position==p)&(positive.roster_state==state)].copy()
        rows.append({
            "position":p,
            "roster_state":state,
            "positive_player_weeks":len(x),
            "positive_worp":x.weekly_worp.sum(),
            "share_of_position_positive_worp":x.weekly_worp.sum()/ptotal if ptotal else 0,
            "median_positive_worp":x.weekly_worp.median() if len(x) else float("nan"),
            "p75_positive_worp":x.weekly_worp.quantile(.75) if len(x) else float("nan"),
            "median_volume":x.volume.median() if len(x) else float("nan"),
            "p75_volume":x.volume.quantile(.75) if len(x) else float("nan"),
        })
summary=pd.DataFrame(rows)
print(summary.to_string(index=False,formatters={
    "positive_worp":"{:.3f}".format,
    "share_of_position_positive_worp":"{:.1%}".format,
    "median_positive_worp":"{:.4f}".format,
    "p75_positive_worp":"{:.4f}".format,
    "median_volume":"{:.1f}".format,
    "p75_volume":"{:.1f}".format,
}))

print("\nYEAR-BY-YEAR SHARE OF POSITIVE WoRP")
yearly=(positive.groupby(["season","position","roster_state"],as_index=False)
        .agg(positive_player_weeks=("weekly_worp","size"),
             positive_worp=("weekly_worp","sum")))
den=(yearly.groupby(["season","position"])["positive_worp"]
     .transform("sum"))
yearly["share_of_position_positive_worp"]=yearly["positive_worp"]/den
print(yearly.to_string(index=False,formatters={
    "positive_worp":"{:.3f}".format,
    "share_of_position_positive_worp":"{:.1%}".format,
}))

# TE-specific TD-dependence guardrail: targets are deliberately sufficient here.
te=positive[positive.position=="TE"].copy()
te["zero_or_one_target"]=te.targets<=1
te["two_or_fewer_targets"]=te.targets<=2
te["td_scored"]=te.total_tds>0
te_rows=[]
for state in states:
    x=te[te.roster_state==state]
    total=x.weekly_worp.sum()
    te_rows.append({
        "roster_state":state,
        "positive_TE_player_weeks":len(x),
        "positive_TE_worp":total,
        "worp_share_targets_le_1":x.loc[x.targets<=1,"weekly_worp"].sum()/total if total else 0,
        "worp_share_targets_le_2":x.loc[x.targets<=2,"weekly_worp"].sum()/total if total else 0,
        "worp_share_with_TD":x.loc[x.total_tds>0,"weekly_worp"].sum()/total if total else 0,
        "median_targets":x.targets.median() if len(x) else float("nan"),
        "p75_targets":x.targets.quantile(.75) if len(x) else float("nan"),
    })
te_summary=pd.DataFrame(te_rows)
print("\nTE TARGET / TD GUARDRAIL")
print(te_summary.to_string(index=False,formatters={
    "positive_TE_worp":"{:.3f}".format,
    "worp_share_targets_le_1":"{:.1%}".format,
    "worp_share_targets_le_2":"{:.1%}".format,
    "worp_share_with_TD":"{:.1%}".format,
    "median_targets":"{:.1f}".format,
    "p75_targets":"{:.1f}".format,
}))

# Human-review cases: top realized positive WoRP by state and position.
case_cols=["season","week","player_id","player_name","position","roster_state",
           "fantasy_points","weekly_worp","volume","volume_metric","carries",
           "targets","receptions","pass_attempts","scrimmage_yards","pass_yards","total_tds"]
cases=[]
for p in positions:
    for state in states:
        cases.append(positive[(positive.position==p)&(positive.roster_state==state)]
                     .sort_values("weekly_worp",ascending=False).head(10)[case_cols])
cases=pd.concat(cases,ignore_index=True)

print("\nTOP 5 REALIZED WoRP CASES — EACH POSITION × STATE")
for p in positions:
    for state in states:
        x=cases[(cases.position==p)&(cases.roster_state==state)].head(5)
        print(f"\n{p} — {state}")
        if x.empty:
            print("(none)")
        else:
            print(x[["season","week","player_name","fantasy_points","weekly_worp",
                     "volume","total_tds"]].to_string(index=False))

summary.to_csv("wookiee_started_benched_free_summary_v0_2_4.csv",index=False)
yearly.to_csv("wookiee_started_benched_free_yearly_v0_2_4.csv",index=False)
te_summary.to_csv("wookiee_te_target_td_guardrail_v0_2_4.csv",index=False)
cases.to_csv("wookiee_started_benched_free_human_cases_v0_2_4.csv",index=False)
m.to_csv("wookiee_started_benched_free_detail_v0_2_4.csv",index=False)

print("\nPASS: STARTED / BENCHED / FREE classification complete and coherent.")
print("INTERPRETATION STOP: this describes where realized value occurred.")
print("It does NOT label BENCHED/FREE value as ex-ante capturable and does NOT judge manager decisions.")


# ======================================================================================
# V0.2.5 — ABSOLUTE VOLUME DECOMPOSITION FOR BENCHED / FREE
# Descriptive only. No Captura inference.
# ======================================================================================
print("\n" + "="*110)
print("V0.2.5 — BENCHED / FREE ABSOLUTE VOLUME DECOMPOSITION")
print("="*110)

# Absolute, interpretable workload bands. These are descriptive bins, NOT thresholds
# of startability/capturability.
def volume_band(row):
    p=row["position"]
    v=row["volume"]
    if p=="QB":
        if v < 25: return "LOW <25"
        if v < 35: return "MID 25-34"
        return "HIGH 35+"
    if p=="RB":
        if v < 8: return "LOW <8"
        if v < 15: return "MID 8-14"
        return "HIGH 15+"
    # WR / TE targets
    if v < 4: return "LOW <4"
    if v < 7: return "MID 4-6"
    return "HIGH 7+"

bf=positive[positive.roster_state.isin(["BENCHED","FREE"])].copy()
bf["volume_band"]=bf.apply(volume_band,axis=1)

band_order=["LOW <25","MID 25-34","HIGH 35+",
            "LOW <8","MID 8-14","HIGH 15+",
            "LOW <4","MID 4-6","HIGH 7+"]

band_rows=[]
for p in positions:
    for state in ["BENCHED","FREE"]:
        x=bf[(bf.position==p)&(bf.roster_state==state)]
        total=x.weekly_worp.sum()
        for band in x.volume_band.unique():
            z=x[x.volume_band==band]
            band_rows.append({
                "position":p,"roster_state":state,"volume_band":band,
                "positive_player_weeks":len(z),
                "positive_worp":z.weekly_worp.sum(),
                "share_of_state_positive_worp":z.weekly_worp.sum()/total if total else 0,
                "median_weekly_worp":z.weekly_worp.median() if len(z) else float("nan"),
                "median_fantasy_points":z.fantasy_points.median() if len(z) else float("nan"),
                "td_worp_share":z.loc[z.total_tds>0,"weekly_worp"].sum()/z.weekly_worp.sum()
                    if z.weekly_worp.sum() else 0,
            })

bands=pd.DataFrame(band_rows)

for p in positions:
    print(f"\n{p}")
    x=bands[bands.position==p]
    print(x.to_string(index=False,formatters={
        "positive_worp":"{:.3f}".format,
        "share_of_state_positive_worp":"{:.1%}".format,
        "median_weekly_worp":"{:.4f}".format,
        "median_fantasy_points":"{:.1f}".format,
        "td_worp_share":"{:.1%}".format,
    }))

# Compact economic view: how much BENCHED/FREE WoRP survives in the HIGH workload band?
survival=[]
for p in positions:
    for state in ["BENCHED","FREE"]:
        x=bf[(bf.position==p)&(bf.roster_state==state)]
        if p=="QB": high=x.volume>=35
        elif p=="RB": high=x.volume>=15
        else: high=x.volume>=7
        total=x.weekly_worp.sum()
        high_w=x.loc[high,"weekly_worp"].sum()
        survival.append({
            "position":p,"roster_state":state,
            "total_positive_worp":total,
            "high_volume_positive_worp":high_w,
            "high_volume_worp_share":high_w/total if total else 0,
            "high_volume_player_weeks":int(high.sum()),
            "all_positive_player_weeks":len(x),
        })

surv=pd.DataFrame(survival)
print("\nHIGH-VOLUME SURVIVAL — DESCRIPTIVE")
print(surv.to_string(index=False,formatters={
    "total_positive_worp":"{:.3f}".format,
    "high_volume_positive_worp":"{:.3f}".format,
    "high_volume_worp_share":"{:.1%}".format,
}))

# Year stability for the high-volume share.
yr=[]
for season in sorted(bf.season.unique()):
    for p in positions:
        for state in ["BENCHED","FREE"]:
            x=bf[(bf.season==season)&(bf.position==p)&(bf.roster_state==state)]
            if x.empty: continue
            if p=="QB": high=x.volume>=35
            elif p=="RB": high=x.volume>=15
            else: high=x.volume>=7
            total=x.weekly_worp.sum()
            yr.append({
                "season":season,"position":p,"roster_state":state,
                "positive_worp":total,
                "high_volume_positive_worp":x.loc[high,"weekly_worp"].sum(),
                "high_volume_worp_share":x.loc[high,"weekly_worp"].sum()/total if total else 0,
            })
yr=pd.DataFrame(yr)

print("\nYEAR-BY-YEAR HIGH-VOLUME SHARE")
print(yr.to_string(index=False,formatters={
    "positive_worp":"{:.3f}".format,
    "high_volume_positive_worp":"{:.3f}".format,
    "high_volume_worp_share":"{:.1%}".format,
}))

bands.to_csv("wookiee_benched_free_absolute_volume_bands_v0_2_5.csv",index=False)
surv.to_csv("wookiee_benched_free_high_volume_survival_v0_2_5.csv",index=False)
yr.to_csv("wookiee_benched_free_high_volume_yearly_v0_2_5.csv",index=False)

print("\nPASS: absolute-volume decomposition completed.")
print("INTERPRETATION STOP: HIGH volume means workload-backed in the same week only.")
print("It does NOT mean ex-ante identifiable, capturable, startable, or a good manager decision.")
