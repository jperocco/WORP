"""Same-format selection sensitivity, not validation of a product quota."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import pandas as pd
from worp_positional_portfolio_simulation import run, POS


def summarize(detail):
    keys=['capacity']+list(POS)
    # Early-season lookbacks can be identical; never count those as extra cases.
    d=detail.drop_duplicates(['capacity','week','effective_lookback','seed']+list(POS)).copy()
    expected=d[['capacity','week','effective_lookback','seed']].drop_duplicates().groupby('capacity').size()
    surface=d.groupby(keys,as_index=False).agg(cases=('week','size'),
        mean_gap=('gap_to_window_best','mean'),worst_gap=('gap_to_window_best','max'),
        mean_opportunity=('mean_opportunity','mean'))
    surface['complete_support']=surface.cases.eq(surface.capacity.map(expected))
    comparable=surface[surface.complete_support].copy()
    # Minimize worst gap: transparent robustness diagnostic, not a new threshold.
    shortlist=comparable.sort_values(['capacity','worst_gap','mean_gap']+list(POS)).groupby('capacity').head(5)
    return surface,shortlist


def main():
    source=Path('research/optionality_multileague')
    out=Path('research/portfolio_sensitivity');out.mkdir(parents=True,exist_ok=True)
    all_rows=[]
    for lookback in (3,5,0):
        for seed in (7000,17000,27000):
            run_dir=out/f'lookback_{lookback}_seed_{seed}'
            with redirect_stdout(io.StringIO()):
                run(source,run_dir,'1180084795436826624',[5,12],256,lookback,seed)
            d=pd.read_csv(run_dir/'composition_detail.csv',dtype={'league_id':str})
            d['lookback']=lookback;d['seed']=seed
            d['effective_lookback']=d.week.map(lambda w:w-1 if lookback==0 else min(lookback,w-1))
            all_rows.append(d)
            print(f'PASS lookback={lookback} seed={seed}',flush=True)
    detail=pd.concat(all_rows,ignore_index=True)
    surface,shortlist=summarize(detail)
    detail.to_csv(out/'all_scenarios.csv',index=False)
    surface.to_csv(out/'robustness_surface.csv',index=False)
    shortlist.to_csv(out/'shortlist.csv',index=False)
    print(shortlist.to_string(index=False))


if __name__=='__main__':
    main()
