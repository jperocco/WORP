from pathlib import Path
import pandas as pd
import numpy as np

# Roster Construction Transition Zone V0.3
# Converts V0.2 crosswalk into descriptive economic landmarks.
# It deliberately does NOT assign STARTER / SCORING BENCH / NON-SCORING labels.

ROOT = Path('.')
JOIN = ROOT / 'wookiee_roster_construction_usage_economic_join_v0_2.csv'
FRONT = ROOT / 'wookiee_roster_construction_frontiers_v0_2.csv'
OUT = ROOT / 'wookiee_roster_construction_transition_zone_v0_3.csv'

if not JOIN.exists():
    raise SystemExit('STOP: run V0.2 first; usage-economic join is missing.')

d = pd.read_csv(JOIN)
needed = {'season','roster_id','player_id','position','real_starts','pos_rank','worp','starter_cutoff_rank','replacement_effective_rank'}
missing = needed - set(d.columns)
if missing:
    raise SystemExit(f'STOP: V0.2 join missing columns: {sorted(missing)}')

d = d[d.position.isin(['QB','RB','WR','TE'])].copy()
d = d.dropna(subset=['real_starts','pos_rank','worp','starter_cutoff_rank','replacement_effective_rank'])
d['rank_minus_starter'] = d.pos_rank - d.starter_cutoff_rank
d['rank_minus_replacement'] = d.pos_rank - d.replacement_effective_rank

# Mutually exclusive utilization bands: avoids the cumulative-threshold illusion.
def usage_band(x):
    if x >= 10: return '10+'
    if x >= 8: return '8-9'
    if x >= 5: return '5-7'
    if x >= 3: return '3-4'
    if x >= 1: return '1-2'
    return '0'

d['usage_band'] = d.real_starts.map(usage_band)
order = ['10+','8-9','5-7','3-4','1-2','0']

rows=[]
for pos in ['QB','RB','WR','TE']:
    for band in order:
        g=d[(d.position==pos)&(d.usage_band==band)]
        if g.empty: continue
        rows.append({
            'position':pos,
            'usage_band':band,
            'n_player_seasons':len(g),
            'median_pos_rank':g.pos_rank.median(),
            'p25_pos_rank':g.pos_rank.quantile(.25),
            'p75_pos_rank':g.pos_rank.quantile(.75),
            'median_worp':g.worp.median(),
            'mean_worp':g.worp.mean(),
            'median_rank_minus_starter':g.rank_minus_starter.median(),
            'median_rank_minus_replacement':g.rank_minus_replacement.median(),
            'share_inside_starter_frontier':(g.rank_minus_starter<=0).mean(),
            'share_inside_replacement_frontier':(g.rank_minus_replacement<=0).mean(),
        })

out=pd.DataFrame(rows)
out['usage_band']=pd.Categorical(out.usage_band,categories=order,ordered=True)
out=out.sort_values(['position','usage_band'])
out.to_csv(OUT,index=False)

print('=== ROSTER CONSTRUCTION TRANSITION ZONE V0.3 ===')
print(f'player-seasons analyzed: {len(d):,}')
print('\nMutually exclusive actual-use bands × economic location:')
print(out.to_string(index=False))

print('\nPOSITION LANDMARKS')
for pos in ['QB','RB','WR','TE']:
    p=out[out.position==pos]
    print(f'\n{pos}')
    for _,r in p.iterrows():
        print(f"  {r.usage_band:>3} starts: n={int(r.n_player_seasons):3d} | median {pos}{int(round(r.median_pos_rank))} | median WoRP={r.median_worp:.3f} | inside starter={r.share_inside_starter_frontier:.1%} | inside repl={r.share_inside_replacement_frontier:.1%}")

print('\nINTERPRETATION RULES')
print('- 10+ / 8-9 = recurring lineup use evidence, not semantic STARTER labels.')
print('- 5-7 = candidate scoring-depth evidence.')
print('- 3-4 / 1-2 = episodic-use evidence; inspect economic compression before calling it useful depth.')
print('- 0 = no realized lineup capture in that season; NOT automatically Non-Scoring ex ante.')
print('- A transition zone is supported only where utilization fades AND economic location deteriorates materially.')
print('- No universal rank cutoff is emitted by this script.')
print(f'\nCreated: {OUT.name}')
