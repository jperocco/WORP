#!/usr/bin/env python3
"""WoRP Lab V0.25 — league-native Roster Diagnostic preflight.

This is the bridge from frozen Roster Construction research to actual roster
diagnostics. It does NOT invent player asset values or exact positional quotas.

What it does
------------
1. Reads the frozen V0.24 decision-equivalence envelopes.
2. Reads V0.15 league-season observations (the known Sleeper universe).
3. Matches real league formats to empirically supported construction envelopes.
4. Reports which league-seasons can receive a direct league-native diagnostic,
   which need nearest-family borrowing, and which remain unsupported.
5. For direct matches, exposes BOTH supported Scoring totals and their broad
   positional envelopes. Positional highs are never summed as quotas.

This is intentionally a preflight: before diagnosing a real roster, we verify
that the league's own structure is represented by evidence rather than silently
applying Wookiee or a universal template.
"""
from pathlib import Path
import pandas as pd

ENV=Path('worp_scoring_core_decision_equivalence_envelopes_v0_24.csv')
OBS=Path('worp_multileague_validation_observations_v0_15.csv')
OUT=Path('worp_roster_diagnostic_preflight_v0_25.csv')
OUT_SUM=Path('worp_roster_diagnostic_preflight_summary_v0_25.csv')
POS=['QB','RB','WR','TE']


def main():
    if not ENV.exists(): raise SystemExit(f'Missing {ENV}; run V0.24 first.')
    if not OBS.exists(): raise SystemExit(f'Missing {OBS}; run V0.15 preflight first.')
    e=pd.read_csv(ENV)
    o=pd.read_csv(OBS,dtype={'league_id':str,'lineage_root':str})
    # V0.24 format_key is the exact league-native structural signature used by
    # the empirical construction research. Direct match is the only status that
    # may feed an automatic roster diagnostic in this version.
    supported=set(e.format_key.astype(str))
    rows=[]
    for _,r in o.iterrows():
        fmt=str(r.get('format_key',''))
        direct=fmt in supported
        er=e[e.format_key.astype(str).eq(fmt)].sort_values('scoring_total') if direct else pd.DataFrame()
        row={
            'league_id':str(r.get('league_id','')),
            'season':int(r.get('season')) if pd.notna(r.get('season')) else None,
            'lineage_root':str(r.get('lineage_root','')),
            'format_key':fmt,
            'diagnostic_support':'DIRECT_EXACT_FORMAT' if direct else 'UNSUPPORTED_NO_AUTOMATIC_DIAGNOSTIC',
            'supported_scoring_totals':'' if not direct else '|'.join(str(int(x)) for x in er.scoring_total.tolist()),
            'n_supported_totals':0 if not direct else len(er),
        }
        if direct:
            # Union across the frozen low/high total candidates gives a broad
            # construction envelope for preflight display only. The eventual
            # roster diagnostic must evaluate the roster against each supported
            # total separately before producing an action.
            for p in POS:
                lows=er[f'{p}_low_050'].dropna(); highs=er[f'{p}_high_050'].dropna()
                row[f'{p}_broad_low']=None if lows.empty else int(lows.min())
                row[f'{p}_broad_high']=None if highs.empty else int(highs.max())
            row['all_ranges_stable_050_to_100']=bool(er.range_stable_050_to_100.all())
            row['construction_statuses']='|'.join(sorted(set(er.status.astype(str))))
        else:
            for p in POS: row[f'{p}_broad_low']=row[f'{p}_broad_high']=None
            row['all_ranges_stable_050_to_100']=False
            row['construction_statuses']=''
        rows.append(row)
    d=pd.DataFrame(rows)
    d.to_csv(OUT,index=False)
    s=(d.groupby(['season','diagnostic_support'],dropna=False).size().reset_index(name='league_seasons'))
    s.to_csv(OUT_SUM,index=False)
    print('V0.25 LEAGUE-NATIVE ROSTER DIAGNOSTIC PREFLIGHT')
    print(f'League-seasons: {len(d)} | exact-format supported: {(d.diagnostic_support=="DIRECT_EXACT_FORMAT").sum()} | unsupported: {(d.diagnostic_support!="DIRECT_EXACT_FORMAT").sum()}')
    print(f'Unique exact formats in observed universe: {d.format_key.nunique()} | directly supported formats: {d[d.diagnostic_support=="DIRECT_EXACT_FORMAT"].format_key.nunique()}')
    print('\nBY SEASON')
    print(s.to_string(index=False))
    print('\nDIRECT-SUPPORT FORMAT COVERAGE')
    x=(d[d.diagnostic_support.eq('DIRECT_EXACT_FORMAT')].groupby('format_key').size().sort_values(ascending=False).reset_index(name='league_seasons'))
    print(x.to_string(index=False))
    print('\nCreated:')
    print(f'- {OUT}\n- {OUT_SUM}')
    print('\nREADING CONTRACT')
    print('- DIRECT_EXACT_FORMAT means the real league structure has empirical V0.24 construction evidence.')
    print('- Unsupported leagues are NOT silently mapped to Wookiee or a universal template.')
    print('- V0.25 does not diagnose players yet; it validates the league-native evidence layer first.')
    print('- Supported Scoring totals remain ranges/candidates, not exact roster-size prescriptions.')
    print('- Positional lows/highs are independent envelope bounds and must not be summed as quotas.')
    print('- Next diagnostic layer may classify an actual roster only after exact-format support is established.')

if __name__=='__main__': main()
