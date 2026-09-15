#!/usr/bin/env python3
"""WoRP Lab — Transparent Positional Curve Review V0.8.2

V0.8.1 showed that an automatic geometric breakpoint can confuse flattening with
real economic impact. V0.8.2 intentionally does LESS: it presents the evidence
needed to choose broad roster-construction ranges without auto-declaring a cutoff.

Inputs: V0.8 cross-season 5-rank positional curve.
Outputs, by format/position:
- median WoRP by 5-rank band;
- adjacent-band WoRP loss;
- WoRP retained vs the top band (descriptive scale only);
- cross-season IQR and sign stability;
- compact review window around the economically relevant portion of the curve.

No waiver logic. No per-player normalization. No universal threshold. No automatic
Scoring/Transition/Non-Scoring label. The point is to make magnitude + compression +
stability visible together, then accept a RANGE when further precision cannot change
a roster decision.
"""
from pathlib import Path
import pandas as pd
import numpy as np

IN=Path('worp_positional_curve_ranges_summary_v0_8.csv')
OUT=Path('worp_positional_curve_review_v0_8_2.csv')
if not IN.exists(): raise SystemExit(f'STOP: missing {IN}; run V0.8 first.')
d=pd.read_csv(IN).sort_values(['format','position','band_start']).copy()
need={'format','position','band_start','band_end','seasons','median_band_worp','p25_band_worp','p75_band_worp'}
miss=need-set(d.columns)
if miss: raise SystemExit(f'STOP: missing columns {sorted(miss)}')

rows=[]
for (fmt,pos),g0 in d.groupby(['format','position'],sort=False):
 g=g0.sort_values('band_start').copy().reset_index(drop=True)
 top=abs(float(g.median_band_worp.iloc[0]))
 g['delta_prev']=g.median_band_worp.diff()
 g['abs_loss_prev']=-g.delta_prev
 g['retained_vs_top']=g.median_band_worp/top if top else np.nan
 g['iqr_width']=g.p75_band_worp-g.p25_band_worp
 # Sign stability: IQR entirely above/below zero vs crossing zero.
 g['sign_stability']=np.where(g.p25_band_worp>0,'POS_STABLE',np.where(g.p75_band_worp<0,'NEG_STABLE','CROSSES_ZERO'))
 # Local compression is descriptive only: median loss across current + previous 2 transitions.
 g['local3_abs_loss']=g.abs_loss_prev.rolling(3,min_periods=1).median()
 # Keep a compact window through the first sustained negative region, plus 3 bands.
 neg=(g.p75_band_worp<0)
 stop_idx=len(g)-1
 if neg.any():
  first=int(np.flatnonzero(neg.to_numpy())[0]); stop_idx=min(len(g)-1,first+3)
 # Always retain enough depth to see the transition; cap at rank 100 for readable output.
 stop_idx=max(stop_idx,min(len(g)-1,11))
 view=g.iloc[:stop_idx+1]
 for _,r in view.iterrows():
  rows.append({'format':fmt,'position':pos,'band_start':int(r.band_start),'band_end':int(r.band_end),'seasons':int(r.seasons),
   'median_worp':r.median_band_worp,'p25_worp':r.p25_band_worp,'p75_worp':r.p75_band_worp,
   'loss_vs_prev_band':r.abs_loss_prev,'local3_loss':r.local3_abs_loss,'retained_vs_top':r.retained_vs_top,
   'iqr_width':r.iqr_width,'sign_stability':r.sign_stability})

out=pd.DataFrame(rows)
out.to_csv(OUT,index=False)
print('='*132);print('POSITIONAL WORP CURVE REVIEW V0.8.2 — MAGNITUDE + COMPRESSION + STABILITY');print('='*132)
for fmt,fg in out.groupby('format',sort=False):
 print(f'\n### {fmt}')
 for pos,pg in fg.groupby('position',sort=False):
  z=pg.copy();z['range']=pos+z.band_start.astype(str)+'-'+pos+z.band_end.astype(str)
  # Print from rank 6 onward; top band retained as scale in CSV but not needed in terminal review.
  z=z[z.band_start>=6]
  print(f'\n{pos}')
  print(z[['range','median_worp','loss_vs_prev_band','local3_loss','retained_vs_top','p25_worp','p75_worp','sign_stability']].round(3).to_string(index=False))
print('\nREVIEW CONTRACT')
print('- Choose broad economic ranges from magnitude + compression + cross-season stability together.')
print('- Do not infer a cutoff from zero crossing alone; zero is context, not the definition of materiality.')
print('- Do not infer a cutoff from slope/compression alone; V0.8.1 showed why that fails.')
print('- Nearby boundaries that imply the same roster decision are the same answer.')
print('- If a position cannot be narrowed beyond ~10 ranks without arbitrary assumptions, keep the wider range and move on.')
print('- Once ranges are decision-stable across formats, STOP curve research and proceed to slot-eligibility / roster-capacity ranges.')
print('\nCreated:',OUT.name)
