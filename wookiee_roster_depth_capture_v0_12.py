#!/usr/bin/env python3
"""WoRP Lab — Historical Roster Depth / Lineup Capture V0.12

Optimized implementation. Same research question as the original V0.12, but avoids
rebuilding/sorting pandas frames inside every roster-week x family loop.

Wookiee reference-league test. Reconstruct each roster-week from Sleeper matchup
snapshots, join realized weekly WoRP + season positional rank, and ask how much ORACLE
lineup WoRP is lost when the roster's Scoring core is capped at candidate whole-roster
families (11..15 Scoring players).

IMPORTANT LIMITS
- EX-POST structural evidence, not an ex-ante roster strategy.
- Core retention uses realized season pos_rank (hindsight), intentionally favorable to
  smaller cores. If a shallow core still loses material Oracle WoRP, that is strong evidence.
- Wookiee is reference evidence only; raw counts are never universalized.
"""
import json, urllib.request
from itertools import product
import pandas as pd

CURRENT_LEAGUE_ID='1317417394439741440'; MAX_LINEAGE=20
POS=('QB','RB','WR','TE')
FLOOR={'QB':1,'RB':2,'WR':2,'TE':1}
CEIL={'QB':5,'RB':6,'WR':8,'TE':3}

def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'WoRPLab/1.0'})
 with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)

def can_fill(c):
 if any(c[p]<FLOOR[p] for p in POS):return False
 rem={p:c[p]-FLOOR[p] for p in POS}
 for rb in range(5):
  for wr in range(5-rb):
   te=4-rb-wr
   if rem['RB']<rb or rem['WR']<wr or rem['TE']<te:continue
   left=rem.copy();left['RB']-=rb;left['WR']-=wr;left['TE']-=te
   if sum(left.values())>=1:return True
 return False

# Precompute every legal exact-11 starter positional composition once.
LINEUP_COUNTS=[]
for q in range(1,3):
 for r in range(2,8):
  for w in range(2,8):
   for t in range(1,7):
    c={'QB':q,'RB':r,'WR':w,'TE':t}
    if sum(c.values())==11 and can_fill(c):LINEUP_COUNTS.append(c)

def oracle_from_pools(pools):
 """Max legal weekly WoRP from already-sorted positional WoRP lists."""
 best=None
 for c in LINEUP_COUNTS:
  if any(len(pools[p])<c[p] for p in POS):continue
  val=sum(sum(pools[p][:c[p]]) for p in POS)
  if best is None or val>best:best=val
 return best

families=[]
for vals in product(*[range(FLOOR[p],CEIL[p]+1) for p in POS]):
 c=dict(zip(POS,vals));total=sum(vals)
 if 11<=total<=15 and can_fill(c):families.append((c,total))
print(f'Prepared {len(families)} candidate Scoring families.',flush=True)

weekly=pd.read_csv('wookiee_2023_2025_weekly_worp.csv',dtype={'player_id':str})
ranks=pd.read_csv('wookiee_2023_2025_rankings_worp.csv',dtype={'player_id':str})[['season','player_id','position','pos_rank']]
weekly=weekly.merge(ranks,on=['season','player_id','position'],how='left')
# Lightweight lookup: tuple, not pandas namedtuple/frame.
lookup={}
for r in weekly[['season','week','player_id','position','weekly_worp','pos_rank']].itertuples(index=False):
 lookup[(int(r.season),int(r.week),str(r.player_id))]=(r.position,float(r.weekly_worp),float(r.pos_rank) if pd.notna(r.pos_rank) else 9999.0)

line=[];seen=set();lid=CURRENT_LEAGUE_ID
for _ in range(MAX_LINEAGE):
 if not lid or lid=='0' or lid in seen:break
 seen.add(lid);lg=get(f'https://api.sleeper.app/v1/league/{lid}')
 season=int(lg.get('season') or 0)
 if season in (2023,2024,2025):line.append((season,lid))
 lid=str(lg.get('previous_league_id') or '')
print('Sleeper seasons: '+', '.join(str(x[0]) for x in sorted(line)),flush=True)

