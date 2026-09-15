#!/usr/bin/env python3
"""WoRP Lab V0.19 — threshold-free falsification of the V0.18 Scoring-core ranges.

Purpose
-------
V0.18 mapped almost every observed format to roughly StartN+3..+5. Before that
becomes product logic, test whether the SAME broad conclusion is visible in the
raw V0.16 empirical curves without using V0.18's compression/loss/event guards.

This script deliberately does NOT create another optimality classifier.
It reports raw economic purchases from each additional Scoring roster spot:
  * marginal mean Oracle-WoRP preserved by +1, +2, ...
  * cumulative share of the observed +0..+6 protection purchased by each depth
  * how much of the TOTAL observed protection is still left on the table after
    each depth
  * whether the largest marginal purchases occur early or late
  * direct comparison of V0.18's proposed range against neighboring depths

No universal .25/.50/.75 semantic threshold is used. Those event rates are
shown only as descriptive context. The falsification question is qualitative:
Does the raw curve itself show that +3..+5 is a broad decision-stable zone, or
was V0.18 manufacturing convergence?

A format is flagged for REVIEW, not automatically failed, when material raw
economic purchase remains AFTER V0.18's upper bound relative to purchases that
occurred before/inside the range. This script never promotes a product rule.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

CURVES=Path('worp_multileague_roster_depth_formats_v0_16.csv')
RANGES=Path('worp_scoring_core_range_candidates_v0_18.csv')
OUT=Path('worp_scoring_core_falsification_v0_19.csv')
OUT_AGG=Path('worp_scoring_core_falsification_summary_v0_19.csv')


def main():
    if not CURVES.exists(): raise SystemExit(f'Missing {CURVES}')
    if not RANGES.exists(): raise SystemExit(f'Missing {RANGES}')
    d=pd.read_csv(CURVES).sort_values(['format_key','surplus_over_starters'])
    r=pd.read_csv(RANGES)
    rows=[]
    for fmt,g in d.groupby('format_key',sort=False):
        g=g.sort_values('surplus_over_starters').copy()
        rr=r[r.format_key.eq(fmt)]
        if rr.empty: continue
        rr=rr.iloc[0]
        base=g[g.surplus_over_starters.eq(0)]
        if base.empty: continue
        base_loss=float(base.iloc[0].mean_lost)
        maxs=int(g.surplus_over_starters.max())
        end=g[g.surplus_over_starters.eq(maxs)]
        end_loss=float(end.iloc[0].mean_lost)
        total_observed_purchase=max(0.0,base_loss-end_loss)
        g['prev_loss']=g.mean_lost.shift(1)
        g['marginal_purchase']=(g.prev_loss-g.mean_lost).clip(lower=0)
        g['cumulative_purchase']=(base_loss-g.mean_lost).clip(lower=0)
        g['share_total_purchase']=g.cumulative_purchase/total_observed_purchase if total_observed_purchase>0 else 0.0
        g['remaining_purchase_to_end']=(g.mean_lost-end_loss).clip(lower=0)
        g['remaining_share_total_purchase']=g.remaining_purchase_to_end/total_observed_purchase if total_observed_purchase>0 else 0.0
        lo=int(rr.surplus_range_low) if pd.notna(rr.surplus_range_low) else None
        hi=int(rr.surplus_range_high) if pd.notna(rr.surplus_range_high) else None
        pre=g[(g.surplus_over_starters>=1) & (g.surplus_over_starters < (lo if lo is not None else 99))].marginal_purchase
        inside=g[(g.surplus_over_starters>=lo) & (g.surplus_over_starters<=hi)].marginal_purchase if lo is not None else pd.Series(dtype=float)
        post=g[g.surplus_over_starters>hi].marginal_purchase if hi is not None else pd.Series(dtype=float)
        pre_peak=float(pre.max()) if len(pre) else 0.0
        inside_peak=float(inside.max()) if len(inside) else 0.0
        post_peak=float(post.max()) if len(post) else 0.0
        ref_peak=max(pre_peak,inside_peak,1e-12)
        post_vs_prior_peak=post_peak/ref_peak
        at_lo=g[g.surplus_over_starters.eq(lo)].iloc[0] if lo is not None and (g.surplus_over_starters==lo).any() else None
        at_hi=g[g.surplus_over_starters.eq(hi)].iloc[0] if hi is not None and (g.surplus_over_starters==hi).any() else None
        # REVIEW is intentionally generous: only catches a late marginal purchase
        # at least half as large as the strongest earlier purchase. It is a
        # falsification alarm, not a semantic materiality threshold or optimizer.
        review=bool(post_peak>0 and post_vs_prior_peak>=0.50)
        rows.append({
            'format_key':fmt,'league_seasons':int(g.league_seasons.max()),'lineages':int(g.lineages.max()),
            'starters':int(g.starters.max()),'v018_low':lo,'v018_high':hi,
            'baseline_mean_lost':base_loss,'end_surplus':maxs,'end_mean_lost':end_loss,
            'total_observed_purchase':total_observed_purchase,
            'share_total_purchase_at_low':float(at_lo.share_total_purchase) if at_lo is not None else None,
            'share_total_purchase_at_high':float(at_hi.share_total_purchase) if at_hi is not None else None,
            'remaining_share_after_high':float(at_hi.remaining_share_total_purchase) if at_hi is not None else None,
            'pre_range_peak_purchase':pre_peak,'inside_range_peak_purchase':inside_peak,
            'post_range_peak_purchase':post_peak,'post_vs_prior_peak':post_vs_prior_peak,
            'falsification_flag':'REVIEW_LATE_PURCHASE' if review else 'NO_LATE_REVERSAL',
            'raw_curve':' | '.join(f'+{int(x.surplus_over_starters)}:{float(x.mean_lost):.4f}' for x in g.itertuples(index=False)),
            'raw_marginals':' | '.join(f'+{int(x.surplus_over_starters)}:{float(x.marginal_purchase):.4f}' for x in g[g.surplus_over_starters>0].itertuples(index=False))
        })
    out=pd.DataFrame(rows)
    out.to_csv(OUT,index=False)

    def band(n):
        if n>=12:return 'high'
        if n>=6:return 'medium'
        return 'low'
    out['support']=out.league_seasons.map(band)
    agg=(out.groupby(['support','falsification_flag'],as_index=False)
         .agg(formats=('format_key','size'),league_seasons=('league_seasons','sum'),
              median_share_purchased_at_low=('share_total_purchase_at_low','median'),
              median_share_purchased_at_high=('share_total_purchase_at_high','median'),
              median_remaining_after_high=('remaining_share_after_high','median'),
              max_post_vs_prior_peak=('post_vs_prior_peak','max')))
    agg.to_csv(OUT_AGG,index=False)

    print('V0.19 THRESHOLD-FREE SCORING-CORE FALSIFICATION')
    print(f'Formats: {len(out)} | late-reversal reviews: {(out.falsification_flag=="REVIEW_LATE_PURCHASE").sum()}')
    print('\nRAW ECONOMIC CHECK AGAINST V0.18 RANGE')
    cols=['format_key','league_seasons','v018_low','v018_high','share_total_purchase_at_low','share_total_purchase_at_high','remaining_share_after_high','post_vs_prior_peak','falsification_flag']
    print(out[cols].round(4).to_string(index=False))
    print('\nSUPPORT SUMMARY')
    print(agg.round(4).to_string(index=False))
    reviews=out[out.falsification_flag.eq('REVIEW_LATE_PURCHASE')]
    if len(reviews):
        print('\nFORMATS REQUIRING MANUAL ECONOMIC REVIEW')
        print(reviews[['format_key','league_seasons','raw_curve','raw_marginals']].to_string(index=False))
    print('\nCreated:')
    print(f'- {OUT}\n- {OUT_AGG}')
    print('\nREADING CONTRACT')
    print('- This is a falsification gate, not a new optimizer or threshold mapper.')
    print('- The key evidence is raw marginal WoRP purchased by successive Scoring spots.')
    print('- NO_LATE_REVERSAL means the raw curve does not contradict V0.18 via a large late resurgence; it does not prove the exact range.')
    print('- REVIEW_LATE_PURCHASE means inspect the raw curve before product promotion.')
    print('- If high-support formats show no late reversals and most observed protection is already purchased by the V0.18 range, +3..+5 convergence is unlikely to be merely an artifact of V0.18 guards.')
    print('- Nearby boundaries that imply the same roster decision remain one range; do not refine +3 vs +4 without decision value.')

if __name__=='__main__': main()
