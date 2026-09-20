"""Whole-roster positional scenarios; estimates, never observed roster quotas.

Frozen weekly WoRP input. One profile per positional rank block of league-team
size, ranked only on preceding weeks. Same simulated holdings across compared
compositions; legal hindsight lineup opportunity is evaluated jointly.
"""
import argparse
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
from worp_optionality_capacity_audit import POS, compositions


def portfolio_counts(capacity, slots, limits):
    minimum = [slots.count(pos) for pos in POS]
    return [counts for counts in itertools.product(*(range(m, limit+1) for m, limit in zip(minimum, limits)))
            if sum(counts) == capacity]


def profile_orders(pool, preceding, teams, max_depth, draws, rng):
    # Randomize ties before stable sorting; no future outcomes enter ordering.
    shuffled = rng.permutation(sorted(pool)).tolist()
    ranking = sorted(shuffled, key=lambda pid: -sum(w.get(pid, 0.) for w in preceding))
    depth = min(max_depth, len(ranking)//teams)
    blocks = np.asarray(ranking[:depth*teams], dtype=object).reshape(depth, teams)
    return np.asarray([[blocks[k, rng.integers(teams)] for k in range(depth)]
                       for _ in range(draws)], dtype=object)


def contribution(selected, scores, max_slots):
    draws, depth = selected.shape
    result = np.zeros((depth+1, draws, max_slots+1))
    values = np.asarray([[max(0., scores.get(pid, 0.)) for pid in row] for row in selected])
    for k in range(1, depth+1):
        top = np.sort(values[:, :k], axis=1)[:, ::-1]
        top = np.pad(top, ((0,0),(0,max_slots)))[:, :max_slots]
        result[k, :, 1:] = np.cumsum(top, axis=1)
    return result


def evaluate(counts, tables, legal):
    draw_count = tables[0].shape[1]
    values = np.zeros((draw_count, len(legal)))
    for j, table in enumerate(tables):
        values += table[counts[j]][:, legal[:, j]]
    return values.max(axis=1)


def run(source, out, league_id, benches, draws):
    manifest = pd.read_csv(source/'selected_league_seasons.csv', dtype={'league_id':str})
    league = manifest.set_index('league_id').loc[league_id]
    slots = [s for s in json.loads(league.roster_positions) if s != 'BN']
    legal = compositions(slots)
    capacities = [len(slots)+b for b in benches]
    weekly = pd.read_csv(source/'cache'/f'weekly_{league_id}.csv', dtype={'player_id':str})
    pmap = json.loads((source/'cache/players.json').read_text())
    outcomes = {int(w):dict(zip(g.player_id,g.weekly_worp)) for w,g in weekly.groupby('week')}
    rows = []
    for week in (4,8,12):
        snapshots = json.loads((source/'cache'/f'matchups_{league_id}_{week-1}.json').read_text())
        pool = set().union(*(set(s.get('players') or []) for s in snapshots))
        prior = [outcomes[w] for w in range(week-3,week)]
        rng = np.random.default_rng(7000+week)
        selected = [profile_orders({pid for pid in pool if pmap.get(pid,{}).get('position') == pos},
                                   prior,int(league.total_rosters),max(capacities),draws,rng) for pos in POS]
        limits = [x.shape[1] for x in selected]
        scenarios = {c:portfolio_counts(c,slots,limits) for c in capacities}
        future = [[contribution(selected[j],outcomes[w],int(legal[:,j].max())) for j in range(4)]
                  for w in range(week,week+4)]
        for capacity, vectors in scenarios.items():
            if not vectors:
                raise ValueError(f'No feasible compositions for capacity {capacity}')
            values = np.array([sum(evaluate(vector,tables,legal) for tables in future) for vector in vectors])
            means = values.mean(axis=1)
            best = float(means.max())
            for vector, mean in zip(vectors,means):
                rows.append(dict(league_id=league_id,season=int(league.season),week=week,
                                 capacity=capacity,bench=capacity-len(slots),draws=draws,
                                 **dict(zip(POS,vector)),mean_opportunity=float(mean),
                                 gap_to_window_best=best-float(mean)))
            print(f'PASS week {week} capacity {capacity}: {len(vectors)} compositions',flush=True)
    out.mkdir(parents=True,exist_ok=True)
    detail = pd.DataFrame(rows)
    detail.to_csv(out/'composition_detail.csv',index=False)
    summary = detail.groupby(['capacity','bench']+list(POS),as_index=False).agg(
        windows=('week','nunique'),mean_opportunity=('mean_opportunity','mean'),
        worst_window_gap=('gap_to_window_best','max'))
    # Require identical window support; a missing profile supply is not a zero.
    summary['comparable_all_windows'] = summary.windows.eq(3)
    summary.to_csv(out/'composition_summary.csv',index=False)
    best = detail.sort_values(['capacity','week','mean_opportunity'],ascending=[True,True,False]).groupby(['capacity','week']).head(1)
    best.to_csv(out/'window_maxima.csv',index=False)
    print(best[['capacity','week']+list(POS)+['mean_opportunity']].to_string(index=False))
    (out/'assumptions.json').write_text(json.dumps(dict(league_id=league_id,season=int(league.season),
        teams=int(league.total_rosters),slots=slots,bench_scenarios=benches,draws=draws,windows=[4,8,12],
        selection='prior-owned league pool, preceding 3-week signed WoRP rank blocks; one profile per team-sized block',
        objective='4-week sum of positive WoRP in legal hindsight lineups; not joint win probability',
        status='modeled sensitivity scenarios; no product quotas'),indent=2)+'\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source',type=Path,default=Path('research/optionality_multileague'))
    p.add_argument('--out',type=Path,default=Path('research/positional_portfolio_simulation'))
    p.add_argument('--league-id',default='1180084795436826624')
    p.add_argument('--benches',type=int,nargs='+',default=[5,12])
    p.add_argument('--draws',type=int,default=64)
    a=p.parse_args()
    run(a.source,a.out,a.league_id,a.benches,a.draws)
