from pathlib import Path
import pandas as pd

ROOT = Path('.')
PATTERNS = [
    '*ex_ante*.csv',
    '*lineup*.csv',
    '*roster*.csv',
    '*blocked_worp*.csv',
    '*season_week_player*.csv',
]

KEY_HINTS = {
    'identity': {'player_id', 'player_name', 'season', 'week', 'roster_id', 'team_id'},
    'position': {'position', 'pos'},
    'realized': {'worp', 'realized_worp', 'target_worp'},
    'prior_signal': {'prior_worp', 'prior_worp_pg', 'st_worp', 'l3_worp', 'ex_ante_score'},
    'manager': {'started', 'is_starter', 'manager_selected', 'real_selected'},
    'oracle': {'oracle_selected', 'optimal_selected'},
    'availability_proxy': {'missing_target_week', 'zero_target_week', 'missing_or_zero'},
}

files = []
seen = set()
for pattern in PATTERNS:
    for p in sorted(ROOT.glob(pattern)):
        if p.is_file() and p.suffix.lower() == '.csv' and p.name not in seen:
            seen.add(p.name)
            files.append(p)

print('=' * 96)
print('WOOKIEE TIER-AWARE LINEUP PREFLIGHT V0.7')
print('=' * 96)
print('Purpose: inspect local research outputs before building the tier-aware lineup audit.')
print('No model result is produced here. This script prevents schema guessing.')
print()

if not files:
    print('STOP: no matching research CSVs found in the current folder.')
    print('Run this script from the WoRP Lab project directory that contains the V0.5/V0.6/V0.6A outputs.')
    raise SystemExit(2)

usable = []
for p in files:
    try:
        df = pd.read_csv(p, nrows=8)
    except Exception as e:
        print(f'FILE: {p.name}')
        print(f'  READ ERROR: {e}')
        print()
        continue

    cols = list(df.columns)
    lower = {c.lower(): c for c in cols}

    print(f'FILE: {p.name}')
    print(f'  columns ({len(cols)}): {cols}')

    found = {}
    for group, hints in KEY_HINTS.items():
        hits = [orig for low, orig in lower.items() if low in hints]
        if hits:
            found[group] = hits
    print(f'  semantic groups found: {found if found else "none"}')

    required_groups = {'identity', 'position', 'realized'}
    has_required = required_groups.issubset(found.keys())
    has_decision_signal = ('manager' in found) or ('prior_signal' in found)

    if has_required and has_decision_signal:
        usable.append((p.name, found))
        print('  candidate for V0.7 join/audit: YES')
    else:
        print('  candidate for V0.7 join/audit: no')
    print()

print('-' * 96)
if not usable:
    print('STOP: no single CSV exposes enough fields to build V0.7 without guessing.')
    print('Next step: use the printed schemas to design an explicit multi-file join.')
    raise SystemExit(3)

print('PASS: at least one local output contains enough structure to design V0.7 safely.')
print('Candidates:')
for name, found in usable:
    print(f'  - {name}: {found}')
print()
print('Next audit target (not executed here):')
print('  1) assign each player-week to a validated economic tier from prior-only information;')
print('  2) measure decision-set composition by tier;')
print('  3) compare Manager vs pregame selector within tier combinations;')
print('  4) STOP if tier splits are too small or do not change roster-construction decisions.')
print('=' * 96)
