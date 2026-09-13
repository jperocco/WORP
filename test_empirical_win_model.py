import numpy as np
from test_synthetic import toy_week
from worp_engine import LeagueSettings, calculate_week_worp

settings = LeagueSettings(teams=12,qb=1,rb=2,wr=3,te=2,flex=2,superflex=1,ppr=0.5,te_premium=1.0)
out, _, _ = calculate_week_worp(toy_week(1), settings, n_sims=5000, seed=101)

# One replacement probability per position/context, and it must come from the empirical model.
by_pos = out.groupby("position").win_prob_replacement.first()
assert len(by_pos) == 4
assert by_pos.between(0, 1).all()
assert not np.allclose(by_pos.to_numpy(), 0.5, atol=1e-6)

# A player scoring exactly replacement points should have ~0 WoRP in that same context.
for pos, p_repl in by_pos.items():
    rows = out[out.position.eq(pos)]
    rp = float(rows.replacement_points.iloc[0])
    # The empirical win function is monotonic: nearest player to replacement should be near zero.
    nearest = rows.iloc[(rows.fantasy_points - rp).abs().argsort()[:1]]
    assert abs(float(nearest.weekly_worp.iloc[0])) < 0.08

print("PASS: empirical win model does not force replacement to 50%")
print({k: round(float(v), 4) for k, v in by_pos.items()})
