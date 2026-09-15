#!/usr/bin/env python3
"""WoRP Lab V0.26 — actual-roster diagnostic snapshot.

First player-level bridge from frozen league-native Roster Construction into
Roster Diagnostic.

Scope is deliberately narrow:
- supported exact formats only (V0.25);
- historical league-season snapshots already represented in our Sleeper universe;
- classify rostered offensive players by league-native season positional WoRP
  rank against the broad material Scoring frontier evidence;
- compare each roster's Scoring count/composition to V0.24 decision-equivalent
  envelopes at supported core totals;
- report diagnostics, not trade/asset-value recommendations.

No asset value. No universal raw-rank threshold. No forced exact quotas.
"""
from pathlib import Path
import pandas as pd
import numpy as np

PREF=Path('worp_roster_diagnostic_preflight_v0_25.csv')
ENV=Path('worp_scoring_core_decision_equivalence_envelopes_v0_24.csv')
# V0.20 detail contains league-season/family empirical support; use its roster
# identifiers only as the supported historical universe, not as player roster.
DETAIL20=Path('worp_scoring_core_positional_family_detail_v0_20.csv')
OUT=Path('worp_roster_diagnostic_snapshot_v0_26.csv')
OUT_SUM=Path('worp_roster_diagnostic_snapshot_summary_v0_26.csv')
POS=['QB','RB','WR','TE']


def choose_env(e, fmt, observed_total):
    g=e[e.format_key.eq(fmt)].copy()
    if g.empty: return None
    g['dist']=(g.scoring_total-observed_total).abs()
    # diagnostic nearest supported total; caller marks exact vs nearest.
    return g.sort_values(['dist','scoring_total']).iloc[0]


def main():
    for p in (PREF,ENV,DETAIL20):
        if not p.exists(): raise SystemExit(f'Missing {p}')
    p=pd.read_csv(PREF,dtype={'league_id':str})
    e=pd.read_csv(ENV)
    d=pd.read_csv(DETAIL20,dtype={'league_id':str})
    supported=p[p.diagnostic_support.eq('DIRECT_EXACT_FORMAT')].copy()

    # V0.20 detail is family-level, so recover the best-observed positional
    # family per real league-season/core total as a diagnostic proxy. This does
    # NOT yet reconstruct current player names; it validates the roster-level
    # diagnostic grammar before live/current snapshot plumbing.
    keys=['format_key','league_id','season','scoring_total']
    best=(d.sort_values('mean_lost').groupby(keys,as_index=False).first())
    rows=[]
    for _,r in best.iterrows():
        env=choose_env(e,r.format_key,int(r.scoring_total))
        if env is None: continue
        row={
            'league_id':r.league_id,'season':int(r.season),'format_key':r.format_key,
            'observed_scoring_total':int(r.scoring_total),
            'reference_scoring_total':int(env.scoring_total),
            'total_support':'EXACT_TOTAL' if int(r.scoring_total)==int(env.scoring_total) else 'NEAREST_SUPPORTED_TOTAL',
            'oracle_mean_lost':float(r.mean_lost),
        }
        inside_all=True
        flags=[]
        for pos in POS:
            n=int(r[pos]); lo=env.get(f'{pos}_low_050',np.nan); hi=env.get(f'{pos}_high_050',np.nan)
            row[pos+'_count']=n; row[pos+'_low']=lo; row[pos+'_high']=hi
            if pd.isna(lo) or pd.isna(hi): state='NO_ENVELOPE'
            elif n<lo: state='BELOW'
            elif n>hi: state='ABOVE'
            else: state='INSIDE'
            row[pos+'_state']=state
            if state!='INSIDE': inside_all=False
            if state in ('BELOW','ABOVE'): flags.append(f'{pos}_{state}')
        row['composition_state']='INSIDE_DECISION_EQUIVALENT_ENVELOPE' if inside_all else 'OUTSIDE_ENVELOPE'
        row['flags']=';'.join(flags)
        rows.append(row)
    o=pd.DataFrame(rows)
    o.to_csv(OUT,index=False)
    if o.empty:
        print('No supported diagnostic rows.'); return
    s=(o.groupby(['format_key','observed_scoring_total','composition_state'],as_index=False)
       .agg(league_season_cores=('league_id','size'),mean_oracle_loss=('oracle_mean_lost','mean')))
    s.to_csv(OUT_SUM,index=False)
    print('V0.26 ROSTER DIAGNOSTIC SNAPSHOT — STRUCTURAL BRIDGE')
    print(f'League-season/core observations: {len(o)}')
    print(o.composition_state.value_counts().to_string())
    print('\nPOSITION FLAGS')
    for pos in POS:
        print(f'{pos}: '+', '.join(f'{k}={v}' for k,v in o[pos+'_state'].value_counts().items()))
    print('\nCreated:')
    print(f'- {OUT}\n- {OUT_SUM}')
    print('\nREADING CONTRACT')
    print('- This is the first roster-diagnostic structural bridge, not yet a live named-player diagnostic.')
    print('- It uses only exact-format-supported league-seasons from V0.25.')
    print('- V0.24 .050 envelope is used because .050 and .100 were decision-identical in 58/58 groups; this is a frozen decision-equivalence view, not a universal WoRP materiality threshold.')
    print('- Positional bounds are envelope constraints, not additive quotas.')
    print('- ABOVE/BELOW means outside the decision-equivalent positional envelope for that supported Scoring-core total; it does not mean buy/sell/drop.')
    print('- Asset value remains out of scope.')
    print('- Next gate is live/current roster plumbing only after this diagnostic grammar behaves coherently.')

if __name__=='__main__': main()
