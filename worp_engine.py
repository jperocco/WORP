from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np
import pandas as pd

FLEX_ELIGIBLE = {"RB", "WR", "TE"}
SF_ELIGIBLE = {"QB", "RB", "WR", "TE"}


@dataclass(frozen=True)
class LeagueSettings:
    teams: int = 12
    qb: int = 1
    rb: int = 2
    wr: int = 3
    te: int = 1
    flex: int = 2
    superflex: int = 1
    ppr: float = 0.5
    te_premium: float = 0.0

    @property
    def fixed_slots(self) -> Dict[str, int]:
        return {
            "QB": self.teams * self.qb,
            "RB": self.teams * self.rb,
            "WR": self.teams * self.wr,
            "TE": self.teams * self.te,
        }

    @property
    def flex_slots(self) -> int:
        return self.teams * self.flex

    @property
    def sf_slots(self) -> int:
        return self.teams * self.superflex


def score_nflverse_weekly(df: pd.DataFrame, settings: LeagueSettings) -> pd.Series:
    """Compute fantasy points from nflverse weekly player-stat columns.

    Passing: 0.04/yd, 4/TD, -2/INT
    Rushing/Receiving: 0.1/yd, 6/TD
    Receptions: league PPR; TE receives additional TE premium.
    Fumbles lost: -2 when available.
    Two-point conversions: +2 when available.
    Missing stat columns are treated as zero.
    """
    def col(name: str) -> pd.Series:
        if name in df.columns:
            return pd.to_numeric(df[name], errors="coerce").fillna(0.0)
        return pd.Series(0.0, index=df.index)

    pos = df.get("position", pd.Series("", index=df.index)).astype(str).str.upper()
    rec_mult = pd.Series(settings.ppr, index=df.index, dtype=float)
    rec_mult = rec_mult + (pos.eq("TE").astype(float) * settings.te_premium)

    pts = (
        col("passing_yards") * 0.04
        + col("passing_tds") * 4.0
        - col("interceptions") * 2.0
        + col("rushing_yards") * 0.10
        + col("rushing_tds") * 6.0
        + col("receiving_yards") * 0.10
        + col("receiving_tds") * 6.0
        + col("receptions") * rec_mult
        - col("sack_fumbles_lost") * 2.0
        - col("rushing_fumbles_lost") * 2.0
        - col("receiving_fumbles_lost") * 2.0
        + col("passing_2pt_conversions") * 2.0
        + col("rushing_2pt_conversions") * 2.0
        + col("receiving_2pt_conversions") * 2.0
    )
    return pts.astype(float)


