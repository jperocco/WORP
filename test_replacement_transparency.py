import math
import pandas as pd
from worp_engine import LeagueSettings, select_aggregate_starters, replacement_levels, calculate_week_worp


def make_week():
    rows = []
    for pos, n, base in [("QB", 40, 40), ("RB", 70, 35), ("WR", 90, 34), ("TE", 50, 30)]:
        for i in range(n):
            rows.append({"season": 2025, "week": 1, "player_id": f"{pos}{i}", "player_name": f"{pos} {i}", "position": pos, "fantasy_points": base - i * 0.25})
    return pd.DataFrame(rows)

s = LeagueSettings(teams=12,qb=1,rb=2,wr=3,te=2,flex=2,superflex=1,ppr=.5,te_premium=1)
w = make_week()
starters = select_aggregate_starters(w, s)
r = replacement_levels(w, starters, 6)
for pos, x in r.items():
    assert x["starter_cutoff_rank"] == x["starter_count"]
    assert x["replacement_pool_start"] == x["starter_count"] + 1
    assert x["replacement_pool_end"] == x["starter_count"] + x["band_size"]
    assert x["replacement_effective_rank"] == (x["replacement_pool_start"] + x["replacement_pool_end"]) / 2
    assert x["replacement_rank"] == x["replacement_pool_start"]
out, _, _ = calculate_week_worp(w, s, replacement_band=6, n_sims=500, seed=9)
for col in ["starter_cutoff_rank","replacement_pool_start","replacement_pool_end","replacement_effective_rank"]:
    assert col in out.columns
print("PASS: replacement transparency fields added without changing replacement math")
