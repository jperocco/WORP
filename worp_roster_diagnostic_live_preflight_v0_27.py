#!/usr/bin/env python3
"""WoRP Lab V0.27 — live/current roster diagnostic preflight.

V0.26 validated the diagnostic grammar historically. V0.27 does NOT yet label
individual current players Scoring/Non-Scoring. It verifies that current Sleeper
leagues can be mapped exactly to frozen V0.24 construction evidence and that
current roster ownership can be fetched cleanly.

This is deliberately a plumbing gate: no Wookiee fallback, no universal format,
no asset value, no invented player cutline.
"""
import json, urllib.request
from pathlib import Path
import pandas as pd

USERNAME='jperocco'; SEASON='2026'
ENV=Path('worp_scoring_core_decision_equivalence_envelopes_v0_24.csv')
OUT=Path('worp_roster_diagnostic_live_preflight_v0_27.csv')
OFF={'QB','RB','WR','TE','FLEX','REC_FLEX','SUPER_FLEX','SUPERFLEX','OP'}

def get(url):
    with urllib.request.urlopen(url,timeout=30) as r: return json.load(r)
def fmt(l):
    rp=l.get('roster_positions') or []; teams=int(l.get('total_rosters') or 0)
    q=rp.count('QB'); rb=rp.count('RB'); wr=rp.count('WR'); te=rp.count('TE')
    flex=rp.count('FLEX')+rp.count('REC_FLEX'); sf=rp.count('SUPER_FLEX')+rp.count('SUPERFLEX')+rp.count('OP')
    start=sum(x in OFF for x in rp)
    s=l.get('scoring_settings') or {}
    # Match existing preflight convention: any material TE premium above base reception scoring.
    rec=float(s.get('rec',0) or 0); te_rec=float(s.get('bonus_rec_te',0) or 0)
    tep='TEP' if te_rec>0 else 'noTEP'
    mode='SF' if sf>0 else '1QB'
    return f'{teams}T|{mode}|Start{start}|QB{q}|RB{rb}|WR{wr}|TE{te}|FLEX{flex}|SFLEX{sf}|{tep}'
def main():
    if not ENV.exists(): raise SystemExit(f'Missing {ENV}')
    e=pd.read_csv(ENV); supported=set(e.format_key.unique())
    u=get(f'https://api.sleeper.app/v1/user/{USERNAME}')
    leagues=get(f"https://api.sleeper.app/v1/user/{u['user_id']}/leagues/nfl/{SEASON}")
    rows=[]
    for l in leagues:
        f=fmt(l); lid=str(l['league_id'])
        try:
            rosters=get(f'https://api.sleeper.app/v1/league/{lid}/rosters')
            my=[r for r in rosters if str(r.get('owner_id'))==str(u['user_id'])]
            myr=my[0] if my else None
            roster_n=len((myr or {}).get('players') or [])
            support='DIRECT_EXACT_FORMAT' if f in supported else 'UNSUPPORTED_NO_AUTOMATIC_DIAGNOSTIC'
            status='READY' if support=='DIRECT_EXACT_FORMAT' and myr else ('NO_USER_ROSTER' if not myr else support)
        except Exception as ex:
            roster_n=0; support='FETCH_ERROR'; status='FETCH_ERROR'
        totals=sorted(e.loc[e.format_key.eq(f),'scoring_total'].astype(int).unique().tolist()) if f in supported else []
        rows.append({'league_id':lid,'league_name':l.get('name',''),'format_key':f,'diagnostic_support':support,'status':status,'current_roster_players':roster_n,'supported_scoring_totals':','.join(map(str,totals))})
    o=pd.DataFrame(rows).sort_values(['status','league_name']); o.to_csv(OUT,index=False)
    print('V0.27 LIVE ROSTER DIAGNOSTIC PREFLIGHT')
    print(f'2026 leagues: {len(o)} | READY exact-format: {(o.status=="READY").sum()} | unsupported: {(o.diagnostic_support=="UNSUPPORTED_NO_AUTOMATIC_DIAGNOSTIC").sum()} | no-user-roster: {(o.status=="NO_USER_ROSTER").sum()} | fetch errors: {(o.status=="FETCH_ERROR").sum()}')
    print('\nREADY LEAGUES')
    cols=['league_name','format_key','current_roster_players','supported_scoring_totals']
    print(o[o.status.eq('READY')][cols].to_string(index=False))
    print(f'\nCreated:\n- {OUT}')
    print('\nREADING CONTRACT')
    print('- READY means current league format exactly matches frozen empirical V0.24 evidence and the user roster is fetchable.')
    print('- Unsupported current formats are not mapped to Wookiee or a nearest format.')
    print('- This script does not classify current players as Scoring/Non-Scoring yet.')
    print('- Current roster size is observed ownership, not a prescribed Scoring-core size.')
    print('- Next step may attach league-native player economics only for READY leagues.')
if __name__=='__main__': main()
