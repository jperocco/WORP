#!/usr/bin/env python3
"""WoRP Lab V0.32 — Roster Construction / Diagnostic closeout.

Product-facing structural artifact. No player names. No asset value.
Consumes the frozen V0.24 decision-equivalent envelopes and V0.30 live
stability output to produce league-native positional construction ranges and a
compact validation summary. This closes the roster-construction research loop;
it does not reopen boundary optimization.
"""
from pathlib import Path
import pandas as pd

ENV=Path('worp_scoring_core_decision_equivalence_envelopes_v0_24.csv')
STAB=Path('worp_roster_diagnostic_live_stability_v0_30.csv')
OUT=Path('worp_roster_construction_product_ranges_v0_32.csv')
SUMMARY=Path('worp_roster_construction_closeout_summary_v0_32.csv')
POS=('QB','RB','WR','TE')

def main():
    for p in (ENV,STAB):
        if not p.exists(): raise SystemExit(f'Missing {p}')
    e=pd.read_csv(ENV); s=pd.read_csv(STAB,dtype={'league_id':str})
    rows=[]
    for fmt,g in e.groupby('format_key',sort=True):
        totals=sorted(g.scoring_total.astype(int).unique())
        row={'format_key':fmt,'scoring_core_low':min(totals),'scoring_core_high':max(totals)}
        for p in POS:
            row[p+'_low']=int(g[p+'_low_050'].min())
            row[p+'_high']=int(g[p+'_high_050'].max())
        rows.append(row)
    ranges=pd.DataFrame(rows); ranges.to_csv(OUT,index=False)
    # Live validation is descriptive only: how often current supported rosters
    # yield stable structural information after boundary-sensitive suppression.
    n=len(s); stable=int(s.diagnostic_confidence.eq('STABLE_DIRECTIONAL_SIGNAL').sum()); inside=int(s.diagnostic_confidence.eq('STRUCTURALLY_INSIDE').sum()); ambiguous=int(s.diagnostic_confidence.eq('NO_STABLE_DIRECTIONAL_SIGNAL').sum())
    summary=pd.DataFrame([{'supported_live_rosters':n,'stable_directional_signal':stable,'structurally_inside':inside,'no_stable_directional_signal':ambiguous,'actionable_or_inside':stable+inside,'actionable_or_inside_share':(stable+inside)/n if n else 0,'product_formats':len(ranges)}])
    summary.to_csv(SUMMARY,index=False)
    print('V0.32 ROSTER CONSTRUCTION / DIAGNOSTIC CLOSEOUT')
    print(f'Product format ranges: {len(ranges)}')
    print(f'Live supported rosters: {n} | stable directional: {stable} | structurally inside: {inside} | suppressed/ambiguous: {ambiguous}')
    print(f'Usable structural read: {stable+inside}/{n} ({(stable+inside)/n:.1%})' if n else 'Usable structural read: n/a')
    print('\nCreated:')
    print(f'- {OUT}')
    print(f'- {SUMMARY}')
    print('\nCLOSEOUT CONTRACT')
    print('- WoRP Roster Construction is positional and league-native; player identity is out of scope.')
    print('- Output is a range/envelope, never an exact positional quota.')
    print('- Independent positional lows/highs are constraints, not additive quotas.')
    print('- Boundary-sensitive live signals are suppressed, not optimized further.')
    print('- Non-Scoring capacity remains optionality capacity once the meaningful Scoring range is satisfied.')
    print('- No asset value, buy/sell/drop, dynasty ranking, or named-player membership is inferred.')
    print('- V0.24 positional composition research remains frozen. V0.32 is the closeout artifact, not a new threshold study.')
    print('- Next work belongs to product integration / Roster Diagnostic presentation, not more Roster Construction research.')
if __name__=='__main__': main()