def _take_top(pool: pd.DataFrame, n: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if n <= 0 or pool.empty:
        return pool.iloc[0:0].copy(), pool.copy()
    pool = pool.sort_values("fantasy_points", ascending=False, kind="mergesort")
    return pool.head(n).copy(), pool.iloc[n:].copy()


def select_aggregate_starters(week_df: pd.DataFrame, settings: LeagueSettings) -> pd.DataFrame:
    """Select a league-wide starter-level pool that maximizes weekly fantasy points.

    Fixed positional slots are filled first. Remaining FLEX + SF slots are solved
    jointly by enumerating how many SF slots go to QBs; the remaining open slots
    are filled by the best remaining RB/WR/TE scores.

    This is an aggregate scarcity model, not a reconstruction of actual rosters.
    """
    df = week_df.copy()
    df["position"] = df["position"].astype(str).str.upper()
    df = df[df["position"].isin(SF_ELIGIBLE)].copy()
    df = df.sort_values("fantasy_points", ascending=False, kind="mergesort")

    fixed_parts = []
    remaining_parts = []
    for pos, n in settings.fixed_slots.items():
        p = df[df.position.eq(pos)].copy()
        chosen, rem = _take_top(p, n)
        fixed_parts.append(chosen)
        remaining_parts.append(rem)

    fixed = pd.concat(fixed_parts, ignore_index=False) if fixed_parts else df.iloc[0:0]
    rem = pd.concat(remaining_parts, ignore_index=False) if remaining_parts else df.iloc[0:0]

    rem_qb = rem[rem.position.eq("QB")].sort_values("fantasy_points", ascending=False)
    rem_rwt = rem[rem.position.isin(FLEX_ELIGIBLE)].sort_values("fantasy_points", ascending=False)

    flex_n = settings.flex_slots
    sf_n = settings.sf_slots
    best = None
    max_qb_sf = min(sf_n, len(rem_qb))
    for qb_sf in range(max_qb_sf + 1):
        rwt_needed = flex_n + (sf_n - qb_sf)
        if rwt_needed > len(rem_rwt):
            continue
        qb_pick = rem_qb.head(qb_sf)
        rwt_pick = rem_rwt.head(rwt_needed)
        total = float(qb_pick.fantasy_points.sum() + rwt_pick.fantasy_points.sum())
        if best is None or total > best[0]:
            best = (total, qb_pick, rwt_pick)

    if best is None:
        qb_pick = rem_qb.head(min(sf_n, len(rem_qb)))
        remaining_sf = max(0, sf_n - len(qb_pick))
        rwt_pick = rem_rwt.head(min(len(rem_rwt), flex_n + remaining_sf))
    else:
        _, qb_pick, rwt_pick = best

    starters = pd.concat([fixed, qb_pick, rwt_pick], ignore_index=False).copy()
    starters = starters.loc[~starters.index.duplicated(keep="first")]
    return starters


def replacement_levels(
    week_df: pd.DataFrame,
    starters: pd.DataFrame,
    replacement_band: int = 6,
) -> Dict[str, Dict[str, float]]:
    """Return weekly positional replacement baselines.

    For each position, count how many players at that position entered the
    aggregate starter pool, then use the median fantasy points of the next
    `replacement_band` players at that position.
    """
    out: Dict[str, Dict[str, float]] = {}
    for pos in ["QB", "RB", "WR", "TE"]:
        all_pos = week_df[week_df.position.astype(str).str.upper().eq(pos)].sort_values(
            "fantasy_points", ascending=False, kind="mergesort"
        )
        starter_count = int((starters.position.astype(str).str.upper() == pos).sum())
        repl_pool = all_pos.iloc[starter_count : starter_count + replacement_band]
        repl_pts = 0.0 if repl_pool.empty else float(repl_pool.fantasy_points.median())
        pool_start = starter_count + 1
        pool_end = starter_count + len(repl_pool)
        effective_rank = (pool_start + pool_end) / 2.0 if len(repl_pool) else float("nan")
        out[pos] = {
            "starter_count": float(starter_count),
            "starter_cutoff_rank": float(starter_count),
            "replacement_pool_start": float(pool_start),
            "replacement_pool_end": float(pool_end),
            "replacement_effective_rank": float(effective_rank),
            # Backward-compatible alias: this is the START of the replacement pool,
            # not the effective median rank.
            "replacement_rank": float(pool_start),
            "replacement_points": repl_pts,
            "band_size": float(len(repl_pool)),
        }
    return out


def _starter_sampling_pools(starters: pd.DataFrame) -> Dict[str, np.ndarray]:
    s = starters.copy()
    s["position"] = s["position"].astype(str).str.upper()
    pools = {
        pos: s[s.position.eq(pos)].fantasy_points.to_numpy(dtype=float)
        for pos in ["QB", "RB", "WR", "TE"]
    }
    pools["FLEX"] = s[s.position.isin(FLEX_ELIGIBLE)].fantasy_points.to_numpy(dtype=float)
    pools["SF"] = s[s.position.isin(SF_ELIGIBLE)].fantasy_points.to_numpy(dtype=float)
    return pools


def _sample_pool_sum(
    rng: np.random.Generator,
    pool: np.ndarray,
    n_sims: int,
    n_slots: int,
) -> np.ndarray:
    if n_slots <= 0:
        return np.zeros(n_sims, dtype=float)
    if len(pool) == 0:
        return np.zeros(n_sims, dtype=float)
    return rng.choice(pool, size=(n_sims, n_slots), replace=True).sum(axis=1)


def simulate_full_team_scores(
    starters: pd.DataFrame,
    settings: LeagueSettings,
    n_sims: int = 8000,
    seed: int = 7,
) -> np.ndarray:
    """Simulate an empirical distribution of complete fantasy-team scores.

    The simulation samples from the observed weekly starter-level scoring pools
    under the requested league format. No Normal distribution is assumed.
    """
    rng = np.random.default_rng(seed)
    pools = _starter_sampling_pools(starters)
    totals = np.zeros(n_sims, dtype=float)
    totals += _sample_pool_sum(rng, pools["QB"], n_sims, settings.qb)
    totals += _sample_pool_sum(rng, pools["RB"], n_sims, settings.rb)
    totals += _sample_pool_sum(rng, pools["WR"], n_sims, settings.wr)
    totals += _sample_pool_sum(rng, pools["TE"], n_sims, settings.te)
    totals += _sample_pool_sum(rng, pools["FLEX"], n_sims, settings.flex)
    totals += _sample_pool_sum(rng, pools["SF"], n_sims, settings.superflex)
    return totals


def simulate_other_roster_scores(
    starters: pd.DataFrame,
    settings: LeagueSettings,
    position: str,
    n_sims: int = 8000,
    seed: int = 7,
) -> np.ndarray:
    """Simulate the rest of a roster while leaving one slot for `position` empty.

    Prefer removing a fixed slot of that position. If a format has zero fixed
    slots at that position, remove an eligible FLEX slot (RB/WR/TE), then an
    eligible Superflex slot as a final fallback.
    """
    position = str(position).upper()
    rng = np.random.default_rng(seed)
    pools = _starter_sampling_pools(starters)

    counts = {
        "QB": settings.qb,
        "RB": settings.rb,
        "WR": settings.wr,
        "TE": settings.te,
        "FLEX": settings.flex,
        "SF": settings.superflex,
    }

    if counts.get(position, 0) > 0:
        counts[position] -= 1
    elif position in FLEX_ELIGIBLE and counts["FLEX"] > 0:
        counts["FLEX"] -= 1
    elif position in SF_ELIGIBLE and counts["SF"] > 0:
        counts["SF"] -= 1
    else:
        raise ValueError(f"League format has no slot eligible for position {position}")

    totals = np.zeros(n_sims, dtype=float)
    for slot in ["QB", "RB", "WR", "TE", "FLEX", "SF"]:
        totals += _sample_pool_sum(rng, pools[slot], n_sims, counts[slot])
    return totals


def _empirical_win_probability(own_scores: np.ndarray, opponent_scores_sorted: np.ndarray) -> float:
    """Expected head-to-head win probability against an empirical opponent sample.

    Each own-team score is evaluated against the empirical opponent ECDF. Ties
    count as half a win. Scores are rounded only for tie detection; the ordering
    uses the original floating values.
    """
    own = np.asarray(own_scores, dtype=float)
    opp = np.asarray(opponent_scores_sorted, dtype=float)
    if len(own) == 0 or len(opp) == 0:
        return float("nan")

    lower = np.searchsorted(opp, own, side="left")
    upper = np.searchsorted(opp, own, side="right")
    wins = lower / len(opp)
    ties = (upper - lower) / len(opp)
    return float(np.mean(wins + 0.5 * ties))


def estimate_week_score_distribution(
    week_df: pd.DataFrame,
    starters: pd.DataFrame,
    settings: LeagueSettings,
    n_sims: int = 8000,
    seed: int = 7,
) -> Tuple[float, float]:
    """Compatibility helper returning mean/sd of the empirical team-score sample."""
    scores = simulate_full_team_scores(starters, settings, n_sims=n_sims, seed=seed)
    return float(scores.mean()), float(scores.std(ddof=1))


def calculate_week_worp(
    week_df: pd.DataFrame,
    settings: LeagueSettings,
    replacement_band: int = 6,
    n_sims: int = 8000,
    seed: int = 7,
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]], Tuple[float, float]]:
    """Calculate weekly WoRP using an empirical Monte Carlo win model.

    Weekly WoRP = P(win with player) - P(win with positional replacement)

    Both probabilities are evaluated across the same simulated roster contexts
    and against an independently simulated empirical opponent-score distribution.
    The replacement team is NOT forced to 50% win probability.
    """
    df = week_df.copy()
    df["position"] = df["position"].astype(str).str.upper()
    df = df[df.position.isin(SF_ELIGIBLE)].copy()

    starters = select_aggregate_starters(df, settings)
    repl = replacement_levels(df, starters, replacement_band=replacement_band)

    opponent_scores = simulate_full_team_scores(
        starters, settings, n_sims=n_sims, seed=seed + 100_003
    )
    opponent_sorted = np.sort(opponent_scores)
    mean_score = float(opponent_scores.mean())
    sd_score = float(opponent_scores.std(ddof=1))

    other_by_pos: Dict[str, np.ndarray] = {}
    repl_prob_by_pos: Dict[str, float] = {}
    for i, pos in enumerate(["QB", "RB", "WR", "TE"]):
        other_scores = simulate_other_roster_scores(
            starters,
            settings,
            position=pos,
            n_sims=n_sims,
            seed=seed + 10_000 * (i + 1),
        )
        other_by_pos[pos] = other_scores
        rp = repl[pos]["replacement_points"]
        repl_prob_by_pos[pos] = _empirical_win_probability(other_scores + rp, opponent_sorted)

    rows = []
    for _, row in df.iterrows():
        pos = row.position
        rp = repl[pos]["replacement_points"]
        player_pts = float(row.fantasy_points)
        porp = player_pts - rp
        other_scores = other_by_pos[pos]
        p_repl = repl_prob_by_pos[pos]
        p_player = _empirical_win_probability(other_scores + player_pts, opponent_sorted)
        rows.append({
            **row.to_dict(),
            "replacement_points": rp,
            "porp": porp,
            "win_prob_replacement": p_repl,
            "win_prob_player": p_player,
            "weekly_worp": p_player - p_repl,
            "starter_cutoff_rank": repl[pos]["starter_cutoff_rank"],
            "replacement_pool_start": repl[pos]["replacement_pool_start"],
            "replacement_pool_end": repl[pos]["replacement_pool_end"],
            "replacement_effective_rank": repl[pos]["replacement_effective_rank"],
            "replacement_rank": repl[pos]["replacement_rank"],
            "win_model": "empirical_monte_carlo",
            "opponent_score_mean": mean_score,
            "opponent_score_sd": sd_score,
        })

    return pd.DataFrame(rows), repl, (mean_score, sd_score)


