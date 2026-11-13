#!/usr/bin/env python3
"""WoRP Lab — League-Native Material Production Frontier V0.2

Priority-zero test: WoRP must adapt when the LEAGUE changes.
Wookiee is only one reference case.

This audit recomputes WoRP from nflverse under deliberately different league
formats, then asks whether the material positional frontier moves in economically
sensible ways. Raw ranks are diagnostics; the product answer remains league-native.
"""
from pathlib import Path
import pandas as pd
import numpy as np

from worp_engine import LeagueSettings, calculate_season_worp
from nflverse_loader import load_nflverse_player_weeks

SEASONS=list(range(2016,2026))
POSITIONS=['QB','RB','WR','TE']
OUT_DETAIL=Path('worp_league_native_material_frontier_detail_v0_2.csv')
OUT_SUM=Path('worp_league_native_material_frontier_summary_v0_2.csv')
OUT_DELTA=Path('worp_league_native_material_frontier_deltas_v0_2.csv')

# Deliberately different structural environments. These are test fixtures, not
# claims about the most common fantasy formats.
FORMATS={
    '10T_1QB_Start8': LeagueSettings(teams=10,qb=1,rb=2,wr=2,te=1,flex=2,superflex=0,ppr=.5,te_premium=0),
    '12T_1QB_Start8': LeagueSettings(teams=12,qb=1,rb=2,wr=2,te=1,flex=2,superflex=0,ppr=.5,te_premium=0),
    '12T_1QB_Start11': LeagueSettings(teams=12,qb=1,rb=2,wr=3,te=1,flex=4,superflex=0,ppr=.5,te_premium=0),
    '12T_SF_Start11': LeagueSettings(teams=12,qb=1,rb=2,wr=3,te=1,flex=3,superflex=1,ppr=.5,te_premium=0),
    '12T_SF_2TE_TEP_Start11': LeagueSettings(teams=12,qb=1,rb=2,wr=3,te=2,flex=2,superflex=1,ppr=.5,te_premium=1.0),
    '14T_SF_Start10': LeagueSettings(teams=14,qb=1,rb=2,wr=2,te=1,flex=3,superflex=1,ppr=.5,te_premium=0),
}

# Fixed sensitivity landmarks. They are NOT universal semantic definitions of
# materiality; movement must survive multiple landmarks to count as robust.
HURDLES=[.25,.50,.75]

all_rows=[]
for fmt,settings in FORMATS.items():
    print('\n'+'='*90); print(fmt); print('='*90)
    # Load once per format because scoring itself changes with PPR/TE premium.
    data=load_nflverse_player_weeks(SEASONS,settings)
    for season in SEASONS:
        d=data[data.season.eq(season)].copy()
        if d.empty:
            print(f'  {season}: missing; skip')
            continue
        weekly,ranking=calculate_season_worp(d,settings,replacement_band=6,n_sims=4000,seed=7)
        ranking=ranking.copy()
        ranking['position']=ranking['position'].astype(str).str.upper()
        ranking['position_rank']=ranking.groupby('position')['worp'].rank(method='first',ascending=False).astype(int)
        for pos in POSITIONS:
            p=ranking[ranking.position.eq(pos)].sort_values('position_rank')
            if p.empty: continue
            for h in HURDLES:
                hit=p[p.worp.ge(h)]
                all_rows.append({
                    'format':fmt,'season':season,'position':pos,'worp_landmark':h,
                    'last_rank_meeting_landmark':int(hit.position_rank.max()) if len(hit) else np.nan,
                    'players_meeting_landmark':len(hit),
                    'replacement_starter_count_median':pd.to_numeric(weekly.loc[weekly.position.eq(pos),'replacement_starter_count'],errors='coerce').median() if 'replacement_starter_count' in weekly.columns else np.nan,
                    'replacement_effective_rank_median':pd.to_numeric(weekly.loc[weekly.position.eq(pos),'replacement_effective_rank'],errors='coerce').median() if 'replacement_effective_rank' in weekly.columns else np.nan,
                })
        print(f'  {season}: done')

detail=pd.DataFrame(all_rows)
if detail.empty: raise SystemExit('STOP: no frontier observations produced.')
detail.to_csv(OUT_DETAIL,index=False)

summary=(detail.groupby(['format','position','worp_landmark'],as_index=False)
    .agg(seasons_observed=('season','nunique'),
         median_last_rank=('last_rank_meeting_landmark','median'),
         p25_last_rank=('last_rank_meeting_landmark',lambda x:x.quantile(.25)),
         p75_last_rank=('last_rank_meeting_landmark',lambda x:x.quantile(.75)),
         min_last_rank=('last_rank_meeting_landmark','min'),
         max_last_rank=('last_rank_meeting_landmark','max'),
         median_replacement_effective_rank=('replacement_effective_rank_median','median')))
summary.to_csv(OUT_SUM,index=False)

# Compare every fixture to 12T 1QB Start8. This is a directional adaptability audit,
# not a claim that this format is a universal baseline.
base='12T_1QB_Start8'
b=summary[summary.format.eq(base)][['position','worp_landmark','median_last_rank']].rename(columns={'median_last_rank':'baseline_median_last_rank'})
delta=summary.merge(b,on=['position','worp_landmark'],how='left')
delta['rank_shift_vs_12T_1QB_Start8']=delta.median_last_rank-delta.baseline_median_last_rank
delta.to_csv(OUT_DELTA,index=False)

print('\n\n=== LEAGUE-NATIVE MATERIAL FRONTIER V0.2 ===')
for h in HURDLES:
    print(f'\nLANDMARK >= {h:.2f} season WoRP — median last rank across seasons')
    z=summary[summary.worp_landmark.eq(h)]
    print(z.pivot(index='format',columns='position',values='median_last_rank').to_string())

print('\nADAPTABILITY DELTAS VS 12T 1QB START8')
for h in HURDLES:
    print(f'\nLANDMARK {h:.2f}')
    z=delta[delta.worp_landmark.eq(h)]
    print(z.pivot(index='format',columns='position',values='rank_shift_vs_12T_1QB_Start8').to_string())

print('\nVALIDATION QUESTIONS')
print('- Team-count test: does 10T vs 12T vs 14T move frontiers materially?')
print('- Start-depth test: does Start11 deepen the relevant RB/WR/TE economy vs Start8?')
print('- SF test: does adding a QB-eligible shared slot materially deepen QB?')
print('- 2TE/TEP test: does TE economics move materially rather than remain Wookiee-fixed?')
print('- Shared-slot test: RB/WR/TE movement must emerge from FLEX competition, not hard-coded positional ownership.')
print('- Robustness: prioritize shifts that survive multiple seasons and more than one WoRP landmark.')
print('- If a format change fails to move a position that should economically move, STOP: adaptability defect before roster construction.')
print('\nCreated:',OUT_DETAIL.name); print('Created:',OUT_SUM.name); print('Created:',OUT_DELTA.name)