records=[]; roster_weeks=0
for season,lid in sorted(line):
 print(f'Processing {season}...',flush=True)
 for week in range(1,19):
  snaps=get(f'https://api.sleeper.app/v1/league/{lid}/matchups/{week}')
  if not snaps:continue
  for snap in snaps:
   rid=snap.get('roster_id');ids=[str(x) for x in (snap.get('players') or [])]
   # Build each positional pool ONCE. rank_pool = (season pos_rank, -weekly_worp, weekly_worp)
   ranked={p:[] for p in POS}
   for pid in ids:
    x=lookup.get((season,week,pid))
    if x is None:continue
    p,ww,pr=x
    if p in POS:ranked[p].append((pr,-ww,ww))
   for p in POS:ranked[p].sort()
   full_pools={p:sorted([x[2] for x in ranked[p]],reverse=True) for p in POS}
   full=oracle_from_pools(full_pools)
   if full is None:continue
   roster_weeks+=1
   # Cache oracle result for each unique positional count tuple this roster-week.
   core_oracle={}
   for c,total in families:
    key=tuple(c[p] for p in POS)
    pools={p:sorted([x[2] for x in ranked[p][:c[p]]],reverse=True) for p in POS}
    val=oracle_from_pools(pools)
    if val is None:continue
    lost=max(0.0,full-val)
    records.append({'season':season,'week':week,'roster_id':rid,'scoring_total':total,
      'qb':c['QB'],'rb':c['RB'],'wr':c['WR'],'te':c['TE'],'full_oracle_worp':full,
      'core_oracle_worp':val,'lost_oracle_worp':lost,'material_025':lost>=.25,'material_050':lost>=.50,'material_075':lost>=.75})
  print(f'  week {week:02d} | analyzed roster-weeks={roster_weeks}',flush=True)

print(f'Building summaries from {len(records):,} family observations...',flush=True)
d=pd.DataFrame(records)
if d.empty:raise SystemExit('FAIL: no joined roster-week observations. Check Sleeper lineage / weekly WoRP IDs.')
d.to_csv('wookiee_roster_depth_capture_detail_v0_12.csv',index=False)
fam=(d.groupby(['scoring_total','qb','rb','wr','te'],as_index=False)
 .agg(roster_weeks=('lost_oracle_worp','size'),mean_lost=('lost_oracle_worp','mean'),median_lost=('lost_oracle_worp','median'),
      total_lost=('lost_oracle_worp','sum'),weeks_025=('material_025','sum'),weeks_050=('material_050','sum'),weeks_075=('material_075','sum')))
fam['rate_025']=fam.weeks_025/fam.roster_weeks;fam['rate_050']=fam.weeks_050/fam.roster_weeks;fam['rate_075']=fam.weeks_075/fam.roster_weeks
fam.to_csv('wookiee_roster_depth_capture_families_v0_12.csv',index=False)
rows=[]
for total,g in fam.groupby('scoring_total'):
 best=g.sort_values(['total_lost','rate_050','rate_025']).iloc[0]
 rows.append({'scoring_total':int(total),'families':len(g),'best_qb':int(best.qb),'best_rb':int(best.rb),'best_wr':int(best.wr),'best_te':int(best.te),
  'best_total_lost':best.total_lost,'best_mean_lost':best.mean_lost,'best_rate_025':best.rate_025,'best_rate_050':best.rate_050,'best_rate_075':best.rate_075,
  'median_family_total_lost':g.total_lost.median(),'worst_family_total_lost':g.total_lost.max()})
s=pd.DataFrame(rows);s.to_csv('wookiee_roster_depth_capture_summary_v0_12.csv',index=False)
print('='*120);print('WOOKIEE ROSTER DEPTH / LINEUP CAPTURE V0.12 — EX-POST UPPER-BOUND TEST');print('='*120)
print(s.round(4).to_string(index=False))
print('\nBEST FAMILIES BY SCORING TOTAL (hindsight-favorable; NOT prescriptions)')
for _,r in s.iterrows():print(f"{int(r.scoring_total)} Scoring -> QB{int(r.best_qb)} RB{int(r.best_rb)} WR{int(r.best_wr)} TE{int(r.best_te)} | total lost={r.best_total_lost:.3f} | >=.50 week rate={r.best_rate_050:.2%}")
print('\nREADING CONTRACT')
print('- Wookiee reference evidence only; raw roster counts are not universal.')
print('- Season pos_rank retention uses hindsight: FAVORABLE upper-bound test for shallow cores.')
print('- .25/.50/.75 are descriptive probes, not universal thresholds.')
print('- Focus on diminishing marginal reduction in material lost WoRP as Scoring total rises.')
print('- If 12->13->14->15 recovers decision-material WoRP, depth matters; if gains collapse, capacity can move to Non-Scoring.')
print('- Nearby families with the same decision collapse to an envelope; do not optimize exact tuple.')
print('\nCreated: wookiee_roster_depth_capture_summary_v0_12.csv')
print('Created: wookiee_roster_depth_capture_families_v0_12.csv')
print('Created: wookiee_roster_depth_capture_detail_v0_12.csv')
