from pathlib import Path
import pandas as pd
import numpy as np

# Roster Construction Marginal Allocation Audit V0.5
# ---------------------------------------------------
# Purpose:
# Put two already-validated descriptive evidence families on the same page:
#   A) realized lineup-use economics (V0.3/V0.4)
#   B) time-local Non-Scoring optionality proxy (existing V0.4 exposure audit)
#
# This script does NOT optimize a roster, does NOT assign permanent roster states,
# and does NOT add produced WoRP to optionality WoRP as if they were equivalent.
# It is a decision crosswalk for the question:
#   after useful scoring depth, what is the opportunity cost of another roster spot?
#
# Important denominator warning:
# - depth economics are player-SEASON outcomes conditional on realized starts.
# - optionality is measured per 100 player-WEEK exposures from a pre-week proxy.
# They are intentionally displayed side-by-side, NOT collapsed into one score.

ROOT = Path('.')
TRANS = ROOT / 'wookiee_roster_construction_transition_zone_v0_3.csv'
OPT = ROOT / 'wookiee_non_scoring_exposure_position_summary_v0_4.csv'
SENS = ROOT / 'wookiee_non_scoring_exposure_sensitivity_v0_4.csv'
OUT = ROOT / 'wookiee_roster_construction_marginal_allocation_v0_5.csv'

for p in [TRANS, OPT, SENS]:
    if not p.exists():
        raise SystemExit(f'STOP: required input missing: {p}')

trans = pd.read_csv(TRANS)
opt = pd.read_csv(OPT)
sens = pd.read_csv(SENS)

need_t = {
    'position','usage_band','n_player_seasons','median_pos_rank','median_worp',
    'share_inside_starter_frontier','share_inside_replacement_frontier'
}
need_o = {
    'position','non_scoring_proxy_player_weeks','promotion_episode_triggers',
    'proxy_promotion_rate_per_player_week','mean_episode_positive_worp_when_promoted',
    'mean_episode_captured_worp_when_promoted','produced_worp_per_100_exposure_weeks',
    'captured_worp_per_100_exposure_weeks'
}
need_s = {'lookback_weeks','position','proxy_promotion_rate_per_player_week'}
for label, df, need in [('transition',trans,need_t),('optionality',opt,need_o),('sensitivity',sens,need_s)]:
    miss = need - set(df.columns)
    if miss:
        raise SystemExit(f'STOP: {label} input missing columns: {sorted(miss)}')

positions = ['QB','RB','WR','TE']
trans = trans[trans.position.isin(positions)].copy()
opt = opt[opt.position.isin(positions)].copy()
sens = sens[sens.position.isin(positions)].copy()

# Keep the two marginal realized-use regions separately. We do not assume that
# 5-7 is always "good depth" or that 1-4 is always "optionality".
depth = trans[trans.usage_band.eq('5-7')].copy()
episodic = trans[trans.usage_band.isin(['3-4','1-2'])].copy()

def weighted_econ(g):
    w = pd.to_numeric(g.n_player_seasons, errors='coerce').fillna(0)
    den = w.sum()
    if den == 0:
        return pd.Series(dtype=float)
    return pd.Series({
        'episodic_n_player_seasons': int(den),
        'episodic_weighted_median_rank_landmark': np.average(g.median_pos_rank, weights=w),
        'episodic_weighted_median_worp_landmark': np.average(g.median_worp, weights=w),
        'episodic_share_inside_replacement': np.average(g.share_inside_replacement_frontier, weights=w),
    })

epi = episodic.groupby('position').apply(weighted_econ, include_groups=False).reset_index()

depth = depth[[
    'position','n_player_seasons','median_pos_rank','median_worp',
    'share_inside_starter_frontier','share_inside_replacement_frontier'
]].rename(columns={
    'n_player_seasons':'depth_5_7_n_player_seasons',
    'median_pos_rank':'depth_5_7_median_pos_rank',
    'median_worp':'depth_5_7_median_worp',
    'share_inside_starter_frontier':'depth_5_7_share_inside_starter',
    'share_inside_replacement_frontier':'depth_5_7_share_inside_replacement',
})

# Sensitivity range for the proxy promotion rate; broad stability matters more
# than a single lookback estimate.
sens_summary = (sens.groupby('position',as_index=False)
    .agg(
        proxy_promotion_rate_min=('proxy_promotion_rate_per_player_week','min'),
        proxy_promotion_rate_max=('proxy_promotion_rate_per_player_week','max'),
    ))

out = depth.merge(epi,on='position',how='outer').merge(opt,on='position',how='outer').merge(sens_summary,on='position',how='left')
out['promotion_rate_sensitivity_spread_pp'] = 100*(out.proxy_promotion_rate_max-out.proxy_promotion_rate_min)

# Decision flags are intentionally coarse and transparent. They are not scores.
# They identify whether realized depth remains economically above replacement and
# whether the optionality evidence is stable enough to compare qualitatively.
out['depth_5_7_economically_supported'] = (
    (out.depth_5_7_median_worp > 0) &
    (out.depth_5_7_share_inside_replacement >= 0.50)
)
out['optionality_proxy_stable'] = out.promotion_rate_sensitivity_spread_pp <= 1.0

# No automatic winner. A positional recommendation would require a common
# roster-spot horizon/denominator or an explicit utility model. Stop before that.
out.to_csv(OUT,index=False)

print('=== ROSTER CONSTRUCTION MARGINAL ALLOCATION V0.5 ===')
print('Side-by-side evidence only; NO composite score and NO final roster prescription.\n')

for pos in positions:
    r = out[out.position.eq(pos)]
    if r.empty: continue
    r=r.iloc[0]
    print(pos)
    print(f"  Scoring-depth landmark (5-7 starts): {pos}{r.depth_5_7_median_pos_rank:.0f} | median WoRP={r.depth_5_7_median_worp:.3f} | inside replacement={r.depth_5_7_share_inside_replacement:.1%}")
    print(f"  Episodic landmark (1-4 starts): approx {pos}{r.episodic_weighted_median_rank_landmark:.0f} | WoRP landmark={r.episodic_weighted_median_worp_landmark:.3f} | inside replacement={r.episodic_share_inside_replacement:.1%}")
    print(f"  Non-Scoring proxy: promotion rate={r.proxy_promotion_rate_per_player_week:.3%}/exposure-week | sensitivity={r.proxy_promotion_rate_min:.3%}-{r.proxy_promotion_rate_max:.3%}")
    print(f"  After proxy promotion: produced={r.mean_episode_positive_worp_when_promoted:.3f} WoRP | captured={r.mean_episode_captured_worp_when_promoted:.3f} WoRP")
    print(f"  Per 100 exposure-weeks: produced={r.produced_worp_per_100_exposure_weeks:.3f} | captured={r.captured_worp_per_100_exposure_weeks:.3f}")
    print(f"  Gates: depth_supported={bool(r.depth_5_7_economically_supported)} | optionality_proxy_stable={bool(r.optionality_proxy_stable)}")
    print()

print('CONCEPTUAL GATE')
print('- Do NOT rank positions by comparing season WoRP directly with WoRP/100 exposure-weeks.')
print('- Do NOT infer trade-value appreciation; no market-value layer exists yet.')
print('- If we want a final "next roster spot" recommendation, the next required step is a common-horizon opportunity-cost model (e.g. expected roster-weeks held / turnover policy).')
print('- That is a conceptual choice, not a harmless technical normalization. STOP there for user alignment.')
print(f'\nCreated: {OUT.name}')
