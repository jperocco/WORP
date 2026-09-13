#!/usr/bin/env python3
"""
WOOKIEE WR SEASON -> WEEK AUDIT V1
PROVOCAÇÃO / NÃO ALTERA O ENGINE

PERGUNTA ÚNICA
--------------
Conforme descemos o ranking sazonal de WR na Wookiee, o WoRP passa de
recorrente para concentrado em poucas semanas?

CONTRATO
--------
- Liga: Wookiee Moves — 1317417394439741440
- Janela: 2023-2025 REG
- Formato e scoring: lidos diretamente do objeto atual da liga Sleeper.
- Fantasy points: calculados com scoring_settings real da Wookiee.
- WoRP: frozen worp_engine.py V0.2.1; replacement band=6; n_sims=8000; seed=7.
- Rank: rank sazonal por WoRP dentro de WR.
- "Semana positiva": weekly_worp > 0.
- Concentração: participação das 2 melhores semanas no SOMATÓRIO DE WoRP POSITIVO.
  (Usamos WoRP positivo no denominador para não distorcer a concentração por semanas negativas.)
- Não modela escalação real, waiver, Captura, mercado, trades ou roster construction.
- Não modifica worp_engine.py.
"""

from pathlib import Path
from collections import Counter
import json
import math
import sys
import urllib.request

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

LEAGUE_ID = "1317417394439741440"
SEASONS = [2023, 2024, 2025]
BASE = "https://api.sleeper.app/v1"
N_SIMS = 8000
SEED = 7
REPLACEMENT_BAND = 6

try:
    from worp_engine import LeagueSettings, calculate_season_worp
except Exception as e:
    raise SystemExit(f"ERRO importando frozen engine: {e}")


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "WoRP-Lab-Season-Week-Audit/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def normalize_roster_positions(roster_positions):
    c = Counter(roster_positions)
    return {
        "teams": 12,
        "qb": c.get("QB", 0),
        "rb": c.get("RB", 0),
        "wr": c.get("WR", 0),
        "te": c.get("TE", 0),
        "flex": c.get("FLEX", 0),
        "superflex": c.get("SUPER_FLEX", 0),
        "bench": c.get("BN", 0),
        "ir": c.get("IR", 0),
        "taxi": c.get("TAXI", 0),
    }


def score_stats(stats, scoring):
    total = 0.0
    for key, weight in scoring.items():
        if not weight:
            continue
        try:
            total += float(weight) * float(stats.get(key, 0) or 0)
        except (TypeError, ValueError):
            pass
    return total


def parse_weekly_records(raw):
    """Return [(player_id, stats_dict), ...] accepting both Sleeper shapes."""
    if isinstance(raw, dict):
        return [(str(pid), stats or {}) for pid, stats in raw.items()]

    if isinstance(raw, list):
        records = []
        for rec in raw:
            if not isinstance(rec, dict):
                continue
            pid = rec.get("player_id")
            if pid is None:
                continue
            stats = rec.get("stats")
            if stats is None:
                stats = {
                    k: v for k, v in rec.items()
                    if k not in {"player_id", "team", "opponent", "game_id"}
                }
            records.append((str(pid), stats or {}))
        return records

    raise TypeError(f"Formato inesperado do endpoint Sleeper: {type(raw).__name__}")


def weeks_to_fraction_positive(values, frac=0.75):
    vals = np.asarray([v for v in values if pd.notna(v) and v > 0], dtype=float)
    if len(vals) == 0:
        return np.nan
    vals = np.sort(vals)[::-1]
    target = vals.sum() * frac
    return int(np.searchsorted(np.cumsum(vals), target, side="left") + 1)


def top_n_positive_share(values, n=2):
    vals = np.asarray([v for v in values if pd.notna(v) and v > 0], dtype=float)
    if len(vals) == 0 or vals.sum() <= 0:
        return np.nan
    vals = np.sort(vals)[::-1]
    return float(vals[:n].sum() / vals.sum())


print("=" * 100)
print("WOOKIEE WR SEASON -> WEEK AUDIT V1 — SLEEPER-NATIVE SCORING + FROZEN WoRP")
print("=" * 100)

