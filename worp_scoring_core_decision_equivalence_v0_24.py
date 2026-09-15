#!/usr/bin/env python3
"""WoRP Lab V0.24 — positional decision-equivalence audit.

Consumes V0.23 family output only; no Sleeper/API recompute.

Goal: determine whether the positional-composition problem contains broad
plateaus of practically equivalent constructions rather than one exact optimum.
This script does NOT create a universal materiality cutoff. It reports the joint
surface of absolute Oracle-WoRP regret and retained protection, plus stability
across several descriptive views.

Key contract:
- absolute regret is primary;
- retained protection is contextual only;
- no exact QB/RB/WR/TE quota is inferred;
- if nearby constructions differ only by small regret, preserve flexibility;
- sensitivity landmarks are diagnostics, never product semantics.
"""
from pathlib import Path
import pandas as pd
import numpy as np

IN=Path('worp_scoring_core_positional_protection_families_v0_23.csv')
OUT=Path('worp_scoring_core_decision_equivalence_v0_24.csv')
OUT_ENV=Path('worp_scoring_core_decision_equivalence_envelopes_v0_24.csv')
POS=['QB','RB','WR','TE']
# Absolute WoRP regret probes are deliberately descriptive landmarks, not a
# universal definition of materiality. They let us see whether envelopes are
# stable without selecting one magic cutoff.
REGRET_VIEWS=(0.025,0.05,0.10,0.15)
PROTECTION_FLOOR=0.90


def main():
    if not IN.exists():
        raise SystemExit(f'Missing {IN}; run V0.23 first.')
    f=pd.read_csv(IN)
    rows=[]; env=[]
    for (fmt,total),g in f.groupby(['format_key','scoring_total'],sort=True):
        g=g.copy()
        # Local best family mean regret is a descriptive anchor only.
        best=float(g.mean_regret.min())
        g['excess_mean_regret_vs_best_family']=g.mean_regret-best
        for rv in REGRET_VIEWS:
            g[f'eq_abs_{int(rv*1000):03d}']=(g.excess_mean_regret_vs_best_family<=rv+1e-12)
            g[f'eq_joint_{int(rv*1000):03d}']=g[f'eq_abs_{int(rv*1000):03d}'] & (g.median_protection_retained>=PROTECTION_FLOOR)
        # Robust equivalence means surviving the strictest absolute view. Since
        # the views are nested, this identifies the inner plateau; wider views
        # remain in output for sensitivity and must be read alongside it.
        strict=REGRET_VIEWS[0]
        g['inner_equivalence_plateau']=g[f'eq_joint_{int(strict*1000):03d}']
        for _,r in g.iterrows():
            row={c:r[c] for c in g.columns}
            rows.append(row)

        er={'format_key':fmt,'scoring_total':int(total),'families_observed':len(g),
            'best_family_mean_regret':best,
            'surface_median_mean_regret':float(g.mean_regret.median()),
            'surface_p75_mean_regret':float(g.mean_regret.quantile(.75)),
            'surface_p90_mean_regret':float(g.mean_regret.quantile(.90))}
        for rv in REGRET_VIEWS:
            k=int(rv*1000)
            q=g[g[f'eq_joint_{k:03d}']]
            er[f'families_joint_eq_{k:03d}']=len(q)
            for p in POS:
                er[f'{p}_low_{k:03d}']=None if q.empty else int(q[p].min())
                er[f'{p}_high_{k:03d}']=None if q.empty else int(q[p].max())
        # Decision-stability diagnostic: if moving from .05 to .10 changes no
        # positional range, further threshold refinement cannot change the
        # roster recommendation and should STOP.
        stable=True
        for p in POS:
            if er[f'{p}_low_050']!=er[f'{p}_low_100'] or er[f'{p}_high_050']!=er[f'{p}_high_100']:
                stable=False
        er['range_stable_050_to_100']=stable
        # Broad plateau if at least two constructions survive at .05 joint view.
        er['status']='BROAD_EQUIVALENCE_PLATEAU' if er['families_joint_eq_050']>=2 else ('NARROW_EVIDENCE' if er['families_joint_eq_050']==1 else 'NO_JOINT_EQUIVALENCE_AT_050')
        env.append(er)

    o=pd.DataFrame(rows); e=pd.DataFrame(env)
    o.to_csv(OUT,index=False); e.to_csv(OUT_ENV,index=False)
    print('V0.24 POSITIONAL DECISION-EQUIVALENCE AUDIT')
    print(f'Format/total groups: {len(e)} | broad plateaus: {(e.status=="BROAD_EQUIVALENCE_PLATEAU").sum()} | narrow: {(e.status=="NARROW_EVIDENCE").sum()} | none@.050: {(e.status=="NO_JOINT_EQUIVALENCE_AT_050").sum()}')
    print(f'Range-stable from .050 to .100 absolute-regret view: {e.range_stable_050_to_100.sum()}/{len(e)}')
    print('\nDECISION-EQUIVALENCE ENVELOPES')
    cols=['format_key','scoring_total','families_observed','best_family_mean_regret','surface_median_mean_regret','families_joint_eq_025','families_joint_eq_050','families_joint_eq_100','families_joint_eq_150','range_stable_050_to_100','status']
    for p in POS: cols += [f'{p}_low_050',f'{p}_high_050',f'{p}_low_100',f'{p}_high_100']
    print(e[cols].to_string(index=False))
    print('\nCreated:')
    print(f'- {OUT}\n- {OUT_ENV}')
    print('\nREADING CONTRACT')
    print('- V0.24 is an audit of decision-equivalence, not a new semantic cutoff model.')
    print('- Absolute Oracle-WoRP regret is primary; retained protection is only a contextual guardrail.')
    print('- .025/.05/.10/.15 are sensitivity landmarks, not universal definitions of meaningful WoRP.')
    print('- The product should preserve broad families when roster decisions are stable across reasonable views.')
    print('- If .05 and .10 produce the same positional envelope, STOP refining that boundary: the roster decision is unchanged.')
    print('- If ranges move materially across views, evidence is threshold-sensitive and should not become a hard positional rule.')
    print('- FLEX/SF means independent positional lows/highs describe an envelope; they are not additive quotas.')

if __name__=='__main__':
    main()
