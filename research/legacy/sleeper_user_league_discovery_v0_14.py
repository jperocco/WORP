#!/usr/bin/env python3
"""WoRP Lab — Sleeper user-linked NFL league discovery V0.14.

Readonly/no-auth inventory. Resolves username -> user_id, queries seasons, records every
league-season observation and format settings. Does not assume Wookiee economics.
"""
import argparse,json,urllib.request
import pandas as pd

BASE='https://api.sleeper.app/v1'
def get(path):
 req=urllib.request.Request(BASE+path,headers={'User-Agent':'WoRPLab/1.0'})
 try:
  with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
 except Exception as e:
  print(f'WARN {path}: {e}',flush=True); return None

def classify(pos,sc):
 starters=[]; bench=0
 for x in pos or []:
  if x in ('BN','IR','TAXI'): bench+=1
  else: starters.append(x)
 sf=sum(x in ('SUPER_FLEX','SUPERFLEX','OP') for x in starters)
 flex=sum(x in ('FLEX','REC_FLEX') for x in starters)
 fixed={p:sum(x==p for x in starters) for p in ('QB','RB','WR','TE')}
 # Sleeper commonly encodes TE premium as bonus_rec_te / bonus_rec_yd_te variants.
 tep={k:v for k,v in (sc or {}).items() if 'te' in k.lower() and ('bonus' in k.lower() or 'rec' in k.lower()) and v not in (0,None)}
 return starters,bench,sf,flex,fixed,tep

ap=argparse.ArgumentParser();ap.add_argument('username',nargs='?',default='jperocco');ap.add_argument('--start',type=int,default=2016);ap.add_argument('--end',type=int,default=2025)
a=ap.parse_args()
u=get('/user/'+a.username)
if not u or not u.get('user_id'):raise SystemExit(f'FAIL: Sleeper user not found: {a.username}')
uid=str(u['user_id']);print(f'User {a.username} -> {uid}',flush=True)
rows=[]
for season in range(a.start,a.end+1):
 leagues=get(f'/user/{uid}/leagues/nfl/{season}') or []
 print(f'{season}: {len(leagues)} NFL league(s)',flush=True)
 for lg in leagues:
  pos=lg.get('roster_positions') or [];sc=lg.get('scoring_settings') or {};settings=lg.get('settings') or {}
  starters,bench,sf,flex,fixed,tep=classify(pos,sc)
  rows.append({'username':a.username,'user_id':uid,'season':season,'league_id':str(lg.get('league_id')),
   'name':lg.get('name'),'previous_league_id':str(lg.get('previous_league_id') or ''),'total_rosters':lg.get('total_rosters'),
   'starter_count':len(starters),'roster_positions_count':len(pos),'listed_bench_slots':bench,
   'fixed_qb':fixed['QB'],'fixed_rb':fixed['RB'],'fixed_wr':fixed['WR'],'fixed_te':fixed['TE'],'flex_slots':flex,'sf_slots':sf,
   'format_qb':'SF' if sf else '1QB','tep_detected':bool(tep),'tep_scoring_keys':json.dumps(tep,sort_keys=True),
   'roster_positions':json.dumps(pos),'scoring_settings':json.dumps(sc,sort_keys=True),'settings':json.dumps(settings,sort_keys=True)})

df=pd.DataFrame(rows)
if df.empty:raise SystemExit('No user-linked NFL leagues found in requested seasons.')
df=df.sort_values(['season','name','league_id'])
df.to_csv('sleeper_user_league_inventory_v0_14.csv',index=False)
print('\nDISCOVERED LEAGUE-SEASONS')
cols=['season','league_id','name','total_rosters','starter_count','roster_positions_count','format_qb','fixed_rb','fixed_wr','fixed_te','flex_slots','sf_slots','tep_detected','previous_league_id']
print(df[cols].to_string(index=False))
print(f'\nUnique league IDs: {df.league_id.nunique()} | league-season rows: {len(df)}')
print('Created: sleeper_user_league_inventory_v0_14.csv')
print('\nREADING CONTRACT')
print('- User-linked discovery only; absence here does not mean a league does not exist on Sleeper.')
print('- Preserve every league-season row for empirical validation; previous_league_id is lineage metadata, not a dedupe instruction.')
print('- Format fields are structural inventory, not WoRP conclusions.')
