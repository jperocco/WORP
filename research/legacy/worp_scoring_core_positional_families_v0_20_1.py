#!/usr/bin/env python3
"""WoRP Lab V0.20.1 — cross-league common-support correction for positional families.

Consumes the expensive V0.20 detail output; no Sleeper/WoRP recomputation needed.

Why this exists
---------------
V0.20 enforced equal roster-week support for a reported family WITHIN each
league-season, but the full output exposed a second-level support problem:
different positional families could be present in different numbers of
league-seasons inside the same exact format/Scoring total. Comparing their mean
loss directly would therefore compare unequal league-season denominators.

V0.20.1 fixes that exactly like the earlier common-support discipline:
for each exact format + Scoring total, only positional families observed on the
FULL common set of represented league-seasons are compared. Each league-season
then receives equal weight. If no family survives full intersection, the group
is UNRESOLVED rather than forced.

The best-quartile envelope remains DESCRIPTIVE ONLY; it is not a semantic
threshold or product quota.
"""
from pathlib import Path
import pandas as pd

IN=Path('worp_scoring_core_positional_family_detail_v0_20.csv')
OUT_FORMAT=Path('worp_scoring_core_positional_family_formats_v0_20_1.csv')
OUT_ENV=Path('worp_scoring_core_positional_family_envelopes_v0_20_1.csv')
POS=['QB','RB','WR','TE']
KEY=['format_key','scoring_total']
FAM=POS

def main():
    if not IN.exists(): raise SystemExit(f'Missing {IN}; run V0.20 full first.')
    d=pd.read_csv(IN,dtype={'league_id':str,'lineage_root':str})
    d['league_season_key']=d.league_id.astype(str)+'|'+d.season.astype(str)
    kept=[]; audit=[]
    for (fmt,total),g in d.groupby(KEY,sort=False):
        league_set=set(g.league_season_key.unique()); expected=len(league_set)
        fam_support=(g.groupby(FAM,as_index=False).agg(
            league_seasons=('league_season_key','nunique'),lineages=('lineage_root','nunique')))
        common_fams=fam_support[fam_support.league_seasons.eq(expected)][FAM]
        if common_fams.empty:
            audit.append({'format_key':fmt,'scoring_total':total,'represented_league_seasons':expected,
                          'families_observed':len(fam_support),'families_full_common_support':0,'status':'UNRESOLVED_NO_COMMON_FAMILY'})
            continue
        gg=g.merge(common_fams,on=FAM,how='inner')
        # Defensive assertion: every retained family must have exactly the same league-season set.
        for famvals,x in gg.groupby(FAM):
            if set(x.league_season_key)!=league_set:
                raise RuntimeError(f'common-support assertion failed: {fmt} total={total} family={famvals}')
        kept.append(gg)
        audit.append({'format_key':fmt,'scoring_total':total,'represented_league_seasons':expected,
                      'families_observed':len(fam_support),'families_full_common_support':len(common_fams),'status':'PASS_COMMON_SUPPORT'})
    if not kept: raise SystemExit('FAIL: no format/total group has a full-common-support family.')
    c=pd.concat(kept,ignore_index=True)
    f=(c.groupby(KEY+FAM,as_index=False).agg(
        league_seasons=('league_season_key','nunique'),lineages=('lineage_root','nunique'),
        mean_lost=('mean_lost','mean'),median_lost=('median_lost','median'),rate_050=('rate_050','mean')))
    f['best_mean_lost']=f.groupby(KEY).mean_lost.transform('min')
    f['family_regret']=f.mean_lost-f.best_mean_lost
    f.to_csv(OUT_FORMAT,index=False)

    audit_df=pd.DataFrame(audit)
    env=[]
    for (fmt,total),g in f.groupby(KEY,sort=False):
        meta=audit_df[(audit_df.format_key==fmt)&(audit_df.scoring_total==total)].iloc[0]
        cut=float(g.family_regret.quantile(.25)); e=g[g.family_regret<=cut+1e-12]
        row={'format_key':fmt,'scoring_total':int(total),
             'surplus_over_starters':int(c[(c.format_key==fmt)&(c.scoring_total==total)].surplus_over_starters.iloc[0]),
             'league_seasons':int(meta.represented_league_seasons),
             'families_observed_before_common_support':int(meta.families_observed),
             'families_tested_common_support':len(g),'efficient_families_descriptive':len(e),
             'best_mean_lost':float(g.mean_lost.min()),'q25_regret_cut_descriptive':cut,'status':'PASS_COMMON_SUPPORT'}
        for p in POS:
            row[p+'_low']=int(e[p].min());row[p+'_high']=int(e[p].max())
        env.append(row)
    # Preserve unresolved groups visibly.
    resolved={(x['format_key'],x['scoring_total']) for x in env}
    for x in audit:
        if (x['format_key'],x['scoring_total']) not in resolved:
            env.append({'format_key':x['format_key'],'scoring_total':int(x['scoring_total']),
                        'league_seasons':int(x['represented_league_seasons']),
                        'families_observed_before_common_support':int(x['families_observed']),
                        'families_tested_common_support':0,'status':x['status']})
    e=pd.DataFrame(env).sort_values(KEY);e.to_csv(OUT_ENV,index=False)

    print('V0.20.1 POSITIONAL FAMILY COMMON-SUPPORT CORRECTION')
    print(f'Format/total groups: {len(audit_df)} | resolved: {(audit_df.status=="PASS_COMMON_SUPPORT").sum()} | unresolved: {(audit_df.status!="PASS_COMMON_SUPPORT").sum()}')
    print('\nSUPPORT AUDIT')
    print(audit_df.to_string(index=False))
    print('\nCORRECTED POSITIONAL FAMILY ENVELOPES')
    cols=['format_key','scoring_total','league_seasons','families_observed_before_common_support','families_tested_common_support','efficient_families_descriptive','best_mean_lost','q25_regret_cut_descriptive','QB_low','QB_high','RB_low','RB_high','WR_low','WR_high','TE_low','TE_high','status']
    print(e[[x for x in cols if x in e.columns]].to_string(index=False))
    print('\nCreated:')
    print(f'- {OUT_FORMAT}\n- {OUT_ENV}')
    print('\nREADING CONTRACT')
    print('- V0.20 raw output is NOT valid for cross-family ranking when league-season support differs.')
    print('- V0.20.1 compares only families present on the exact same league-season set within format + Scoring total.')
    print('- Every represented league-season receives equal weight.')
    print('- UNRESOLVED is preferred to silently changing the denominator.')
    print('- Best-quartile envelope remains descriptive only; do not promote it as an exact positional quota.')
    print('- The next gate should test decision-material positional exclusions, not refine quartile boundaries.')

if __name__=='__main__': main()
