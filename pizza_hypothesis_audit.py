
from pathlib import Path
import sys
import numpy as np
import pandas as pd

try:
    import nflreadpy as nfl
except ImportError:
    print("ERRO: nflreadpy não está instalado neste ambiente.")
    print("Rode: pip install nflreadpy")
    sys.exit(1)

BASE = Path.cwd()
WEEKLY = BASE / "worp_2016_2025_weekly.csv"
RANKINGS = BASE / "worp_2016_2025_rankings.csv"

for p in [WEEKLY, RANKINGS]:
    if not p.exists():
        print(f"ERRO: não encontrei {p.name} na pasta atual.")
        sys.exit(1)

print("Pizza Hypothesis Audit — PROVOCAÇÃO / NÃO ALTERA O PRODUTO")
print("=" * 72)

w = pd.read_csv(WEEKLY)
r = pd.read_csv(RANKINGS)

# --- WoRP universe: WR only, 2016-2025 ---
w = w[(w["position"] == "WR") & (w["season"].between(2016, 2025))].copy()
r = r[(r["position"] == "WR") & (r["season"].between(2016, 2025))].copy()

# Season positional rank for every player-week.
w = w.merge(
    r[["season", "player_id", "pos_rank", "games", "worp"]],
    on=["season", "player_id"],
    how="left",
    validate="many_to_one",
)

# Format-relative starter-demand boundary:
# median weekly WR starter cutoff for each season.
weekly_boundary = (
    w.groupby(["season", "week"], as_index=False)["starter_cutoff_rank"]
    .first()
)
season_boundary = (
    weekly_boundary.groupby("season")["starter_cutoff_rank"]
    .median()
    .rename("wr_starter_boundary")
)
w = w.merge(season_boundary, on="season", how="left")

# Distance from typical starter demand.
w["rank_distance"] = w["pos_rank"] - w["wr_starter_boundary"]

# Bands are relative to the actual format-derived boundary.
def band(row):
    d = row["rank_distance"]
    if pd.isna(d):
        return np.nan
    if d <= -12:
        return "CORE (12+ ranks inside boundary)"
    if d <= 0:
        return "STARTER EDGE (last 12 inside)"
    if d <= 12:
        return "TAIL 1 (+1 to +12)"
    if d <= 24:
        return "TAIL 2 (+13 to +24)"
    return "DEEP TAIL (+25+)"

w["structural_band"] = w.apply(band, axis=1)

print("\nLoading NFL team weekly stats from nflverse...")
team = nfl.load_team_stats(
    list(range(2016, 2026)),
    summary_level="week"
).to_pandas()

need = {"season", "week", "team", "attempts", "sacks_suffered", "targets"}
missing = need - set(team.columns)
if missing:
    print("ERRO: team stats estão sem colunas esperadas:", sorted(missing))
    print("Colunas disponíveis:", list(team.columns))
    sys.exit(1)

if "season_type" in team.columns:
    team = team[team["season_type"].astype(str).str.upper().isin(["REG", "REGULAR"])].copy()

team = team[list(need)].copy()

# Match naming used by WoRP files if needed.
team["team"] = team["team"].replace({
    "LAR": "LA",
    "STL": "LA",
    "OAK": "LV",
    "SD": "LAC",
    "JAC": "JAX",
    "WSH": "WAS",
})

# Passing-volume proxies.
team["pass_plays_proxy"] = team["attempts"].fillna(0) + team["sacks_suffered"].fillna(0)

# Standardize within season so 2016 vs 2025 league environment does not drive results.
for col in ["pass_plays_proxy", "targets"]:
    team[col + "_z"] = team.groupby("season")[col].transform(
        lambda s: (s - s.mean()) / s.std(ddof=0) if s.std(ddof=0) > 0 else 0.0
    )

# Composite "pizza": mean standardized pass plays and targets.
team["pizza_z"] = team[["pass_plays_proxy_z", "targets_z"]].mean(axis=1)

d = w.merge(
    team[
        [
            "season", "week", "team",
            "attempts", "sacks_suffered", "targets",
            "pass_plays_proxy", "pass_plays_proxy_z",
            "targets_z", "pizza_z"
        ]
    ],
    on=["season", "week", "team"],
    how="inner",
    validate="many_to_one",
)

print(f"Matched WR player-weeks: {len(d):,}")
print(f"Seasons: {d['season'].min()}-{d['season'].max()}")
print(f"Teams matched: {d['team'].nunique()}")

if len(d) < 1000:
    print("ERRO: match muito pequeno; abortando para evitar conclusão frágil.")
    sys.exit(1)

# Keep meaningful observed player-season sample; rank itself defines depth.
d = d.dropna(subset=["weekly_worp", "pos_rank", "pizza_z", "rank_distance"]).copy()

