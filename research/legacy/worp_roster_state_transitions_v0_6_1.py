#!/usr/bin/env python3
"""WoRP Lab — Roster State Transitions V0.6.1
Measure actual week-to-week state changes, especially BENCH->START and NON_SCORING->SCORING.
FREE is a roster state, not required to produce WoRP.
Wookiee 2023-25 reference audit only.
"""
import json, urllib.request
from pathlib import Path
import pandas as pd
WORP=Path('wookiee_2023_2025_weekly_worp.csv')
LEAGUES={2023:'950220100039311360',2024:'1050961255520923648',2025:'1182581249532833792'}
POS=['QB','RB','WR','TE']
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'WoRPLab/0.6.1'})
 with urllib.request.urlopen(req,timeout=90) as r:return json.loads(r.read().decode())
def snap(lid,wk):
 rows=get(f'https://api.sleeper.app/v1/league/{lid}/matchups/{wk}') or []; d={}
 for r in rows:
  rid=r.get('roster_id'); st={str(x) for x in (r.get('starters') or []) if x and str(x)!='0'}
  for p in (r.get('players') or []): d[str(p)]=(rid,str(p) in st)
 return d
def main():
 w=pd.read_csv(WORP);w.player_id=w.player_id.astype(str);w.weekly_worp=pd.to_numeric(w.weekly_worp,errors='coerce').fillna(0)
 w=w[w.season.isin(LEAGUES)&w.position.isin(POS)&w.week.between(1,18)]
 ident=w[['season','player_id','player_name','position']].drop_duplicates(['season','player_id'])
 states=[]
 for season,lid in LEAGUES.items():
  for wk in range(1,19):
   s=snap(lid,wk); ww=w[(w.season==season)&(w.week==wk)].set_index('player_id').weekly_worp.to_dict()
   for x in ident[ident.season==season].itertuples():
    if x.player_id not in s: state='FREE'
    else:
     rid,started=s[x.player_id]; val=float(ww.get(x.player_id,0))
     state='STARTED' if started else ('BENCHED_SCORING' if val>0 else 'ROSTERED_NON_SCORING')
    states.append((season,wk,x.player_id,x.player_name,x.position,state,float(ww.get(x.player_id,0))))
 d=pd.DataFrame(states,columns=['season','week','player_id','player_name','position','state','weekly_worp'])
 nxt=d[['season','week','player_id','state','weekly_worp']].copy();nxt.week-=1;nxt=nxt.rename(columns={'state':'next_state','weekly_worp':'next_worp'})
 z=d.merge(nxt,on=['season','week','player_id'],how='inner');z=z[z.week<18];z['transition']=z.state+' -> '+z.next_state
 summary=z.groupby(['position','state','next_state']).size().reset_index(name='n')
 den=z.groupby(['position','state']).size().reset_index(name='denominator');summary=summary.merge(den,on=['position','state']);summary['rate']=summary.n/summary.denominator
 key=summary[((summary.state=='BENCHED_SCORING')&(summary.next_state=='STARTED'))|((summary.state=='ROSTERED_NON_SCORING')&(summary.next_state.isin(['BENCHED_SCORING','STARTED'])))|((summary.state=='FREE')&(summary.next_state=='ROSTERED_NON_SCORING'))].copy()
 z.to_csv('worp_roster_state_transitions_detail_v0_6_1.csv',index=False);summary.to_csv('worp_roster_state_transitions_summary_v0_6_1.csv',index=False);key.to_csv('worp_roster_state_transitions_key_v0_6_1.csv',index=False)
 print('='*100);print('WORP ROSTER STATE TRANSITIONS V0.6.1');print('='*100);print(key.to_string(index=False))
 print('\nNEXT: use these transition rates to test how often existing roster depth, rather than waiver scoring, absorbs lineup demand.')
if __name__=='__main__':main()
