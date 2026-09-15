#!/usr/bin/env python3
"""WoRP Lab V0.23 — whole-core positional protection test.

Purpose
-------
V0.21 established pairwise directional evidence for positional Scoring-family
composition. V0.22 is explicitly rejected as a materiality gate because it
scaled materiality to the distribution of pairwise deltas, which can make tiny
absolute WoRP differences look important.

V0.23 changes the denominator. It asks: within the SAME league-season and the
SAME total Scoring-core size, how much of the economic protection available at
that core size does a positional family preserve versus the best observed
family for that league-season?

This is a whole-roster regret/protection diagnostic, not a new magic cutoff and
not an exact QB/RB/WR/TE quota generator. It intentionally reports the full
protection distribution and broad sensitivity summaries so product logic can
preserve decision-equivalent constructions.

Inputs are V0.20 detail only; no Sleeper/API recompute.
"""
from pathlib import Path
import pandas as pd
import numpy as np

IN=Path('worp_scoring_core_positional_family_detail_v0_20.csv')
OUT_DETAIL=Path('worp_scoring_core_positional_protection_detail_v0_23.csv')
OUT_FAM=Path('worp_scoring_core_positional_protection_families_v0_23.csv')
OUT_ENV=Path('worp_scoring_core_positional_protection_envelopes_v0_23.csv')
POS=['QB','RB','WR','TE']
# Sensitivity views only. These are NOT semantic product thresholds.
PROTECTION_VIEWS=(0.90,0.95,0.975)


def main():
    if not IN.exists():
        raise SystemExit(f'Missing {IN}; run V0.20 first.')
    d=pd.read_csv(IN,dtype={'league_id':str,'lineage_root':str})
    d['ls']=d.league_id.astype(str)+'|'+d.season.astype(str)

    # Within each exact league-season + core total, the best observed positional
    # family is the local whole-roster benchmark. mean_lost is Oracle-WoRP lost;
    # lower is better. Family regret is therefore excess loss versus that best
    # observed family on identical support.
    keys=['format_key','scoring_total','ls']
    d['best_mean_lost_same_ls_total']=d.groupby(keys)['mean_lost'].transform('min')
    d['family_regret']=d['mean_lost']-d['best_mean_lost_same_ls_total']

    # Economic protection available from positional composition at this core
    # size is the observed spread from worst to best family in that SAME
    # league-season. Protection retained = 1 - regret/spread. When the entire
    # family surface is effectively tied, all families are decision-equivalent
    # and receive protection=1 rather than manufacturing distinctions.
    d['worst_mean_lost_same_ls_total']=d.groupby(keys)['mean_lost'].transform('max')
    d['composition_protection_span']=d['worst_mean_lost_same_ls_total']-d['best_mean_lost_same_ls_total']
    eps=1e-12
    d['protection_retained']=np.where(
        d.composition_protection_span.abs()<=eps,
        1.0,
        1.0-(d.family_regret/d.composition_protection_span)
    ).clip(0,1)

    # Keep raw absolute regret because the project contract says tiny WoRP
    # differences can remain economic zero even if relative protection differs.
    detail_cols=['format_key','scoring_total','league_id','season','ls']+POS+[
        'mean_lost','best_mean_lost_same_ls_total','worst_mean_lost_same_ls_total',
        'composition_protection_span','family_regret','protection_retained'
    ]
    d[detail_cols].to_csv(OUT_DETAIL,index=False)

    fam_rows=[]
    fam_keys=['format_key','scoring_total']+POS
    for k,g in d.groupby(fam_keys,sort=True):
        row={c:v for c,v in zip(fam_keys,k)}
        row.update({
            'league_seasons_observed':g.ls.nunique(),
            'mean_regret':g.family_regret.mean(),
            'median_regret':g.family_regret.median(),
            'p75_regret':g.family_regret.quantile(.75),
            'p90_regret':g.family_regret.quantile(.90),
            'mean_protection_retained':g.protection_retained.mean(),
            'median_protection_retained':g.protection_retained.median(),
            'p25_protection_retained':g.protection_retained.quantile(.25),
            'worst_quartile_protection_retained':g.protection_retained.quantile(.25),
        })
        for v in PROTECTION_VIEWS:
            row[f'share_protection_ge_{int(v*1000):03d}']=(g.protection_retained>=v).mean()
        fam_rows.append(row)
    f=pd.DataFrame(fam_rows)
    f.to_csv(OUT_FAM,index=False)

    # Envelope summaries are sensitivity diagnostics only. A family is called
    # stable across views if its median retained protection clears every view;
    # raw regret remains visible and must be consulted before product exclusion.
    env=[]
    for (fmt,total),g in f.groupby(['format_key','scoring_total'],sort=True):
        stable=g[g.median_protection_retained>=max(PROTECTION_VIEWS)].copy()
        row={
            'format_key':fmt,'scoring_total':int(total),'families_observed':len(g),
            'families_high_protection_all_views':len(stable),
            'status':'NO_HIGH_PROTECTION_FAMILY' if stable.empty else ('NARROW_EVIDENCE_ONE_FAMILY' if len(stable)==1 else 'PROTECTION_ENVELOPE'),
            'median_family_mean_regret':g.mean_regret.median(),
            'median_family_p90_regret':g.p90_regret.median(),
        }
        for p in POS:
            row[p+'_low']=None if stable.empty else int(stable[p].min())
            row[p+'_high']=None if stable.empty else int(stable[p].max())
        env.append(row)
    e=pd.DataFrame(env)
    e.to_csv(OUT_ENV,index=False)

    print('V0.23 WHOLE-CORE POSITIONAL PROTECTION TEST')
    print(f'Format/total groups: {len(e)} | protection envelopes: {(e.status=="PROTECTION_ENVELOPE").sum()} | narrow-one-family: {(e.status=="NARROW_EVIDENCE_ONE_FAMILY").sum()} | no-high-protection: {(e.status=="NO_HIGH_PROTECTION_FAMILY").sum()}')
    print(f'Family observations: {len(f)}')
    print('\nPROTECTION ENVELOPES — SENSITIVITY VIEW, NOT QUOTAS')
    print(e.to_string(index=False))
    print('\nABSOLUTE REGRET CONTEXT')
    print(f"family mean_regret p50={f.mean_regret.median():.4f} | p75={f.mean_regret.quantile(.75):.4f} | p90={f.mean_regret.quantile(.90):.4f}")
    print(f"family p90_regret p50={f.p90_regret.median():.4f} | p75={f.p90_regret.quantile(.75):.4f} | p90={f.p90_regret.quantile(.90):.4f}")
    print('\nCreated:')
    print(f'- {OUT_DETAIL}\n- {OUT_FAM}\n- {OUT_ENV}')
    print('\nREADING CONTRACT')
    print('- V0.22 relative-delta materiality is rejected and must not be used for product logic.')
    print('- V0.23 benchmarks every family against the best observed positional family in the SAME league-season and SAME total Scoring-core size.')
    print('- family_regret is excess Oracle-WoRP loss from positional composition; this is the primary economic quantity.')
    print('- protection_retained describes how much of the observed positional-composition protection span the family preserves.')
    print('- 90%/95%/97.5% are sensitivity views only, not universal semantic thresholds.')
    print('- Relative protection NEVER overrides absolute regret: tiny WoRP differences can still be economic zero.')
    print('- The goal is broad decision-equivalent positional envelopes, not exact QB/RB/WR/TE quotas.')
    print('- FLEX/SF positional highs must not be summed independently as a prescribed roster.')

if __name__=='__main__':
    main()
