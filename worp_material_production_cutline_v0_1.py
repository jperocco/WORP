#!/usr/bin/env python3
"""WoRP Lab — Material Production Cutline V0.1

Primary question:
At what positional depth does normal sporting production cease to generate
material winning impact with enough consistency and cross-season repeatability?

This is deliberately NOT a waiver threshold, roster-state classifier, or market-value model.
It uses the existing 2016-2025 WoRP history and seeks robust decision zones rather than
optimizing an exact rank cutoff.
"""
from pathlib import Path
import pandas as pd
import numpy as np

WEEKLY = Path('worp_2016_2025_weekly.csv')
RANKINGS = Path('worp_2016_2025_rankings.csv')
OUT_RANK = Path('worp_material_production_cutline_by_rank_v0_1.csv')
OUT_BAND = Path('worp_material_production_cutline_by_band_v0_1.csv')
OUT_SEASON = Path('worp_material_production_cutline_by_season_v0_1.csv')
POSITIONS = ['QB','RB','WR','TE']

for p in [WEEKLY, RANKINGS]:
    if not p.exists():
        raise SystemExit(f'STOP: required input missing: {p}')

w = pd.read_csv(WEEKLY)
r = pd.read_csv(RANKINGS)

# Resolve common schema variants without silently inventing fields.
def pick(df, names, label):
    for n in names:
        if n in df.columns:
            return n
    raise SystemExit(f'STOP: cannot identify {label}. Available columns: {list(df.columns)}')

season_c = pick(r, ['season','year'], 'season column in rankings')
pos_c = pick(r, ['position','pos'], 'position column in rankings')
rank_c = pick(r, ['rank','position_rank','pos_rank','worp_rank'], 'positional rank column in rankings')
worp_c = pick(r, ['worp','season_worp','total_worp'], 'WoRP column in rankings')
player_c = pick(r, ['player_id','gsis_id','player','player_name'], 'player identity column in rankings')

# Weekly is used only to estimate the scale of meaningful weekly impact, not to define
# a universal semantic hurdle. We expose distribution landmarks for PM/research review.
w_season = pick(w, ['season','year'], 'season column in weekly')
w_pos = pick(w, ['position','pos'], 'position column in weekly')
w_worp = pick(w, ['worp','weekly_worp'], 'WoRP column in weekly')

r = r[r[pos_c].isin(POSITIONS)].copy()
r[rank_c] = pd.to_numeric(r[rank_c], errors='coerce')
r[worp_c] = pd.to_numeric(r[worp_c], errors='coerce')
r = r.dropna(subset=[season_c,pos_c,rank_c,worp_c])
r[rank_c] = r[rank_c].astype(int)

w = w[w[w_pos].isin(POSITIONS)].copy()
w[w_worp] = pd.to_numeric(w[w_worp], errors='coerce')
positive_weekly = w.loc[w[w_worp] > 0, w_worp].dropna()
if positive_weekly.empty:
    raise SystemExit('STOP: no positive weekly WoRP observations found.')

landmarks = {
    'weekly_positive_p50': positive_weekly.quantile(.50),
    'weekly_positive_p75': positive_weekly.quantile(.75),
    'weekly_positive_p85': positive_weekly.quantile(.85),
    'weekly_positive_p90': positive_weekly.quantile(.90),
}

# Rank-level cross-season stability. The core evidence is magnitude + consistency + repeatability.
rank_rows=[]
for pos in POSITIONS:
    z=r[r[pos_c].eq(pos)]
    for rank, g in z.groupby(rank_c):
        vals=g[worp_c].dropna()
        if vals.empty: continue
        rank_rows.append({
            'position':pos,
            'rank':int(rank),
            'seasons_observed':int(g[season_c].nunique()),
            'median_season_worp':vals.median(),
            'mean_season_worp':vals.mean(),
            'p25_season_worp':vals.quantile(.25),
            'p75_season_worp':vals.quantile(.75),
            'share_seasons_positive_worp':(vals>0).mean(),
            'share_seasons_worp_ge_0_25':(vals>=.25).mean(),
            'share_seasons_worp_ge_0_50':(vals>=.50).mean(),
            'share_seasons_worp_ge_0_75':(vals>=.75).mean(),
        })
