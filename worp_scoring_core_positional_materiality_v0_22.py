#!/usr/bin/env python3
"""WoRP Lab V0.22 — decision-materiality gate for positional exclusions.

Consumes V0.21 pairwise comparisons only; no Sleeper/API recompute.

V0.21 established legitimate pairwise common support and a descriptive 75%
dominance screen. V0.22 asks the missing WoRP question: are those repeated
wins economically large enough to matter, or are we excluding families because
of tiny but consistent differences?

No new universal WoRP cutoff is introduced. Materiality is evaluated relative
to the economic scale of each exact format + Scoring-total pairwise surface.
The script reports sensitivity at several relative landmarks and, crucially,
checks whether V0.21's exclusions survive across those landmarks. The product
should only learn constraints that are robust to reasonable materiality views.
"""
from pathlib import Path
import pandas as pd
import numpy as np

PAIR=Path('worp_scoring_core_positional_pairwise_v0_21.csv')
FAM=Path('worp_scoring_core_positional_family_gate_v0_21.csv')
OUT=Path('worp_scoring_core_positional_materiality_v0_22.csv')
OUT_ENV=Path('worp_scoring_core_positional_material_envelopes_v0_22.csv')
POS=['QB','RB','WR','TE']
LANDMARKS=(0.10,0.20,0.30)  # sensitivity probes only; not semantic thresholds


def tup(prefix,r):
    return tuple(int(r[f'{prefix}_{p}']) for p in POS)


def main():
    if not PAIR.exists() or not FAM.exists():
        raise SystemExit('Missing V0.21 outputs; run V0.21 first.')
    p=pd.read_csv(PAIR); f=pd.read_csv(FAM)
    rows=[]; env=[]
    for (fmt,total),g in p.groupby(['format_key','scoring_total'],sort=True):
        fg=f[(f.format_key==fmt)&(f.scoring_total==total)].copy()
        fams=[tuple(int(r[p]) for p in POS) for _,r in fg.iterrows()]
        # Economic scale is endogenous to this exact pairwise surface: median
        # absolute non-zero mean loss difference. We do not import .25/.50/etc.
        absd=g.mean_delta_A_minus_B.abs(); nz=absd[absd>1e-12]
        scale=float(nz.median()) if len(nz) else 0.0
        state={lm:{x:0 for x in fams} for lm in LANDMARKS}
        evidence={lm:{x:0 for x in fams} for lm in LANDMARKS}
        for _,r in g.iterrows():
            a=tup('A',r); b=tup('B',r); md=float(r.mean_delta_A_minus_B); med=float(r.median_delta_A_minus_B)
            # Winner consistency is inherited from V0.21's robustness idea;
            # materiality now additionally requires delta magnitude relative to
            # this surface's own economic scale.
            winner=None; loser=None; consistency=0.0; mag=abs(md)
            if md>0 and med>=0:
                winner=b; loser=a; consistency=float(r.B_better_share)
            elif md<0 and med<=0:
                winner=a; loser=b; consistency=float(r.A_better_share)
            for lm in LANDMARKS:
                if winner is None: continue
                evidence[lm][loser]+=1
                hurdle=scale*lm
                if consistency>=.75 and mag>=hurdle-1e-12:
                    state[lm][loser]+=1
        for fam in fams:
            base=fg[(fg.QB==fam[0])&(fg.RB==fam[1])&(fg.WR==fam[2])&(fg.TE==fam[3])].iloc[0]
            row={'format_key':fmt,'scoring_total':int(total),'QB':fam[0],'RB':fam[1],'WR':fam[2],'TE':fam[3],
                 'league_seasons_observed':int(base.league_seasons_observed),'v021_status':base.status,
                 'surface_median_abs_pair_delta':scale}
            surv=[]
            for lm in LANDMARKS:
                key=f'material_dominations_rel_{int(lm*100):02d}'
                row[key]=state[lm][fam]
                surv.append(state[lm][fam]>0)
            row['excluded_all_materiality_views']=all(surv)
            row['excluded_any_materiality_view']=any(surv)
            row['materiality_status']='ROBUST_MATERIAL_EXCLUSION' if all(surv) else ('SENSITIVE_EXCLUSION' if any(surv) else 'NO_MATERIAL_EXCLUSION')
            rows.append(row)
        rg=pd.DataFrame([x for x in rows if x['format_key']==fmt and x['scoring_total']==int(total)])
        keep=rg[~rg.excluded_all_materiality_views]
        er={'format_key':fmt,'scoring_total':int(total),'families_observed':len(rg),
            'robust_material_exclusions':int(rg.excluded_all_materiality_views.sum()),
            'families_preserved':len(keep),
            'status':'UNRESOLVED' if keep.empty else ('NARROW_EVIDENCE_ONE_FAMILY' if len(keep)==1 else 'MATERIALITY_ENVELOPE'),
            'surface_median_abs_pair_delta':scale}
        for pos in POS:
            er[pos+'_low']=None if keep.empty else int(keep[pos].min()); er[pos+'_high']=None if keep.empty else int(keep[pos].max())
        env.append(er)
    o=pd.DataFrame(rows); e=pd.DataFrame(env)
    o.to_csv(OUT,index=False); e.to_csv(OUT_ENV,index=False)
    print('V0.22 POSITIONAL DECISION-MATERIALITY GATE')
    print(f'Format/total groups: {len(e)} | materiality envelopes: {(e.status=="MATERIALITY_ENVELOPE").sum()} | narrow-one-family: {(e.status=="NARROW_EVIDENCE_ONE_FAMILY").sum()} | unresolved: {(e.status=="UNRESOLVED").sum()}')
    print(f'Families: {len(o)} | robust material exclusions: {(o.materiality_status=="ROBUST_MATERIAL_EXCLUSION").sum()} | sensitive: {(o.materiality_status=="SENSITIVE_EXCLUSION").sum()} | no material exclusion: {(o.materiality_status=="NO_MATERIAL_EXCLUSION").sum()}')
    print('\nMATERIALITY ENVELOPES')
    print(e.to_string(index=False))
    print('\nV0.21 EXCLUSION SURVIVAL')
    x=o[o.v021_status.eq('DOMINATED_DESCRIPTIVE')]
    if len(x):
        print(x.materiality_status.value_counts().to_string())
    else: print('No V0.21 descriptive exclusions found.')
    print('\nCreated:'); print(f'- {OUT}\n- {OUT_ENV}')
    print('\nREADING CONTRACT')
    print('- V0.22 does not choose a new exact positional quota.')
    print('- 10%/20%/30% are sensitivity landmarks relative to each exact surface own median pairwise delta; they are not semantic WoRP thresholds.')
    print('- A robust material exclusion must survive every tested materiality view plus V0.21 directional consistency.')
    print('- If V0.21 exclusions disappear once magnitude matters, preserve those roster constructions as decision-equivalent.')
    print('- If broad positional constraints survive across materiality views and supported formats, they are candidates for league-native Roster Construction logic.')
    print('- Small statistically/repeatedly directional differences remain economic zero when they do not change a roster decision.')

if __name__=='__main__': main()
