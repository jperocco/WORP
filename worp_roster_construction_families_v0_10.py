#!/usr/bin/env python3
"""WoRP Lab — Whole-Roster Construction Families V0.10

Enumerate complete Scoring roster constructions using league-native positional
frontiers plus slot eligibility. Goal: identify broad, decision-useful families —
not one mathematically 'optimal' roster.

A construction is viable when:
1) it can legally fill every starting slot (fixed + FLEX + SF);
2) its positional Scoring counts stay within league-native economic supply ceilings;
3) it carries at least the fixed starter floor at every position;
4) we report the Pareto-efficient layer by total Scoring capacity: constructions
   using fewer Scoring roster spots are preferred only when they preserve the same
   legal starting coverage.

This deliberately does NOT claim that minimum Scoring count is automatically best.
It exposes the trade-off surface and how much roster capacity remains for
Non-Scoring/optionality. No waiver, asset value, ADP, or per-player WoRP.
"""
from dataclasses import dataclass
from itertools import product
import math
import pandas as pd

@dataclass(frozen=True)
class Fmt:
 teams:int; qb:int; rb:int; wr:int; te:int; flex:int; sf:int; roster:int

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

def can_fill(f,c):
 """Exact eligibility feasibility for one team's starting lineup."""
 if c['QB']<f.qb or c['RB']<f.rb or c['WR']<f.wr or c['TE']<f.te:return False
 rem={p:c[p]-getattr(f,p.lower()) for p in POS}
 # Assign FLEX among RB/WR/TE, then SF from anything remaining.
 for fr in range(f.flex+1):
  for fw in range(f.flex-fr+1):
   ft=f.flex-fr-fw
   if rem['RB']<fr or rem['WR']<fw or rem['TE']<ft:continue
   left=rem.copy();left['RB']-=fr;left['WR']-=fw;left['TE']-=ft
   if f.sf==0:return True
   if sum(left[p] for p in POS)>=f.sf:return True
 return False

rows=[]
for name,f in FORMATS.items():
 # Economic per-team ceilings use high frontier only as availability ceiling, NOT target.
 ceilings={p:max(getattr(f,p.lower()),math.ceil(FRONTIERS[name][p][1]/f.teams)) for p in POS}
 floors={p:getattr(f,p.lower()) for p in POS}
 for vals in product(*[range(floors[p],ceilings[p]+1) for p in POS]):
  c=dict(zip(POS,vals))
  if not can_fill(f,c):continue
  total=sum(vals)
  if total>f.roster:continue
  rows.append({'format':name,**{p.lower():c[p] for p in POS},'scoring_total':total,
               'non_scoring_capacity':f.roster-total,'roster_size':f.roster})

allv=pd.DataFrame(rows)
allv.to_csv('worp_roster_construction_all_viable_v0_10.csv',index=False)
summary=[];families=[]
for name,g in allv.groupby('format',sort=False):
 min_total=int(g.scoring_total.min())
 # Show minimum through +3 Scoring spots: enough to expose coverage-vs-optionality trade-offs
 # without pretending deep redundant Scoring is automatically useful.
 surface=g[g.scoring_total<=min_total+3].copy()
 for t,tg in surface.groupby('scoring_total'):
  rec={'format':name,'scoring_total':int(t),'non_scoring_capacity':int(tg.non_scoring_capacity.iloc[0]),'n_constructions':len(tg)}
  for p in ('qb','rb','wr','te'):
   rec[p+'_low']=int(tg[p].min());rec[p+'_high']=int(tg[p].max())
  summary.append(rec)
 # Compact family list: unique positional tuples on the surface.
 for _,r in surface.sort_values(['scoring_total','qb','rb','wr','te']).iterrows():
  families.append(r.to_dict())

s=pd.DataFrame(summary); fam=pd.DataFrame(families)
s.to_csv('worp_roster_construction_families_v0_10.csv',index=False)
fam.to_csv('worp_roster_construction_surface_v0_10.csv',index=False)
print('='*120);print('WHOLE-ROSTER CONSTRUCTION FAMILIES V0.10');print('='*120)
for fmt,g in s.groupby('format',sort=False):
 print(f'\n### {fmt}')
 print(g[['scoring_total','non_scoring_capacity','n_constructions','qb_low','qb_high','rb_low','rb_high','wr_low','wr_high','te_low','te_high']].to_string(index=False))
 # Print only minimum and +1 exact tuples for human inspection.
 mn=int(g.scoring_total.min()); q=fam[(fam['format']==fmt)&(fam.scoring_total<=mn+1)]
 print('minimum/+1 candidate tuples (QB,RB,WR,TE):')
 print(q[['scoring_total','non_scoring_capacity','qb','rb','wr','te']].to_string(index=False))
print('\nREADING CONTRACT')
print('- Minimum Scoring is a coverage boundary, NOT proof of optimality.')
print('- Compare minimum, +1, +2, +3 families as a trade-off surface.')
print('- Positional ranges at each total show interpositional substitution created by FLEX/SF.')
print('- Do not recommend a tuple merely because it leaves the most Non-Scoring spots.')
print('- Next test: add resilience / lineup-capture requirements and ask which families survive without redundant Scoring.')
print('- If neighboring families imply the same roster decision, collapse them into one envelope and STOP.')
print('\nCreated: worp_roster_construction_families_v0_10.csv')
print('Created: worp_roster_construction_surface_v0_10.csv')
print('Created: worp_roster_construction_all_viable_v0_10.csv')
