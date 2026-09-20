"""Select full compositions by earlier manual-policy outcomes, then test later."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from worp_positional_portfolio_simulation import POS, profile_orders, portfolio_counts
from worp_optionality_capacity_audit import compositions


def prefix_tables(selected, prediction, realized, zero, max_slots):
    draws,depth=selected.shape
    pred=np.full((depth+1,draws,max_slots+1),-np.inf)
    actual=np.zeros_like(pred);pred[:,:,0]=0.
    x=np.array([[prediction.get(pid,0.) for pid in row] for row in selected])
    y=np.array([[realized.get(pid,zero) for pid in row] for row in selected])
    for k in range(1,depth+1):
        order=np.argsort(-x[:,:k],axis=1,kind='stable')
        take=min(k,max_slots)
        pred[k,:,1:take+1]=np.cumsum(np.take_along_axis(x[:,:k],order,axis=1),axis=1)[:,:take]
        actual[k,:,1:take+1]=np.cumsum(np.take_along_axis(y[:,:k],order,axis=1),axis=1)[:,:take]
    return pred,actual


def score(vector,tables,legal):
    pred=sum(tables[j][0][vector[j]][:,legal[:,j]] for j in range(4))
    actual=sum(tables[j][1][vector[j]][:,legal[:,j]] for j in range(4))
    chosen=pred.argmax(axis=1)
    if not np.isfinite(pred.max(axis=1)).all():
        raise ValueError('Unfillable lineup')
    return actual[np.arange(len(chosen)),chosen]


def select_past(surface,test_week):
    train=surface[surface.week.lt(test_week)].copy()
    if train.empty:return None
    train['regret']=train.groupby(['week','seed']).capture.transform('max')-train.capture
    n=len(train[['week','seed']].drop_duplicates())
    g=train.groupby(list(POS),as_index=False).agg(n=('capture','size'),worst=('regret','max'),mean=('regret','mean'))
    g=g[g.n.eq(n)].sort_values(['worst','mean']+list(POS))
    return None if g.empty else {p:int(g.iloc[0][p]) for p in POS}


def test_choice(surface,week):
    chosen=select_past(surface,week)
    if chosen is None:return {'status':'no_training_support'}
    test=surface[surface.week.eq(week)]
    selected=test
    for pos,n in chosen.items():selected=selected[selected[pos].eq(n)]
    if len(selected)!=3:return {**chosen,'status':'chosen_unavailable'}
    oracle=test.groupby('seed').capture.max()
    return {**chosen,'status':'evaluated','capture':selected.capture.mean(),
            'test_regret':(oracle-selected.set_index('seed').capture).mean()}


def main():
    source=Path('research/optionality_multileague');out=Path('research/manual_composition');out.mkdir(parents=True,exist_ok=True)
    manifest=pd.read_csv(source/'selected_league_seasons.csv',dtype={'league_id':str})
    pmap=json.loads((source/'cache/players.json').read_text())
    protocol=dict(seeds=[7000,17000,27000],draws=256,profile_lookback=3,lineup_lookbacks=[3,5],
                  windows=[4,8,12],test_windows=[8,12],benches=[5,12],
                  selection='minimize worst earlier-window signed-capture regret, then mean regret and lexical counts',
                  benchmark='previously frozen perfect-opportunity choices evaluated by the same manual policy',
                  caveats='retrospective simulated rank-block rosters; no injury/bye filters; no automatic product acceptance')
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    results=[]
    for league in manifest.itertuples():
        lid=league.league_id;slots=[s for s in json.loads(league.roster_positions) if s!='BN'];legal=compositions(slots)
        weekly=pd.read_csv(source/'cache'/f'weekly_{lid}.csv',dtype={'player_id':str})
        worp={int(w):dict(zip(g.player_id,g.weekly_worp)) for w,g in weekly.groupby('week')}
        fp={int(w):dict(zip(g.player_id,g.fantasy_points)) for w,g in weekly.groupby('week')}
        zero={}
        for (w,p),g in weekly[weekly.fantasy_points.eq(0)].groupby(['week','position']):
            if g.weekly_worp.max()-g.weekly_worp.min()>1e-12:raise ValueError('Zero outcome inconsistency')
            zero[w,p]=float(g.weekly_worp.iloc[0])
        rows=[]
        for start in (4,8,12):
            snaps=json.loads((source/'cache'/f'matchups_{lid}_{start-1}.json').read_text())
            pool=set().union(*(set(s.get('players') or []) for s in snaps))
            predictions={}
            for lookback in (3,5):
                for week in range(start,start+4):
                    prior=list(range(max(1,week-lookback),week))
                    predictions[lookback,week]={pid:sum(fp[w].get(pid,0.) for w in prior)/len(prior) for pid in pool}
            for seed in protocol['seeds']:
                rng=np.random.default_rng(seed+start)
                holdings=[profile_orders({pid for pid in pool if pmap.get(pid,{}).get('position')==pos},
                    [worp[w] for w in range(start-3,start)],int(league.total_rosters),len(slots)+12,256,rng) for pos in POS]
                for lookback in (3,5):
                    weeks=[[prefix_tables(holdings[j],predictions[lookback,w],worp[w],zero[w,p],int(legal[:,j].max()))
                            for j,p in enumerate(POS)] for w in range(start,start+4)]
                    for bench in (5,12):
                        capacity=len(slots)+bench
                        for vector in portfolio_counts(capacity,slots,[x.shape[1] for x in holdings]):
                            capture=sum(score(vector,tables,legal) for tables in weeks).mean()
                            rows.append(dict(week=start,seed=seed,lookback=lookback,bench=bench,capacity=capacity,
                                             **dict(zip(POS,vector)),capture=float(capture)))
        surface=pd.DataFrame(rows)
        # Per-league checkpoint makes full selection surfaces auditable/replayable.
        surface.to_csv(out/f'surface_{lid}.csv',index=False)
        for bench in (5,12):
            for lookback in (3,5):
                part=surface[surface.bench.eq(bench)&surface.lookback.eq(lookback)]
                for week in (8,12):
                    results.append(dict(league_id=lid,season=league.season,stratum=league.stratum,bench=bench,
                        capacity=len(slots)+bench,lookback=lookback,test_week=week,**test_choice(part,week)))
        pd.DataFrame(results).to_csv(out/'fold_results.csv',index=False)
        print('PASS',lid,flush=True)
    r=pd.DataFrame(results)
    old=pd.read_csv('research/manual_capture/case_results.csv',dtype={'league_id':str})
    keys=['league_id','bench','lookback','test_week']
    paired=r[r.status.eq('evaluated')].merge(old[keys+['signed_capture']],on=keys,validate='one_to_one')
    paired['gain_vs_old_choice']=paired.capture-paired.signed_capture
    paired.to_csv(out/'paired_comparison.csv',index=False)
    league_means=paired.groupby(['league_id','stratum','bench','lookback'],as_index=False).agg(
        folds=('test_week','size'),gain=('gain_vs_old_choice','mean'))
    summary=league_means.groupby(['stratum','bench','lookback'],as_index=False).agg(
        league_seasons=('league_id','size'),folds=('folds','sum'),mean_gain=('gain','mean'),
        min_league_gain=('gain','min'),max_league_gain=('gain','max'))
    summary.to_csv(out/'summary.csv',index=False)
    print(r.status.value_counts().to_string());print(summary.to_string(index=False))


if __name__=='__main__':main()
