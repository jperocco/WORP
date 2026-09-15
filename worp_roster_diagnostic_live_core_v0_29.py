#!/usr/bin/env python3
"""WoRP Lab V0.29 — live roster Scoring-core diagnostic.

Consumes V0.28 live league-native player economics plus frozen V0.24
construction envelopes. For each READY current roster, test every supported
Scoring-core total for its exact format by retaining the roster's best realized
2026 positional WoRP ranks and asking whether that positional composition can
sit inside the decision-equivalent envelope.

This is a diagnostic bridge, not a player valuation model:
- no asset value;
- no universal raw-rank cutline;
- no buy/sell/drop action;
- current 2026 realized WoRP is used only to order which rostered players would
  occupy a candidate Scoring core;
- supported core totals remain a range, not an exact prescription.
"""
from pathlib import Path
import pandas as pd
import numpy as np

LIVE=Path('worp_roster_diagnostic_live_economics_v0_28.csv')
ENV=Path('worp_scoring_core_decision_equivalence_envelopes_v0_24.csv')
OUT=Path('worp_roster_diagnostic_live_core_v0_29.csv')
OUT_SUM=Path('worp_roster_diagnostic_live_core_summary_v0_29.csv')
POS=('QB','RB','WR','TE')

def main():
    for p in (LIVE,ENV):
        if not p.exists(): raise SystemExit(f'Missing {p}')
    live=pd.read_csv(LIVE,dtype={'league_id':str,'player_id':str})
    env=pd.read_csv(ENV)
    rows=[]
    for (lid,name,fmt),r in live.groupby(['league_id','league_name','format_key'],sort=True):
        ee=env[env.format_key.eq(fmt)].copy()
        if ee.empty: continue
        rr=r.sort_values(['season_worp','mean_weekly_worp','pos_rank'],ascending=[False,False,True],kind='mergesort')
        for _,e in ee.sort_values('scoring_total').iterrows():
            total=int(e.scoring_total)
            if len(rr)<total: continue
            core=rr.head(total)
            counts=core.position.value_counts().to_dict()
            flags=[]; states={}; inside=True
            for p in POS:
                n=int(counts.get(p,0)); lo=e.get(f'{p}_low_050',np.nan); hi=e.get(f'{p}_high_050',np.nan)
                if pd.isna(lo) or pd.isna(hi): state='NO_ENVELOPE'; inside=False
                elif n<int(lo): state='BELOW'; flags.append(f'{p}_BELOW'); inside=False
                elif n>int(hi): state='ABOVE'; flags.append(f'{p}_ABOVE'); inside=False
                else: state='INSIDE'
                states[p]=(n,lo,hi,state)
            rows.append({
                'league_id':lid,'league_name':name,'format_key':fmt,
                'rostered_offense':len(rr),'candidate_scoring_total':total,
                'core_realized_worp':float(core.season_worp.sum()),
                'composition_state':'INSIDE_DECISION_EQUIVALENT_ENVELOPE' if inside else 'OUTSIDE_ENVELOPE',
                'flags':';'.join(flags),
                **{f'{p}_count':states[p][0] for p in POS},
                **{f'{p}_low':states[p][1] for p in POS},
                **{f'{p}_high':states[p][2] for p in POS},
                **{f'{p}_state':states[p][3] for p in POS},
                'core_players':' | '.join(f"{x.position}:{x.player_name}({int(x.pos_rank) if pd.notna(x.pos_rank) else '?'})" for _,x in core.iterrows())
            })
    o=pd.DataFrame(rows); o.to_csv(OUT,index=False)
    if o.empty:
        print('No live core diagnostics produced.'); return
    sumrows=[]
    for (lid,name,fmt),g in o.groupby(['league_id','league_name','format_key'],sort=True):
        good=g[g.composition_state.eq('INSIDE_DECISION_EQUIVALENT_ENVELOPE')]
        # `DataFrame.flags` is a pandas metadata attribute, so column access must
        # use brackets here. Attribute access silently resolves to pandas Flags.
        flag_values=g['flags'].fillna('')
        flags_seen=';'.join(sorted(set(x for z in flag_values for x in str(z).split(';') if x)))
        sumrows.append({'league_id':lid,'league_name':name,'format_key':fmt,
            'candidate_totals':','.join(map(str,sorted(g.candidate_scoring_total.unique()))),
            'inside_totals':','.join(map(str,sorted(good.candidate_scoring_total.unique()))),
            'diagnostic_state':'HAS_DECISION_EQUIVALENT_CORE' if not good.empty else 'NO_CANDIDATE_CORE_INSIDE_ENVELOPE',
            'flags_seen':flags_seen})
    s=pd.DataFrame(sumrows); s.to_csv(OUT_SUM,index=False)
    print('V0.29 LIVE ROSTER SCORING-CORE DIAGNOSTIC')
    print(f'Current rosters diagnosed: {len(s)} | has decision-equivalent core: {(s.diagnostic_state=="HAS_DECISION_EQUIVALENT_CORE").sum()} | none inside: {(s.diagnostic_state=="NO_CANDIDATE_CORE_INSIDE_ENVELOPE").sum()}')
    print('\nCORE-CANDIDATE STATES')
    print(o.composition_state.value_counts().to_string())
    print('\nPOSITION FLAGS ACROSS CANDIDATES')
    for p in POS:
        print(f'{p}: '+', '.join(f'{k}={v}' for k,v in o[p+"_state"].value_counts().items()))
    print('\nROSTER SUMMARY')
    print(s[['league_name','candidate_totals','inside_totals','diagnostic_state','flags_seen']].to_string(index=False))
    print(f'\nCreated:\n- {OUT}\n- {OUT_SUM}')
    print('\nREADING CONTRACT')
    print('- V0.29 applies only frozen exact-format V0.24 envelopes to V0.28 live league-native economics.')
    print('- It tests ALL supported Scoring-core totals for the format; it does not choose one magic total.')
    print('- Players are ordered by realized 2026 league-native WoRP only to form candidate cores; this is not a future projection or dynasty value.')
    print('- INSIDE means at least that candidate positional composition is structurally decision-equivalent under the frozen evidence.')
    print('- OUTSIDE/ABOVE/BELOW is a roster-structure flag, not buy/sell/drop advice.')
    print('- If multiple totals are INSIDE, preserve the range; do not optimize the boundary.')
    print('- Asset value remains out of scope.')
if __name__=='__main__': main()
