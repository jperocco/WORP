#!/usr/bin/env python3
"""WoRP Lab — Marginal Scoring Range V0.7.2

Turns V0.7.1 into the decision-facing diagnostic we actually need.
For each season/position/rank band, measure:
- positive WoRP produced per player in the band;
- positive WoRP produced per scoring week;
- repeatability (median positive weeks);
- marginal drop versus the immediately shallower band;
- share of total positional positive WoRP contributed by the band.

No universal materiality threshold is imposed. Output exposes the curve so we can
identify the zone where deeper rostered Scoring stops buying meaningful impact.
Wookiee 2023-25 is reference evidence only; league-native translation follows.
"""
from pathlib import Path
import pandas as pd

TRANS=Path('worp_roster_state_transitions_detail_v0_6_1.csv')
RANK=Path('wookiee_2023_2025_rankings_worp.csv')
POS=['QB','RB','WR','TE']
BANDS=[(1,8),(9,16),(17,24),(25,32),(33,40),(41,50),(51,60),(61,72),(73,90),(91,120),(121,999)]

def pick(df,names):
 for n in names:
  if n in df.columns:return n
 raise KeyError(names)

def main():
 d=pd.read_csv(TRANS);r=pd.read_csv(RANK)
 d.player_id=d.player_id.astype(str);r.player_id=r.player_id.astype(str)
 rc=pick(r,['position_rank','pos_rank','rank']);r[rc]=pd.to_numeric(r[rc],errors='coerce')
 ranks=r[['season','player_id','position',rc]].drop_duplicates(['season','player_id']).rename(columns={rc:'rank'})
 x=d[d.position.isin(POS)&d.state.isin(['STARTED','BENCHED_SCORING'])&d.weekly_worp.gt(0)].merge(ranks,on=['season','player_id','position'],how='left')
 x=x[x['rank'].notna()].copy()
 ps=x.groupby(['season','position','player_id','rank'],as_index=False).agg(positive_weeks=('week','nunique'),positive_worp=('weekly_worp','sum'))
 rows=[]
 for (yr,pos),g in ps.groupby(['season','position']):
  total=g.positive_worp.sum()
  for lo,hi in BANDS:
   q=g[g['rank'].between(lo,hi)]; n=len(q); weeks=q.positive_weeks.sum(); bw=q.positive_worp.sum()
   rows.append({'season':yr,'position':pos,'rank_lo':lo,'rank_hi':hi,'band':f'{pos}{lo}+' if hi==999 else f'{pos}{lo}-{pos}{hi}',
    'players':n,'positive_weeks':weeks,'median_positive_weeks':q.positive_weeks.median() if n else 0,
    'band_positive_worp':bw,'worp_per_player':bw/n if n else 0,'worp_per_positive_week':bw/weeks if weeks else 0,
    'share_position_positive_worp':bw/total if total else 0})
 b=pd.DataFrame(rows).sort_values(['season','position','rank_lo'])
 # Normalize adjacent marginal change inside each season/position before cross-season aggregation.
 b['prev_worp_per_player']=b.groupby(['season','position']).worp_per_player.shift(1)
 b['retention_vs_prev_band']=b.worp_per_player/b.prev_worp_per_player.replace(0,pd.NA)
 b['drop_vs_prev_band']=1-b.retention_vs_prev_band
 s=b.groupby(['position','rank_lo','rank_hi','band'],as_index=False).agg(
  seasons=('season','nunique'),median_worp_per_player=('worp_per_player','median'),
  median_worp_per_positive_week=('worp_per_positive_week','median'),median_positive_weeks=('median_positive_weeks','median'),
  median_share=('share_position_positive_worp','median'),median_retention_vs_prev=('retention_vs_prev_band','median'),
  median_drop_vs_prev=('drop_vs_prev_band','median'))
 b.to_csv('worp_scoring_marginal_range_by_season_v0_7_2.csv',index=False);s.to_csv('worp_scoring_marginal_range_summary_v0_7_2.csv',index=False)
 print('='*125);print('WORP MARGINAL SCORING RANGE V0.7.2');print('='*125)
 for pos in POS:
  print(f'\n{pos}');print(s[s.position==pos][['band','median_worp_per_player','median_worp_per_positive_week','median_positive_weeks','median_share','median_retention_vs_prev','median_drop_vs_prev']].to_string(index=False))
 print('\nREAD: seek a sustained collapse in per-player impact + repeatability, not a single arbitrary rank or positive-WoRP event.')
 print('No cutoff is auto-declared. The result must be interpreted for material decision impact, then translated league-natively.')
if __name__=='__main__':main()
