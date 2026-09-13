import numpy as np
import pandas as pd
from worp_engine import (
    LeagueSettings,
    calculate_week_worp,
    calculate_season_worp,
    select_aggregate_starters,
    replacement_levels,
)


def toy_week(week=1):
    rows=[]
    rng=np.random.default_rng(100+week)
    counts={"QB":40,"RB":70,"WR":90,"TE":45}
    means={"QB":18,"RB":10,"WR":9,"TE":7}
    sds={"QB":6,"RB":6,"WR":6,"TE":5}
    for pos,n in counts.items():
        vals=np.maximum(0,rng.normal(means[pos],sds[pos],n))
        for i,v in enumerate(vals,1):
            rows.append({"season":2025,"week":week,"player_id":f"{pos}{i:03}","player_name":f"{pos} Player {i}","position":pos,"fantasy_points":round(float(v),2)})
    return pd.DataFrame(rows)


def main():
    settings=LeagueSettings(teams=12,qb=1,rb=2,wr=3,te=2,flex=2,superflex=1,ppr=0.5,te_premium=1.0)
    w=toy_week(1)
    starters=select_aggregate_starters(w,settings)
    repl=replacement_levels(w,starters,6)
    out,_,dist=calculate_week_worp(w,settings,n_sims=3000,seed=11)

    assert len(starters)==12*(1+2+3+2+2+1)
    assert all(repl[p]["replacement_points"]>=0 for p in repl)
    assert out.weekly_worp.notna().all()
    assert out.win_prob_player.between(0,1).all()
    assert out.win_prob_replacement.between(0,1).all()
    assert set(out.win_model.unique()) == {"empirical_monte_carlo"}
    # Player win probability and WoRP must be monotonic with weekly fantasy points within position.
    assert (out.sort_values("fantasy_points").groupby("position").weekly_worp.diff().dropna() >= -1e-12).all()
    # V0.2 must not hard-code every replacement context to exactly 50%.
    unique_repl_probs = out.groupby("position").win_prob_replacement.first().round(6)
    assert not np.allclose(unique_repl_probs.to_numpy(), 0.5, atol=1e-6)

    all_weeks=pd.concat([toy_week(i) for i in range(1,5)],ignore_index=True)
    weekly,season=calculate_season_worp(all_weeks,settings,n_sims=1500,seed=13)
    assert not season.empty and weekly.week.nunique()==4

    print("PASS: synthetic empirical WoRP tests")
    print("Starter counts:", starters.position.value_counts().to_dict())
    print("Replacement:", {k: round(v['replacement_points'],2) for k,v in repl.items()})
    print("Empirical opponent score mean/sd:", tuple(round(x,2) for x in dist))
    print("Replacement win probabilities:", {k: round(float(v),4) for k,v in unique_repl_probs.items()})
    print("Top 5 synthetic WoRP:")
    print(season.head(5)[["player_name","position","fantasy_points","porp","worp","avg_replacement_win_prob"]].to_string(index=False))

if __name__=="__main__":
    main()
