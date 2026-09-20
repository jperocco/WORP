"""Fixed-rule chronological validation. Test outcomes never select counts."""
from contextlib import redirect_stdout
from pathlib import Path
import io
import json
import pandas as pd
from worp_positional_portfolio_simulation import run, POS


def choose_training(detail, test_week):
    train=detail[detail.week.lt(test_week)].copy()
    if train.empty:
        return None
    expected=len(train[['week','seed']].drop_duplicates())
    surface=train.groupby(list(POS),as_index=False).agg(
        cases=('week','size'),worst_gap=('gap_to_window_best','max'),mean_gap=('gap_to_window_best','mean'))
    complete=surface[surface.cases.eq(expected)]
    if complete.empty:
        return None
    return complete.sort_values(['worst_gap','mean_gap']+list(POS)).iloc[0]


def evaluate_fold(detail, test_week):
    selected=choose_training(detail,test_week)
    if selected is None:
        return {'status':'no_training_support'}
    vector={p:int(selected[p]) for p in POS}
    test=detail[detail.week.eq(test_week)].copy()
    chosen=test
    for p,v in vector.items():
        chosen=chosen[chosen[p].eq(v)]
    # Infeasible candidates are recorded; test supply cannot trigger reselection.
    if len(chosen)!=3:
        return {**vector,'status':'selected_composition_unavailable'}
    return {**vector,'status':'evaluated','mean_opportunity':chosen.mean_opportunity.mean(),
            'mean_gap':chosen.gap_to_window_best.mean(),
            'max_seed_gap':chosen.gap_to_window_best.max(),
            'train_last_outcome_week':test_week-1}


def main():
    source=Path('research/optionality_multileague')
    out=Path('research/portfolio_temporal_validation');out.mkdir(parents=True,exist_ok=True)
    manifest=pd.read_csv(source/'selected_league_seasons.csv',dtype={'league_id':str})
    protocol=dict(league_seasons=manifest.league_id.tolist(),lookback=3,seeds=[7000,17000,27000],
                  draws=256,benches=[5,12],folds={'8':[4],'12':[4,8]},
                  rule='minimize worst training opportunity gap, then mean gap, then lexical positional counts',
                  unsupported='record failure, never reselect from test data',
                  caveat='retrospective chronological validation, not pristine untouched holdout: earlier development examined some windows')
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    results=[]
    for row in manifest.itertuples():
        frames=[]
        for seed in protocol['seeds']:
            directory=out/'runs'/f'{row.league_id}_{seed}'
            with redirect_stdout(io.StringIO()):
                run(source,directory,row.league_id,[5,12],256,3,seed)
            d=pd.read_csv(directory/'composition_detail.csv',dtype={'league_id':str})
            d['seed']=seed;frames.append(d)
        d=pd.concat(frames,ignore_index=True)
        slots=json.loads(row.roster_positions)
        starters=len([s for s in slots if s!='BN'])
        for bench in (5,12):
            capacity=starters+bench
            for test_week in (8,12):
                result=evaluate_fold(d[d.capacity.eq(capacity)],test_week)
                results.append(dict(league_id=row.league_id,season=row.season,stratum=row.stratum,
                                    capacity=capacity,bench=bench,test_week=test_week,**result))
        pd.DataFrame(results).to_csv(out/'fold_results.csv',index=False)
        print(f'PASS {row.league_id} ({row.stratum})',flush=True)
    r=pd.DataFrame(results)
    evaluated=r[r.status.eq('evaluated')]
    league=evaluated.groupby(['league_id','season','stratum','bench'],as_index=False).agg(
        folds=('test_week','size'),mean_gap=('mean_gap','mean'),worst_gap=('mean_gap','max'))
    league.to_csv(out/'league_summary.csv',index=False)
    summary=league.groupby(['stratum','bench'],as_index=False).agg(
        league_seasons=('league_id','size'),folds=('folds','sum'),
        mean_league_gap=('mean_gap','mean'),worst_fold_gap=('worst_gap','max'))
    summary.to_csv(out/'summary.csv',index=False)
    print(r.status.value_counts().to_string())
    print(summary.to_string(index=False))


if __name__=='__main__':
    main()
