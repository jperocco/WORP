#!/usr/bin/env python3
"""Wookiee Positional State-Change Impact Audit V0.6.2

Uses V0.6 shock events + V0.6.1 forward persistence detail to measure the user's
actual question at a common event level:
  how often does a low-use positional pool generate a durable state-change candidate,
  and what sporting impact follows?

No trade-value inference. No final roster prescription. No arbitrary rank cutoff.
"""
from pathlib import Path
import pandas as pd
import numpy as np

EVENTS=Path('wookiee_positional_state_change_events_v0_6.csv')
PERSIST=Path('wookiee_positional_state_change_persistence_detail_v0_6_1.csv')
POOL=Path('wookiee_positional_state_change_pool_detail_v0_6.csv')
OUT=Path('wookiee_positional_state_change_impact_v0_6_2.csv')
POSITIONS=['QB','RB','WR','TE']

for p in [EVENTS,PERSIST,POOL]:
    if not p.exists(): raise SystemExit(f'STOP: required input missing: {p}')
ev=pd.read_csv(EVENTS); pe=pd.read_csv(PERSIST); pool=pd.read_csv(POOL)
keys=['season','roster_id','player_id','trigger_week']
need_e=set(keys+['position','delta_vs_prior'])
need_p=set(keys+['forward_horizon','future_positive_worp','future_captured_positive_worp','future_real_starts','mean_future_worp','share_future_weeks_above_prior_baseline'])
for name,df,need in [('events',ev,need_e),('persistence',pe,need_p)]:
    miss=need-set(df.columns)
    if miss: raise SystemExit(f'STOP: {name} missing columns: {sorted(miss)}')

# Full 4-week forward horizon only: trigger excluded by V0.6.1.
p4=pe[pe.forward_horizon.eq(4)].copy()
m=ev.merge(p4,on=keys,how='inner',suffixes=('','_p'))
if len(m)==0: raise SystemExit('STOP: no events with full 4-week forward horizon.')

# Two transparent durability lenses. Neither is declared semantic truth.
# A: broad regime persistence = majority of future weeks above pre-shock baseline.
# B: lineup-relevant promotion = >=2 REAL starts in the next four weeks.
m['durable_regime_proxy']=m.share_future_weeks_above_prior_baseline>=0.50
m['lineup_promotion_proxy']=m.future_real_starts>=2
m['durable_and_lineup']=m.durable_regime_proxy & m.lineup_promotion_proxy

# Denominator = positional low-use pool player-weeks from V0.6.
pool_counts=pool.groupby('position').size().to_dict()
rows=[]
for pos in POSITIONS:
    x=m[m.position.eq(pos)].copy(); den=pool_counts.get(pos,0)
    if x.empty: continue
    for label,flag in [
        ('ALL_FULL_HORIZON_SHOCKS',pd.Series(True,index=x.index)),
        ('DURABLE_REGIME',x.durable_regime_proxy),
        ('LINEUP_PROMOTION_2PLUS_STARTS',x.lineup_promotion_proxy),
        ('DURABLE_AND_LINEUP',x.durable_and_lineup),
    ]:
        y=x[flag]
        rows.append({
            'position':pos,'lens':label,'pool_player_weeks':den,
            'eligible_events':len(x),'events':len(y),
            'events_per_100_pool_weeks':100*len(y)/den if den else np.nan,
            'share_of_full_horizon_shocks':len(y)/len(x),
            'mean_future_positive_worp':y.future_positive_worp.mean() if len(y) else np.nan,
            'median_future_positive_worp':y.future_positive_worp.median() if len(y) else np.nan,
            'mean_future_captured_worp':y.future_captured_positive_worp.mean() if len(y) else np.nan,
            'median_future_captured_worp':y.future_captured_positive_worp.median() if len(y) else np.nan,
            'total_future_positive_worp':y.future_positive_worp.sum(),
            'total_future_captured_worp':y.future_captured_positive_worp.sum(),
            'future_capture_share':y.future_captured_positive_worp.sum()/y.future_positive_worp.sum() if y.future_positive_worp.sum()>0 else np.nan,
            'captured_worp_per_100_pool_weeks':100*y.future_captured_positive_worp.sum()/den if den else np.nan,
            'mean_future_real_starts':y.future_real_starts.mean() if len(y) else np.nan,
            'mean_future_worp':y.mean_future_worp.mean() if len(y) else np.nan,
        })
out=pd.DataFrame(rows)
out.to_csv(OUT,index=False)

print('=== POSITIONAL STATE-CHANGE IMPACT V0.6.2 ===')
print('Trigger week excluded; only events with a complete 4-week future horizon.')
print('DURABLE = >=50% future weeks above the player pre-shock baseline.')
print('LINEUP PROMOTION = >=2 REAL starts in the next 4 weeks.\n')
for lens in ['ALL_FULL_HORIZON_SHOCKS','DURABLE_REGIME','LINEUP_PROMOTION_2PLUS_STARTS','DURABLE_AND_LINEUP']:
    print(lens)
    z=out[out.lens.eq(lens)]
    for _,r in z.iterrows():
        print(f"  {r.position}: {int(r.events)}/{int(r.eligible_events)} events | {r.events_per_100_pool_weeks:.3f}/100 pool-wk | future WoRP={r.mean_future_positive_worp:.3f} | captured={r.mean_future_captured_worp:.3f} | capture={r.future_capture_share:.1%} | captured/100 pool-wk={r.captured_worp_per_100_pool_weeks:.3f}")
    print()
print('DECISION GATE')
print('- Compare frequency AND impact. A position can create many transitions but weak sporting payoff, or fewer transitions with larger payoff.')
print('- DURABLE_AND_LINEUP is the strictest sporting state-change proxy here; it is still ex-post.')
print('- If positional conclusions differ materially between DURABLE_REGIME and LINEUP_PROMOTION, do not collapse them into one state definition.')
print('- Market appreciation remains outside this dataset.')
print(f'\nCreated: {OUT.name}')