# ---------- lightweight OLS helpers (numpy only) ----------
def ols_r2(y, X):
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    X = np.column_stack([np.ones(len(X)), X])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    pred = X @ beta
    ss_res = np.sum((y - pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return beta, r2

def simple_stats(g):
    if len(g) < 30:
        return pd.Series(dtype=float)
    beta, r2 = ols_r2(g["weekly_worp"], g[["pizza_z"]])
    q = pd.qcut(g["pizza_z"], 4, labels=False, duplicates="drop")
    tmp = g.assign(_q=q)
    lo = tmp.loc[tmp["_q"] == tmp["_q"].min(), "weekly_worp"].mean()
    hi = tmp.loc[tmp["_q"] == tmp["_q"].max(), "weekly_worp"].mean()
    return pd.Series({
        "n_player_weeks": len(g),
        "mean_weekly_worp": g["weekly_worp"].mean(),
        "pizza_slope_worp_per_1sd": beta[1],
        "pizza_r2": r2,
        "top_minus_bottom_pizza_quartile_worp": hi - lo,
        "mean_pos_rank": g["pos_rank"].mean(),
        "mean_boundary": g["wr_starter_boundary"].mean(),
    })

order = [
    "CORE (12+ ranks inside boundary)",
    "STARTER EDGE (last 12 inside)",
    "TAIL 1 (+1 to +12)",
    "TAIL 2 (+13 to +24)",
    "DEEP TAIL (+25+)",
]

band_results = (
    d.groupby("structural_band", observed=True)
    .apply(simple_stats, include_groups=False)
    .reindex(order)
)

# ---------- Incremental explanatory power ----------
# Baseline controls: season fixed effects + positional rank.
# Test: how much R² is added by pizza and by pizza x tail distance.
model = d.copy()
season_dummies = pd.get_dummies(model["season"].astype(str), drop_first=True, dtype=float)
rank = model["pos_rank"].astype(float).to_numpy()
pizza = model["pizza_z"].astype(float).to_numpy()
tail_distance = np.maximum(model["rank_distance"].astype(float).to_numpy(), 0.0)

X_base = np.column_stack([rank, season_dummies.to_numpy()])
_, r2_base = ols_r2(model["weekly_worp"], X_base)

X_pizza = np.column_stack([X_base, pizza])
_, r2_pizza = ols_r2(model["weekly_worp"], X_pizza)

interaction = pizza * tail_distance
X_interact = np.column_stack([X_base, pizza, tail_distance, interaction])
beta_interact, r2_interact = ols_r2(model["weekly_worp"], X_interact)

delta_r2_pizza = r2_pizza - r2_base
delta_r2_interaction = r2_interact - r2_pizza

# ---------- Tail only ----------
tail = d[d["rank_distance"] > 0].copy()
beta_tail, r2_tail = ols_r2(tail["weekly_worp"], tail[["pizza_z"]])

# ---------- Same test by season for robustness ----------
season_rows = []
for season, g in tail.groupby("season"):
    if len(g) < 50:
        continue
    b, r2s = ols_r2(g["weekly_worp"], g[["pizza_z"]])
    q = pd.qcut(g["pizza_z"], 4, labels=False, duplicates="drop")
    gg = g.assign(_q=q)
    delta = (
        gg.loc[gg["_q"] == gg["_q"].max(), "weekly_worp"].mean()
        - gg.loc[gg["_q"] == gg["_q"].min(), "weekly_worp"].mean()
    )
    season_rows.append({
        "season": season,
        "tail_n": len(g),
        "tail_pizza_slope": b[1],
        "tail_pizza_r2": r2s,
        "tail_top_minus_bottom_quartile": delta,
    })
season_df = pd.DataFrame(season_rows)

print("\nFORMAT-RELATIVE WR STARTER DEMAND BOUNDARY")
print(season_boundary.to_string())

print("\nHOW MUCH DOES THE PIZZA EXPLAIN? — BY STRUCTURAL BAND")
print(
    band_results[
        [
            "n_player_weeks",
            "mean_pos_rank",
            "mean_boundary",
            "pizza_slope_worp_per_1sd",
            "pizza_r2",
            "top_minus_bottom_pizza_quartile_worp",
        ]
    ].round(6).to_string()
)

print("\nTAIL-ONLY SUMMARY")
print(f"Tail player-weeks: {len(tail):,}")
print(f"WoRP slope per +1 SD pizza: {beta_tail[1]:.6f}")
print(f"Pizza-only R² in tail: {r2_tail:.6%}")

print("\nINCREMENTAL EXPLANATORY POWER")
print(f"Baseline R² (season FE + pos rank): {r2_base:.6%}")
print(f"+ pizza R²:                         {r2_pizza:.6%}")
print(f"Incremental ΔR² from pizza:         {delta_r2_pizza:.6%}")
print(f"+ pizza x tail-distance R²:         {r2_interact:.6%}")
print(f"Extra ΔR² from interaction:         {delta_r2_interaction:.6%}")

print("\nTAIL ROBUSTNESS BY SEASON")
print(season_df.round(6).to_string(index=False))

# Save complete outputs.
band_results.reset_index().to_csv("pizza_hypothesis_band_results.csv", index=False)
season_df.to_csv("pizza_hypothesis_tail_by_season.csv", index=False)

summary = pd.DataFrame([{
    "matched_wr_player_weeks": len(d),
    "tail_player_weeks": len(tail),
    "tail_pizza_slope_worp_per_1sd": beta_tail[1],
    "tail_pizza_r2": r2_tail,
    "baseline_r2": r2_base,
    "baseline_plus_pizza_r2": r2_pizza,
    "incremental_r2_pizza": delta_r2_pizza,
    "with_interaction_r2": r2_interact,
    "incremental_r2_interaction": delta_r2_interaction,
}])
summary.to_csv("pizza_hypothesis_summary.csv", index=False)

print("\nSaved:")
print("  pizza_hypothesis_summary.csv")
print("  pizza_hypothesis_band_results.csv")
print("  pizza_hypothesis_tail_by_season.csv")
print("\nIMPORTANT: exploratory provocation only. No WoRP engine/UI/product changes.")
