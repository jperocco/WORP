"""Pre-game lineup policies on previously frozen chronological compositions."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from worp_positional_portfolio_simulation import profile_orders, POS
from worp_optionality_capacity_audit import compositions


def lineup_outcomes(holdings, prediction, realized, zero_values, legal):
    legal=legal[np.all(legal<=np.array([h.shape[1] for h in holdings]),axis=1)]
    if not len(legal):
        raise ValueError('Cannot fill starting lineup')
    draws=len(holdings[0]);pred=np.zeros((draws,len(legal)))
    signed=np.zeros_like(pred);positive=np.zeros_like(pred);oracle=np.zeros_like(pred)
    for j,h in enumerate(holdings):
        x=np.array([[prediction.get(pid,0.) for pid in row] for row in h])
        y=np.array([[realized.get(pid,zero_values[POS[j]]) for pid in row] for row in h])
        order=np.argsort(-x,axis=1,kind='stable')
        ordered=np.take_along_axis(y,order,axis=1)
        def sums(a):
            return np.c_[np.zeros(draws),np.cumsum(a,axis=1)][:,legal[:,j]]
        pred+=sums(np.take_along_axis(x,order,axis=1))
        signed+=sums(ordered)
        positive+=sums(np.maximum(ordered,0.))
        oracle+=sums(np.sort(np.maximum(y,0.),axis=1)[:,::-1])
    choice=pred.argmax(axis=1);idx=np.arange(draws)
    return signed[idx,choice],positive[idx,choice],oracle.max(axis=1)


def main():
    source=Path('research/optionality_multileague');out=Path('research/manual_capture');out.mkdir(parents=True,exist_ok=True)
    folds=pd.read_csv('research/portfolio_temporal_validation/fold_results.csv',dtype={'league_id':str})
    manifest=pd.read_csv(source/'selected_league_seasons.csv',dtype={'league_id':str}).set_index('league_id')
    pmap=json.loads((source/'cache/players.json').read_text())
    protocol=dict(policies=['prior_3_week_mean_fantasy_points','prior_5_week_mean_fantasy_points'],
        compositions='frozen earlier-data choices from temporal validation; no reselection',
        draws=256,seeds=[7000,17000,27000],
        missing_weekly_stats='assume zero fantasy points; use same-week positional frozen-engine zero-point WoRP',
        deployment_gate='no automatic approval from aggregate capture; divergent policy conclusions block recommendation; no new percentage threshold',
        limitations='simple baseline policies, no historical injury/bye availability or external projections; not observed manager decisions')
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    rows=[]
    for lid,group in folds[folds.status.eq('evaluated')].groupby('league_id'):
        league=manifest.loc[lid];slots=[s for s in json.loads(league.roster_positions) if s!='BN'];legal=compositions(slots)
        d=pd.read_csv(source/'cache'/f'weekly_{lid}.csv',dtype={'player_id':str})
        worp={int(w):dict(zip(g.player_id,g.weekly_worp)) for w,g in d.groupby('week')}
        points={int(w):dict(zip(g.player_id,g.fantasy_points)) for w,g in d.groupby('week')}
        zero={}
        for (w,p),g in d[d.fantasy_points.eq(0)].groupby(['week','position']):
            if g.weekly_worp.max()-g.weekly_worp.min()>1e-12:
                raise ValueError('Inconsistent zero-point engine values')
            zero[int(w),p]=float(g.weekly_worp.iloc[0])
        for start,g in group.groupby('test_week'):
            snap=json.loads((source/'cache'/f'matchups_{lid}_{start-1}.json').read_text())
            pool=set().union(*(set(s.get('players') or []) for s in snap))
            for seed in protocol['seeds']:
                rng=np.random.default_rng(seed+start)
                selected=[profile_orders({pid for pid in pool if pmap.get(pid,{}).get('position')==pos},
                    [worp[w] for w in range(start-3,start)],int(league.total_rosters),len(slots)+12,256,rng) for pos in POS]
                for fold in g.itertuples():
                    holdings=[selected[j][:,:int(getattr(fold,p))] for j,p in enumerate(POS)]
                    for lookback in (3,5):
                        signed=np.zeros(256);positive=np.zeros(256);oracle=np.zeros(256)
                        for week in range(start,start+4):
                            prior=list(range(max(1,week-lookback),week))
                            prediction={pid:sum(points[w].get(pid,0.) for w in prior)/len(prior) for pid in pool}
                            a,b,c=lineup_outcomes(holdings,prediction,worp[week],{p:zero[week,p] for p in POS},legal)
                            signed+=a;positive+=b;oracle+=c
                        rows.append(dict(league_id=lid,season=fold.season,stratum=fold.stratum,bench=fold.bench,
                            capacity=fold.capacity,test_week=start,seed=seed,lookback=lookback,
                            signed_capture=signed.mean(),positive_capture=positive.mean(),
                            negative_capture=(signed-positive).mean(),oracle_positive=oracle.mean()))
        print('PASS',lid,flush=True)
    r=pd.DataFrame(rows);r.to_csv(out/'capture_detail.csv',index=False)
    cases=r.groupby(['league_id','season','stratum','bench','capacity','test_week','lookback'],as_index=False).mean(numeric_only=True)
    cases['positive_capture_fraction']=cases.positive_capture/cases.oracle_positive.replace(0,np.nan)
    cases.to_csv(out/'case_results.csv',index=False)
    leagues=cases.groupby(['league_id','stratum','bench','lookback'],as_index=False).agg(
        positive=('positive_capture','sum'),oracle=('oracle_positive','sum'),negative=('negative_capture','mean'))
    leagues['fraction']=leagues.positive/leagues.oracle.replace(0,np.nan)
    summary=leagues.groupby(['stratum','bench','lookback'],as_index=False).agg(
        league_seasons=('league_id','size'),mean_capture_fraction=('fraction','mean'),mean_negative_capture=('negative','mean'))
    summary.to_csv(out/'summary.csv',index=False)
    keys=['league_id','season','stratum','test_week','lookback']
    paired=cases[cases.bench.eq(12)].merge(cases[cases.bench.eq(5)],on=keys,suffixes=('_12','_5'))
    metrics=['signed_capture','positive_capture','oracle_positive']
    for metric in metrics:
        paired['delta_'+metric]=paired[metric+'_12']-paired[metric+'_5']
    paired[keys+['delta_'+m for m in metrics]].to_csv(out/'paired_bench_results.csv',index=False)
    print(summary.to_string(index=False))


if __name__=='__main__':
    main()
