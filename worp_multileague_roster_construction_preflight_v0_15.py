#!/usr/bin/env python3
"""WoRP Lab — Multi-league Roster Construction Preflight V0.15.

Consumes Sleeper discovery V0.14 and builds the league-native empirical-validation
manifest. This is deliberately a preflight: it does not invent WoRP mappings or
claim roster-count optima. It tells us which discovered league-seasons are
structurally distinct, which have enough lineage for replication, and what the
next empirical harness must test.
"""
from pathlib import Path
import json
import pandas as pd

INFILE = Path('sleeper_user_league_inventory_v0_14.csv')
OUT_OBS = Path('worp_multileague_validation_observations_v0_15.csv')
OUT_FORMATS = Path('worp_multileague_validation_formats_v0_15.csv')
OUT_LINEAGES = Path('worp_multileague_validation_lineages_v0_15.csv')

if not INFILE.exists():
    raise SystemExit('Missing sleeper_user_league_inventory_v0_14.csv. Run V0.14 first.')

df = pd.read_csv(INFILE, dtype={'league_id': str, 'previous_league_id': str})
if df.empty:
    raise SystemExit('Discovery inventory is empty.')

for c in ['season','total_rosters','starter_count','roster_positions_count','fixed_qb','fixed_rb','fixed_wr','fixed_te','flex_slots','sf_slots']:
    if c in df:
        df[c] = pd.to_numeric(df[c], errors='coerce')

def parse_positions(x):
    try: return json.loads(x) if pd.notna(x) else []
    except Exception: return []

def as_bool(x):
    # CSV-safe boolean parsing: bool('False') is True in Python, so never use it here.
    if isinstance(x, bool): return x
    if pd.isna(x): return False
    return str(x).strip().lower() in {'1','true','t','yes','y'}

def nonstarter_count(pos):
    return sum(p in ('BN','IR','TAXI') for p in pos)

def roster_size(pos):
    # Active fantasy roster capacity = starters + BN. IR/TAXI are separate holding states.
    return sum(p not in ('IR','TAXI') for p in pos)

def format_key(r):
    return '|'.join([
        f"{int(r.total_rosters) if pd.notna(r.total_rosters) else 'NA'}T",
        'SF' if (r.sf_slots or 0) > 0 else '1QB',
        f"Start{int(r.starter_count) if pd.notna(r.starter_count) else 'NA'}",
        f"QB{int(r.fixed_qb or 0)}", f"RB{int(r.fixed_rb or 0)}", f"WR{int(r.fixed_wr or 0)}", f"TE{int(r.fixed_te or 0)}",
        f"FLEX{int(r.flex_slots or 0)}", f"SFLEX{int(r.sf_slots or 0)}",
        'TEP' if as_bool(r.tep_detected) else 'noTEP'
    ])

positions = df.roster_positions.map(parse_positions)
df['active_roster_size'] = positions.map(roster_size)
df['holding_slots'] = positions.map(nonstarter_count)
df['scoring_surplus_capacity'] = df.active_roster_size - df.starter_count
df['format_key'] = df.apply(format_key, axis=1)

# Build dynasty lineage roots using previous_league_id edges present in the inventory.
ids = set(df.league_id.dropna().astype(str))
prev = {str(r.league_id): str(r.previous_league_id) for r in df.itertuples()
        if pd.notna(r.previous_league_id) and str(r.previous_league_id) not in ('','nan','None')}
def root(lid):
    seen=set(); cur=str(lid)
    while cur in prev and prev[cur] in ids and cur not in seen:
        seen.add(cur); cur=prev[cur]
    return cur
df['lineage_root'] = df.league_id.map(root)

# Structural support flags only. Empirical WoRP compatibility is checked by V0.16.
df['structurally_supported'] = (
    df.total_rosters.notna() & df.starter_count.notna() &
    (df.starter_count > 0) & (df.active_roster_size >= df.starter_count)
)
df['needs_worp_mapping'] = True

df.to_csv(OUT_OBS, index=False)

formats = (df.groupby('format_key', dropna=False)
    .agg(league_seasons=('league_id','size'), unique_leagues=('league_id','nunique'),
         seasons=('season','nunique'), lineages=('lineage_root','nunique'),
         min_season=('season','min'), max_season=('season','max'),
         teams=('total_rosters','median'), starters=('starter_count','median'),
         roster_size=('active_roster_size','median'), surplus_capacity=('scoring_surplus_capacity','median'))
    .reset_index().sort_values(['league_seasons','seasons'], ascending=False))
formats.to_csv(OUT_FORMATS, index=False)

lineages = (df.groupby('lineage_root')
    .agg(name=('name','first'), league_seasons=('league_id','size'), seasons=('season','nunique'),
         min_season=('season','min'), max_season=('season','max'), formats=('format_key','nunique'))
    .reset_index().sort_values(['seasons','league_seasons'], ascending=False))
lineages['replication_candidate'] = lineages.seasons >= 2
lineages.to_csv(OUT_LINEAGES, index=False)

print('V0.15 MULTI-LEAGUE PREFLIGHT')
print(f'League-season observations: {len(df)}')
print(f'Unique league IDs: {df.league_id.nunique()}')
print(f'Unique structural formats: {df.format_key.nunique()}')
print(f'Lineages: {df.lineage_root.nunique()}')
print(f'Multi-season lineage candidates: {int(lineages.replication_candidate.sum())}')
print('\nTOP STRUCTURAL FORMATS')
print(formats.head(25).to_string(index=False))
print('\nTOP LINEAGES')
print(lineages.head(25).to_string(index=False))
print('\nCreated:')
print(f'- {OUT_OBS}')
print(f'- {OUT_FORMATS}')
print(f'- {OUT_LINEAGES}')
print('\nREADING CONTRACT')
print('- This preflight does NOT claim an optimal Scoring count.')
print('- Wookiee 13–15 is not copied into other formats.')
print('- Starting lineup size, team count, slot eligibility, roster size and TEP remain independent league-native inputs.')
print('- V0.16 must join each supported league-season to league-native weekly WoRP, reconstruct roster-weeks, and compare Scoring-core sizes on common support.')
print('- .25/.50/.75 remain sensitivity probes; no universal 4% threshold.')
