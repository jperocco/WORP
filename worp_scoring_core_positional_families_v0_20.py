#!/usr/bin/env python3
"""WoRP Lab V0.20 — league-native positional Scoring-family experiment.

Question
--------
Given the V0.18/V0.19 league-native TOTAL Scoring-core range, how can that
capacity be distributed across QB/RB/WR/TE without forcing an exact quota?

This is an empirical extension of V0.16. For each supported Sleeper
league-season it:
1) recomputes league-native weekly WoRP from that league's own scoring/settings;
2) reconstructs real roster-week ownership;
3) tests every feasible positional retention family at the V0.18 low/high total;
4) compares each family to the FULL-roster Oracle on the SAME common support;
5) aggregates family loss within exact structural formats with equal
   league-season weighting;
6) reports a broad efficient family set rather than one exact tuple.

Important: retention uses realized season positional WoRP rank, so this remains
an ex-post, hindsight-favorable structural upper-bound test. It does not claim
ex-ante draft/waiver identifiability.
"""
from __future__ import annotations
import argparse, json, urllib.request
from itertools import product
from pathlib import Path
import pandas as pd
from sleeper_native_loader import fetch_player_map, load_sleeper_player_weeks, validate_weekly_contract
from worp_engine import LeagueSettings, calculate_season_worp

API='https://api.sleeper.app/v1'
OBS=Path('worp_multileague_validation_observations_v0_15.csv')
RANGES=Path('worp_scoring_core_range_candidates_v0_18.csv')
OUT_DETAIL=Path('worp_scoring_core_positional_family_detail_v0_20.csv')
OUT_FORMAT=Path('worp_scoring_core_positional_family_formats_v0_20.csv')
OUT_ENVELOPE=Path('worp_scoring_core_positional_family_envelopes_v0_20.csv')
POS=('QB','RB','WR','TE')

def get(path):
    req=urllib.request.Request(API+path,headers={'User-Agent':'WoRP-Lab-PosFamilies/0.20'})
    with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)

def counts(xs):
    o={}
    for x in xs or []:o[x]=o.get(x,0)+1
    return o

def settings_from_league(lg):
    c=counts(lg.get('roster_positions') or []); sc=lg.get('scoring_settings') or {}
    return LeagueSettings(teams=int(lg.get('total_rosters') or 0),qb=int(c.get('QB',0)),rb=int(c.get('RB',0)),wr=int(c.get('WR',0)),te=int(c.get('TE',0)),flex=int(c.get('FLEX',0)+c.get('REC_FLEX',0)),superflex=int(c.get('SUPER_FLEX',0)+c.get('SUPERFLEX',0)+c.get('OP',0)),ppr=float(sc.get('rec',0) or 0),te_premium=float(sc.get('bonus_rec_te',0) or 0))

def lineups(s):
    fixed={'QB':s.qb,'RB':s.rb,'WR':s.wr,'TE':s.te}; seen=set()
    for fr in range(s.flex+1):
      for fw in range(s.flex-fr+1):
        ft=s.flex-fr-fw
        for sq in range(s.superflex+1):
          for sr in range(s.superflex-sq+1):
            for sw in range(s.superflex-sq-sr+1):
              st=s.superflex-sq-sr-sw
              seen.add((fixed['QB']+sq,fixed['RB']+fr+sr,fixed['WR']+fw+sw,fixed['TE']+ft+st))
    return [dict(zip(POS,x)) for x in sorted(seen)]

def oracle(pools,lcs):
    best=None
    for c in lcs:
        if any(len(pools[p])<c[p] for p in POS):continue
        v=sum(sum(pools[p][:c[p]]) for p in POS)
        best=v if best is None or v>best else best
    return best

def families(total,lcs,ceilings):
    floors={p:min(c[p] for c in lcs) for p in POS}; out=[]
    for vals in product(*[range(floors[p],ceilings[p]+1) for p in POS]):
        if sum(vals)!=total:continue
        c=dict(zip(POS,vals))
        if any(all(c[p]>=lc[p] for p in POS) for lc in lcs):out.append(c)
    return out