print("\nCONTRACT")
print("Question: does WR WoRP become less recurrent / more spike-concentrated down the season rank curve?")
print("Window: 2023-2025 REG")
print(f"WoRP control: replacement_band={REPLACEMENT_BAND} | n_sims={N_SIMS} | seed={SEED}")
print("Excluded from this gate: real lineup decisions, waiver, Captura, market, trades, roster construction.")

print("\nLoading Wookiee league object...")
league = get_json(f"{BASE}/league/{LEAGUE_ID}")
roster_positions = league.get("roster_positions") or []
scoring = league.get("scoring_settings") or {}

if not roster_positions:
    raise SystemExit("ERRO: league object sem roster_positions.")
if not scoring:
    raise SystemExit("ERRO: league object sem scoring_settings.")

fmt = normalize_roster_positions(roster_positions)
print(f"League: {league.get('name')}")
print("Roster positions:", roster_positions)
print(
    "Parsed starters: "
    f"{fmt['qb']}QB {fmt['rb']}RB {fmt['wr']}WR {fmt['te']}TE "
    f"{fmt['flex']}FLEX {fmt['superflex']}SF"
)
print(f"Non-zero scoring keys: {sum(1 for v in scoring.values() if v)}")

# FP already arrive fully scored from Sleeper scoring_settings below.
# Therefore ppr/te_premium are 0 here to avoid double-scoring; these fields do
# not change precomputed fantasy_points inside the frozen WoRP calculation.
settings = LeagueSettings(
    teams=fmt["teams"],
    qb=fmt["qb"],
    rb=fmt["rb"],
    wr=fmt["wr"],
    te=fmt["te"],
    flex=fmt["flex"],
    superflex=fmt["superflex"],
    ppr=0.0,
    te_premium=0.0,
)

print("\nLoading Sleeper player metadata...")
players = get_json(f"{BASE}/players/nfl")
position_by_id = {}
name_by_id = {}
for pid, meta in players.items():
    meta = meta or {}
    pos = meta.get("position")
    if pos in {"QB", "RB", "WR", "TE"}:
        position_by_id[str(pid)] = pos
        full = meta.get("full_name") or (
            str(meta.get("first_name") or "") + " " + str(meta.get("last_name") or "")
        ).strip()
        name_by_id[str(pid)] = full or str(pid)

all_weekly = []
all_rankings = []

for season in SEASONS:
    print(f"\n{'-'*100}\nSeason {season}: loading Sleeper weekly stats...")
    season_rows = []

    for week in range(1, 19):
        raw = get_json(
            f"https://api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular"
        )
        try:
            records = parse_weekly_records(raw)
        except TypeError as e:
            raise SystemExit(f"ERRO season={season} week={week}: {e}")

        n_kept = 0
        for pid, stats in records:
            pos = position_by_id.get(pid)
            if pos not in {"QB", "RB", "WR", "TE"}:
                continue

            fp = score_stats(stats, scoring)
            season_rows.append({
                "season": season,
                "week": week,
                "player_id": pid,
                "player_name": name_by_id.get(pid, pid),
                "position": pos,
                "fantasy_points": fp,
            })
            n_kept += 1

        print(f"  Week {week:2d}: {n_kept:4d} QB/RB/WR/TE player rows")

    season_df = pd.DataFrame(season_rows)
    if season_df.empty:
        raise SystemExit(f"ERRO: zero player-week rows para {season}.")

    required = {"season", "week", "player_id", "player_name", "position", "fantasy_points"}
    missing = required - set(season_df.columns)
    if missing:
        raise SystemExit(f"ERRO: input do engine sem colunas: {sorted(missing)}")

    # Defensive duplicate check before frozen engine.
    dup = season_df.duplicated(["season", "week", "player_id"], keep=False)
    if dup.any():
        sample = season_df.loc[dup, ["season","week","player_id","player_name"]].head(20)
        raise SystemExit(
            "FAIL: player-week duplicado antes do frozen engine.\n"
            + sample.to_string(index=False)
        )

    print(f"Running frozen WoRP engine for {season}...")
    weekly, ranking = calculate_season_worp(
        season_df,
        settings,
        replacement_band=REPLACEMENT_BAND,
        n_sims=N_SIMS,
        seed=SEED,
    )

    weekly = weekly.copy()
    ranking = ranking.copy()

    if "season" not in weekly.columns:
        weekly["season"] = season
    if "season" not in ranking.columns:
        ranking["season"] = season

    all_weekly.append(weekly)
    all_rankings.append(ranking)

    print(
        f"  Engine output: {len(weekly):,} player-weeks | "
        f"{len(ranking):,} player-seasons"
    )

