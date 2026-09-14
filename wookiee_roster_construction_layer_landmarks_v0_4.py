from pathlib import Path
import pandas as pd

# Roster Construction Layer Landmarks V0.4
# ------------------------------------------------------------
# Purpose:
# Translate the V0.3 usage/economic bands into per-roster positional counts.
# This is still descriptive evidence, not an optimized roster prescription.
# It answers: historically, how many players at each position occupied recurring,
# depth, episodic, or unused lineup-use bands on a typical roster-season?
#
# IMPORTANT: these bands are empirical utilization landmarks only. They are NOT
# permanent player classes and are NOT the final Starter / Scoring Bench /
# Non-Scoring allocation.

ROOT = Path('.')
FULL = ROOT / 'wookiee_full_roster_blocked_worp_player_week_v0_5.csv'
TRANS = ROOT / 'wookiee_roster_construction_transition_zone_v0_3.csv'
OUT_COUNTS = ROOT / 'wookiee_roster_construction_layer_counts_v0_4.csv'
OUT_SUMMARY = ROOT / 'wookiee_roster_construction_layer_landmarks_v0_4.csv'

for p in [FULL, TRANS]:
    if not p.exists():
        raise SystemExit(f'STOP: required input missing: {p}')

full = pd.read_csv(FULL)
trans = pd.read_csv(TRANS)
needed = {'season','week','roster_id','player_id','position','real_state'}
missing = needed - set(full.columns)
if missing:
    raise SystemExit(f'STOP: full-roster input missing columns: {sorted(missing)}')

full = full[full.position.isin(['QB','RB','WR','TE'])].copy()
real_values = set(full.real_state.dropna().astype(str).unique())
if not real_values.issubset({'REAL_STARTED','REAL_BENCHED'}):
    raise SystemExit(f'STOP: unexpected real_state values: {sorted(real_values)}')
full['real_started'] = full.real_state.eq('REAL_STARTED')

usage = (
    full.groupby(['season','roster_id','player_id','position'], as_index=False)
        .agg(real_starts=('real_started','sum'), observed_weeks=('week','nunique'))
)

def usage_band(x):
    if x >= 10: return '10+'
    if x >= 8: return '8-9'
    if x >= 5: return '5-7'
    if x >= 3: return '3-4'
    if x >= 1: return '1-2'
    return '0'

usage['usage_band'] = usage.real_starts.map(usage_band)
order = ['10+','8-9','5-7','3-4','1-2','0']

# Complete roster-season-position grid so zero counts are retained.
rosters = usage[['season','roster_id']].drop_duplicates()
positions = pd.DataFrame({'position':['QB','RB','WR','TE']})
bands = pd.DataFrame({'usage_band':order})
grid = rosters.merge(positions, how='cross').merge(bands, how='cross')
counts = (
    usage.groupby(['season','roster_id','position','usage_band'], as_index=False)
         .size().rename(columns={'size':'players'})
)
counts = grid.merge(counts, on=['season','roster_id','position','usage_band'], how='left')
counts['players'] = counts.players.fillna(0).astype(int)
counts.to_csv(OUT_COUNTS, index=False)

summary = (
    counts.groupby(['position','usage_band'], as_index=False)
          .agg(
              roster_count=('roster_id','size'),
              players_median=('players','median'),
              players_mean=('players','mean'),
              players_p25=('players',lambda s:s.quantile(.25)),
              players_p75=('players',lambda s:s.quantile(.75)),
          )
)

# Attach V0.3 economic landmarks for the same mutually exclusive band.
keep = [
    'position','usage_band','n_player_seasons','median_pos_rank','median_worp',
    'share_inside_starter_frontier','share_inside_replacement_frontier'
]
missing_trans = set(keep) - set(trans.columns)
if missing_trans:
    raise SystemExit(f'STOP: V0.3 output missing columns: {sorted(missing_trans)}')
summary = summary.merge(trans[keep], on=['position','usage_band'], how='left', validate='one_to_one')
summary['usage_band'] = pd.Categorical(summary.usage_band, categories=order, ordered=True)
summary = summary.sort_values(['position','usage_band'])
summary.to_csv(OUT_SUMMARY, index=False)

print('=== ROSTER CONSTRUCTION LAYER LANDMARKS V0.4 ===')
print(f'roster-seasons: {len(rosters):,}')
print('\nTypical roster composition by realized usage band:')
for pos in ['QB','RB','WR','TE']:
    print(f'\n{pos}')
    p = summary[summary.position.eq(pos)]
    for _,r in p.iterrows():
        econ = 'NA' if pd.isna(r.median_pos_rank) else f'{pos}{int(round(r.median_pos_rank))}'
        worp = 'NA' if pd.isna(r.median_worp) else f'{r.median_worp:.3f}'
        print(
            f"  {str(r.usage_band):>3}: median roster count={r.players_median:.1f} "
            f"(IQR {r.players_p25:.1f}-{r.players_p75:.1f}) | economic median={econ} | WoRP={worp}"
        )

# Aggregate practical descriptive buckets, still not semantic final states.
# recurring = 8+ starts; depth = 5-7; episodic = 1-4; unused = 0.
u = usage.copy()
def bucket(x):
    if x >= 8: return 'RECURRING_8PLUS'
    if x >= 5: return 'DEPTH_5_7'
    if x >= 1: return 'EPISODIC_1_4'
    return 'UNUSED_0'
u['bucket'] = u.real_starts.map(bucket)
agg = u.groupby(['season','roster_id','position','bucket'], as_index=False).size().rename(columns={'size':'players'})
agg_grid = rosters.merge(positions,how='cross').merge(pd.DataFrame({'bucket':['RECURRING_8PLUS','DEPTH_5_7','EPISODIC_1_4','UNUSED_0']}),how='cross')
agg = agg_grid.merge(agg,on=['season','roster_id','position','bucket'],how='left')
agg['players']=agg.players.fillna(0)
agg_summary=(agg.groupby(['position','bucket'],as_index=False)
               .agg(players_median=('players','median'),players_mean=('players','mean')))
print('\nCompact utilization architecture (descriptive only):')
print(agg_summary.to_string(index=False))

print('\nDECISION GATE')
print('- V0.4 gives roster-slot magnitude, not a final prescription.')
print('- Next step is to compare DEPTH_5_7 / EPISODIC_1_4 economics across positions against optionality evidence.')
print('- If that comparison does not change a roster-allocation decision, STOP instead of tuning rank cutoffs.')
print(f'\nCreated: {OUT_COUNTS.name}')
print(f'Created: {OUT_SUMMARY.name}')
