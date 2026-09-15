#!/usr/bin/env python3
"""WoRP Lab — Multi-League Empirical Roster-Depth Capture V0.16.

League-native extension of the Wookiee V0.12/V0.12.2 experiment.

For each supported Sleeper league-season discovered by V0.15:
1) fetch exact league scoring + slot structure;
2) compute exact Sleeper-native weekly fantasy points;
3) compute league-native weekly WoRP with the WoRP engine;
4) reconstruct real roster-week ownership from Sleeper matchups;
5) compare whole-roster Scoring-core sizes on COMMON SUPPORT.

This is an ex-post, hindsight-favorable structural test. Retention uses realized
season positional WoRP rank, deliberately favoring leaner Scoring cores. It does
NOT claim an ex-ante optimal roster strategy and does NOT import Wookiee's 13–15
range into other formats.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from functools import lru_cache
from itertools import product
from pathlib import Path

import pandas as pd

from sleeper_native_loader import fetch_player_map, load_sleeper_player_weeks, validate_weekly_contract
from worp_engine import LeagueSettings, calculate_season_worp

API = 'https://api.sleeper.app/v1'
INFILE = Path('worp_multileague_validation_observations_v0_15.csv')
OUT_DETAIL = Path('worp_multileague_roster_depth_detail_v0_16.csv')
OUT_LEAGUES = Path('worp_multileague_roster_depth_leagues_v0_16.csv')
OUT_FORMATS = Path('worp_multileague_roster_depth_formats_v0_16.csv')
POS = ('QB','RB','WR','TE')
PROBES = (0.25,0.50,0.75)


def get(path):
    req=urllib.request.Request(API+path,headers={'User-Agent':'WoRP-Lab-MultiLeague/0.16'})
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.load(r)


def counts(roster_positions):
    out={}
    for p in roster_positions or []: out[p]=out.get(p,0)+1
    return out


def settings_from_league(lg):
    c=counts(lg.get('roster_positions') or [])
    sc=lg.get('scoring_settings') or {}
    return LeagueSettings(
        teams=int(lg.get('total_rosters') or 0),
        qb=int(c.get('QB',0)), rb=int(c.get('RB',0)), wr=int(c.get('WR',0)), te=int(c.get('TE',0)),
        flex=int(c.get('FLEX',0)+c.get('REC_FLEX',0)),
        superflex=int(c.get('SUPER_FLEX',0)+c.get('SUPERFLEX',0)+c.get('OP',0)),
        ppr=float(sc.get('rec',0.0) or 0.0),
        te_premium=float(sc.get('bonus_rec_te',0.0) or 0.0),
    )


def starter_count(lg):
    return sum(p not in ('BN','IR','TAXI') for p in (lg.get('roster_positions') or []))


def lineup_compositions(settings):
    """All positional count vectors that can fill the league's aggregate slot types."""
    fixed={'QB':settings.qb,'RB':settings.rb,'WR':settings.wr,'TE':settings.te}
    flex=settings.flex; sf=settings.superflex
    seen=set()
    # Allocate FLEX among R/W/T and SF among Q/R/W/T. Small integer space.
    for fr in range(flex+1):
      for fw in range(flex-fr+1):
        ft=flex-fr-fw
        for sq in range(sf+1):
          for sr in range(sf-sq+1):
            for sw in range(sf-sq-sr+1):
              st=sf-sq-sr-sw
              c=(fixed['QB']+sq, fixed['RB']+fr+sr, fixed['WR']+fw+sw, fixed['TE']+ft+st)
              seen.add(c)
    return [dict(zip(POS,x)) for x in sorted(seen)]


def oracle(pools, lineups):
    best=None
    for c in lineups:
        if any(len(pools[p])<c[p] for p in POS): continue
        val=sum(sum(pools[p][:c[p]]) for p in POS)
        if best is None or val>best: best=val
    return best


def feasible_families(total, lineups, ceilings):
    floors={p:min(c[p] for c in lineups) for p in POS}
    fam=[]
    ranges=[range(floors[p],ceilings[p]+1) for p in POS]
    for vals in product(*ranges):
        if sum(vals)!=total: continue
        c=dict(zip(POS,vals))
        if any(all(c[p]>=lc[p] for p in POS) for lc in lineups): fam.append(c)
    return fam


