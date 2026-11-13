#!/usr/bin/env python3
"""WoRP Lab — Sleeper user league inventory V0.1
Resolve username -> user_id -> NFL leagues, follow historical lineage, and inventory formats.
Readonly Sleeper API only. No WoRP conclusions are made here.
"""
import json, urllib.request, time
import pandas as pd

USERNAME='jperocco'
SEASONS=range(2026,2022,-1)  # current + historical discovery window

def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'WoRPLab/1.0'})
 with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)

def slot_summary(pos):
 pos=pos or []
 bench=sum(1 for x in pos if x in ('BN','BENCH'))
 starters=[x for x in pos if x not in ('BN','BENCH','IR','TAXI')]
 return starters,bench

u=get(f'https://api.sleeper.app/v1/user/{USERNAME}')
if not u or not u.get('user_id'):raise SystemExit(f'FAIL: Sleeper user not found: {USERNAME}')
uid=str(u['user_id'])
print(f'User: {USERNAME} | user_id={uid}',flush=True)

# Discover user's leagues by season, then follow previous_league_id lineage to avoid losing
# historical seasons when a current league is renewed under a new ID.
discovered={}
for season in SEASONS:
 try: leagues=get(f'https://api.sleeper.app/v1/user/{uid}/leagues/nfl/{season}') or []
 except Exception as e:
  print(f'{season}: discovery error: {e}',flush=True);continue
 print(f'{season}: {len(leagues)} NFL leagues',flush=True)
 for lg in leagues:discovered[str(lg['league_id'])]=lg

queue=list(discovered)
seen=set()
while queue:
 lid=queue.pop(0)
 if lid in seen or not lid or lid=='0':continue
 seen.add(lid)
 lg=discovered.get(lid)
 if lg is None:
  try:lg=get(f'https://api.sleeper.app/v1/league/{lid}')
  except Exception as e:
   print(f'lineage fetch failed {lid}: {e}',flush=True);continue
  if lg:discovered[lid]=lg
 prev=str((lg or {}).get('previous_league_id') or '')
 if prev and prev!='0' and prev not in seen:queue.append(prev)

rows=[]
for lid,lg in discovered.items():
 if not lg:continue
 season=int(lg.get('season') or 0)
 rp=lg.get('roster_positions') or []
 starters,bench=slot_summary(rp)
 settings=lg.get('settings') or {}; scoring=lg.get('scoring_settings') or {}
 # Count actual rosters as a cross-check; total_rosters is canonical league setting when present.
 try:nrosters=len(get(f'https://api.sleeper.app/v1/league/{lid}/rosters') or [])
 except:nrosters=None
 teams=int(lg.get('total_rosters') or nrosters or 0)
 rows.append({
  'league_id':lid,'season':season,'name':lg.get('name',''),'status':lg.get('status',''),
  'teams':teams,'actual_rosters':nrosters,'starters':len(starters),'roster_positions_total':len(rp),
  'bench_slots':bench,'starter_slots':'|'.join(starters),'roster_positions':'|'.join(rp),
  'has_sf':any(x in ('SUPER_FLEX','SUPERFLEX') for x in starters),
  'flex_slots':sum(1 for x in starters if x in ('FLEX','REC_FLEX','WRRB_FLEX','WRRBTE_FLEX')),
  'sf_slots':sum(1 for x in starters if x in ('SUPER_FLEX','SUPERFLEX')),
  'qb_slots':starters.count('QB'),'rb_slots':starters.count('RB'),'wr_slots':starters.count('WR'),'te_slots':starters.count('TE'),
  'taxi_slots':settings.get('taxi_slots'),'reserve_slots':settings.get('reserve_slots'),
  'previous_league_id':lg.get('previous_league_id'),'scoring_json':json.dumps(scoring,sort_keys=True)
 })
 time.sleep(.02)

df=pd.DataFrame(rows)
if df.empty:raise SystemExit('FAIL: no leagues discovered.')
df=df.sort_values(['season','name','league_id'],ascending=[False,True,True])
df.to_csv('sleeper_user_league_inventory_v0_1.csv',index=False)

# Current/latest representative per lineage/name-format view; retain every league-season in CSV.
print('\n'+'='*150);print('SLEEPER USER LEAGUE INVENTORY V0.1');print('='*150)
cols=['season','name','league_id','teams','starters','roster_positions_total','qb_slots','rb_slots','wr_slots','te_slots','flex_slots','sf_slots','taxi_slots']
print(df[cols].to_string(index=False))
print('\nFORMAT COUNTS (league-seasons)')
fmt=(df.groupby(['teams','starters','qb_slots','rb_slots','wr_slots','te_slots','flex_slots','sf_slots'],dropna=False)
 .size().reset_index(name='league_seasons').sort_values('league_seasons',ascending=False))
print(fmt.to_string(index=False))
print('\nCreated: sleeper_user_league_inventory_v0_1.csv')
print('NEXT GATE: inspect format diversity and historical coverage before running multi-league depth capture.')
