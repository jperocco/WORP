from pathlib import Path
import pandas as pd

# Roster Construction Worksheet V0.1
# Research instrument only. Does NOT classify semantic roster states and does
# NOT introduce a universal positional cutoff.
#
# Goal: inventory the evidence already available locally so the next pass can
# estimate league-native Scoring Depth / Transition / Optionality zones.

ROOT = Path('.')

CANDIDATES = {
    'full_roster': [
        'wookiee_full_roster_blocked_worp_player_week_v0_5.csv',
    ],
    'ex_ante': [
        'wookiee_ex_ante_lineup_player_week_v0_6.csv',
    ],
    'promotion_exposure': [
        'wookiee_non_scoring_exposure_audit_v0_4_player_week.csv',
        'wookiee_non_scoring_exposure_player_week_v0_4.csv',
    ],
}


def find_first(names):
    for name in names:
        p = ROOT / name
        if p.exists():
            return p
    return None


paths = {k: find_first(v) for k, v in CANDIDATES.items()}

print('=== ROSTER CONSTRUCTION WORKSHEET V0.1 ===')
print('Research instrument; no frontend changes; no new cutoff claims.\n')
print('Local evidence inventory:')
for key, p in paths.items():
    print(f'  {key:20s}: {p if p else "MISSING"}')

if paths['full_roster'] is None:
    raise SystemExit('\nSTOP: required full-roster player-week file is missing.')

full = pd.read_csv(paths['full_roster'])
required = {'season','week','roster_id','player_id','position','weekly_worp','real_state','oracle_state'}
missing = required - set(full.columns)
if missing:
    raise SystemExit(f'STOP: full-roster file missing columns: {sorted(missing)}')

# One row per player-week expected; retain only offensive fantasy positions.
full = full[full['position'].isin(['QB','RB','WR','TE'])].copy()
full['real_started'] = full['real_state'].astype(str).str.upper().eq('STARTED')
full['oracle_started'] = full['oracle_state'].astype(str).str.upper().eq('STARTED')

# Historical realized lineup-use depth. This is descriptive evidence only,
# not the Scoring Bench definition.
usage = (
    full.groupby(['season','roster_id','player_id','position'], as_index=False)
        .agg(
            observed_weeks=('week','nunique'),
            real_starts=('real_started','sum'),
            oracle_starts=('oracle_started','sum'),
            total_worp=('weekly_worp','sum'),
        )
)

rows = []
for pos in ['QB','RB','WR','TE']:
    g = usage[usage.position.eq(pos)]
    if g.empty:
        continue
    for threshold in [1,2,3,4,5,6,8,10]:
        real_counts = (
            g.assign(hit=g.real_starts.ge(threshold))
             .groupby(['season','roster_id'])['hit'].sum()
        )
        oracle_counts = (
            g.assign(hit=g.oracle_starts.ge(threshold))
             .groupby(['season','roster_id'])['hit'].sum()
        )
        rows.append({
            'position': pos,
            'min_starts': threshold,
            'real_players_median': float(real_counts.median()),
            'real_players_mean': float(real_counts.mean()),
            'oracle_players_median': float(oracle_counts.median()),
            'oracle_players_mean': float(oracle_counts.mean()),
        })

util = pd.DataFrame(rows)
util.to_csv('wookiee_roster_construction_utilization_v0_1.csv', index=False)

# Position-level realized/captured context from the same historical roster data.
pos = (
    full.groupby('position', as_index=False)
        .agg(
            player_weeks=('player_id','size'),
            total_worp=('weekly_worp','sum'),
            positive_worp=('weekly_worp', lambda s: s.clip(lower=0).sum()),
            real_started_weeks=('real_started','sum'),
            oracle_started_weeks=('oracle_started','sum'),
        )
)
pos.to_csv('wookiee_roster_construction_position_context_v0_1.csv', index=False)

# Worksheet intentionally leaves economic zones unresolved. The next pass must
# combine league-specific slot eligibility + WoRP curves/replacement with this
# historical utilization evidence. Blank fields prevent false precision.
worksheet = pd.DataFrame([
    {'position':'QB','starting_demand':'FORMAT_DERIVED','scoring_depth_zone':'TBD','transition_zone':'TBD','optionality_hurdle':'TBD','confidence':'TBD','reason':'Resolve from QB-eligible slots + relative economic quality; QB3 is not automatically Non-Scoring.'},
    {'position':'RB','starting_demand':'FORMAT_DERIVED','scoring_depth_zone':'TBD','transition_zone':'TBD','optionality_hurdle':'TBD','confidence':'TBD','reason':'Resolve shared FLEX demand before comparing additional RB depth with contingent optionality.'},
    {'position':'WR','starting_demand':'FORMAT_DERIVED','scoring_depth_zone':'TBD','transition_zone':'TBD','optionality_hurdle':'TBD','confidence':'TBD','reason':'Find format-dependent cut zone where lineup utility fades; do not convert deep-WR compression into a universal cutoff.'},
    {'position':'TE','starting_demand':'FORMAT_DERIVED','scoring_depth_zone':'TBD','transition_zone':'TBD','optionality_hurdle':'TBD','confidence':'TBD','reason':'Resolve TE/2TE/TEP slot demand before interpreting depth or optionality.'},
])
worksheet.to_csv('wookiee_roster_construction_worksheet_v0_1.csv', index=False)

print('\nPASS: descriptive utilization evidence built')
print('Created: wookiee_roster_construction_utilization_v0_1.csv')
print('Created: wookiee_roster_construction_position_context_v0_1.csv')
print('Created: wookiee_roster_construction_worksheet_v0_1.csv')
print('\nUtilization preview:')
print(util.to_string(index=False))
print('\nNEXT GATE: inspect this output before assigning any Scoring Depth / Transition / Optionality ranges.')
