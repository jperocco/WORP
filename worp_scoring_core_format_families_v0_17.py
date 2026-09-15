#!/usr/bin/env python3
"""WoRP Lab V0.17 — league-native Scoring-core family condenser.

Consumes the completed V0.16 305-league-season format surface and answers the
next structural question without inventing a universal WoRP/loss threshold:
which league inputs materially change the SHAPE of the Scoring-depth curve?

Outputs:
1) one row per format/surplus with marginal loss reduction and retained-loss ratio;
2) structural-family surfaces that pool exact formats only after removing ONE
   input at a time (team count, QB mode, StartN, TE/TEP, FLEX structure);
3) matched-pair contrasts where two observed formats differ on exactly one
   structural dimension;
4) a compact format signature table for downstream settings -> range logic.

IMPORTANT: V0.17 deliberately does NOT auto-label an exact optimal surplus.
The project contract says nearby boundaries that imply the same roster decision
are the same answer, and V0.8.1 already showed that a mechanical compression
classifier can discover a tail after economic relevance has died. V0.17 exposes
stable broad elbows and causal-looking matched contrasts; product range mapping
comes only from decision-stable evidence, not a hidden threshold.
"""
from __future__ import annotations

from pathlib import Path
import re
import pandas as pd

INFILE=Path('worp_multileague_roster_depth_formats_v0_16.csv')
OUT_SURFACE=Path('worp_scoring_core_format_surface_v0_17.csv')
OUT_FAMILIES=Path('worp_scoring_core_structural_families_v0_17.csv')
OUT_PAIRS=Path('worp_scoring_core_matched_contrasts_v0_17.csv')
OUT_SIGNATURES=Path('worp_scoring_core_format_signatures_v0_17.csv')

DIMENSIONS=['teams','qb_mode','starters','qb','rb','wr','te','flex','sflex','tep']


def parse_format(s):
    parts=str(s).split('|')
    out={'teams':None,'qb_mode':None,'starters':None,'qb':0,'rb':0,'wr':0,'te':0,'flex':0,'sflex':0,'tep':False}
    for x in parts:
        if re.fullmatch(r'\d+T',x): out['teams']=int(x[:-1])
        elif x in ('1QB','SF'): out['qb_mode']=x
        elif x.startswith('Start'): out['starters']=int(x[5:])
        elif re.fullmatch(r'QB\d+',x): out['qb']=int(x[2:])
        elif re.fullmatch(r'RB\d+',x): out['rb']=int(x[2:])
        elif re.fullmatch(r'WR\d+',x): out['wr']=int(x[2:])
        elif re.fullmatch(r'TE\d+',x): out['te']=int(x[2:])
        elif re.fullmatch(r'FLEX\d+',x): out['flex']=int(x[4:])
        elif re.fullmatch(r'SFLEX\d+',x): out['sflex']=int(x[5:])
        elif x=='TEP': out['tep']=True
        elif x=='noTEP': out['tep']=False
    return out


def weighted_mean(g,col,w='league_seasons'):
    x=pd.to_numeric(g[col],errors='coerce'); ww=pd.to_numeric(g[w],errors='coerce').fillna(0)
    ok=x.notna() & ww.gt(0)
    return (x[ok]*ww[ok]).sum()/ww[ok].sum() if ok.any() else float('nan')


