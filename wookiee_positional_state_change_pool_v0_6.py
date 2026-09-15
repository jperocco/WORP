#!/usr/bin/env python3
"""
Wookiee Positional State-Change Pool Audit V0.6

Question
--------
For a reasonably broad pool of low-current-use rostered players at each position,
how often does the POSITIONAL POOL generate a materially superior WoRP regime,
how persistent is that regime, and how much of its value is actually captured?

Design principles
-----------------
1. Pool-first, not arbitrary WR60/RB50/etc cutoffs.
2. Pregame eligibility only: pool membership uses prior observations / prior WoRP /
   prior REAL and ORACLE use, never target-week outcomes.
3. Do not hard-code "very superior WoRP" before seeing the positional distribution.
   We report the full distribution and percentile-based shock thresholds (P75/P85/P90)
   within position as sensitivity landmarks, not semantic truth.
4. A one-week spike is separated from a persistent regime change.
5. Produced WoRP and captured WoRP are separate. Captured means REAL_STARTED only.
6. This is sporting-value research only. Trade/market appreciation is not measured.

Inputs (local)
--------------
wookiee_ex_ante_lineup_player_week_v0_6.csv

Outputs
-------
wookiee_positional_state_change_pool_detail_v0_6.csv
wookiee_positional_state_change_events_v0_6.csv
wookiee_positional_state_change_summary_v0_6.csv
wookiee_positional_state_change_threshold_sensitivity_v0_6.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path('wookiee_ex_ante_lineup_player_week_v0_6.csv')
OUT_DETAIL = Path('wookiee_positional_state_change_pool_detail_v0_6.csv')
OUT_EVENTS = Path('wookiee_positional_state_change_events_v0_6.csv')
OUT_SUMMARY = Path('wookiee_positional_state_change_summary_v0_6.csv')
OUT_SENS = Path('wookiee_positional_state_change_threshold_sensitivity_v0_6.csv')
POSITIONS = ['QB','RB','WR','TE']
LOOKBACK = 5
MIN_PRIOR_OBS = 2
PCTS = [0.75,0.85,0.90]
PRIMARY_PCT = 0.85
POST_WEEKS = 3


def as_bool(s):
    if s.dtype == bool:
        return s
    return s.astype(str).str.lower().isin(['true','1','yes'])


def safe_div(a,b):
    return float(a/b) if b else np.nan


def main():
    if not BASE.exists():
        raise SystemExit(f'STOP: required input missing: {BASE}')
    d = pd.read_csv(BASE)
    need = {'season','week','roster_id','player_id','player_name','position','weekly_worp','real_started','oracle_started'}
    miss = need - set(d.columns)
    if miss:
        raise SystemExit(f'STOP: base missing columns: {sorted(miss)}')
    d = d[d.position.isin(POSITIONS)].copy()
    d['real_started'] = as_bool(d.real_started)
    d['oracle_started'] = as_bool(d.oracle_started)
    d['weekly_worp'] = pd.to_numeric(d.weekly_worp, errors='coerce').fillna(0.0)
    d = d.sort_values(['season','roster_id','player_id','week']).drop_duplicates(['season','week','roster_id','player_id'],keep='last')
    gcols=['season','roster_id','player_id']

    # Pregame pool signals.
    d['prior_obs'] = d.groupby(gcols).cumcount()
    d['prior_real_l5'] = d.groupby(gcols)['real_started'].transform(lambda s:s.astype(int).shift(1).rolling(LOOKBACK,min_periods=1).sum())
    d['prior_oracle_l5'] = d.groupby(gcols)['oracle_started'].transform(lambda s:s.astype(int).shift(1).rolling(LOOKBACK,min_periods=1).sum())
    d['prior_worp_l5'] = d.groupby(gcols)['weekly_worp'].transform(lambda s:s.shift(1).rolling(LOOKBACK,min_periods=1).mean())

    # Broad low-current-use pool. We deliberately avoid rank cutoffs. A player enters
    # after at least 2 prior observations and no REAL/ORACLE selection in the recent
    # window. This is the validated V0.4 conservative proxy architecture.
    d['pool_eligible'] = (
        (d.prior_obs >= MIN_PRIOR_OBS) &
        (d.prior_real_l5.fillna(0)==0) &
        (d.prior_oracle_l5.fillna(0)==0)
    )
    pool=d[d.pool_eligible].copy()
    if pool.empty:
        raise SystemExit('STOP: positional pool is empty.')

    # Improvement over player's own recent baseline. This avoids using the same raw
    # WoRP hurdle for positions with different economics.
    pool['worp_delta_vs_prior'] = pool.weekly_worp - pool.prior_worp_l5.fillna(0)
    pool['positive_worp'] = pool.weekly_worp.clip(lower=0)

    # Positional shock thresholds are descriptive percentiles of positive deltas.
    thresholds=[]
    for pos,g in pool.groupby('position'):
        positive_delta=g.loc[g.worp_delta_vs_prior>0,'worp_delta_vs_prior']
        for p in PCTS:
            thresholds.append({'position':pos,'percentile':p,'delta_threshold':positive_delta.quantile(p) if len(positive_delta) else np.nan})
    th=pd.DataFrame(thresholds)
    primary=th[th.percentile.eq(PRIMARY_PCT)][['position','delta_threshold']].rename(columns={'delta_threshold':'primary_delta_threshold'})
    pool=pool.merge(primary,on='position',how='left',validate='many_to_one')
    pool['primary_shock']=(pool.worp_delta_vs_prior>=pool.primary_delta_threshold) & (pool.weekly_worp>0)

    # Build event windows from each shock. Overlapping shocks for same player are
    # de-duplicated: once an event opens, another trigger inside its post window is
    # not counted as a new state-change opportunity.
    all_rows=d.set_index(['season','roster_id','player_id','week'])
    events=[]
    last_end={}
    for r in pool[pool.primary_shock].sort_values(['season','roster_id','player_id','week']).itertuples():
        key=(r.season,r.roster_id,r.player_id)
        if key in last_end and r.week <= last_end[key]:
            continue
        weeks=list(range(int(r.week),int(r.week)+POST_WEEKS))
        xs=[]
        for w in weeks:
            idx=(r.season,r.roster_id,r.player_id,w)
            if idx in all_rows.index:
                z=all_rows.loc[idx]
                if isinstance(z,pd.DataFrame): z=z.iloc[-1]
                xs.append((w,z))
        if not xs:
            continue
        produced=sum(max(float(z.weekly_worp),0) for _,z in xs)
        captured=sum(max(float(z.weekly_worp),0) for _,z in xs if bool(z.real_started))
        positive_weeks=sum(float(z.weekly_worp)>0 for _,z in xs)
        real_start_weeks=sum(bool(z.real_started) for _,z in xs)
        oracle_weeks=sum(bool(z.oracle_started) for _,z in xs)
        # Persistence is outcome evidence, not an ex-ante state label: at least 2
        # observed post-window weeks with positive WoRP OR at least 2 REAL starts.
        persistent=(positive_weeks>=2) or (real_start_weeks>=2)
        events.append({
            'season':r.season,'roster_id':r.roster_id,'player_id':r.player_id,
            'player_name':r.player_name,'position':r.position,'trigger_week':r.week,
            'prior_worp_l5':r.prior_worp_l5,'trigger_worp':r.weekly_worp,
            'delta_vs_prior':r.worp_delta_vs_prior,'delta_threshold':r.primary_delta_threshold,
            'observed_event_weeks':len(xs),'positive_event_weeks':positive_weeks,
            'real_start_event_weeks':real_start_weeks,'oracle_event_weeks':oracle_weeks,
            'persistent_regime_proxy':persistent,'positive_worp_produced':produced,
            'positive_worp_captured':captured,
            'capture_share':safe_div(captured,produced),
        })
        last_end[key]=int(r.week)+POST_WEEKS-1
    ev=pd.DataFrame(events)
    if ev.empty:
        raise SystemExit('STOP: no primary shock events detected.')

    # Position-level impact. Pool exposure is the denominator the user asked for:
    # how often the positional set creates a material change opportunity.
    rows=[]
    for pos in POSITIONS:
        p=pool[pool.position.eq(pos)]
        e=ev[ev.position.eq(pos)]
        pe=e[e.persistent_regime_proxy]
        rows.append({
            'position':pos,
            'pool_player_weeks':len(p),
            'unique_pool_players':p.player_id.nunique(),
            'material_shock_events':len(e),
            'shock_events_per_100_pool_weeks':100*safe_div(len(e),len(p)),
            'persistent_events':len(pe),
            'persistent_events_per_100_pool_weeks':100*safe_div(len(pe),len(p)),
            'persistent_share_of_events':safe_div(len(pe),len(e)),
            'mean_event_positive_worp_produced':e.positive_worp_produced.mean(),
            'median_event_positive_worp_produced':e.positive_worp_produced.median(),
            'mean_event_positive_worp_captured':e.positive_worp_captured.mean(),
            'median_event_positive_worp_captured':e.positive_worp_captured.median(),
            'total_positive_worp_produced':e.positive_worp_produced.sum(),
            'total_positive_worp_captured':e.positive_worp_captured.sum(),
            'captured_worp_per_100_pool_weeks':100*safe_div(e.positive_worp_captured.sum(),len(p)),
            'produced_worp_per_100_pool_weeks':100*safe_div(e.positive_worp_produced.sum(),len(p)),
            'event_capture_share':safe_div(e.positive_worp_captured.sum(),e.positive_worp_produced.sum()),
        })
    summary=pd.DataFrame(rows)

    # Threshold sensitivity: if the positional story flips wildly between P75/P85/P90,
    # we stop before claiming a robust hierarchy.
    sens=[]
    for pos in POSITIONS:
        p=pool[pool.position.eq(pos)]
        for pct in PCTS:
            threshold=th[(th.position.eq(pos))&(th.percentile.eq(pct))].delta_threshold.iloc[0]
            hits=p[(p.worp_delta_vs_prior>=threshold)&(p.weekly_worp>0)]
            sens.append({
                'position':pos,'percentile':pct,'delta_threshold':threshold,
                'pool_player_weeks':len(p),'shock_player_weeks':len(hits),
                'shock_rate_per_100_pool_weeks':100*safe_div(len(hits),len(p)),
                'median_trigger_worp':hits.weekly_worp.median() if len(hits) else np.nan,
                'median_delta_vs_prior':hits.worp_delta_vs_prior.median() if len(hits) else np.nan,
            })
    sens=pd.DataFrame(sens)

    pool.to_csv(OUT_DETAIL,index=False)
    ev.to_csv(OUT_EVENTS,index=False)
    summary.to_csv(OUT_SUMMARY,index=False)
    sens.to_csv(OUT_SENS,index=False)

    print('=== POSITIONAL STATE-CHANGE POOL AUDIT V0.6 ===')
    print(f'Pool definition: >= {MIN_PRIOR_OBS} prior observations + 0 REAL/ORACLE selections in prior {LOOKBACK} weeks')
    print(f'Primary material-shock landmark: within-position P{int(PRIMARY_PCT*100)} positive WoRP delta vs own prior-{LOOKBACK} baseline')
    print(f'Impact window: trigger week + next {POST_WEEKS-1} weeks; overlapping events de-duplicated\n')
    print('POSITION SUMMARY')
    print(summary.round(4).to_string(index=False))
    print('\nTHRESHOLD SENSITIVITY')
    print(sens.round(4).to_string(index=False))
    print('\nGUARDRAILS')
    print('- Percentile shock thresholds are distributional landmarks, not final state definitions.')
    print('- Persistent regime is an ex-post impact proxy, not proof of an NFL role change.')
    print('- Pool frequency + persistence + produced/captured impact should be read together.')
    print('- No market/trade appreciation is measured.')
    print('- If positional ordering is unstable across P75/P85/P90 or driven by tiny samples, STOP before roster prescription.')
    print(f'\nCreated: {OUT_DETAIL.name}')
    print(f'Created: {OUT_EVENTS.name}')
    print(f'Created: {OUT_SUMMARY.name}')
    print(f'Created: {OUT_SENS.name}')

if __name__=='__main__':
    main()
