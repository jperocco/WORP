#!/usr/bin/env python3
"""WoRP Lab — Positional Curve Zone Candidates V0.8.1

Purpose: convert V0.8 league-native positional curves into RANGE candidates for
Strong Impact -> Transition -> Economic Tail, without pretending an exact rank
cutline exists.

This is a diagnostic, not a semantic oracle. It uses curve SHAPE and cross-season
stability. No waiver logic, no per-player WoRP, no asset value, no universal WoRP
hurdle. Candidate boundaries are snapped to 5-rank bands and uncertainty is reported
as ranges. If nearby boundaries imply the same roster decision, treat them as one
answer and STOP rather than optimize rank precision.

Method (deliberately simple/reversible):
1) Work on V0.8 cross-season median 5-rank positional curve.
2) Calculate local 3-band absolute decline (slope magnitude).
3) Define each position/format's own early-curve reference slope as median decline
   across the first six available band transitions (through roughly rank 35).
4) A compression candidate begins where the local 3-band decline falls to <=50% of
   that league/position reference AND remains compressed in at least 2 of 3 bands.
5) Tail candidate begins only after compression, where |median WoRP| is small relative
   to that position/format's top-band magnitude (<=5%) AND local decline remains
   compressed. 5% is a sensitivity rule for candidate discovery, NOT a definition of
   materiality; 3% and 8% are also reported to expose boundary sensitivity.
6) Cross-season p25/p75 width is carried into output; unstable boundaries must not be
   promoted to product logic.

The PM/researcher still interprets the candidate zones. This script is designed to
show whether broad ranges are obvious enough to proceed to roster construction.
"""
from pathlib import Path
import pandas as pd
import numpy as np

IN=Path('worp_positional_curve_ranges_summary_v0_8.csv')
OUT=Path('worp_positional_curve_zones_v0_8_1.csv')
if not IN.exists(): raise SystemExit(f'STOP: missing {IN}; run V0.8 first.')
d=pd.read_csv(IN).sort_values(['format','position','band_start']).copy()
need={'format','position','band_start','band_end','median_band_worp','p25_band_worp','p75_band_worp'}
miss=need-set(d.columns)
if miss: raise SystemExit(f'STOP: missing columns: {sorted(miss)}')

rows=[]
for (fmt,pos),g0 in d.groupby(['format','position'],sort=False):
 g=g0.copy().sort_values('band_start').reset_index(drop=True)
 # Positive decline means the curve loses WoRP as rank deepens.
 g['decline']=-(g['median_band_worp'].diff())
 g['local3_decline']=g['decline'].rolling(3,min_periods=2).median()
 early=g.loc[(g.band_start<=31)&g.decline.notna(),'decline']
 early=early[early>0]
 ref=float(early.median()) if len(early) else np.nan
 g['compressed']=g.local3_decline.le(ref*.50) if np.isfinite(ref) else False
 # Require persistence: at least two compressed flags in current + next two bands.
 future2=g['compressed'].astype(int).rolling(3,min_periods=1).sum().shift(-2)
 future1=g['compressed'].astype(int).rolling(2,min_periods=1).sum().shift(-1)
 g['compression_persistent']=((future2>=2)|(future1>=2)) & g['compressed']
 comp=g[g.compression_persistent]
 comp_start=int(comp.band_start.iloc[0]) if len(comp) else np.nan
 comp_end=int(comp.band_end.iloc[0]) if len(comp) else np.nan
 top=abs(float(g.median_band_worp.iloc[0]))
 sensitivity={}
 for pct in [.03,.05,.08]:
  small=g.median_band_worp.abs().le(top*pct)
  after=g.band_start.ge(comp_start) if np.isfinite(comp_start) else pd.Series(False,index=g.index)
  cand=g[small & g.compression_persistent & after]
  # If compression flag temporarily breaks after the transition, permit a stable
  # small-WoRP tail when the next two observed declines are also small vs reference.
  if cand.empty and np.isfinite(comp_start):
   cand=g[small & after & g.local3_decline.le(ref*.65)]
  sensitivity[pct]=int(cand.band_start.iloc[0]) if len(cand) else np.nan
 tail_start=sensitivity[.05]
 # Boundary uncertainty is intentionally one band on either side. This encodes the
 # product contract that adjacent ranks are not worth fake precision.
 def zone(x):
  if not np.isfinite(x): return (np.nan,np.nan)
  return (max(1,int(x)-5),int(x)+5)
 c_lo,c_hi=zone(comp_start); t_lo,t_hi=zone(tail_start)
 rows.append({
  'format':fmt,'position':pos,'reference_early_decline':ref,
  'transition_candidate_start':comp_start,'transition_boundary_low':c_lo,'transition_boundary_high':c_hi,
  'tail_candidate_start_3pct':sensitivity[.03],'tail_candidate_start_5pct':tail_start,'tail_candidate_start_8pct':sensitivity[.08],
  'tail_boundary_low':t_lo,'tail_boundary_high':t_hi,
  'curve_top_band_worp':g.median_band_worp.iloc[0],
  'median_cross_season_iqr_width':(g.p75_band_worp-g.p25_band_worp).median(),
 })

out=pd.DataFrame(rows)
out['tail_sensitivity_span']=out[['tail_candidate_start_3pct','tail_candidate_start_5pct','tail_candidate_start_8pct']].max(axis=1)-out[['tail_candidate_start_3pct','tail_candidate_start_5pct','tail_candidate_start_8pct']].min(axis=1)
out['tail_sensitivity_stable']=out.tail_sensitivity_span.le(10)
out.to_csv(OUT,index=False)

print('='*125);print('POSITIONAL CURVE ZONE CANDIDATES V0.8.1');print('='*125)
for fmt,g in out.groupby('format',sort=False):
 print(f'\n### {fmt}')
 z=g[['position','transition_boundary_low','transition_boundary_high','tail_boundary_low','tail_boundary_high','tail_candidate_start_3pct','tail_candidate_start_5pct','tail_candidate_start_8pct','tail_sensitivity_stable','median_cross_season_iqr_width']].copy()
 print(z.round(3).to_string(index=False))
print('\nINTERPRETATION CONTRACT')
print('- These are candidate ZONES, not exact cutlines.')
print('- 3/5/8% are sensitivity probes only; they do not define Scoring or Non-Scoring.')
print('- A stable broad range is sufficient if nearby boundaries imply the same roster decision.')
print('- If sensitivity moves a boundary >10 ranks, mark it unresolved rather than force a result.')
print('- League-format movement must remain economically coherent.')
print('- Next step only after review: translate accepted positional zones into roster-capacity ranges using slot eligibility.')
print('\nCreated:',OUT.name)
