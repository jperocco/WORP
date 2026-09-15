#!/usr/bin/env python3
"""WoRP Lab V0.31 — named-player membership for stable live diagnostics.

Attach names to V0.30 stable structural signals without turning names into
asset recommendations. For each stable ABOVE/BELOW position, report robust
candidate-core membership across all supported Scoring-core totals:
- ALWAYS_CORE: player is in every candidate core;
- SOMETIMES_CORE: player is only in some candidate cores;
- NEVER_CORE rostered players are omitted from the compact diagnostic.

This preserves uncertainty across the frozen core-total range and avoids
pretending a single boundary is exact.
"""
from pathlib import Path
import pandas as pd

CORE=Path('worp_roster_diagnostic_live_core_v0_29.csv')
STAB=Path('worp_roster_diagnostic_live_stability_v0_30.csv')
LIVE=Path('worp_roster_diagnostic_live_economics_v0_28.csv')
OUT=Path('worp_roster_diagnostic_named_membership_v0_31.csv')
POS=('QB','RB','WR','TE')

def parse_core(s):
    # V0.29 serializes `POS:Name(rank)` separated by pipes. Player names can
    # contain punctuation, so membership is matched back to V0.28 by the exact
    # `POS:player_name(` prefix rather than trying to parse rank text.
    return str(s or '')

def main():
    for p in (CORE,STAB,LIVE):
        if not p.exists():raise SystemExit(f'Missing {p}')
    c=pd.read_csv(CORE,dtype={'league_id':str}); s=pd.read_csv(STAB,dtype={'league_id':str}); l=pd.read_csv(LIVE,dtype={'league_id':str,'player_id':str})
    rows=[]
    for _,sr in s[s.diagnostic_confidence.eq('STABLE_DIRECTIONAL_SIGNAL')].iterrows():
        lid=sr.league_id; cg=c[c.league_id.eq(lid)]; lr=l[l.league_id.eq(lid)]
        totals=sorted(cg.candidate_scoring_total.unique()); nt=len(totals)
        for p in POS:
            st=sr[p+'_stability']
            if st not in ('STABLE_ABOVE','STABLE_BELOW'):continue
            pr=lr[lr.position.eq(p)].copy()
            for _,x in pr.iterrows():
                needle=f'{p}:{x.player_name}('
                present=sum(needle in parse_core(z) for z in cg.core_players)
                if present==0:continue
                membership='ALWAYS_CORE' if present==nt else 'SOMETIMES_CORE'
                rows.append({'league_id':lid,'league_name':sr.league_name,'format_key':sr.format_key,
                    'position':p,'structural_signal':st.replace('STABLE_',''),'player_id':x.player_id,'player_name':x.player_name,
                    'pos_rank':x.pos_rank,'season_worp':x.season_worp,'mean_weekly_worp':x.mean_weekly_worp,
                    'candidate_totals':sr.candidate_totals,'core_membership':membership,'cores_present':present,'cores_tested':nt})
    o=pd.DataFrame(rows)
    if not o.empty:o=o.sort_values(['league_name','position','core_membership','season_worp'],ascending=[True,True,True,False])
    o.to_csv(OUT,index=False)
    print('V0.31 NAMED-PLAYER DIAGNOSTIC MEMBERSHIP')
    print(f'Stable-signal leagues: {s.diagnostic_confidence.eq("STABLE_DIRECTIONAL_SIGNAL").sum()} | named membership rows: {len(o)}')
    if not o.empty:
        print('\nMEMBERSHIP')
        print(o.core_membership.value_counts().to_string())
        print('\nSIGNAL x POSITION')
        print(o.groupby(['position','structural_signal']).size().to_string())
        print('\nEXAMPLES (first 30)')
        print(o[['league_name','position','structural_signal','player_name','pos_rank','season_worp','core_membership']].head(30).to_string(index=False))
    print(f'\nCreated:\n- {OUT}')
    print('\nREADING CONTRACT')
    print('- Names explain stable roster-structure signals; they are not buy/sell/drop recommendations or asset values.')
    print('- ALWAYS_CORE means robust membership across every supported Scoring-core total for that league.')
    print('- SOMETIMES_CORE is boundary-sensitive membership and must not be presented as a hard cutline.')
    print('- A position being ABOVE does not mean every named player there is excess; BELOW does not identify a player to acquire.')
    print('- Current 2026 realized WoRP orders membership only; it is not a future projection.')
    print('- Next product gate can translate stable structure + robust membership into a compact roster diagnostic while suppressing boundary-sensitive names.')
if __name__=='__main__':main()