weekly = pd.concat(all_weekly, ignore_index=True)
rankings = pd.concat(all_rankings, ignore_index=True)

# -------------------------------------------------------------------------
# SANITY / RECONCILIATION
# -------------------------------------------------------------------------
need_w = {"season","week","player_id","player_name","position","weekly_worp"}
need_r = {"season","player_id","player_name","position","worp","games"}
missing_w = need_w - set(weekly.columns)
missing_r = need_r - set(rankings.columns)
if missing_w:
    raise SystemExit(f"ERRO: weekly output sem colunas: {sorted(missing_w)}")
if missing_r:
    raise SystemExit(f"ERRO: ranking output sem colunas: {sorted(missing_r)}")

sum_weekly = (
    weekly.groupby(["season","player_id"], as_index=False)["weekly_worp"]
    .sum()
    .rename(columns={"weekly_worp":"weekly_sum"})
)
recon = rankings[["season","player_id","worp"]].merge(
    sum_weekly, on=["season","player_id"], how="left", validate="one_to_one"
)
recon["abs_diff"] = (recon["worp"] - recon["weekly_sum"].fillna(0)).abs()
max_recon = float(recon["abs_diff"].max()) if len(recon) else np.nan

print("\n" + "=" * 100)
print("1. ENGINE RECONCILIATION")
print("=" * 100)
print(f"Player-seasons: {len(rankings):,}")
print(f"Weekly rows: {len(weekly):,}")
print(f"Max |season WoRP - sum weekly WoRP|: {max_recon:.12f}")
if not np.isfinite(max_recon) or max_recon > 1e-8:
    raise SystemExit("FAIL: season WoRP does not reconcile to weekly WoRP.")
print("PASS: season WoRP reconciles exactly (floating tolerance) to weekly WoRP.")

# -------------------------------------------------------------------------
# WR UNIVERSE + SEASON RANK
# -------------------------------------------------------------------------
wr_r = rankings[rankings["position"] == "WR"].copy()
wr_w = weekly[weekly["position"] == "WR"].copy()

