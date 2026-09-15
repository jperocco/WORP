#!/usr/bin/env python3
"""WoRP Lab — Empirical Scoring Range V0.7

Purpose: locate the observed positional rank range occupied by players who
actually generated positive WoRP while STARTED or BENCHED in Wookiee 2023-25.
This is a historical reference audit, NOT a universal league cutline.

Scoring = weekly WoRP > 0 while rostered (started or benched).
Non-Scoring = rostered weekly WoRP <= 0 or FREE. FREE is not required to score.

Outputs rank distributions and season consistency. The next product step is to
translate these reference ranges through each league's native slot/replacement
economics rather than hard-code Wookiee ranks.
"""
from pathlib import Path
import pandas as pd

TRANS=Path('worp_roster_state_transitions_detail_v0_6_1.csv')
RANK=Path('wookiee_2023_2025_rankings_worp.csv')
POS=['QB','RB','WR','TE']

def pick(df,names):
 for n in names:
  if n in df.columns:return n
 raise KeyError(f'missing {names}; columns={list(df.columns)}')

def main():
 if not TRANS.exists():raise FileNotFoundError(TRANS)
 if not RANK.exists():raise FileNotFoundError(RANK)
 d=pd.read_csv(TRANS);r=pd.read_csv(RANK)
 d.player_id=d.player_id.astype(str);r.player_id=r.player_id.astype(str)
 rc=pick(r,['position_rank','pos_rank','rank'])
 r[rc]=pd.to_numeric(r[rc],errors='coerce')
 ranks=r[['season','player_id','position',rc]].drop_duplicates(['season','player_id']).rename(columns={rc:'season_pos_rank'})
 # Current-week rostered scoring observations. STARTED must also have positive WoRP.
 x=d[d.position.isin(POS)&d.state.isin(['STARTED','BENCHED_SCORING'])&d.weekly_worp.gt(0)].merge(ranks,on=['season','player_id','position'],how='left')
 x=x[x.season_pos_rank.notna()].copy()
 # Player-season: how often was this player actually a positive-WoRP scoring option?
 ps=x.groupby(['season','position','player_id','season_pos_rank'],as_index=False).agg(scoring_weeks=('week','nunique'),total_scoring_worp=('weekly_worp','sum'))
 # Range landmarks by season. Use quantiles + max; no arbitrary semantic cutoff.
 season=[]
 for (yr,pos),g in ps.groupby(['season','position']):
  season.append({'season':yr,'position':pos,'scoring_players':g.player_id.nunique(),
   'rank_p50':g.season_pos_rank.quantile(.50),'rank_p75':g.season_pos_rank.quantile(.75),
   'rank_p90':g.season_pos_rank.quantile(.90),'rank_p95':g.season_pos_rank.quantile(.95),
   'deepest_scoring_rank':g.season_pos_rank.max(),
   'rank_p50_2plus_weeks':g.loc[g.scoring_weeks.ge(2),'season_pos_rank'].quantile(.50),
   'rank_p90_2plus_weeks':g.loc[g.scoring_weeks.ge(2),'season_pos_rank'].quantile(.90),
   'deepest_2plus_weeks':g.loc[g.scoring_weeks.ge(2),'season_pos_rank'].max(),
   'rank_p90_5plus_weeks':g.loc[g.scoring_weeks.ge(5),'season_pos_rank'].quantile(.90),
   'deepest_5plus_weeks':g.loc[g.scoring_weeks.ge(5),'season_pos_rank'].max()})
 s=pd.DataFrame(season)
 summary=s.groupby('position',as_index=False).agg(
  seasons=('season','nunique'),median_rank_p90=('rank_p90','median'),median_rank_p95=('rank_p95','median'),
  median_deepest=('deepest_scoring_rank','median'),median_rank_p90_2plus=('rank_p90_2plus_weeks','median'),
  median_deepest_2plus=('deepest_2plus_weeks','median'),median_rank_p90_5plus=('rank_p90_5plus_weeks','median'),
  median_deepest_5plus=('deepest_5plus_weeks','median'))
 ps.to_csv('worp_scoring_range_player_season_v0_7.csv',index=False);s.to_csv('worp_scoring_range_by_season_v0_7.csv',index=False);summary.to_csv('worp_scoring_range_summary_v0_7.csv',index=False)
 print('='*115);print('WORP EMPIRICAL SCORING RANGE V0.7 — Wookiee reference');print('='*115);print(summary.to_string(index=False))
 print('\nBY SEASON');print(s.to_string(index=False))
 print('\nREADING: 1-week positives show episodic tail; 2+ and 5+ scoring weeks progressively isolate repeatable Scoring depth.')
 print('No rank here is a universal cutline. League-native translation comes after the empirical range is located.')
if __name__=='__main__':main()
