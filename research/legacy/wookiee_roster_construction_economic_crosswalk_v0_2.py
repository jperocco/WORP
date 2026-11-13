from pathlib import Path
import pandas as pd
import numpy as np

# Roster Construction Economic Crosswalk V0.2
# ------------------------------------------------------------
# Purpose:
# Cross actual historical lineup-use depth with season positional WoRP rank.
# This is an evidence crosswalk, NOT a semantic state classifier and NOT a
# universal Starter / Scoring Bench / Optionality cutoff.
#
# It deliberately joins actual roster-season player usage to the economic
# ranking of the SAME player in the SAME season. This avoids the crude shortcut
# of multiplying roster depth by league size and calling that a positional rank.
#
# Inputs are expected to exist locally in the WoRP repo.

ROOT = Path('.')
FULL_PATH = ROOT / 'wookiee_full_roster_blocked_worp_player_week_v0_5.csv'
RANK_PATH = ROOT / 'wookiee_2023_2025_rankings_worp.csv'

for p in [FULL_PATH, RANK_PATH]:
    if not p.exists():
        raise SystemExit(f'STOP: required input missing: {p}')

full = pd.read_csv(FULL_PATH)
rank = pd.read_csv(RANK_PATH)

full_required = {
    'season','week','roster_id','player_id','player_name','position',
    'weekly_worp','real_state','oracle_state'
}
rank_required = {
    'season','player_id','player_name','position','games','worp','pos_rank',
    'avg_starter_cutoff_rank','avg_replacement_effective_rank'
}

missing_full = full_required - set(full.columns)
missing_rank = rank_required - set(rank.columns)
if missing_full:
    raise SystemExit(f'STOP: full-roster input missing columns: {sorted(missing_full)}')
if missing_rank:
    raise SystemExit(f'STOP: ranking input missing columns: {sorted(missing_rank)}')

POSITIONS = ['QB','RB','WR','TE']
full = full[full['position'].isin(POSITIONS)].copy()
rank = rank[rank['position'].isin(POSITIONS)].copy()

# Validate canonical roster-state labels before doing economics.
real_values = set(full['real_state'].dropna().astype(str).unique())
oracle_values = set(full['oracle_state'].dropna().astype(str).unique())
if not real_values.issubset({'REAL_STARTED','REAL_BENCHED'}):
    raise SystemExit(f'STOP: unexpected real_state values: {sorted(real_values)}')
if not oracle_values.issubset({'ORACLE_SELECTED','ORACLE_BLOCKED'}):
    raise SystemExit(f'STOP: unexpected oracle_state values: {sorted(oracle_values)}')

full['real_started'] = full['real_state'].eq('REAL_STARTED')
full['oracle_started'] = full['oracle_state'].eq('ORACLE_SELECTED')
full['positive_weekly_worp'] = pd.to_numeric(full['weekly_worp'], errors='coerce').fillna(0).clip(lower=0)

# player_id can differ in dtype across generated files. Normalize only for join.
full['_pid'] = full['player_id'].astype(str).str.strip()
rank['_pid'] = rank['player_id'].astype(str).str.strip()

# One season-position-player economic row is expected.
rdup = rank.duplicated(['season','_pid','position'], keep=False)
if rdup.any():
    sample = rank.loc[rdup, ['season','player_id','player_name','position']].head(10)
    raise SystemExit('STOP: duplicate season/player/position rows in rankings:\n' + sample.to_string(index=False))

# Aggregate actual roster use first. A player may appear for multiple rosters in
# a season due to trades; roster_id is intentionally retained.
usage = (
    full.groupby(['season','roster_id','_pid','player_id','player_name','position'], as_index=False)
        .agg(
            observed_weeks=('week','nunique'),
            real_starts=('real_started','sum'),
            oracle_starts=('oracle_started','sum'),
            roster_week_worp=('weekly_worp','sum'),
            roster_positive_worp=('positive_weekly_worp','sum'),
        )
)

rank_cols = [
    'season','_pid','position','games','worp','pos_rank',
    'avg_starter_cutoff_rank','avg_replacement_effective_rank'
]
joined = usage.merge(rank[rank_cols], on=['season','_pid','position'], how='left', validate='many_to_one')

matched = joined['pos_rank'].notna()
match_rate = float(matched.mean()) if len(joined) else np.nan
print('=== ROSTER CONSTRUCTION ECONOMIC CROSSWALK V0.2 ===')
print(f'usage rows: {len(joined):,}')
print(f'economic-rank matched: {matched.sum():,}/{len(joined):,} ({match_rate:.2%})')

# A poor identity join invalidates the economic crosswalk. Do not silently use
# player names as a substitute because names are not a validated identity key.
if len(joined) and match_rate < 0.95:
    miss = joined.loc[~matched, ['season','player_id','player_name','position']].drop_duplicates().head(25)
    print('\nUnmatched sample:')
    print(miss.to_string(index=False))
    raise SystemExit('\nSTOP: player-id join below 95%; resolve identity mapping before interpretation.')

