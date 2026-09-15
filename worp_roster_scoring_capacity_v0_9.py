#!/usr/bin/env python3
"""WoRP Lab — League-Native Scoring Roster Capacity V0.9

First roster-construction bridge after closing positional-curve research.

Question: given a league's slot eligibility and a BROAD economically relevant
Scoring frontier by position, how many Scoring players of each position can a roster
reasonably carry before additional capacity becomes redundant?

This does NOT optimize a single exact roster. It enumerates feasible positional
allocations against league-wide scoring supply and starting-slot demand, then reports
allocation ENVELOPES. Remaining roster capacity belongs to Non-Scoring/optionality.

Important:
- Frontier inputs are provisional broad ranges from V0.8.2 review, not universal ranks.
- No waiver logic, asset value, ADP, trade value or per-player WoRP.
- FLEX/SF are handled through eligibility, not traditional slot labels.
- Output is a research diagnostic. It does not claim that every roster should hold the
  upper bound of every positional envelope simultaneously.
"""
from dataclasses import dataclass
from itertools import product
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
# Broad end-of-material-Scoring envelopes from V0.8.2 review.
# These are deliberately ranges. A later league-settings engine should infer them
# directly from the league-native curve rather than hard-code fixture values.
FRONTIERS={
 '10T_1QB_Start8':{'QB':(10,15),'RB':(35,40),'WR':(40,50),'TE':(10,15)},
 '12T_1QB_Start8':{'QB':(15,20),'RB':(40,50),'WR':(50,60),'TE':(15,20)},
 '12T_1QB_Start11':{'QB':(15,20),'RB':(55,70),'WR':(75,90),'TE':(30,40)},
 '12T_SF_Start11':{'QB':(40,50),'RB':(50,65),'WR':(70,85),'TE':(25,35)},
 '12T_SF_2TE_TEP_Start11':{'QB':(40,50),'RB':(50,60),'WR':(65,75),'TE':(35,45)},
 '14T_SF_Start10':{'QB':(45,55),'RB':(55,70),'WR':(75,90),'TE':(30,35)},
}
POS=('QB','RB','WR','TE')

def feasible_start_allocs(f):
 """All per-team starter-count vectors allowed by fixed + FLEX/SF eligibility."""
 base={'QB':f.qb,'RB':f.rb,'WR':f.wr,'TE':f.te}
 allocs=[]
 # FLEX: RB/WR/TE. SF: QB/RB/WR/TE.
 for flex_rb in range(f.flex+1):
  for flex_wr in range(f.flex-flex_rb+1):
   flex_te=f.flex-flex_rb-flex_wr
   for sfpos in (POS if f.sf else (None,)):
    x=base.copy();x['RB']+=flex_rb;x['WR']+=flex_wr;x['TE']+=flex_te
    if sfpos:x[sfpos]+=1
    allocs.append(x)
 return allocs

rows=[]
for name,f in FORMATS.items():
 starts=feasible_start_allocs(f)
 for bound in ('low','high'):
  supply={p:FRONTIERS[name][p][0 if bound=='low' else 1] for p in POS}
  per_team={p:supply[p]/f.teams for p in POS}
  # Minimum starting demand across legal slot allocations and maximum legal demand.
  start_min={p:min(x[p] for x in starts) for p in POS}
  start_max={p:max(x[p] for x in starts) for p in POS}
  for p in POS:
   # Scoring supply per team is the economic capacity ceiling in expectation.
   # A roster cannot usefully be told to carry fewer than its fixed starter floor.
   lo=start_min[p]
   hi=max(lo,per_team[p])
   rows.append({'format':name,'frontier_bound':bound,'position':p,
    'league_scoring_supply':supply[p],'scoring_supply_per_team':per_team[p],
    'fixed_start_floor':start_min[p],'max_eligible_start_demand':start_max[p],
    'candidate_scoring_roster_floor':lo,'candidate_scoring_roster_ceiling':hi,
    'roster_size':f.roster,'teams':f.teams})

raw=pd.DataFrame(rows)
# Collapse frontier low/high uncertainty into per-position allocation envelopes.
out=(raw.groupby(['format','position'],as_index=False)
 .agg(scoring_supply_low=('league_scoring_supply','min'),scoring_supply_high=('league_scoring_supply','max'),
      supply_per_team_low=('scoring_supply_per_team','min'),supply_per_team_high=('scoring_supply_per_team','max'),
      fixed_start_floor=('fixed_start_floor','first'),max_eligible_start_demand=('max_eligible_start_demand','first'),
      roster_size=('roster_size','first'),teams=('teams','first')))
# Do not pretend fractional league-average supply is an exact roster count. Report
# integer envelope using floor/ceil only as readable bounds.
out['scoring_count_low']=out[['fixed_start_floor','supply_per_team_low']].max(axis=1).apply(lambda x:int(x//1))
out['scoring_count_high']=out[['fixed_start_floor','supply_per_team_high']].max(axis=1).apply(lambda x:int(-(-x//1)))
out.to_csv('worp_roster_scoring_capacity_v0_9.csv',index=False)
raw.to_csv('worp_roster_scoring_capacity_detail_v0_9.csv',index=False)

print('='*116);print('ROSTER SCORING CAPACITY V0.9 — LEAGUE-NATIVE ENVELOPES');print('='*116)
for fmt,g in out.groupby('format',sort=False):
 print(f'\n### {fmt}')
 z=g[['position','scoring_supply_low','scoring_supply_high','supply_per_team_low','supply_per_team_high','fixed_start_floor','max_eligible_start_demand','scoring_count_low','scoring_count_high']].copy()
 print(z.round(2).to_string(index=False))
 # Aggregate is intentionally shown as a range, not a prescription.
 print(f"candidate total Scoring slots (sum of positional envelopes, NOT simultaneous optimum): {int(z.scoring_count_low.sum())}-{int(z.scoring_count_high.sum())}")
 print(f"roster size: {int(g.roster_size.iloc[0])}")
print('\nREADING CONTRACT')
print('- This is a CAPACITY envelope, not an optimal roster prescription.')
print('- Do not sum positional upper bounds and call that the recommended roster.')
print('- FLEX/SF create interpositional competition; the next test must enumerate whole-roster constructions.')
print('- If an envelope barely changes across reasonable frontier uncertainty, treat it as decision-stable.')
print('- Remaining roster capacity after an efficient Scoring construction is Non-Scoring/optionality capacity.')
print('- Next: enumerate whole-roster allocations and test which broad constructions satisfy slot demand without redundant Scoring.')
print('\nCreated: worp_roster_scoring_capacity_v0_9.csv')
print('Created: worp_roster_scoring_capacity_detail_v0_9.csv')
