#!/usr/bin/env python3
"""WoRP Lab — V0.12.1 seasonal replication.
Reads V0.12 detail output and tests whether the shallow-core elbow replicates by season.
No new model assumptions; .25/.50/.75 remain descriptive probes.

IMPORTANT: Wookiee has 11 starters. The resulting raw 13–15 counts are reference-league
evidence only. Product translation must normalize against starting-lineup demand and slot
eligibility before applying to Start8/Start10/etc. This script therefore also reports
Scoring surplus above starters (scoring_total - 11), which is the quantity to examine
before league-native translation.
"""
import pandas as pd

SRC='wookiee_roster_depth_capture_detail_v0_12.csv'
d=pd.read_csv(SRC)
STARTERS=11
keys=['season','scoring_total','qb','rb','wr','te']
fam=(d.groupby(keys,as_index=False)
 .agg(roster_weeks=('lost_oracle_worp','size'),total_lost=('lost_oracle_worp','sum'),
      mean_lost=('lost_oracle_worp','mean'),weeks_025=('material_025','sum'),
      weeks_050=('material_050','sum'),weeks_075=('material_075','sum')))
for x in ('025','050','075'):fam['rate_'+x]=fam['weeks_'+x]/fam.roster_weeks
fam['scoring_surplus_vs_starters']=fam.scoring_total-STARTERS
fam.to_csv('wookiee_roster_depth_replication_families_v0_12_1.csv',index=False)

rows=[]
for (season,total),g in fam.groupby(['season','scoring_total']):
 # Preserve V0.12 favorable-to-shallow-core convention: choose composition with least total loss.
 best=g.sort_values(['total_lost','rate_050','rate_025']).iloc[0]
 rows.append({'season':int(season),'starters':STARTERS,'scoring_total':int(total),
  'scoring_surplus_vs_starters':int(total-STARTERS),'families':len(g),
  'best_qb':int(best.qb),'best_rb':int(best.rb),'best_wr':int(best.wr),'best_te':int(best.te),
  'best_total_lost':best.total_lost,'best_mean_lost':best.mean_lost,
  'best_rate_025':best.rate_025,'best_rate_050':best.rate_050,'best_rate_075':best.rate_075,
  'median_family_total_lost':g.total_lost.median()})
s=pd.DataFrame(rows).sort_values(['season','scoring_total'])
# Marginal change in material-loss rate when adding one Scoring slot.
s['delta_rate_050_vs_prev']=s.groupby('season').best_rate_050.diff()
s['delta_rate_025_vs_prev']=s.groupby('season').best_rate_025.diff()
s.to_csv('wookiee_roster_depth_replication_summary_v0_12_1.csv',index=False)

print('='*124)
print('WOOKIEE ROSTER DEPTH REPLICATION V0.12.1 — BY SEASON')
print('='*124)
for season,g in s.groupby('season'):
 print(f'\n### {season} | starting lineup={STARTERS}')
 cols=['scoring_total','scoring_surplus_vs_starters','best_qb','best_rb','best_wr','best_te',
       'best_mean_lost','best_rate_025','best_rate_050','best_rate_075','delta_rate_050_vs_prev']
 print(g[cols].round(4).to_string(index=False))

print('\nREPLICATION VIEW — >=.50 LOSS RATE')
piv=s.pivot(index='scoring_total',columns='season',values='best_rate_050')
print((piv*100).round(2).to_string())
print('\nREADING CONTRACT')
print('- Replication asks whether the 13–15 Scoring region is persistent across 2023/2024/2025, not which exact count wins.')
print('- 13/14/15 are Wookiee raw counts because Wookiee starts 11. Also read them as +2/+3/+4 Scoring above starters.')
print('- Do NOT transfer +2/+3/+4 mechanically to other formats; Start8/Start10/Start11 have different positional and interpositional demand.')
print('- Next league-native step must use starting-lineup size + slot eligibility + positional economic frontiers together.')
print('- If adjacent counts have the same decision implication, collapse to a broad envelope and STOP exact-count refinement.')
print('- .25/.50/.75 are probes only; prioritize material decision changes, not tiny numerical differences.')
print('\nCreated: wookiee_roster_depth_replication_summary_v0_12_1.csv')
print('Created: wookiee_roster_depth_replication_families_v0_12_1.csv')