rank_df=pd.DataFrame(rank_rows).sort_values(['position','rank'])
rank_df.to_csv(OUT_RANK,index=False)

# Five-rank bands reduce false precision and make the transition zone visible.
band_rows=[]
for pos in POSITIONS:
    z=r[r[pos_c].eq(pos)].copy()
    if z.empty: continue
    z['band_start']=((z[rank_c]-1)//5)*5+1
    z['band_end']=z['band_start']+4
    for (bs,be),g in z.groupby(['band_start','band_end']):
        vals=g[worp_c].dropna()
        if vals.empty: continue
        # season-band median asks whether the whole depth region, not one outlier, remains material.
        sb=g.groupby(season_c)[worp_c].median()
        band_rows.append({
            'position':pos,
            'band_start':int(bs),'band_end':int(be),
            'player_seasons':len(vals),
            'seasons_observed':int(g[season_c].nunique()),
            'median_player_season_worp':vals.median(),
            'p75_player_season_worp':vals.quantile(.75),
            'median_season_band_worp':sb.median(),
            'share_seasons_band_median_positive':(sb>0).mean(),
            'share_seasons_band_median_ge_0_25':(sb>=.25).mean(),
            'share_seasons_band_median_ge_0_50':(sb>=.50).mean(),
            'share_seasons_band_median_ge_0_75':(sb>=.75).mean(),
        })
band_df=pd.DataFrame(band_rows).sort_values(['position','band_start'])
band_df.to_csv(OUT_BAND,index=False)

# Season-specific last ranks crossing sensitivity landmarks. These are descriptive landmarks,
# not the final cutline. Repeatability across seasons is the key diagnostic.
season_rows=[]
for (season,pos),g in r.groupby([season_c,pos_c]):
    g=g.sort_values(rank_c)
    for h in [0.0,.25,.50,.75]:
        hit=g[g[worp_c]>=h] if h>0 else g[g[worp_c]>0]
        season_rows.append({
            'season':season,'position':pos,'season_worp_landmark':h,
            'last_rank_meeting_landmark':int(hit[rank_c].max()) if len(hit) else np.nan,
            'players_meeting_landmark':len(hit),
        })
season_df=pd.DataFrame(season_rows).sort_values(['position','season_worp_landmark','season'])
season_df.to_csv(OUT_SEASON,index=False)

print('=== MATERIAL PRODUCTION CUTLINE V0.1 ===')
print('Question: where does normal positional production stop mattering enough to win?')
print('NOT a waiver threshold. NOT a market-value model. NOT an exact roster-state classifier.\n')
print('WEEKLY POSITIVE-WORP SCALE (distributional context only)')
for k,v in landmarks.items(): print(f'  {k}: {v:.4f}')

print('\nFIVE-RANK BANDS — CROSS-SEASON VIEW')
for pos in POSITIONS:
    print(f'\n{pos}')
    z=band_df[band_df.position.eq(pos)].head(20)
    if len(z):
        print(z[['band_start','band_end','seasons_observed','median_season_band_worp','share_seasons_band_median_positive','share_seasons_band_median_ge_0_25','share_seasons_band_median_ge_0_50']].round(3).to_string(index=False))

print('\nSEASON LANDMARKS')
for pos in POSITIONS:
    print(f'\n{pos}')
    z=season_df[season_df.position.eq(pos)]
    if len(z):
        p=z.pivot(index='season',columns='season_worp_landmark',values='last_rank_meeting_landmark')
        print(p.to_string())

print('\nDECISION CONTRACT')
print('- Magnitude + consistency + cross-season repeatability define the useful region.')
print('- Five-rank bands are primary to avoid fake precision.')
print('- 0.25/0.50/0.75 season-WoRP landmarks are sensitivity, not semantic truth.')
print('- Small residual WoRP after the material region is economic noise unless it changes a roster decision.')
print('- Do not call the resulting frontier a waiver threshold.')
print('- If adjacent bands differ only trivially and the roster decision is unchanged, STOP.')
print(f'\nCreated: {OUT_RANK.name}')
print(f'Created: {OUT_BAND.name}')
print(f'Created: {OUT_SEASON.name}')
