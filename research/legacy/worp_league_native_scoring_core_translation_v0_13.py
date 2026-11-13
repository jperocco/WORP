#!/usr/bin/env python3
"""WoRP Lab — League-Native Scoring Core Translation V0.13

Translate the replicated Wookiee depth result into FORMAT-SPECIFIC research envelopes
without universalizing Wookiee's raw 13–15 count or its +2/+4 surplus.

Inputs already established by prior research:
- starting lineup size and slot eligibility by fixture;
- broad league-native material Scoring frontiers by position (V0.8.2);
- Wookiee replication says exact-starter coverage is too shallow and meaningful depth
  exists beyond starters, but Wookiee raw counts are reference evidence only.

Method here is deliberately structural, not a fitted optimizer:
1) enumerate every legal exact starting-lineup positional composition for the format;
2) derive league-wide economically relevant Scoring supply per position from frontier ranges;
3) enumerate whole-roster Scoring counts that can fill the lineup and do not exceed economic supply;
4) report construction families by SURPLUS above starters, not by Wookiee raw count;
5) expose how much positional redundancy is economically available relative to legal slot demand.

No assumption that +2/+3/+4 is universal. No waiver, asset value, per-player WoRP, or exact
optimal roster. This is the translation gate before empirical validation in other leagues.
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

def nstarters(f):return f.qb+f.rb+f.wr+f.te+f.flex+f.sf

def can_fill(f,c):
 if c['QB']<f.qb or c['RB']<f.rb or c['WR']<f.wr or c['TE']<f.te:return False
 rem={'QB':c['QB']-f.qb,'RB':c['RB']-f.rb,'WR':c['WR']-f.wr,'TE':c['TE']-f.te}
 for fr in range(f.flex+1):
  for fw in range(f.flex-fr+1):
   ft=f.flex-fr-fw
   if rem['RB']<fr or rem['WR']<fw or rem['TE']<ft:continue
   left=rem.copy();left['RB']-=fr;left['WR']-=fw;left['TE']-=ft
   if f.sf==0 or sum(left.values())>=f.sf:return True
 return False

def exact_lineup_comps(f):
 s=nstarters(f);out=[]
 # bounds safely exceed any exact starter demand
 for q in range(f.qb,s+1):
  for r in range(f.rb,s+1):
   for w in range(f.wr,s+1):
    for t in range(f.te,s+1):
     c={'QB':q,'RB':r,'WR':w,'TE':t}
     if sum(c.values())==s and can_fill(f,c):out.append(c)
 return out

rows=[];posrows=[]
for name,f in FORMATS.items():
 s=nstarters(f); legal=exact_lineup_comps(f)
 demand_min={p:min(c[p] for c in legal) for p in POS}
 demand_max={p:max(c[p] for c in legal) for p in POS}
 # Per-team economic supply envelope. Fractions are retained as economics; integer ceilings
 # are only enumeration bounds, not recommended roster counts.
 econ_low={p:FRONTIERS[name][p][0]/f.teams for p in POS}
 econ_high={p:FRONTIERS[name][p][1]/f.teams for p in POS}
 cap={p:max(demand_min[p],math.ceil(econ_high[p])) for p in POS}
 for p in POS:
  posrows.append({'format':name,'position':p,'teams':f.teams,'starters':s,
   'legal_start_demand_min':demand_min[p],'legal_start_demand_max':demand_max[p],
   'economic_scoring_supply_per_team_low':econ_low[p],'economic_scoring_supply_per_team_high':econ_high[p],
   'economic_redundancy_above_fixed_floor_low':max(0,econ_low[p]-demand_min[p]),
   'economic_redundancy_above_fixed_floor_high':max(0,econ_high[p]-demand_min[p])})
 # Enumerate all viable scoring cores up to +6 beyond starters only to expose the surface.
 # +6 is a display/research window, NOT a candidate optimum or Wookiee-derived rule.
 for vals in product(*[range(demand_min[p],cap[p]+1) for p in POS]):
  c=dict(zip(POS,vals));total=sum(vals);surplus=total-s
  if surplus<0 or surplus>6 or total>f.roster or not can_fill(f,c):continue
  rows.append({'format':name,'teams':f.teams,'starters':s,'roster_size':f.roster,
   'scoring_total':total,'scoring_surplus_vs_starters':surplus,
   'non_scoring_capacity':f.roster-total,**{p.lower():c[p] for p in POS}})

allc=pd.DataFrame(rows); pos=pd.DataFrame(posrows)
allc.to_csv('worp_league_native_scoring_core_constructions_v0_13.csv',index=False)
pos.to_csv('worp_league_native_scoring_core_position_context_v0_13.csv',index=False)
summary=[]
for (fmt,sur),g in allc.groupby(['format','scoring_surplus_vs_starters'],sort=False):
 rec={'format':fmt,'starters':int(g.starters.iloc[0]),'roster_size':int(g.roster_size.iloc[0]),
      'scoring_surplus_vs_starters':int(sur),'scoring_total':int(g.scoring_total.iloc[0]),
      'non_scoring_capacity':int(g.non_scoring_capacity.iloc[0]),'n_constructions':len(g)}
 for p in ('qb','rb','wr','te'):
  rec[p+'_low']=int(g[p].min());rec[p+'_high']=int(g[p].max())
 summary.append(rec)
s=pd.DataFrame(summary)
s.to_csv('worp_league_native_scoring_core_summary_v0_13.csv',index=False)

print('='*132);print('LEAGUE-NATIVE SCORING CORE TRANSLATION V0.13');print('='*132)
for fmt,g in s.groupby('format',sort=False):
 ctx=pos[pos.format.eq(fmt)]
 print(f"\n### {fmt} | starters={int(g.starters.iloc[0])} | roster={int(g.roster_size.iloc[0])}")
 print('POSITIONAL CONTEXT: legal starter demand + economic Scoring supply per team')
 print(ctx[['position','legal_start_demand_min','legal_start_demand_max','economic_scoring_supply_per_team_low','economic_scoring_supply_per_team_high']].round(2).to_string(index=False))
 print('WHOLE-ROSTER SURPLUS SURFACE (translation candidates, not recommendations)')
 print(g[['scoring_surplus_vs_starters','scoring_total','non_scoring_capacity','n_constructions','qb_low','qb_high','rb_low','rb_high','wr_low','wr_high','te_low','te_high']].to_string(index=False))
print('\nREADING CONTRACT')
print('- Starting-lineup size is explicit and format-specific. Start8/Start10/Start11 are NOT scaled copies.')
print('- Slot eligibility is explicit: FLEX and SF alter legal positional demand.')
print('- Team count enters through league-wide economic Scoring supply per team.')
print('- Roster size caps total capacity but does not automatically inflate Scoring need.')
print('- Wookiee +2/+4 is NOT imposed here. Surplus 0..6 is only a transparent candidate surface.')
print('- This script translates constraints; it does NOT empirically prove the correct surplus for non-Wookiee formats.')
print('- Next gate requires empirical multi-league / multi-format validation before productizing roster-count envelopes.')
print('- If evidence is unavailable for a format, preserve uncertainty rather than manufacture a universal count.')
print('\nCreated: worp_league_native_scoring_core_summary_v0_13.csv')
print('Created: worp_league_native_scoring_core_position_context_v0_13.csv')
print('Created: worp_league_native_scoring_core_constructions_v0_13.csv')
