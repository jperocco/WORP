#!/usr/bin/env python3
"""WoRP Lab — League-Native Positional Curve Ranges V0.8

First-principles roster-construction input: expose WoRP as a POSITIONAL curve.
No waiver logic, no player-normalized WoRP, no exact cutline, no auto-classification.
We deliberately use ranges/bands because roster construction is a game decision,
not an exercise in false rank precision.

For each tested league format, season and position, calculate season WoRP, rank the
position, then summarize 5-rank bands. Cross-season medians/p25/p75 expose curve
shape and stability. Adjacent-band delta exposes where additional positional depth
stops buying meaningful WoRP. Interpretation happens AFTER seeing the curve.
"""
from pathlib import Path
import pandas as pd
from worp_engine import LeagueSettings, calculate_season_worp
from nflverse_loader import load_nflverse_player_weeks

SEASONS=list(range(2016,2026)); POS=['QB','RB','WR','TE']
FORMATS={
 '10T_1QB_Start8':LeagueSettings(teams=10,qb=1,rb=2,wr=2,te=1,flex=2,superflex=0,ppr=.5,te_premium=0),
 '12T_1QB_Start8':LeagueSettings(teams=12,qb=1,rb=2,wr=2,te=1,flex=2,superflex=0,ppr=.5,te_premium=0),
 '12T_1QB_Start11':LeagueSettings(teams=12,qb=1,rb=2,wr=3,te=1,flex=4,superflex=0,ppr=.5,te_premium=0),
 '12T_SF_Start11':LeagueSettings(teams=12,qb=1,rb=2,wr=3,te=1,flex=3,superflex=1,ppr=.5,te_premium=0),
 '12T_SF_2TE_TEP_Start11':LeagueSettings(teams=12,qb=1,rb=2,wr=3,te=2,flex=2,superflex=1,ppr=.5,te_premium=1.0),
 '14T_SF_Start10':LeagueSettings(teams=14,qb=1,rb=2,wr=2,te=1,flex=3,superflex=1,ppr=.5,te_premium=0),
}
OUT_DETAIL=Path('worp_positional_curve_ranges_detail_v0_8.csv');OUT_SUM=Path('worp_positional_curve_ranges_summary_v0_8.csv')
rows=[]
for fmt,settings in FORMATS.items():
 print('\n'+fmt)
 data=load_nflverse_player_weeks(SEASONS,settings)
 for season in SEASONS:
  d=data[data.season.eq(season)].copy()
  if d.empty:continue
  _,ranking=calculate_season_worp(d,settings,replacement_band=6,n_sims=4000,seed=7)
  ranking=ranking.copy();ranking['position']=ranking.position.astype(str).str.upper()
  ranking['rank']=ranking.groupby('position').worp.rank(method='first',ascending=False).astype(int)
  ranking['band_start']=((ranking['rank']-1)//5)*5+1;ranking['band_end']=ranking.band_start+4
  for (pos,bs,be),g in ranking[ranking.position.isin(POS)].groupby(['position','band_start','band_end']):
   if bs>120:continue
   rows.append({'format':fmt,'season':season,'position':pos,'band_start':int(bs),'band_end':int(be),
    'band_median_worp':g.worp.median(),'band_p25_worp':g.worp.quantile(.25),'band_p75_worp':g.worp.quantile(.75)})
  print(f'  {season}: done')
detail=pd.DataFrame(rows).sort_values(['format','position','season','band_start'])
detail.to_csv(OUT_DETAIL,index=False)
summary=(detail.groupby(['format','position','band_start','band_end'],as_index=False)
 .agg(seasons=('season','nunique'),median_band_worp=('band_median_worp','median'),p25_band_worp=('band_median_worp',lambda x:x.quantile(.25)),p75_band_worp=('band_median_worp',lambda x:x.quantile(.75))))
summary=summary.sort_values(['format','position','band_start'])
summary['prev_band_worp']=summary.groupby(['format','position']).median_band_worp.shift(1)
summary['delta_from_prev_band']=summary.median_band_worp-summary.prev_band_worp
summary.to_csv(OUT_SUM,index=False)
print('\n'+'='*110);print('POSITIONAL WORP CURVE — 5-RANK RANGES');print('='*110)
for fmt in FORMATS:
 print(f'\n### {fmt}')
 for pos in POS:
  z=summary[(summary.format==fmt)&(summary.position==pos)].head(18).copy()
  if z.empty:continue
  z['range']=pos+z.band_start.astype(str)+'-'+pos+z.band_end.astype(str)
  print(f'\n{pos}');print(z[['range','median_band_worp','p25_band_worp','p75_band_worp','delta_from_prev_band']].round(3).to_string(index=False))
print('\nREADING CONTRACT')
print('- Read ranges/zones, not exact ranks.')
print('- Look for sustained curve compression where deeper bands cease to change roster decisions materially.')
print('- Do not auto-label Scoring/Transition/Non-Scoring from one numeric threshold.')
print('- Similar adjacent ranges that imply the same roster decision are the same answer; STOP rather than chase rank precision.')
print('- Format shifts must move the curve coherently before any roster-construction rule is accepted.')
print('\nCreated:',OUT_DETAIL.name);print('Created:',OUT_SUM.name)