joined = joined[matched].copy()
joined['pos_rank'] = pd.to_numeric(joined['pos_rank'], errors='coerce')
joined['worp'] = pd.to_numeric(joined['worp'], errors='coerce')
joined['avg_starter_cutoff_rank'] = pd.to_numeric(joined['avg_starter_cutoff_rank'], errors='coerce')
joined['avg_replacement_effective_rank'] = pd.to_numeric(joined['avg_replacement_effective_rank'], errors='coerce')

# Economic distance fields are descriptive. Positive rank_minus_* means the
# player finished deeper than that season's league-native economic frontier.
joined['rank_minus_starter_cutoff'] = joined['pos_rank'] - joined['avg_starter_cutoff_rank']
joined['rank_minus_replacement'] = joined['pos_rank'] - joined['avg_replacement_effective_rank']
joined['above_starter_cutoff'] = joined['pos_rank'] <= joined['avg_starter_cutoff_rank']
joined['above_replacement'] = joined['pos_rank'] <= joined['avg_replacement_effective_rank']

joined.to_csv('wookiee_roster_construction_usage_economic_join_v0_2.csv', index=False)

THRESHOLDS = [1,2,3,4,5,6,8,10]
rows = []
for pos in POSITIONS:
    g = joined[joined['position'].eq(pos)]
    for n in THRESHOLDS:
        x = g[g['real_starts'].ge(n)]
        if x.empty:
            continue
        rows.append({
            'position': pos,
            'min_real_starts': n,
            'roster_player_seasons': len(x),
            'median_pos_rank': float(x['pos_rank'].median()),
            'p25_pos_rank': float(x['pos_rank'].quantile(.25)),
            'p75_pos_rank': float(x['pos_rank'].quantile(.75)),
            'median_season_worp': float(x['worp'].median()),
            'mean_season_worp': float(x['worp'].mean()),
            'share_above_starter_cutoff': float(x['above_starter_cutoff'].mean()),
            'share_above_replacement': float(x['above_replacement'].mean()),
            'median_rank_minus_starter_cutoff': float(x['rank_minus_starter_cutoff'].median()),
            'median_rank_minus_replacement': float(x['rank_minus_replacement'].median()),
        })

thresholds = pd.DataFrame(rows)
thresholds.to_csv('wookiee_roster_construction_economic_by_usage_v0_2.csv', index=False)

# Complementary rank-band view: how often players in each economic region were
# actually used. Bands are mechanical 12-rank windows for diagnosis only; they
# are NOT tiers and carry no semantic label.
def rank_band(r):
    if pd.isna(r):
        return None
    lo = int((int(r)-1)//12*12 + 1)
    hi = lo + 11
    return f'{lo:02d}-{hi:02d}'

joined['rank_band_12'] = joined['pos_rank'].map(rank_band)
band = (
    joined.groupby(['position','rank_band_12'], as_index=False)
        .agg(
            roster_player_seasons=('player_id','size'),
            median_pos_rank=('pos_rank','median'),
            median_season_worp=('worp','median'),
            mean_real_starts=('real_starts','mean'),
            median_real_starts=('real_starts','median'),
            share_1plus_real_start=('real_starts', lambda s: float((s >= 1).mean())),
            share_5plus_real_starts=('real_starts', lambda s: float((s >= 5).mean())),
            share_8plus_real_starts=('real_starts', lambda s: float((s >= 8).mean())),
        )
)
# Numeric sorting helper; remove it from saved output.
band['_lo'] = band['rank_band_12'].str.split('-').str[0].astype(int)
band = band.sort_values(['position','_lo']).drop(columns=['_lo'])
band.to_csv('wookiee_roster_construction_economic_rank_bands_v0_2.csv', index=False)

# Diagnostic season-level economic frontiers by position. This establishes that
# the comparison is league-native rather than a hard-coded rank cutoff.
frontier = (
    rank.groupby(['season','position'], as_index=False)
        .agg(
            starter_cutoff_rank=('avg_starter_cutoff_rank','median'),
            replacement_effective_rank=('avg_replacement_effective_rank','median'),
        )
)
frontier.to_csv('wookiee_roster_construction_frontiers_v0_2.csv', index=False)

print('\nLeague-native economic frontiers:')
print(frontier.to_string(index=False))
print('\nActual-use × economic-rank crosswalk:')
print(thresholds.to_string(index=False))
print('\nCreated:')
print('  wookiee_roster_construction_usage_economic_join_v0_2.csv')
print('  wookiee_roster_construction_economic_by_usage_v0_2.csv')
print('  wookiee_roster_construction_economic_rank_bands_v0_2.csv')
print('  wookiee_roster_construction_frontiers_v0_2.csv')
print('\nINTERPRETATION GATE: use these as economic landmarks only. Do not turn a rank band into a universal roster-state cutoff without a material decision test.')