def native_weekly(lg,season,pmap,n_sims):
    s=settings_from_league(lg)
    w,_=load_sleeper_player_weeks([season],lg.get('scoring_settings') or {},player_map=pmap);validate_weekly_contract(w)
    weekly,ranks=calculate_season_worp(w,s,replacement_band=6,n_sims=n_sims,seed=7)
    return weekly.merge(ranks[['season','player_id','position','pos_rank']],on=['season','player_id','position'],how='left'),s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--max-leagues',type=int,default=0);ap.add_argument('--n-sims',type=int,default=2500);a=ap.parse_args()
    if not OBS.exists() or not RANGES.exists():raise SystemExit('Missing V0.15 observations or V0.18 ranges.')
    obs=pd.read_csv(OBS,dtype={'league_id':str,'lineage_root':str}); rr=pd.read_csv(RANGES)
    obs=obs[obs.structurally_supported.astype(str).str.lower().isin(['true','1'])].copy();obs=obs[pd.to_numeric(obs.season,errors='coerce').between(2023,2025)]
    obs=obs[obs.format_key.isin(set(rr[rr.status.eq('observed_range_candidate')].format_key))].sort_values(['format_key','season','league_id'])
    if a.max_leagues>0:obs=obs.head(a.max_leagues)
    print('V0.20 POSITIONAL SCORING FAMILIES',flush=True);print(f'League-seasons: {len(obs)} | formats: {obs.format_key.nunique()} | n_sims={a.n_sims}',flush=True)
    pmap=fetch_player_map(); detail=[];fails=[]
    for ix,r in enumerate(obs.itertuples(index=False),1):
      try:
        lg=get(f'/league/{r.league_id}'); season=int(r.season); weekly,s=native_weekly(lg,season,pmap,a.n_sims); lcs=lineups(s)
        rg=rr[rr.format_key.eq(r.format_key)].iloc[0]; totals=sorted(set([int(rg.scoring_core_low),int(rg.scoring_core_high)]))
        active=sum(x not in ('IR','TAXI') for x in (lg.get('roster_positions') or [])); totals=[t for t in totals if t<=active]
        lookup={(int(x.week),str(x.player_id)):(x.position,float(x.weekly_worp),float(x.pos_rank) if pd.notna(x.pos_rank) else 9999.) for x in weekly[['week','player_id','position','weekly_worp','pos_rank']].itertuples(index=False)}
        ceilings={p:max(max(c[p] for c in lcs),min(active,12)) for p in POS}; fam={t:families(t,lcs,ceilings) for t in totals}
        acc={(t,tuple(c[p] for p in POS)):[] for t in totals for c in fam[t]}; common=0
        for week in range(1,19):
          for snap in get(f'/league/{r.league_id}/matchups/{week}') or []:
            ranked={p:[] for p in POS}
            for pid in [str(x) for x in (snap.get('players') or [])]:
              x=lookup.get((week,pid))
              if x and x[0] in POS:ranked[x[0]].append((x[2],-x[1],x[1]))
            for p in POS:ranked[p].sort()
            fullp={p:sorted([x[2] for x in ranked[p]],reverse=True) for p in POS}; full=oracle(fullp,lcs)
            if full is None:continue
            vals={}; feasible_all=True
            for t in totals:
              for c in fam[t]:
                key=(t,tuple(c[p] for p in POS)); pools={p:sorted([x[2] for x in ranked[p][:c[p]]],reverse=True) for p in POS}; v=oracle(pools,lcs)
                vals[key]=None if v is None else max(0.,full-v)
              # Common support requires at least one feasible family for each target total; individual families retain their own legal support below.
              if not any(vals[(t,tuple(c[p] for p in POS))] is not None for c in fam[t]):feasible_all=False
            if not feasible_all:continue
            common+=1
            for key,v in vals.items():
              if v is not None:acc[key].append(v)
        if not common:raise RuntimeError('no common roster-week support')
        for (t,key),vals in acc.items():
          if len(vals)!=common:continue # equal denominator across reported families
          q,rbc,wrc,te=key
          detail.append({'league_id':r.league_id,'season':season,'lineage_root':r.lineage_root,'format_key':r.format_key,'scoring_total':t,'surplus_over_starters':t-int(rg.starters),'QB':q,'RB':rbc,'WR':wrc,'TE':te,'common_roster_weeks':common,'mean_lost':sum(vals)/len(vals),'median_lost':pd.Series(vals).median(),'rate_050':sum(v>=.50 for v in vals)/len(vals)})
        print(f'[{ix}/{len(obs)}] PASS {season} | {lg.get("name")} | common={common}',flush=True)
      except Exception as e:
        fails.append((r.league_id,r.season,repr(e)));print(f'[{ix}/{len(obs)}] FAIL {r.league_id}: {e}',flush=True)
    d=pd.DataFrame(detail)
    if d.empty:raise SystemExit('FAIL: no positional-family observations.')
    d.to_csv(OUT_DETAIL,index=False)
    f=(d.groupby(['format_key','scoring_total','surplus_over_starters','QB','RB','WR','TE'],as_index=False).agg(league_seasons=('league_id','size'),lineages=('lineage_root','nunique'),mean_lost=('mean_lost','mean'),median_lost=('median_lost','median'),rate_050=('rate_050','mean')))
    # Family regret is relative to best observed family at SAME format + total, not a universal threshold.
    f['best_mean_lost']=f.groupby(['format_key','scoring_total']).mean_lost.transform('min');f['family_regret']=f.mean_lost-f.best_mean_lost
    f.to_csv(OUT_FORMAT,index=False)
    # Transparent efficient envelope: retain families in the best quartile of regret within each exact format/total.
    # Quartile is a descriptive shortlist, NOT product cutoff. We report positional min/max across it.
    env=[]
    for (fmt,t),g in f.groupby(['format_key','scoring_total']):
      cut=g.family_regret.quantile(.25); e=g[g.family_regret<=cut+1e-12]
      row={'format_key':fmt,'scoring_total':t,'surplus_over_starters':int(g.surplus_over_starters.iloc[0]),'league_seasons':int(g.league_seasons.max()),'families_tested':len(g),'efficient_families':len(e),'best_mean_lost':float(g.mean_lost.min()),'q25_regret_cut_descriptive':float(cut)}
      for p in POS:row[p+'_low']=int(e[p].min());row[p+'_high']=int(e[p].max())
      env.append(row)
    e=pd.DataFrame(env).sort_values(['format_key','scoring_total']);e.to_csv(OUT_ENVELOPE,index=False)
    print('\nPOSITIONAL FAMILY ENVELOPES — descriptive best-quartile shortlist, NOT exact quotas')
    print(e.to_string(index=False))
    print(f'\nPASS league-seasons: {d[["league_id","season"]].drop_duplicates().shape[0]} | failures: {len(fails)}')
    print('Created:');print(f'- {OUT_DETAIL}\n- {OUT_FORMAT}\n- {OUT_ENVELOPE}')
    print('\nREADING CONTRACT')
    print('- Total Scoring capacity comes from the already-frozen V0.18/V0.19 league-native range; V0.20 studies positional distribution only.')
    print('- FLEX/SF are handled by legal lineup compositions; positional ranges must NOT be summed independently.')
    print('- Family regret is relative to the best family at the same exact format and Scoring total.')
    print('- The best-quartile envelope is a descriptive research shortlist, not a semantic threshold or final product rule.')
    print('- If many distinct families are decision-equivalent, preserve flexibility; do not manufacture exact QB/RB/WR/TE quotas.')
    print('- If one position repeatedly excludes alternatives by material WoRP loss across supported formats, that is a candidate construction constraint for the next gate.')
if __name__=='__main__':main()
