#!/usr/bin/env python3
"""WoRP Lab — Impact-Weighted Scoring Range V0.7.1

Corrects V0.7's 'any positive week = Scoring' mistake.
Question: by season/position rank, where is the WoRP that actually matters concentrated?

No arbitrary absolute WoRP threshold is imposed. We measure cumulative share of
positive rostered WoRP captured by progressively deeper season-rank ranges, plus
repeatability (positive scoring weeks). The economic frontier is therefore read
from marginal WoRP added by deeper rank bands, not from mere existence of a hit.

Wookiee 2023-25 is a reference audit only; league-native translation remains mandatory.
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
 # Positive WoRP while rostered; started + bench. This measures produced Scoring value,
 # not lineup capture. Bench value matters for roster construction.
 x=d[d.position.isin(POS)&d.state.isin(['STARTED','BENCHED_SCORING'])&d.weekly_worp.gt(0)].merge(ranks,on=['season','player_id','position'],how='left')
 x=x[x['rank'].notna()].copy()
 ps=x.groupby(['season','position','player_id','rank'],as_index=False).agg(positive_weeks=('week','nunique'),positive_worp=('weekly_worp','sum'))
 rows=[]
 for (yr,pos),g in ps.groupby(['season','position']):
  total=g.positive_worp.sum()
  for lo,hi in BANDS:
   q=g[g['rank'].between(lo,hi)]
   bw=q.positive_worp.sum(); label=f'{pos}{lo}+' if hi==999 else f'{pos}{lo}-{pos}{hi}'
   rows.append({'season':yr,'position':pos,'rank_lo':lo,'rank_hi':hi,'band':label,
    'players_with_positive_worp':q.player_id.nunique(),'median_positive_weeks':q.positive_weeks.median() if len(q) else 0,
    'band_positive_worp':bw,'share_of_position_positive_worp':bw/total if total else 0})
 b=pd.DataFrame(rows).sort_values(['season','position','rank_lo'])
 b['cumulative_share']=b.groupby(['season','position']).share_of_position_positive_worp.cumsum()
 # Cross-season medians show both impact and repeatability of each deeper band.
 s=b.groupby(['position','rank_lo','rank_hi','band'],as_index=False).agg(
  seasons=('season','nunique'),median_band_worp=('band_positive_worp','median'),
  median_share=('share_of_position_positive_worp','median'),median_cumulative_share=('cumulative_share','median'),
  median_players=('players_with_positive_worp','median'),median_positive_weeks=('median_positive_weeks','median'))
 # Marginal tail remaining after each band: directly answers how much positional WoRP lies deeper.
 s['median_tail_share_after_band']=1-s.median_cumulative_share
 b.to_csv('worp_scoring_impact_range_by_season_v0_7_1.csv',index=False);s.to_csv('worp_scoring_impact_range_summary_v0_7_1.csv',index=False)
 print('='*120);print('WORP IMPACT-WEIGHTED SCORING RANGE V0.7.1');print('='*120)
 for pos in POS:
  print(f'\n{pos}');print(s[s.position==pos][['band','median_band_worp','median_share','median_cumulative_share','median_tail_share_after_band','median_positive_weeks']].to_string(index=False))
 print('\nREAD: focus on where deeper bands stop adding material WoRP AND repeatability collapses. No positive-hit cutoff is used.')
 print('Do not promote the resulting Wookiee rank to universal product logic; next step is league-native translation.')
if __name__=='__main__':main()
