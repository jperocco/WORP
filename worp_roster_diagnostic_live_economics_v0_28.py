#!/usr/bin/env python3
"""WoRP Lab V0.28 — live league-native player economics.

For READY 2026 Sleeper leagues from V0.27, compute current-season WoRP using the
exact league scoring/slot structure, attach the user's current roster, and show
where each rostered offensive player sits on that league's positional WoRP
curve.

Important: this does NOT yet force a Scoring/Non-Scoring label. The purpose is
to validate the live player-economics layer before applying the frozen roster
construction envelope. WoRP remains positional economics; no asset value.
"""
from __future__ import annotations
import argparse, json, urllib.request
from functools import lru_cache
from pathlib import Path
import pandas as pd
from sleeper_native_loader import fetch_player_map, load_sleeper_player_weeks, validate_weekly_contract
from worp_engine import LeagueSettings, calculate_season_worp

API='https://api.sleeper.app/v1'; SEASON=2026; USERNAME='jperocco'
IN=Path('worp_roster_diagnostic_live_preflight_v0_27.csv')
OUT=Path('worp_roster_diagnostic_live_economics_v0_28.csv')
OUT_SUM=Path('worp_roster_diagnostic_live_economics_summary_v0_28.csv')
POS=('QB','RB','WR','TE')

def get(path):
    req=urllib.request.Request(API+path,headers={'User-Agent':'WoRP-Lab-LiveDiagnostic/0.28'})
    with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
def counts(rp):
    o={}
    for p in rp or []:o[p]=o.get(p,0)+1
    return o
def settings(lg):
    c=counts(lg.get('roster_positions') or []); s=lg.get('scoring_settings') or {}
    return LeagueSettings(teams=int(lg.get('total_rosters') or 0),qb=int(c.get('QB',0)),rb=int(c.get('RB',0)),wr=int(c.get('WR',0)),te=int(c.get('TE',0)),flex=int(c.get('FLEX',0)+c.get('REC_FLEX',0)),superflex=int(c.get('SUPER_FLEX',0)+c.get('SUPERFLEX',0)+c.get('OP',0)),ppr=float(s.get('rec',0) or 0),te_premium=float(s.get('bonus_rec_te',0) or 0))
@lru_cache(maxsize=None)
def league(lid):return get('/league/'+str(lid))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--max-leagues',type=int,default=0); ap.add_argument('--n-sims',type=int,default=1500); a=ap.parse_args()
    if not IN.exists():raise SystemExit(f'Missing {IN}; run V0.27 first.')
    inv=pd.read_csv(IN,dtype={'league_id':str}); inv=inv[inv.status.eq('READY')].copy()
    if a.max_leagues:inv=inv.head(a.max_leagues)
    u=get('/user/'+USERNAME); uid=str(u['user_id']); pm=fetch_player_map()
    # Player fantasy points depend on scoring settings, not roster slots. Cache by
    # exact scoring JSON so repeated leagues sharing scoring avoid duplicate load.
    weekly_cache={}; rows=[]; failures=[]
    for i,r in inv.iterrows():
        lid=str(r.league_id)
        try:
            lg=league(lid); sc=lg.get('scoring_settings') or {}; sk=json.dumps(sc,sort_keys=True)
            if sk not in weekly_cache:
                w,_=load_sleeper_player_weeks([SEASON],sc,player_map=pm); validate_weekly_contract(w); weekly_cache[sk]=w
            w=weekly_cache[sk]; st=settings(lg)
            ww,ranks=calculate_season_worp(w,st,replacement_band=6,n_sims=a.n_sims,seed=7)
            # Current-season positional economics: season rank plus realized WoRP to date.
            agg=(ww[ww.position.isin(POS)].groupby(['player_id','player_name','position'],as_index=False)
                 .agg(weeks=('week','nunique'),season_worp=('worp','sum'),mean_weekly_worp=('worp','mean')))
            rr=ranks[['player_id','position','pos_rank']].drop_duplicates(['player_id','position'])
            agg=agg.merge(rr,on=['player_id','position'],how='left')
            rosters=get('/league/'+lid+'/rosters'); mine=next((x for x in rosters if str(x.get('owner_id'))==uid),None)
            if not mine:raise RuntimeError('user roster not found')
            ids=set(str(x) for x in (mine.get('players') or []))
            minecon=agg[agg.player_id.astype(str).isin(ids)].copy()
            for _,p in minecon.iterrows():
                rows.append({'league_id':lid,'league_name':r.league_name,'format_key':r.format_key,'player_id':str(p.player_id),'player_name':p.player_name,'position':p.position,'pos_rank':p.pos_rank,'weeks':p.weeks,'season_worp':p.season_worp,'mean_weekly_worp':p.mean_weekly_worp})
            print(f"[{len(rows):5d} player rows] {r.league_name}: roster offense with 2026 WoRP={len(minecon)}")
        except Exception as ex:
            failures.append({'league_id':lid,'league_name':r.league_name,'error':repr(ex)}); print('FAIL',r.league_name,repr(ex))
    o=pd.DataFrame(rows); o.to_csv(OUT,index=False)
    if not o.empty:
        s=(o.groupby(['league_id','league_name','format_key','position'],as_index=False).agg(rostered_players=('player_id','size'),best_pos_rank=('pos_rank','min'),worst_pos_rank=('pos_rank','max'),rostered_season_worp=('season_worp','sum')))
        s.to_csv(OUT_SUM,index=False)
    print('\nV0.28 LIVE LEAGUE-NATIVE PLAYER ECONOMICS')
    print(f'READY leagues attempted: {len(inv)} | successes: {len(inv)-len(failures)} | failures: {len(failures)} | rostered offensive player rows: {len(o)}')
    print(f'Created:\n- {OUT}\n- {OUT_SUM}')
    print('\nREADING CONTRACT')
    print('- Every player WoRP/rank is recomputed under that league exact 2026 scoring and slot economics.')
    print('- pos_rank is league-native current-season positional rank, not a universal dynasty rank.')
    print('- season_worp is realized 2026 WoRP to date; it is not asset value or a future projection.')
    print('- V0.28 deliberately does NOT force Scoring/Non-Scoring labels or buy/sell/drop actions.')
    print('- Next gate applies frozen Scoring-core/envelope logic only after live economics are verified.')
if __name__=='__main__':main()