def calculate_season_worp(
    player_weeks: pd.DataFrame,
    settings: LeagueSettings,
    replacement_band: int = 6,
    n_sims: int = 8000,
    seed: int = 7,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    required = {"season", "week", "player_id", "player_name", "position", "fantasy_points"}
    missing = required - set(player_weeks.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    weekly_outputs = []
    for (season, week), g in player_weeks.groupby(["season", "week"], sort=True):
        out, _, _ = calculate_week_worp(
            g,
            settings,
            replacement_band=replacement_band,
            n_sims=n_sims,
            seed=seed + int(week),
        )
        weekly_outputs.append(out)

    weekly = (
        pd.concat(weekly_outputs, ignore_index=True)
        if weekly_outputs
        else player_weeks.iloc[0:0].copy()
    )

    season = (
        weekly.groupby(["season", "player_id", "player_name", "position"], as_index=False)
        .agg(
            games=("week", "nunique"),
            fantasy_points=("fantasy_points", "sum"),
            porp=("porp", "sum"),
            worp=("weekly_worp", "sum"),
            avg_replacement_points=("replacement_points", "mean"),
            avg_starter_cutoff_rank=("starter_cutoff_rank", "mean"),
            avg_replacement_pool_start=("replacement_pool_start", "mean"),
            avg_replacement_pool_end=("replacement_pool_end", "mean"),
            avg_replacement_effective_rank=("replacement_effective_rank", "mean"),
            avg_replacement_rank=("replacement_rank", "mean"),
            avg_replacement_win_prob=("win_prob_replacement", "mean"),
        )
        .sort_values(["season", "worp"], ascending=[True, False])
    )
    season["overall_rank"] = season.groupby("season")["worp"].rank(method="first", ascending=False).astype(int)
    season["pos_rank"] = season.groupby(["season", "position"])["worp"].rank(method="first", ascending=False).astype(int)
    return weekly, season
