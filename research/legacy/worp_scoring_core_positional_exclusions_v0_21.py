#!/usr/bin/env python3
"""WoRP Lab V0.21 — pairwise positional exclusion gate.

Uses the expensive V0.20 league-season detail only; no Sleeper/API recompute.

Why this exists
---------------
V0.20.1 correctly exposed denominator drift, but requiring one family to exist in
EVERY league-season of a large exact-format group can over-correct: a 70-season
format may leave only 0-4 universal families. That is an audit result, not a
sound basis for positional prescription.

V0.21 therefore asks a narrower question aligned with the product contract:
when two positional Scoring families are both observable in the SAME
league-seasons, does one repeatedly incur more Oracle-WoRP loss than the other?
It reports pairwise common-support evidence and positional count ranges among
families that are not repeatedly dominated. It does NOT manufacture exact
QB/RB/WR/TE quotas and it does NOT impute unsupported formats.

Important: V0.20 retention is ex-post season positional rank, so this remains a
hindsight-favorable structural upper-bound test, not ex-ante identifiability.
"""
from pathlib import Path
from itertools import combinations
import pandas as pd

IN=Path('worp_scoring_core_positional_family_detail_v0_20.csv')
OUT_PAIR=Path('worp_scoring_core_positional_pairwise_v0_21.csv')
OUT_FAM=Path('worp_scoring_core_positional_family_gate_v0_21.csv')
OUT_ENV=Path('worp_scoring_core_positional_exclusion_envelopes_v0_21.csv')
POS=['QB','RB','WR','TE']


def fid(r):
    return tuple(int(r[p]) for p in POS)


def main():
    if not IN.exists(): raise SystemExit(f'Missing {IN}; run V0.20 first.')
    d=pd.read_csv(IN,dtype={'league_id':str,'lineage_root':str})
    d['ls']=d.league_id.astype(str)+'|'+d.season.astype(str)
    d['family']=[fid(r) for _,r in d.iterrows()]
    pair_rows=[]; fam_rows=[]; env_rows=[]

    for (fmt,total),g in d.groupby(['format_key','scoring_total'],sort=True):
        # Series.eq(tuple) is interpreted by pandas as elementwise comparison
        # against a tuple-like sequence and raises a length mismatch. Build the
        # family mask explicitly so each cell's tuple is compared as one scalar.
        fams=sorted(set(g['family'].tolist()))
        by={f:g[g['family'].map(lambda x, target=f: x == target)].set_index('ls') for f in fams}
        # Pairwise comparisons use only the exact intersection for that pair.
        for a,b in combinations(fams,2):
            common=sorted(set(by[a].index)&set(by[b].index))
            if not common: continue
            xa=by[a].loc[common,'mean_lost'].astype(float)
            xb=by[b].loc[common,'mean_lost'].astype(float)
            delta=xa-xb # positive => A loses more WoRP than B
            pair_rows.append({
                'format_key':fmt,'scoring_total':int(total),
                'A_QB':a[0],'A_RB':a[1],'A_WR':a[2],'A_TE':a[3],
                'B_QB':b[0],'B_RB':b[1],'B_WR':b[2],'B_TE':b[3],
                'common_league_seasons':len(common),
                'mean_delta_A_minus_B':delta.mean(),
                'median_delta_A_minus_B':delta.median(),
                'A_better_share':(delta<0).mean(),
                'B_better_share':(delta>0).mean(),
                'tie_share':(delta.abs()<1e-12).mean(),
            })

        pg=pd.DataFrame([x for x in pair_rows if x['format_key']==fmt and x['scoring_total']==int(total)])
        # Descriptive dominance: no magic WoRP cutoff. A family is flagged only
        # when another family beats it on their shared support in >=75% of
        # league-seasons AND the mean/median deltas point the same direction.
        # 75% is a robustness screen, not a semantic product threshold; output
        # includes raw shares/deltas so sensitivity can be judged directly.
        dominated={f:0 for f in fams}; comparisons={f:0 for f in fams}; strongest={f:0.0 for f in fams}
        for _,r in pg.iterrows():
            a=(int(r.A_QB),int(r.A_RB),int(r.A_WR),int(r.A_TE)); b=(int(r.B_QB),int(r.B_RB),int(r.B_WR),int(r.B_TE))
            comparisons[a]+=1; comparisons[b]+=1
            md=float(r.mean_delta_A_minus_B); med=float(r.median_delta_A_minus_B)
            if md>0 and med>=0 and float(r.B_better_share)>=.75:
                dominated[a]+=1; strongest[a]=max(strongest[a],md)
            if md<0 and med<=0 and float(r.A_better_share)>=.75:
                dominated[b]+=1; strongest[b]=max(strongest[b],-md)
        for f in fams:
            fam_rows.append({'format_key':fmt,'scoring_total':int(total),'QB':f[0],'RB':f[1],'WR':f[2],'TE':f[3],
                             'league_seasons_observed':by[f].index.nunique(),'pairwise_comparisons':comparisons[f],
                             'robust_dominations':dominated[f],'strongest_mean_loss_when_dominated':strongest[f],
                             'status':'NONDOMINATED' if dominated[f]==0 else 'DOMINATED_DESCRIPTIVE'})
        fg=pd.DataFrame([x for x in fam_rows if x['format_key']==fmt and x['scoring_total']==int(total)])
        nd=fg[fg.status.eq('NONDOMINATED')]
        # Require at least two nondominated families to call an envelope; one
        # survivor is reported as narrow evidence, not an exact prescription.
        row={'format_key':fmt,'scoring_total':int(total),'families_observed':len(fams),
             'nondominated_families':len(nd),'status':'UNRESOLVED' if nd.empty else ('NARROW_EVIDENCE_ONE_FAMILY' if len(nd)==1 else 'PAIRWISE_ENVELOPE')}
        for p in POS:
            row[p+'_low']=None if nd.empty else int(nd[p].min()); row[p+'_high']=None if nd.empty else int(nd[p].max())
        env_rows.append(row)

    p=pd.DataFrame(pair_rows); f=pd.DataFrame(fam_rows); e=pd.DataFrame(env_rows)
    p.to_csv(OUT_PAIR,index=False); f.to_csv(OUT_FAM,index=False); e.to_csv(OUT_ENV,index=False)
    print('V0.21 PAIRWISE POSITIONAL EXCLUSION GATE')
    print(f'Format/total groups: {len(e)} | pairwise envelope: {(e.status=="PAIRWISE_ENVELOPE").sum()} | narrow-one-family: {(e.status=="NARROW_EVIDENCE_ONE_FAMILY").sum()} | unresolved: {(e.status=="UNRESOLVED").sum()}')
    print('\nPOSITIONAL EXCLUSION ENVELOPES')
    print(e.to_string(index=False))
    print('\nCreated:')
    print(f'- {OUT_PAIR}\n- {OUT_FAM}\n- {OUT_ENV}')
    print('\nREADING CONTRACT')
    print('- Pairwise comparisons always use the SAME league-seasons for the two families being compared.')
    print('- This avoids both V0.20 denominator drift and V0.20.1 universal-intersection over-correction.')
    print('- Dominance is descriptive robustness evidence, not a semantic WoRP threshold.')
    print('- Positional ranges are constraints/envelopes only; FLEX/SF means positional highs must NOT be summed as quotas.')
    print('- NARROW_EVIDENCE_ONE_FAMILY is not permission to prescribe that exact tuple.')
    print('- The product target is decision-material positional exclusions; if alternatives are not repeatedly dominated, preserve roster-construction flexibility.')

if __name__=='__main__': main()