wr_r["pos_rank"] = (
    wr_r.groupby("season")["worp"]
    .rank(method="first", ascending=False)
    .astype(int)
)
wr_r["roster_tier"] = ((wr_r["pos_rank"] - 1) // 12 + 1).astype(int)

wr_w = wr_w.merge(
    wr_r[["season","player_id","pos_rank","roster_tier","games","worp"]],
    on=["season","player_id"],
    how="left",
    validate="many_to_one",
)

if wr_w["pos_rank"].isna().any():
    raise SystemExit("FAIL: WR weekly rows sem season rank após merge.")

# Player-season recurrence / concentration metrics.
player_rows = []
for (season, pid), g in wr_w.groupby(["season","player_id"], sort=False):
    g = g.sort_values("week")
    first = g.iloc[0]
    vals = g["weekly_worp"].astype(float)
    positive = vals[vals > 0]

    games = int(first["games"]) if pd.notna(first["games"]) else len(g)
    # Use engine "games" denominator. If zero, protect division.
    positive_weeks = int((vals > 0).sum())
    player_rows.append({
        "season": int(season),
        "player_id": pid,
        "player_name": first["player_name"],
        "pos_rank": int(first["pos_rank"]),
        "roster_tier": int(first["roster_tier"]),
        "games": games,
        "season_worp": float(first["worp"]),
        "positive_weeks": positive_weeks,
        "positive_week_pct": positive_weeks / games if games > 0 else np.nan,
        "positive_worp_sum": float(positive.sum()) if len(positive) else 0.0,
        "top2_positive_share": top_n_positive_share(vals, n=2),
        "weeks_to_75pct_positive": weeks_to_fraction_positive(vals, frac=0.75),
        "median_weekly_worp": float(vals.median()),
        "mean_weekly_worp": float(vals.mean()),
        "max_weekly_worp": float(vals.max()),
    })

players_wr = pd.DataFrame(player_rows)

# Focus on first 6 12-team tiers for the structural question.
tier_sample = players_wr[players_wr["roster_tier"].between(1, 6)].copy()
tier_summary = (
    tier_sample.groupby("roster_tier")
    .agg(
        player_seasons=("player_id","size"),
        mean_season_worp=("season_worp","mean"),
        mean_positive_weeks=("positive_weeks","mean"),
        mean_positive_week_pct=("positive_week_pct","mean"),
        mean_top2_positive_share=("top2_positive_share","mean"),
        mean_weeks_to_75pct_positive=("weeks_to_75pct_positive","mean"),
        median_weekly_worp=("median_weekly_worp","mean"),
    )
    .reset_index()
)
tier_summary["tier"] = tier_summary["roster_tier"].map(lambda x: f"WR{int(x)}*")

cols = [
    "tier","player_seasons","mean_season_worp","mean_positive_weeks",
    "mean_positive_week_pct","mean_top2_positive_share",
    "mean_weeks_to_75pct_positive","median_weekly_worp"
]
tier_summary = tier_summary[cols]

print("\n" + "=" * 100)
print("2. WOOKEE-NATIVE WR TIER RECURRENCE / CONCENTRATION")
print("=" * 100)
pretty = tier_summary.copy()
pretty["mean_positive_week_pct"] *= 100
pretty["mean_top2_positive_share"] *= 100
print(
    pretty.to_string(
        index=False,
        formatters={
            "mean_season_worp": lambda x: f"{x:.3f}",
            "mean_positive_weeks": lambda x: f"{x:.2f}",
            "mean_positive_week_pct": lambda x: f"{x:.1f}%",
            "mean_top2_positive_share": lambda x: f"{x:.1f}%",
            "mean_weeks_to_75pct_positive": lambda x: f"{x:.2f}",
            "median_weekly_worp": lambda x: f"{x:.4f}",
        }
    )
)

# Exact ranks around the conceptual examples / threshold region.
RANKS_OF_INTEREST = [1, 12, 20, 24, 30, 36, 40, 45, 48, 50, 54, 60, 66, 72]
exact = players_wr[players_wr["pos_rank"].isin(RANKS_OF_INTEREST)].copy()
exact_summary = (
    exact.groupby("pos_rank")
    .agg(
        seasons=("season","nunique"),
        mean_season_worp=("season_worp","mean"),
        mean_positive_weeks=("positive_weeks","mean"),
        mean_positive_week_pct=("positive_week_pct","mean"),
        mean_top2_positive_share=("top2_positive_share","mean"),
        mean_weeks_to_75pct_positive=("weeks_to_75pct_positive","mean"),
    )
    .reset_index()
    .sort_values("pos_rank")
)

print("\n" + "=" * 100)
print("3. EXACT SEASON WR RANKS")
print("=" * 100)
exact_pretty = exact_summary.copy()
exact_pretty["mean_positive_week_pct"] *= 100
exact_pretty["mean_top2_positive_share"] *= 100
print(
    exact_pretty.to_string(
        index=False,
        formatters={
            "mean_season_worp": lambda x: f"{x:.3f}",
            "mean_positive_weeks": lambda x: f"{x:.2f}",
            "mean_positive_week_pct": lambda x: f"{x:.1f}%",
            "mean_top2_positive_share": lambda x: f"{x:.1f}%",
            "mean_weeks_to_75pct_positive": lambda x: f"{x:.2f}",
        }
    )
)

# Season-by-season tiers, to ensure one season is not creating the signal.
by_season_tier = (
    tier_sample.groupby(["season","roster_tier"])
    .agg(
        mean_season_worp=("season_worp","mean"),
        mean_positive_weeks=("positive_weeks","mean"),
        mean_positive_week_pct=("positive_week_pct","mean"),
        mean_top2_positive_share=("top2_positive_share","mean"),
        mean_weeks_to_75pct_positive=("weeks_to_75pct_positive","mean"),
    )
    .reset_index()
)
by_season_tier["tier"] = by_season_tier["roster_tier"].map(lambda x: f"WR{int(x)}*")

print("\n" + "=" * 100)
print("4. YEAR-BY-YEAR CHECK")
print("=" * 100)
for season in SEASONS:
    s = by_season_tier[by_season_tier["season"] == season].copy()
    if s.empty:
        continue
    s["mean_positive_week_pct"] *= 100
    s["mean_top2_positive_share"] *= 100
    print(f"\n{season}")
    print(
        s[[
            "tier","mean_season_worp","mean_positive_weeks",
            "mean_positive_week_pct","mean_top2_positive_share",
            "mean_weeks_to_75pct_positive"
        ]].to_string(
            index=False,
            formatters={
                "mean_season_worp": lambda x: f"{x:.3f}",
                "mean_positive_weeks": lambda x: f"{x:.2f}",
                "mean_positive_week_pct": lambda x: f"{x:.1f}%",
                "mean_top2_positive_share": lambda x: f"{x:.1f}%",
                "mean_weeks_to_75pct_positive": lambda x: f"{x:.2f}",
            }
        )
    )

# Simple structural diagnostic: Spearman rank-tier relation to recurrence/concentration.
# Uses pandas-only Spearman.
diag = players_wr[players_wr["pos_rank"].between(1, 72)].copy()
corrs = {
    "rank vs season_worp": diag["pos_rank"].corr(diag["season_worp"], method="spearman"),
    "rank vs positive_weeks": diag["pos_rank"].corr(diag["positive_weeks"], method="spearman"),
    "rank vs positive_week_pct": diag["pos_rank"].corr(diag["positive_week_pct"], method="spearman"),
    "rank vs top2_positive_share": diag["pos_rank"].corr(diag["top2_positive_share"], method="spearman"),
    "rank vs weeks_to_75pct_positive": diag["pos_rank"].corr(diag["weeks_to_75pct_positive"], method="spearman"),
}

print("\n" + "=" * 100)
print("5. MONOTONICITY DIAGNOSTIC — SPEARMAN, WR1-WR72")
print("=" * 100)
for k, v in corrs.items():
    print(f"{k:36s}: {v:+.4f}")

# Save outputs.
weekly_path = ROOT / "wookiee_2023_2025_weekly_worp.csv"
rank_path = ROOT / "wookiee_2023_2025_rankings_worp.csv"
player_path = ROOT / "wookiee_wr_season_week_player_metrics.csv"
tier_path = ROOT / "wookiee_wr_season_week_tiers.csv"
exact_path = ROOT / "wookiee_wr_season_week_exact_ranks.csv"
season_path = ROOT / "wookiee_wr_season_week_by_season.csv"

weekly.to_csv(weekly_path, index=False)
rankings.to_csv(rank_path, index=False)
players_wr.to_csv(player_path, index=False)
tier_summary.to_csv(tier_path, index=False)
exact_summary.to_csv(exact_path, index=False)
by_season_tier.to_csv(season_path, index=False)

print("\nSaved:")
for p in [weekly_path, rank_path, player_path, tier_path, exact_path, season_path]:
    print(f"  {p.name}")

print("\nGATE")
print("Interpretar SOMENTE Season -> Week: recorrência e concentração do WoRP por rank/tier de WR.")
print("Se o perfil não deteriorar claramente descendo a curva, MATAR/ESTACIONAR esta linha.")
print("Se deteriorar de forma clara e razoavelmente consistente entre 2023-2025, AVANÇAR.")
print("Não inferir Captura real, waiver, market value, trade value ou roster construction neste teste.")
