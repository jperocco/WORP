#!/usr/bin/env python3
"""Wookiee Big-Impact Replication Audit V0.7.1

Tests whether the V0.7 material right-tail story repeats across independent slices
already available in the local historical sample. No new threshold optimization.
Primary material hurdle is fixed at 0.50 four-week WoRP because V0.7 showed that
below this level much of the positional separation can be small-impact noise.
Sensitivity retains 0.25/0.75 but does not tune a cutoff.

Replication slices:
- season
- roster_id (league/team environment proxy; descriptive only)

The audit reports produced and captured big hits from the validated low-use pool.
It does not infer market value or final roster prescription.
"""
from pathlib import Path
import pandas as pd
import numpy as np

EVENTS=Path('wookiee_positional_state_change_events_v0_6.csv')
PERSIST=Path('wookiee_positional_state_change_persistence_detail_v0_6_1.csv')
POOL=Path('wookiee_positional_state_change_pool_detail_v0_6.csv')
OUT=Path('wookiee_positional_big_impact_replication_v0_7_1.csv')
OUT_SEASON=Path('wookiee_positional_big_impact_replication_by_season_v0_7_1.csv')
POSITIONS=['QB','RB','WR','TE']
HURDLES=[0.25,0.50,0.75]

for p in [EVENTS,PERSIST,POOL]:
    if not p.exists(): raise SystemExit(f'STOP: required input missing: {p}')
ev=pd.read_csv(EVENTS); pe=pd.read_csv(PERSIST); pool=pd.read_csv(POOL)
keys=['season','roster_id','player_id','trigger_week']
p4=pe[(pe.horizon_weeks.eq(4))&(pe.future_weeks_observed.eq(4))].copy()
m=ev.merge(p4,on=keys,how='inner',suffixes=('','_p'))
if m.empty: raise SystemExit('STOP: no complete 4-week events.')

# Pool denominators by season/position. This is the cleanest independent temporal
# replication available without inventing new external data.
pden=pool.groupby(['season','position']).size().rename('pool_player_weeks').reset_index()
rows=[]
for season in sorted(set(pool.season).intersection(set(m.season))):
    for pos in POSITIONS:
        x=m[(m.season.eq(season))&(m.position.eq(pos))]
        dd=pden[(pden.season.eq(season))&(pden.position.eq(pos))]
        den=int(dd.pool_player_weeks.iloc[0]) if len(dd) else 0
        if not den: continue
        for h in HURDLES:
            prod=x[x.future_positive_worp>=h]
            cap=x[x.future_captured_positive_worp>=h]
            rows.append({'season':season,'position':pos,'hurdle':h,'pool_player_weeks':den,'full_horizon_shocks':len(x),'produced_big_hits':len(prod),'captured_big_hits':len(cap),'produced_hits_per_100_pool_weeks':100*len(prod)/den,'captured_hits_per_100_pool_weeks':100*len(cap)/den,'total_produced_big_hit_worp':prod.future_positive_worp.sum(),'total_captured_big_hit_worp':cap.future_captured_positive_worp.sum()})
out=pd.DataFrame(rows); out.to_csv(OUT_SEASON,index=False)

# Compact replication diagnostics at the material 0.50 hurdle.
z=out[out.hurdle.eq(.50)].copy()
diag=[]
for pos in POSITIONS:
    x=z[z.position.eq(pos)]
    if x.empty: continue
    seasons=len(x)
    with_prod=(x.produced_big_hits>0).sum(); with_cap=(x.captured_big_hits>0).sum()
    diag.append({'position':pos,'seasons_observed':seasons,'seasons_with_produced_050_hit':with_prod,'share_seasons_with_produced_050_hit':with_prod/seasons,'seasons_with_captured_050_hit':with_cap,'share_seasons_with_captured_050_hit':with_cap/seasons,'total_produced_050_hits':x.produced_big_hits.sum(),'total_captured_050_hits':x.captured_big_hits.sum(),'median_produced_hits_per_100_by_season':x.produced_hits_per_100_pool_weeks.median(),'max_produced_hits_per_100_by_season':x.produced_hits_per_100_pool_weeks.max()})
diag=pd.DataFrame(diag); diag.to_csv(OUT,index=False)

print('=== BIG-IMPACT REPLICATION V0.7.1 ===')
print('Primary hurdle fixed BEFORE this test: >=0.50 WoRP over the next 4 complete weeks.\n')
print(diag.round(4).to_string(index=False))
print('\nBY-SEASON MATERIAL HITS (>=0.50)')
print(z[['season','position','pool_player_weeks','produced_big_hits','captured_big_hits','produced_hits_per_100_pool_weeks','captured_hits_per_100_pool_weeks']].round(4).to_string(index=False))
print('\nDECISION GATE')
print('- A pooled result is stronger if material hits recur across seasons rather than coming from one season.')
print('- WR 0/76 in pooled V0.7 is especially informative if WR remains zero across every observed season.')
print('- QB/RB/TE conclusions require caution if all material hits concentrate in one season.')
print('- Do not chase 0.50 vs nearby cutoffs; 0.25 and 0.75 are sensitivity only.')
print('- If material events remain too sparse after temporal replication, STOP and broaden historical data rather than overfit this sample.')
print(f'\nCreated: {OUT.name}'); print(f'Created: {OUT_SEASON.name}')
