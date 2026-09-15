#!/usr/bin/env python3
"""WoRP Lab V0.30 — live diagnostic stability gate.

V0.29 showed many current rosters outside frozen decision-equivalent envelopes.
Before turning those flags into product diagnostics, test whether the conclusion
is stable across candidate Scoring-core totals. This prevents one boundary/tie
from becoming a fake roster story.

No new economic threshold is introduced. The gate asks only whether a position
is consistently ABOVE/BELOW/INSIDE across the already-supported total range.
"""
from pathlib import Path
import pandas as pd

IN=Path('worp_roster_diagnostic_live_core_v0_29.csv')
OUT=Path('worp_roster_diagnostic_live_stability_v0_30.csv')
POS=('QB','RB','WR','TE')

def classify(vals):
    vals=[str(x) for x in vals if pd.notna(x)]
    u=set(vals)
    if len(u)==1:return 'STABLE_'+next(iter(u))
    # If the sign changes across supported totals, do not publish a directional story.
    if 'ABOVE' in u and 'BELOW' in u:return 'UNSTABLE_DIRECTION'
    return 'BOUNDARY_SENSITIVE'

def main():
    if not IN.exists():raise SystemExit(f'Missing {IN}; run V0.29 first.')
    d=pd.read_csv(IN,dtype={'league_id':str})
    rows=[]
    for (lid,name,fmt),g in d.groupby(['league_id','league_name','format_key'],sort=True):
        row={'league_id':lid,'league_name':name,'format_key':fmt,
             'candidate_totals':','.join(map(str,sorted(g.candidate_scoring_total.unique()))),
             'inside_totals':','.join(map(str,sorted(g.loc[g.composition_state.eq('INSIDE_DECISION_EQUIVALENT_ENVELOPE'),'candidate_scoring_total'].unique())))}
        publish=[]; suppress=[]
        for p in POS:
            st=classify(g[p+'_state'].tolist()); row[p+'_stability']=st
            if st in ('STABLE_ABOVE','STABLE_BELOW'):publish.append(p+'_'+st.replace('STABLE_',''))
            elif st!='STABLE_INSIDE':suppress.append(p+'_'+st)
        row['stable_directional_flags']=';'.join(publish)
        row['suppressed_boundary_flags']=';'.join(suppress)
        row['diagnostic_confidence']='STABLE_DIRECTIONAL_SIGNAL' if publish else ('STRUCTURALLY_INSIDE' if all(row[p+'_stability']=='STABLE_INSIDE' for p in POS) else 'NO_STABLE_DIRECTIONAL_SIGNAL')
        rows.append(row)
    o=pd.DataFrame(rows);o.to_csv(OUT,index=False)
    print('V0.30 LIVE DIAGNOSTIC STABILITY GATE')
    print(f'Rosters: {len(o)}')
    print('\nDIAGNOSTIC CONFIDENCE')
    print(o.diagnostic_confidence.value_counts().to_string())
    print('\nSTABLE DIRECTIONAL FLAGS')
    exploded=[]
    for x in o.stable_directional_flags.fillna(''):
        exploded += [z for z in x.split(';') if z]
    print(pd.Series(exploded).value_counts().to_string() if exploded else 'none')
    print('\nPOSITION STABILITY')
    for p in POS:print(p+': '+', '.join(f'{k}={v}' for k,v in o[p+'_stability'].value_counts().items()))
    print(f'\nCreated:\n- {OUT}')
    print('\nREADING CONTRACT')
    print('- Stable directional flag = same ABOVE or BELOW conclusion across every supported Scoring-core total for that current league.')
    print('- Boundary-sensitive or direction-changing flags are suppressed from product interpretation.')
    print('- This adds no new WoRP threshold and does not refine frozen V0.24 boundaries.')
    print('- A stable structural flag is still not buy/sell/drop advice; it is evidence for roster-balance diagnosis.')
    print('- Next gate should inspect named-player membership only for stable signals and preserve range uncertainty.')
if __name__=='__main__':main()
