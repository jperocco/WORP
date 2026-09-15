#!/usr/bin/env python3
"""WoRP Lab — Roster Construction Frontier V0.3

Translate the validated league-native Material Production Frontier into a first
roster-construction diagnostic WITHOUT pretending that a raw rank is a roster target.

Question:
How much materially useful production exists beyond each league's aggregate starter
replacement environment, and how does that scoring-depth reserve change by format?

This script intentionally does NOT:
- define a waiver threshold;
- value assets/trades;
- prescribe an exact roster count;
- classify individual players as optionality/cloggers.

It measures the economic bridge we need before those later questions:
material frontier relative to replacement demand.
"""
from pathlib import Path
import pandas as pd
import numpy as np

SRC = Path('worp_league_native_material_frontier_summary_v0_2.csv')
OUT = Path('worp_roster_construction_frontier_v0_3.csv')
OUT_POS = Path('worp_roster_construction_frontier_position_summary_v0_3.csv')

if not SRC.exists():
    raise SystemExit(f'STOP: missing {SRC}')

df = pd.read_csv(SRC)
need = {'format','position','worp_landmark','seasons_observed','median_last_rank',
        'p25_last_rank','p75_last_rank','median_replacement_effective_rank'}
missing = need - set(df.columns)
if missing:
    raise SystemExit(f'STOP: missing columns: {sorted(missing)}')

# Primary descriptive bridge. Positive reserve means the material frontier extends
# beyond the league's effective replacement rank; negative means the selected
# material hurdle is inside replacement. Neither case is automatically good/bad.
df['material_reserve_players'] = (
    df['median_last_rank'] - df['median_replacement_effective_rank']
)
df['frontier_to_replacement_ratio'] = (
    df['median_last_rank'] / df['median_replacement_effective_rank'].replace(0, np.nan)
)
df['frontier_iqr_width'] = df['p75_last_rank'] - df['p25_last_rank']

# Robustness flag is intentionally descriptive, not a semantic truth threshold.
# We require all 10 seasons for the current validated historical panel.
df['full_decade_observed'] = df['seasons_observed'].eq(10)

df.to_csv(OUT, index=False)

# Position/format summary across the three sensitivity landmarks. The median reserve
# tells us whether a format systematically creates material scoring depth beyond
# replacement rather than relying on one arbitrary hurdle.
pos = (df.groupby(['format','position'], as_index=False)
       .agg(
           median_material_reserve=('material_reserve_players','median'),
           min_material_reserve=('material_reserve_players','min'),
           max_material_reserve=('material_reserve_players','max'),
           median_frontier_ratio=('frontier_to_replacement_ratio','median'),
           median_frontier_iqr=('frontier_iqr_width','median'),
           landmarks_observed=('worp_landmark','nunique'),
       ))
pos.to_csv(OUT_POS, index=False)

print('=== ROSTER CONSTRUCTION FRONTIER V0.3 ===')
print('Question: how much material production exists beyond aggregate replacement demand?')
print('Positive reserve = material frontier deeper than effective replacement rank.')
print('This is NOT yet an exact roster-count recommendation.\n')

for landmark in sorted(df.worp_landmark.unique()):
    z = df[df.worp_landmark.eq(landmark)]
    table = z.pivot(index='format', columns='position', values='material_reserve_players')
    print(f'LANDMARK >= {landmark:.2f} season WoRP — material reserve vs replacement')
    print(table.round(1).to_string())
    print()

print('ROBUST CROSS-LANDMARK VIEW — median reserve')
print(pos.pivot(index='format', columns='position', values='median_material_reserve').round(1).to_string())

print('\nINTERPRETATION CONTRACT')
print('- This quantifies scoring-depth economic room beyond replacement, by league.')
print('- A larger reserve does not automatically mean roster every player in it.')
print('- A negative reserve does not mean the position is unimportant; it means the chosen material hurdle is concentrated above replacement.')
print('- Look for format-sensitive, cross-landmark patterns; do not optimize exact ranks.')
print('- If reserve differences are tiny and do not change construction decisions, classify as noise and STOP.')
print('- Next step after validation: combine this economic reserve with actual roster/lineup use, preferably multi-league Sleeper data.')
print(f'\nCreated: {OUT.name}')
print(f'Created: {OUT_POS.name}')
