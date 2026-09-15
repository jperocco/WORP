#!/usr/bin/env python3
"""WoRP Lab — Roster Construction Resilience / Roster-Size Stress Test V0.11

Fixes the key limitation of V0.10: roster size must be an active economic constraint,
not merely a column printed beside the result.

This test keeps league format and slot eligibility separate from roster capacity and
stress-tests multiple roster sizes for each format. It asks how the feasible whole-
roster Scoring families change as benches get shallow/deep.

It does NOT assume deeper roster = more Scoring. Extra capacity may rationally remain
Non-Scoring optionality. It also does NOT impose an arbitrary backup-at-every-position
rule. Instead it reports coverage resilience under simple one-player-loss scenarios:
what share of rostered Scoring players can be removed one at a time while the remaining
Scoring roster can still legally fill the starting lineup.

This is a structural diagnostic, not a final optimizer.
"""
from dataclasses import dataclass
from itertools import product
import math
import pandas as pd

@dataclass(frozen=True)
class Fmt:
 teams:int; qb:int; rb:int; wr:int; te:int; flex:int; sf:int; default_roster:int
FORMATS={
 '10T_1QB_Start8':Fmt(10,1,2,2,1,2,0,20),
 '12T_1QB_Start8':Fmt(12,1,2,2,1,2,0,24),
 '12T_1QB_Start11':Fmt(12,1,2,3,1,4,0,28),
 '12T_SF_Start11':Fmt(12,1,2,3,1,3,1,28),
 '12T_SF_2TE_TEP_Start11':Fmt(12,1,2,3,2,2,1,28),
 '14T_SF_Start10':Fmt(14,1,2,2,1,3,1,26),
}
FRONTIERS={
 '10T_1QB_Start8':{'QB':(10,15),'RB':(35,40),'WR':(40,50),'TE':(10,15)},
 '12T_1QB_Start8':{'QB':(15,20),'RB':(40,50),'WR':(50,60),'TE':(15,20)},
 '12T_1QB_Start11':{'QB':(15,20),'RB':(55,70),'WR':(75,90),'TE':(30,40)},
 '12T_SF_Start11':{'QB':(40,50),'RB':(50,65),'WR':(70,85),'TE':(25,35)},
 '12T_SF_2TE_TEP_Start11':{'QB':(40,50),'RB':(50,60),'WR':(65,75),'TE':(35,45)},
 '14T_SF_Start10':{'QB':(45,55),'RB':(55,70),'WR':(75,90),'TE':(30,35)},
}
POS=('QB','RB','WR','TE')

def starts(f): return f.qb+f.rb+f.wr+f.te+f.flex+f.sf

def can_fill(f,c):
 if any(c[p]<getattr(f,p.lower()) for p in POS): return False
 rem={p:c[p]-getattr(f,p.lower()) for p in POS}
 for fr in range(f.flex+1):
  for fw in range(f.flex-fr+1):
   ft=f.flex-fr-fw
   if rem['RB']<fr or rem['WR']<fw or rem['TE']<ft: continue
   left=rem.copy(); left['RB']-=fr;left['WR']-=fw;left['TE']-=ft
   if f.sf==0 or sum(left.values())>=f.sf:return True
 return False

def one_loss_coverage(f,c):
 """Weighted share of individual Scoring-player losses that preserve legal coverage."""
 total=sum(c.values()); ok=0
 for p,n in c.items():
  if n<=0:continue
  x=c.copy();x[p]-=1
  if can_fill(f,x):ok+=n
 return ok/total if total else 0

rows=[]
for name,f in FORMATS.items():
 s=starts(f)
 # Stress roster size from shallow (starters+3) through deep (starters+20), always
 # including fixture/default size. This makes roster size a variable rather than a fixture identity.
 sizes=sorted(set([s+3,s+6,s+9,s+12,s+16,s+20,f.default_roster]))
 ceilings={p:max(getattr(f,p.lower()),math.ceil(FRONTIERS[name][p][1]/f.teams)) for p in POS}
 floors={p:getattr(f,p.lower()) for p in POS}
 tuples=[]
 for vals in product(*[range(floors[p],ceilings[p]+1) for p in POS]):
  c=dict(zip(POS,vals)); total=sum(vals)
  if can_fill(f,c):tuples.append((c,total,one_loss_coverage(f,c)))
 for roster in sizes:
  valid=[x for x in tuples if x[1]<=roster]
  if not valid:continue
  min_sc=min(x[1] for x in valid)
  # For each Scoring total through +4, summarize the resilience frontier.
  for total in range(min_sc,min(min_sc+4,roster)+1):
   band=[x for x in valid if x[1]==total]
   if not band:continue
   best=max(x[2] for x in band); robust=[x for x in band if abs(x[2]-best)<1e-12]
   rec={'format':name,'teams':f.teams,'starters':s,'roster_size':roster,'bench_size':roster-s,
        'scoring_total':total,'non_scoring_capacity':roster-total,'n_viable':len(band),
        'best_one_loss_coverage':best,'n_best_resilience':len(robust)}
   for p in POS:
    rec[p.lower()+'_low']=min(x[0][p] for x in robust);rec[p.lower()+'_high']=max(x[0][p] for x in robust)
   rows.append(rec)

out=pd.DataFrame(rows)
out.to_csv('worp_roster_construction_resilience_v0_11.csv',index=False)
print('='*128);print('ROSTER CONSTRUCTION RESILIENCE V0.11 — ROSTER SIZE IS ACTIVE');print('='*128)
for fmt,g in out.groupby('format',sort=False):
 print(f'\n### {fmt}')
 # Compact: best-resilience envelope at each roster size and scoring total.
 z=g[['roster_size','bench_size','scoring_total','non_scoring_capacity','best_one_loss_coverage','qb_low','qb_high','rb_low','rb_high','wr_low','wr_high','te_low','te_high']]
 print(z.round(3).to_string(index=False))
print('\nREADING CONTRACT')
print('- Roster size is an input dimension. Do not hard-code Wookiee/default roster depth as product truth.')
print('- More bench slots do NOT automatically imply more Scoring players; extra capacity can remain Non-Scoring optionality.')
print('- One-loss coverage is a resilience diagnostic, not a universal requirement or objective function.')
print('- Compare whether preferred Scoring envelopes change when bench size changes materially.')
print('- If Scoring envelope is stable while roster grows, the added slots are structurally optionality capacity.')
print('- If shallow rosters force trade-offs, preserve those as league-native construction constraints.')
print('- Next: use historical lineup-capture evidence to test which resilient families actually avoid meaningful missed WoRP.')
print('\nCreated: worp_roster_construction_resilience_v0_11.csv')