def league_native_weekly(lg, season, player_map, n_sims):
    settings=settings_from_league(lg)
    all_weeks,_=load_sleeper_player_weeks([season],lg.get('scoring_settings') or {},player_map=player_map)
    validate_weekly_contract(all_weeks)
    weekly,ranks=calculate_season_worp(all_weeks,settings,replacement_band=6,n_sims=n_sims,seed=7)
    ranks=ranks[['season','player_id','position','pos_rank']]
    return weekly.merge(ranks,on=['season','player_id','position'],how='left'),settings


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--max-leagues',type=int,default=0,help='0 = all eligible league-seasons; use small N for smoke test')
    ap.add_argument('--n-sims',type=int,default=2500,help='Monte Carlo simulations per WoRP week; 2500 research default')
    ap.add_argument('--min-format-observations',type=int,default=3,help='Only empirical-format summaries with at least this many league-seasons')
    a=ap.parse_args()
    if not INFILE.exists(): raise SystemExit('Missing V0.15 observations CSV.')
    obs=pd.read_csv(INFILE,dtype={'league_id':str,'previous_league_id':str,'lineage_root':str})
    obs=obs[obs.structurally_supported.astype(str).str.lower().isin(['true','1'])].copy()
    # Current exact weekly Sleeper stats support is 2023 onward in this discovered sample.
    obs=obs[pd.to_numeric(obs.season,errors='coerce').between(2023,2025)].copy()
    # Start with formats that have replication/support. Rare formats remain future validation, not discarded evidence.
    support=obs.groupby('format_key').size()
    obs=obs[obs.format_key.map(support)>=a.min_format_observations].copy()
    obs=obs.sort_values(['format_key','season','league_id'])
    if a.max_leagues>0: obs=obs.head(a.max_leagues)
    print('V0.16 MULTI-LEAGUE EMPIRICAL ROSTER DEPTH',flush=True)
    print(f'Eligible league-seasons: {len(obs)} | formats: {obs.format_key.nunique()} | n_sims={a.n_sims}',flush=True)
    print('Common-support comparison is enforced WITHIN each league-season.',flush=True)
    player_map=fetch_player_map()
    detail=[]; failures=[]
    total_obs=len(obs)
    for ix,r in enumerate(obs.itertuples(index=False),start=1):
        season=int(r.season); lid=str(r.league_id)
        try:
            lg=get(f'/league/{lid}')
            if not lg: raise RuntimeError('league not found')
            if int(lg.get('season') or season)!=season: raise RuntimeError('league season mismatch')
            weekly,settings=league_native_weekly(lg,season,player_map,a.n_sims)
            lineups=lineup_compositions(settings)
            start_n=starter_count(lg)
            # Candidate Scoring core: starters through +6, bounded by active roster capacity.
            active=sum(p not in ('IR','TAXI') for p in (lg.get('roster_positions') or []))
            totals=list(range(start_n,min(active,start_n+6)+1))
            lookup={(int(x.week),str(x.player_id)):(x.position,float(x.weekly_worp),float(x.pos_rank) if pd.notna(x.pos_rank) else 9999.)
                    for x in weekly[['week','player_id','position','weekly_worp','pos_rank']].itertuples(index=False)}
            # Family ceilings from players actually owned in this league-season, not universal raw-rank constants.
            ceilings={p:max(max(c[p] for c in lineups), min(active, 12)) for p in POS}
            fam={t:feasible_families(t,lineups,ceilings) for t in totals}
            rw=[]
            for week in range(1,19):
                snaps=get(f'/league/{lid}/matchups/{week}') or []
                for snap in snaps:
                    rid=snap.get('roster_id'); ids=[str(x) for x in (snap.get('players') or [])]
                    ranked={p:[] for p in POS}
                    for pid in ids:
                        x=lookup.get((week,pid))
                        if not x: continue
                        p,ww,pr=x
                        if p in POS: ranked[p].append((pr,-ww,ww))
                    for p in POS: ranked[p].sort()
                    fullp={p:sorted([x[2] for x in ranked[p]],reverse=True) for p in POS}
                    full=oracle(fullp,lineups)
                    if full is None: continue
                    row={'week':week,'roster_id':rid,'full':full,'lost':{}}
                    for t in totals:
                        best=None
                        for c in fam[t]:
                            pools={p:sorted([x[2] for x in ranked[p][:c[p]]],reverse=True) for p in POS}
                            val=oracle(pools,lineups)
                            if val is None: continue
                            lost=max(0.,full-val)
                            if best is None or lost<best: best=lost
                        row['lost'][t]=best
                    rw.append(row)
            # Equal denominator: retain only roster-weeks feasible for EVERY candidate total.
            common=[x for x in rw if all(x['lost'].get(t) is not None for t in totals)]
            if not common: raise RuntimeError('no common-support roster-weeks')
            for t in totals:
                vals=[x['lost'][t] for x in common]
                rec={'league_id':lid,'league_name':lg.get('name'),'season':season,'format_key':r.format_key,
                     'lineage_root':r.lineage_root,'teams':settings.teams,'starters':start_n,'active_roster_size':active,
                     'scoring_total':t,'surplus_over_starters':t-start_n,'common_roster_weeks':len(vals),
                     'mean_lost':sum(vals)/len(vals),'median_lost':pd.Series(vals).median()}
                for q in PROBES: rec[f'rate_{int(q*100):03d}']=sum(v>=q for v in vals)/len(vals)
                detail.append(rec)
            print(f'[{ix}/{total_obs}] PASS {season} | {lg.get("name")} | {r.format_key} | common={len(common)}',flush=True)
        except Exception as e:
            failures.append({'league_id':lid,'season':season,'format_key':r.format_key,'error':repr(e)})
            print(f'[{ix}/{total_obs}] FAIL {season} {lid}: {e}',flush=True)
    d=pd.DataFrame(detail)
    if d.empty: raise SystemExit('FAIL: no empirical observations produced.')
    d.to_csv(OUT_DETAIL,index=False)
    # League-season surface: already one row per scoring total on equal within-league support.
    d.to_csv(OUT_LEAGUES,index=False)
    # Format aggregation gives each league-season equal weight, avoiding large-league/week domination.
    f=(d.groupby(['format_key','starters','surplus_over_starters'],as_index=False)
       .agg(league_seasons=('league_id','size'),lineages=('lineage_root','nunique'),mean_lost=('mean_lost','mean'),
            median_lost=('median_lost','median'),rate_025=('rate_025','mean'),rate_050=('rate_050','mean'),rate_075=('rate_075','mean'))
       .sort_values(['format_key','surplus_over_starters']))
    f.to_csv(OUT_FORMATS,index=False)
    if failures: pd.DataFrame(failures).to_csv('worp_multileague_roster_depth_failures_v0_16.csv',index=False)
    print('\nFORMAT SURFACE — common support within each league-season; equal league-season weighting')
    print(f.round(4).to_string(index=False))
    print(f'\nPASS league-seasons: {d[["league_id","season"]].drop_duplicates().shape[0]} | failures: {len(failures)}')
    print('Created:')
    print(f'- {OUT_DETAIL}\n- {OUT_LEAGUES}\n- {OUT_FORMATS}')
    if failures: print('- worp_multileague_roster_depth_failures_v0_16.csv')
    print('\nREADING CONTRACT')
    print('- League-native scoring and WoRP are recomputed from each Sleeper league settings object.')
    print('- Scoring totals are expressed as surplus over that league\'s own starting-lineup size.')
    print('- Retention by season pos_rank is hindsight-favorable to lean cores: this is an upper-bound structural test.')
    print('- Comparisons use common roster-week support within league-season; formats weight league-seasons equally.')
    print('- Wookiee 13–15 is NOT imposed. Look for format-specific broad elbows/ranges and coherent adaptation.')
    print('- .25/.50/.75 are sensitivity probes only. No universal loss-rate threshold or exact optimum is asserted.')

if __name__=='__main__': main()
