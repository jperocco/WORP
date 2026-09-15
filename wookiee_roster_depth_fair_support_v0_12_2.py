#!/usr/bin/env python3
"""WoRP Lab — Wookiee roster-depth V0.12.2: fair-support correction.

Consumes V0.12 detail. For each roster-week and Scoring total N=11..15, chooses the
best feasible positional family for that SAME roster-week (minimum lost Oracle WoRP),
then restricts comparison to roster-weeks supported at every N. This removes unequal-
denominator bias and tests Scoring-core SIZE rather than one fixed QB/RB/WR/TE tuple.

Still an ex-post, hindsight-favorable Wookiee reference test. .25/.50/.75 are probes.
"""
import pandas as pd

IN='wookiee_roster_depth_capture_detail_v0_12.csv'
TOTALS=list(range(11,16))
KEY=['season','week','roster_id']

d=pd.read_csv(IN)
need=set(KEY+['scoring_total','qb','rb','wr','te','full_oracle_worp','core_oracle_worp','lost_oracle_worp'])
missing=need-set(d.columns)
if missing: raise SystemExit(f'FAIL: {IN} missing columns: {sorted(missing)}')
d=d[d.scoring_total.isin(TOTALS)].copy()
print(f'Loaded {len(d):,} family observations.',flush=True)

# Best feasible family independently within each roster-week x Scoring-total.
d=d.sort_values(KEY+['scoring_total','lost_oracle_worp','qb','rb','wr','te'])
best=d.groupby(KEY+['scoring_total'],as_index=False).first()

# Feasibility diagnostics before common-support restriction.
all_rw=d[KEY].drop_duplicates().shape[0]
feas=(best.groupby('scoring_total').size().reindex(TOTALS,fill_value=0).rename('feasible_roster_weeks').reset_index())
feas['all_roster_weeks']=all_rw
feas['feasibility_rate']=feas.feasible_roster_weeks/all_rw

counts=best.groupby(KEY).scoring_total.nunique()
common=counts[counts.eq(len(TOTALS))].reset_index()[KEY]
fair=best.merge(common,on=KEY,how='inner')
common_n=len(common)
print(f'Roster-weeks observed: {all_rw:,} | common support across 11..15: {common_n:,} ({common_n/all_rw:.2%})',flush=True)
if common_n==0: raise SystemExit('FAIL: no common-support roster-weeks across Scoring totals 11..15.')

for x in (.25,.50,.75): fair[f'material_{int(x*100):03d}']=fair.lost_oracle_worp.ge(x)
fair.to_csv('wookiee_roster_depth_fair_support_detail_v0_12_2.csv',index=False)
feas.to_csv('wookiee_roster_depth_fair_support_feasibility_v0_12_2.csv',index=False)

def summarize(g):
 return pd.Series({
  'roster_weeks':len(g),
  'mean_lost':g.lost_oracle_worp.mean(),
  'median_lost':g.lost_oracle_worp.median(),
  'total_lost':g.lost_oracle_worp.sum(),
  'rate_025':g.material_025.mean(),
  'rate_050':g.material_050.mean(),
  'rate_075':g.material_075.mean(),
 })

overall=fair.groupby('scoring_total').apply(summarize,include_groups=False).reset_index()
season=fair.groupby(['season','scoring_total']).apply(summarize,include_groups=False).reset_index()
overall.to_csv('wookiee_roster_depth_fair_support_summary_v0_12_2.csv',index=False)
season.to_csv('wookiee_roster_depth_fair_support_by_season_v0_12_2.csv',index=False)

print('\n'+'='*110)
print('V0.12.2 — FAIR SUPPORT / FLEXIBLE FAMILY')
print('='*110)
print('\nFEASIBILITY BEFORE COMMON SUPPORT')
print(feas.to_string(index=False,formatters={'feasibility_rate':'{:.2%}'.format}))
print('\nCOMMON-SUPPORT OVERALL')
print(overall.round(4).to_string(index=False))
print('\nCOMMON-SUPPORT BY SEASON')
print(season.round(4).to_string(index=False))
print('\nREADING CONTRACT')
print('- Every Scoring total is compared on the same roster-weeks.')
print('- Within each roster-week x total, the best feasible positional family is used: favorable envelope, not exact-tuple policy.')
print('- Season pos_rank retention inherited from V0.12 remains hindsight-favorable.')
print('- .25/.50/.75 remain descriptive sensitivity probes, not universal semantic thresholds.')
print('- Wookiee is reference evidence only; do not universalize raw counts.')
print('- Judge broad decision-stable ranges and material reductions, not decimal noise.')
print('\nCreated: wookiee_roster_depth_fair_support_summary_v0_12_2.csv')
print('Created: wookiee_roster_depth_fair_support_by_season_v0_12_2.csv')
print('Created: wookiee_roster_depth_fair_support_feasibility_v0_12_2.csv')
print('Created: wookiee_roster_depth_fair_support_detail_v0_12_2.csv')
