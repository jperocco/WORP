#!/usr/bin/env python3
"""Wookiee Positional Big-Impact Tail Audit V0.7

Research principle: WoRP Lab cares about materially consequential outcomes, not tiny
mean differences. This audit asks which low-use positional pools generate the RIGHT
TAIL of future WoRP after a shock.

Trigger week is excluded. Full 4-week forward horizon only.
"""
from pathlib import Path
import pandas as pd
import numpy as np

EVENTS=Path('wookiee_positional_state_change_events_v0_6.csv')
PERSIST=Path('wookiee_positional_state_change_persistence_detail_v0_6_1.csv')
POOL=Path('wookiee_positional_state_change_pool_detail_v0_6.csv')
OUT_SUM=Path('wookiee_positional_big_impact_tail_summary_v0_7.csv')
OUT_DIST=Path('wookiee_positional_big_impact_tail_distribution_v0_7.csv')
POSITIONS=['QB','RB','WR','TE']
HURDLES=[0.25,0.50,0.75,1.00]

for p in [EVENTS,PERSIST,POOL]:
    if not p.exists(): raise SystemExit(f'STOP: required input missing: {p}')
ev=pd.read_csv(EVENTS); pe=pd.read_csv(PERSIST); pool=pd.read_csv(POOL)
keys=['season','roster_id','player_id','trigger_week']
required={'horizon_weeks','future_weeks_observed','future_positive_worp','future_captured_positive_worp'}
miss=required-set(pe.columns)
if miss: raise SystemExit(f'STOP: persistence detail missing columns: {sorted(miss)}')
# V0.6.1 schema uses horizon_weeks. Require all 4 future weeks to avoid late-season truncation.
p4=pe[(pe.horizon_weeks.eq(4)) & (pe.future_weeks_observed.eq(4))].copy()
m=ev.merge(p4,on=keys,how='inner',suffixes=('','_p'))
if m.empty: raise SystemExit('STOP: no full-horizon events.')
pool_counts=pool.groupby('position').size().to_dict()

dist=[]
for pos in POSITIONS:
    x=m[m.position.eq(pos)]
    if x.empty: continue
    for metric in ['future_positive_worp','future_captured_positive_worp']:
        s=pd.to_numeric(x[metric],errors='coerce').dropna()
        dist.append({'position':pos,'metric':metric,'n_events':len(s),'p50':s.quantile(.50),'p75':s.quantile(.75),'p85':s.quantile(.85),'p90':s.quantile(.90),'p95':s.quantile(.95),'max':s.max(),'mean':s.mean()})
dist=pd.DataFrame(dist); dist.to_csv(OUT_DIST,index=False)

rows=[]
for pos in POSITIONS:
    x=m[m.position.eq(pos)].copy(); den=pool_counts.get(pos,0)
    if x.empty or not den: continue
    for hurdle in HURDLES:
        prod=x[x.future_positive_worp>=hurdle]
        cap=x[x.future_captured_positive_worp>=hurdle]
        rows.append({'position':pos,'four_week_worp_hurdle':hurdle,'pool_player_weeks':den,'full_horizon_shocks':len(x),'produced_big_hits':len(prod),'produced_big_hits_per_100_pool_weeks':100*len(prod)/den,'produced_big_hit_share_of_shocks':len(prod)/len(x),'captured_big_hits':len(cap),'captured_big_hits_per_100_pool_weeks':100*len(cap)/den,'captured_big_hit_share_of_shocks':len(cap)/len(x),'capture_conversion_of_big_produced_hits':len(x[(x.future_positive_worp>=hurdle)&(x.future_captured_positive_worp>=hurdle)])/len(prod) if len(prod) else np.nan,'total_future_worp_from_produced_big_hits':prod.future_positive_worp.sum(),'total_captured_worp_from_captured_big_hits':cap.future_captured_positive_worp.sum(),'median_future_worp_when_big_hit':prod.future_positive_worp.median() if len(prod) else np.nan,'median_captured_worp_when_big_hit':cap.future_captured_positive_worp.median() if len(cap) else np.nan})
out=pd.DataFrame(rows); out.to_csv(OUT_SUM,index=False)

print('=== POSITIONAL BIG-IMPACT TAIL V0.7 ===')
print('Trigger excluded; complete next-4-week horizon only.')
print('Research rule: tiny WoRP differences are NOISE. We care about consequential right-tail outcomes.\n')
print('IMPACT DISTRIBUTION'); print(dist.round(4).to_string(index=False))
print('\nABSOLUTE 4-WEEK WORP HURDLES')
for h in HURDLES:
    print(f'\nHURDLE >= {h:.2f} WoRP')
    z=out[out.four_week_worp_hurdle.eq(h)]
    for _,r in z.iterrows():
        print(f"  {r.position}: produced {int(r.produced_big_hits)} ({r.produced_big_hits_per_100_pool_weeks:.3f}/100 pool-wk) | captured {int(r.captured_big_hits)} ({r.captured_big_hits_per_100_pool_weeks:.3f}/100 pool-wk) | produced->captured conversion {r.capture_conversion_of_big_produced_hits:.1%}")
print('\nDECISION RULES')
print('- Ignore small mean gaps. Focus on frequency and magnitude of the material right tail.')
print('- Do not pick one hurdle because it favors a position. Look for ordering that survives 0.25/0.50/0.75/1.00 WoRP.')
print('- If a positional difference exists only below a material hurdle, classify it as noise for roster construction.')
print('- If counts become tiny, invoke the relevance/STOP rule instead of over-interpreting.')
print('- This measures sporting impact only; market appreciation remains separate.')
print(f'\nCreated: {OUT_DIST.name}'); print(f'Created: {OUT_SUM.name}')
