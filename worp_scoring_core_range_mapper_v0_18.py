#!/usr/bin/env python3
"""WoRP Lab V0.18 — decision-stable league-native Scoring-core range mapper.

Consumes V0.17's observed exact-format surfaces. This is intentionally NOT an
optimizer and does not invent a universal WoRP/loss threshold. Instead it asks:
for each observed league format, where does the Scoring-depth curve enter a
broad region of diminishing, decision-immaterial gains?

The output is an empirical RANGE candidate, not an exact optimum. A format can
remain UNRESOLVED when the observed +0..+6 window does not contain a stable
plateau. Unsupported formats are not imputed here.

Method:
- Work with marginal reduction in mean Oracle-WoRP lost when adding one Scoring
  roster spot beyond the offensive starting lineup.
- Estimate each format's own early-gain scale from +1/+2 marginal reductions.
- A plateau candidate begins only after the curve has materially compressed
  relative to its OWN early gain, and remains compressed for consecutive steps.
- Guard against false tails: remaining absolute loss and >=.50 loss-event rate
  must also be low relative to the format's own start-only baseline.
- Return a 2-slot range around the first decision-stable plateau. The exact
  boundary is deliberately not claimed.

This is a transparent research mapper. Product promotion requires coherent
cross-format behavior and review of unresolved/low-support cases.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

INFILE=Path('worp_scoring_core_format_surface_v0_17.csv')
OUT=Path('worp_scoring_core_range_candidates_v0_18.csv')
OUT_SUMMARY=Path('worp_scoring_core_range_family_summary_v0_18.csv')

# Relative guards, not universal WoRP thresholds.
MARGINAL_COMPRESSION=0.35   # <=35% of own early marginal-gain scale
LOSS_REMAINING_RATIO=0.25   # <=25% of own start-only mean loss
EVENT050_REMAINING_RATIO=0.35  # <=35% of own start-only >=.50 event rate
CONSECUTIVE=2


def safe_ratio(a,b):
    if pd.isna(a) or pd.isna(b) or b<=0: return None
    return float(a)/float(b)


def classify_support(n):
    if n>=12: return 'high'
    if n>=6: return 'medium'
    return 'low'


def main():
    if not INFILE.exists(): raise SystemExit(f'Missing {INFILE}. Run V0.17 first.')
    d=pd.read_csv(INFILE).sort_values(['format_key','surplus_over_starters'])
    req={'format_key','teams','qb_mode','starters','te','flex','sflex','tep','league_seasons','lineages',
         'surplus_over_starters','mean_lost','rate_050','marginal_loss_reduction'}
    miss=req-set(d.columns)
    if miss: raise SystemExit(f'Missing columns: {sorted(miss)}')

    rows=[]
    for fmt,g in d.groupby('format_key',sort=False):
        g=g.sort_values('surplus_over_starters').reset_index(drop=True)
        base=g[g.surplus_over_starters.eq(0)]
        if base.empty: continue
        base_loss=float(base.iloc[0].mean_lost)
        base_event=float(base.iloc[0].rate_050)
        early=g[g.surplus_over_starters.isin([1,2])].marginal_loss_reduction.dropna()
        early=early[early.gt(0)]
        early_scale=float(early.median()) if len(early) else None
        candidates=[]
        diagnostics=[]
        for i,r in g.iterrows():
            s=int(r.surplus_over_starters)
            if s<1 or early_scale is None or early_scale<=0: continue
            m=float(r.marginal_loss_reduction) if pd.notna(r.marginal_loss_reduction) else None
            mr=safe_ratio(m,early_scale) if m is not None else None
            lr=safe_ratio(r.mean_lost,base_loss)
            er=safe_ratio(r.rate_050,base_event)
            # If baseline has no >=.50 events, event guard is already satisfied.
            event_ok=(base_event<=0) or (er is not None and er<=EVENT050_REMAINING_RATIO)
            ok=(mr is not None and mr<=MARGINAL_COMPRESSION and
                lr is not None and lr<=LOSS_REMAINING_RATIO and event_ok)
            diagnostics.append((s,ok,mr,lr,er))
        # Require consecutive compressed points so one noisy marginal step cannot define boundary.
        for j in range(len(diagnostics)-CONSECUTIVE+1):
            window=diagnostics[j:j+CONSECUTIVE]
            if all(x[1] for x in window) and all(window[k+1][0]==window[k][0]+1 for k in range(len(window)-1)):
                candidates.append(window[0][0]); break
        plateau=candidates[0] if candidates else None
        meta=g.iloc[0]
        if plateau is None:
            lo=hi=None; status='unresolved_in_observed_window'
        else:
            # Range rather than exact point: plateau onset and one additional resilience slot.
            lo=int(plateau); hi=min(int(g.surplus_over_starters.max()),lo+1); status='observed_range_candidate'
        rows.append({
            'format_key':fmt,'teams':int(meta.teams),'qb_mode':meta.qb_mode,'starters':int(meta.starters),
            'te':int(meta.te),'flex':int(meta.flex),'sflex':int(meta.sflex),'tep':bool(meta.tep),
            'league_seasons':int(meta.league_seasons),'lineages':int(meta.lineages),
            'support':classify_support(int(meta.league_seasons)),
            'baseline_mean_lost':base_loss,'baseline_rate_050':base_event,'early_gain_scale':early_scale,
            'surplus_range_low':lo,'surplus_range_high':hi,
            'scoring_core_low':int(meta.starters)+lo if lo is not None else None,
            'scoring_core_high':int(meta.starters)+hi if hi is not None else None,
            'status':status,
            'diagnostic_points':';'.join(f'+{s}:ok={int(ok)},marg={mr:.3f if mr is not None else float("nan")},loss={lr:.3f if lr is not None else float("nan")},evt50={er:.3f if er is not None else float("nan")}' for s,ok,mr,lr,er in [])
        })
    out=pd.DataFrame(rows)
    out.to_csv(OUT,index=False)

    resolved=out[out.status.eq('observed_range_candidate')].copy()
    if len(resolved):
        summary=(resolved.groupby(['starters','qb_mode','teams'],as_index=False)
                 .agg(formats=('format_key','size'),league_seasons=('league_seasons','sum'),
                      median_surplus_low=('surplus_range_low','median'),median_surplus_high=('surplus_range_high','median'),
                      min_surplus_low=('surplus_range_low','min'),max_surplus_high=('surplus_range_high','max'))
                 .sort_values(['starters','qb_mode','teams']))
    else: summary=pd.DataFrame()
    summary.to_csv(OUT_SUMMARY,index=False)

    print('V0.18 DECISION-STABLE SCORING-CORE RANGE MAPPER')
    print(f'Formats: {len(out)} | resolved: {(out.status=="observed_range_candidate").sum()} | unresolved: {(out.status!="observed_range_candidate").sum()}')
    print('\nOBSERVED RANGE CANDIDATES')
    cols=['format_key','league_seasons','support','surplus_range_low','surplus_range_high','scoring_core_low','scoring_core_high','status']
    print(out[cols].to_string(index=False))
    if len(summary):
        print('\nSTARTN / QB-MODE / TEAM-COUNT SUMMARY')
        print(summary.to_string(index=False))
    print('\nCreated:')
    print(f'- {OUT}\n- {OUT_SUMMARY}')
    print('\nREADING CONTRACT')
    print('- These are broad observed range candidates, NOT exact optima or universal starters+X rules.')
    print('- Guards are relative to each format own curve; .25/.50/.75 remain sensitivity probes, not semantic thresholds.')
    print('- Unresolved means the observed +0..+6 window does not justify a range; do not force one.')
    print('- Low-support formats remain uncertain even when a candidate is shown.')
    print('- Before product promotion, verify adaptation is coherent across StartN, team count, SF/1QB, TE/TEP and FLEX structure.')

if __name__=='__main__': main()