def main():
    if not INFILE.exists(): raise SystemExit(f'Missing {INFILE}. Run V0.16.1 full sample first.')
    d=pd.read_csv(INFILE)
    required={'format_key','starters','surplus_over_starters','league_seasons','lineages','mean_lost','rate_025','rate_050','rate_075'}
    miss=required-set(d.columns)
    if miss: raise SystemExit(f'Missing columns: {sorted(miss)}')

    meta=pd.DataFrame([{'format_key':k,**parse_format(k)} for k in d.format_key.unique()])
    d=d.merge(meta,on='format_key',how='left',suffixes=('','_parsed'))
    if 'starters_parsed' in d:
        bad=d[d.starters_parsed.notna() & (d.starters.astype(int)!=d.starters_parsed.astype(int))]
        if len(bad): raise SystemExit('Format parser StartN mismatch; stop rather than infer.')
        d=d.drop(columns=['starters_parsed'])

    d=d.sort_values(['format_key','surplus_over_starters']).copy()
    d['baseline_mean_lost']=d.groupby('format_key').mean_lost.transform('first')
    d['loss_ratio_vs_start_only']=d.mean_lost/d.baseline_mean_lost.replace(0,pd.NA)
    d['loss_removed_vs_start_only']=1-d.loss_ratio_vs_start_only
    d['marginal_loss_reduction']=d.groupby('format_key').mean_lost.shift(1)-d.mean_lost
    d['marginal_reduction_share_of_baseline']=d.marginal_loss_reduction/d.baseline_mean_lost.replace(0,pd.NA)
    d['next_marginal_loss_reduction']=d.groupby('format_key').marginal_loss_reduction.shift(-1)
    d['next_gain_ratio']=d.next_marginal_loss_reduction/d.marginal_loss_reduction.replace(0,pd.NA)
    d.to_csv(OUT_SURFACE,index=False)

    # Pool exact observed formats after dropping one structural dimension at a time.
    fam=[]
    for dropped in DIMENSIONS:
        keep=[x for x in DIMENSIONS if x!=dropped]
        for keys,g in d.groupby(keep+['surplus_over_starters'],dropna=False):
            if not isinstance(keys,tuple): keys=(keys,)
            rec=dict(zip(keep+['surplus_over_starters'],keys))
            rec['dimension_varied']=dropped
            rec['levels']=','.join(sorted(map(str,g[dropped].dropna().unique())))
            rec['n_exact_formats']=g.format_key.nunique()
            rec['league_seasons']=int(g.league_seasons.sum())
            rec['lineages_upper_bound']=int(g.lineages.sum())
            for c in ['mean_lost','rate_025','rate_050','rate_075','loss_ratio_vs_start_only','marginal_reduction_share_of_baseline']:
                rec[c]=weighted_mean(g,c)
            fam.append(rec)
    families=pd.DataFrame(fam)
    # Useful family evidence requires actual variation, not a renamed exact format.
    families=families[families.n_exact_formats>=2].copy()
    families.to_csv(OUT_FAMILIES,index=False)

    # Matched exact-format contrasts: differ on exactly one structural dimension.
    # Compare curves at common surplus points and report max/mean absolute separation.
    signatures=meta.copy()
    pairs=[]
    formats=list(signatures.format_key)
    byfmt={k:d[d.format_key.eq(k)].set_index('surplus_over_starters') for k in formats}
    for i,a in enumerate(formats):
        ma=signatures[signatures.format_key.eq(a)].iloc[0]
        for b in formats[i+1:]:
            mb=signatures[signatures.format_key.eq(b)].iloc[0]
            diffs=[x for x in DIMENSIONS if ma[x]!=mb[x]]
            if len(diffs)!=1: continue
            dim=diffs[0]
            common=sorted(set(byfmt[a].index)&set(byfmt[b].index))
            if len(common)<2: continue
            delta=(byfmt[a].loc[common,'mean_lost']-byfmt[b].loc[common,'mean_lost']).abs()
            pairs.append({'dimension':dim,'format_a':a,'level_a':ma[dim],'format_b':b,'level_b':mb[dim],
                          'common_surplus_points':len(common),'mean_abs_mean_lost_delta':delta.mean(),
                          'max_abs_mean_lost_delta':delta.max(),
                          'league_seasons_a':int(byfmt[a].league_seasons.max()),
                          'league_seasons_b':int(byfmt[b].league_seasons.max())})
    pairs=pd.DataFrame(pairs)
    if not pairs.empty: pairs=pairs.sort_values(['dimension','max_abs_mean_lost_delta'],ascending=[True,False])
    pairs.to_csv(OUT_PAIRS,index=False)

    # Format-level signatures: no recommendation, just enough information to map
    # settings to an empirically observed curve/range in the next product layer.
    sig=[]
    for k,g in d.groupby('format_key'):
        m=meta[meta.format_key.eq(k)].iloc[0].to_dict()
        m.update({'league_seasons':int(g.league_seasons.max()),'lineages':int(g.lineages.max()),
                  'baseline_mean_lost':float(g.iloc[0].mean_lost),
                  'mean_lost_plus1':float(g[g.surplus_over_starters.eq(1)].mean_lost.iloc[0]) if (g.surplus_over_starters==1).any() else None,
                  'mean_lost_plus2':float(g[g.surplus_over_starters.eq(2)].mean_lost.iloc[0]) if (g.surplus_over_starters==2).any() else None,
                  'mean_lost_plus3':float(g[g.surplus_over_starters.eq(3)].mean_lost.iloc[0]) if (g.surplus_over_starters==3).any() else None,
                  'mean_lost_plus4':float(g[g.surplus_over_starters.eq(4)].mean_lost.iloc[0]) if (g.surplus_over_starters==4).any() else None,
                  'mean_lost_plus5':float(g[g.surplus_over_starters.eq(5)].mean_lost.iloc[0]) if (g.surplus_over_starters==5).any() else None,
                  'mean_lost_plus6':float(g[g.surplus_over_starters.eq(6)].mean_lost.iloc[0]) if (g.surplus_over_starters==6).any() else None})
        sig.append(m)
    pd.DataFrame(sig).sort_values(DIMENSIONS).to_csv(OUT_SIGNATURES,index=False)

    print('V0.17 SCORING-CORE FORMAT FAMILIES')
    print(f'Exact formats: {d.format_key.nunique()} | league-seasons represented: {int(d.groupby("format_key").league_seasons.max().sum())}')
    print(f'Matched one-dimension format pairs: {len(pairs)}')
    if not pairs.empty:
        print('\nDECISION-MATERIAL STRUCTURAL CONTRASTS — largest observed curve separations')
        x=(pairs.groupby('dimension',as_index=False)
           .agg(matched_pairs=('dimension','size'),median_max_curve_delta=('max_abs_mean_lost_delta','median'),max_curve_delta=('max_abs_mean_lost_delta','max'))
           .sort_values('max_curve_delta',ascending=False))
        print(x.round(4).to_string(index=False))
    print('\nCreated:')
    for p in [OUT_SURFACE,OUT_FAMILIES,OUT_PAIRS,OUT_SIGNATURES]: print(f'- {p}')
    print('\nREADING CONTRACT')
    print('- No universal loss threshold and no automatic exact optimum.')
    print('- Compare broad curve shapes and matched structural contrasts; nearby decision-equivalent boundaries are one range.')
    print('- Small WoRP/loss differences that cannot change roster construction are noise, even when statistically visible.')
    print('- Roster size is not promoted as Scoring demand; V0.11 already showed extra capacity can flow to Non-Scoring.')
    print('- Product mapping may use an observed format directly; unsupported formats must preserve uncertainty or borrow only from structurally matched families.')

if __name__=='__main__': main()
