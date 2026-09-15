#!/usr/bin/env python3
"""Post-shock persistence audit V0.6.1.

Companion to V0.6. The V0.6 trigger week is useful for detecting a shock but can
inflate apparent persistence. This audit excludes the trigger week and asks what
happens AFTER it over 1/2/3/4-week forward horizons.

No semantic state label is emitted. The output is a positional impact profile:
future WoRP, future starts/selections, and how often the player's future WoRP stays
above his own pre-trigger baseline.
"""
from pathlib import Path
import pandas as pd
import numpy as np

BASE=Path('wookiee_ex_ante_lineup_player_week_v0_6.csv')
EVENTS=Path('wookiee_positional_state_change_events_v0_6.csv')
OUT_DETAIL=Path('wookiee_positional_state_change_persistence_detail_v0_6_1.csv')
OUT_SUM=Path('wookiee_positional_state_change_persistence_summary_v0_6_1.csv')
HORIZONS=[1,2,3,4]
POSITIONS=['QB','RB','WR','TE']

def as_bool(s):
    if s.dtype==bool:return s
    return s.astype(str).str.lower().isin(['true','1','yes'])

def safe(a,b): return float(a/b) if b else np.nan

if not BASE.exists() or not EVENTS.exists():
    raise SystemExit('STOP: run V0.6 first; required local inputs are missing.')
b=pd.read_csv(BASE); e=pd.read_csv(EVENTS)
need_b={'season','week','roster_id','player_id','position','weekly_worp','real_started','oracle_started'}
need_e={'season','roster_id','player_id','position','trigger_week','prior_worp_l5'}
if need_b-set(b.columns): raise SystemExit(f'STOP: base missing {sorted(need_b-set(b.columns))}')
if need_e-set(e.columns): raise SystemExit(f'STOP: events missing {sorted(need_e-set(e.columns))}')
b=b[b.position.isin(POSITIONS)].copy(); b['real_started']=as_bool(b.real_started); b['oracle_started']=as_bool(b.oracle_started)
b['weekly_worp']=pd.to_numeric(b.weekly_worp,errors='coerce').fillna(0)
b=b.sort_values(['season','roster_id','player_id','week']).drop_duplicates(['season','week','roster_id','player_id'],keep='last')
lookup={(r.season,r.roster_id,r.player_id,int(r.week)):r for r in b.itertuples()}
rows=[]
for ev in e.itertuples():
    baseline=0.0 if pd.isna(ev.prior_worp_l5) else float(ev.prior_worp_l5)
    for h in HORIZONS:
        xs=[]
        for w in range(int(ev.trigger_week)+1,int(ev.trigger_week)+h+1):
            r=lookup.get((ev.season,ev.roster_id,ev.player_id,w))
            if r is not None: xs.append(r)
        if not xs: continue
        worps=np.array([float(r.weekly_worp) for r in xs])
        positive=np.clip(worps,0,None)
        real=np.array([bool(r.real_started) for r in xs])
        oracle=np.array([bool(r.oracle_started) for r in xs])
        rows.append({
            'season':ev.season,'roster_id':ev.roster_id,'player_id':ev.player_id,'position':ev.position,
            'trigger_week':ev.trigger_week,'horizon_weeks':h,'future_weeks_observed':len(xs),'prior_worp_l5':baseline,
            'future_mean_worp':worps.mean(),'future_median_worp':np.median(worps),'future_positive_worp':positive.sum(),
            'future_captured_positive_worp':positive[real].sum(),'future_real_start_weeks':real.sum(),
            'future_oracle_weeks':oracle.sum(),'future_weeks_above_baseline':(worps>baseline).sum(),
            'future_mean_above_baseline':bool(worps.mean()>baseline),
            'future_majority_weeks_above_baseline':bool((worps>baseline).sum()>=np.ceil(len(xs)/2)),
        })
d=pd.DataFrame(rows)
if d.empty: raise SystemExit('STOP: no post-trigger observations found.')
d.to_csv(OUT_DETAIL,index=False)

summary=[]
for (pos,h),g in d.groupby(['position','horizon_weeks']):
    # Full-horizon rows prevent late-season truncated windows from masquerading as persistence.
    full=g[g.future_weeks_observed.eq(h)]
    if full.empty: continue
    summary.append({
        'position':pos,'horizon_weeks':h,'events_with_full_horizon':len(full),
        'share_future_mean_above_baseline':full.future_mean_above_baseline.mean(),
        'share_majority_weeks_above_baseline':full.future_majority_weeks_above_baseline.mean(),
        'share_with_any_real_start':(full.future_real_start_weeks>0).mean(),
        'share_with_2plus_real_starts':(full.future_real_start_weeks>=2).mean(),
        'share_with_any_oracle_selection':(full.future_oracle_weeks>0).mean(),
        'median_future_mean_worp':full.future_mean_worp.median(),
        'mean_future_positive_worp':full.future_positive_worp.mean(),
        'mean_future_captured_positive_worp':full.future_captured_positive_worp.mean(),
        'total_future_positive_worp':full.future_positive_worp.sum(),
        'total_future_captured_positive_worp':full.future_captured_positive_worp.sum(),
        'capture_share':safe(full.future_captured_positive_worp.sum(),full.future_positive_worp.sum()),
    })
s=pd.DataFrame(summary).sort_values(['horizon_weeks','position'])
s.to_csv(OUT_SUM,index=False)
print('=== POSITIONAL STATE-CHANGE PERSISTENCE V0.6.1 ===')
print('Trigger week EXCLUDED. Full forward horizons only in summary.\n')
for h in HORIZONS:
    print(f'FORWARD {h} WEEK(S)')
    x=s[s.horizon_weeks.eq(h)]
    for r in x.itertuples():
        print(f'  {r.position}: n={r.events_with_full_horizon} | mean>baseline={r.share_future_mean_above_baseline:.1%} | majority>baseline={r.share_majority_weeks_above_baseline:.1%} | any REAL start={r.share_with_any_real_start:.1%} | 2+ REAL={r.share_with_2plus_real_starts:.1%} | future +WoRP={r.mean_future_positive_worp:.3f} | captured={r.mean_future_captured_positive_worp:.3f} | capture share={r.capture_share:.1%}')
    print()
print('DECISION GATE')
print('- V0.6 shock frequency alone is not a state change; V0.6.1 tests whether value survives after the shock.')
print('- Read frequency (V0.6), persistence, lineup use, and captured impact together.')
print('- If a position generates many shocks but little post-trigger persistence/capture, treat that as weak optionality evidence.')
print('- No market appreciation is inferred.')
print(f'\nCreated: {OUT_DETAIL.name}')
print(f'Created: {OUT_SUM.name}')
