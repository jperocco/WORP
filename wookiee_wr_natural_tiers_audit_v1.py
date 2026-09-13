#!/usr/bin/env python3
"""
WOOKIEE WR NATURAL TIERS AUDIT V1
PROVOCAÇÃO -> TESTE | NÃO ALTERA O ENGINE

PERGUNTA ÚNICA
--------------
Existem "tiers naturais" na curva de WR da Wookiee quando usamos WoRP +
recorrência/concentração semanal, ou os blocos de 12 (WR1*, WR2*...) são
apenas convenção da comunidade?

HIPÓTESE ESPECÍFICA SECUNDÁRIA
------------------------------
Pode existir uma "fungibility zone" profunda em que diferenças de rank
(p.ex. algo como WR45 vs WR70/80/90) carregam pouca diferença econômica.

CONTRATO
--------
- Liga: Wookiee Moves — 1317417394439741440
- Janela: 2023-2025 REG
- Formato/scoring: Sleeper real da liga
- WoRP: worp_engine.py congelado; replacement_band=6; n_sims=8000; seed=7
- Não usa market value, trades, waiver, Captura ou roster construction.
- Não força tiers de 12.
- Procura mudanças de regime por métrica separadamente.
- Não cria um "composite score" arbitrário.

MÉTRICAS
--------
1) season_worp
2) positive_week_pct
3) top2_positive_share
4) weeks_to_75pct_positive

MÉTODO
------
A) Constrói curva média por rank (3 seasons por rank quando disponível).
B) Suaviza apenas para detecção de regime com rolling median de 5 ranks.
C) Para cada métrica, testa 1..5 segmentos lineares contíguos
   (mínimo 8 ranks por segmento) e escolhe K por BIC.
D) Agrupa changepoints próximos (±5 ranks) para procurar consenso entre métricas.
E) Faz "tail flatness audit": mede a mudança esperada a cada +12 ranks,
   normalizada pela amplitude WR1-WR90 da própria métrica.

IMPORTANTE
----------
- O output de changepoints é evidência exploratória, não tier definitivo.
- Um breakpoint isolado em uma métrica NÃO vira tier.
- "Fungível" só avança se a cauda ficar relativamente plana em múltiplas métricas.
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

CACHE_PLAYER = ROOT / "wookiee_wr_season_week_player_metrics.csv"
CACHE_WEEKLY = ROOT / "wookiee_2023_2025_weekly_worp.csv"
CACHE_RANKINGS = ROOT / "wookiee_2023_2025_rankings_worp.csv"

PROFILE_OUT = ROOT / "wookiee_wr_natural_tier_rank_profile.csv"
SEGMENTS_OUT = ROOT / "wookiee_wr_natural_tier_segments.csv"
BREAKS_OUT = ROOT / "wookiee_wr_natural_tier_breakpoints.csv"
TAIL_OUT = ROOT / "wookiee_wr_tail_flatness.csv"

METRICS = [
    "season_worp",
    "positive_week_pct",
    "top2_positive_share",
    "weeks_to_75pct_positive",
]

MAX_RANK = 96
MIN_SEGMENT = 8
MAX_SEGMENTS = 5
SMOOTH_WINDOW = 5

try:
    from worp_engine import LeagueSettings, calculate_season_worp
except Exception as e:
    raise SystemExit(f"ERRO importando frozen engine: {e}")


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "WoRP-Lab-Natural-Tiers-Audit/1.0"},
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


def build_player_metrics():
    print("\nNo usable player-metrics cache found. Rebuilding Wookiee-native 2023-2025 WoRP...")
    league = get_json(f"{BASE}/league/{LEAGUE_ID}")
    roster_positions = league.get("roster_positions") or []
    scoring = league.get("scoring_settings") or {}
    if not roster_positions or not scoring:
        raise SystemExit("ERRO: Sleeper league object missing roster_positions/scoring_settings.")

    fmt = normalize_roster_positions(roster_positions)
    print(f"League: {league.get('name')}")
    print(
        f"Starters: {fmt['qb']}QB {fmt['rb']}RB {fmt['wr']}WR {fmt['te']}TE "
        f"{fmt['flex']}FLEX {fmt['superflex']}SF"
    )
    print(f"Non-zero scoring keys: {sum(1 for v in scoring.values() if v)}")

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

    print("Loading player metadata...")
    players = get_json(f"{BASE}/players/nfl")
    position_by_id, name_by_id = {}, {}
    for pid, meta in players.items():
        meta = meta or {}
        pos = meta.get("position")
        if pos in {"QB", "RB", "WR", "TE"}:
            pid = str(pid)
            position_by_id[pid] = pos
            full = meta.get("full_name") or (
                str(meta.get("first_name") or "") + " " + str(meta.get("last_name") or "")
            ).strip()
            name_by_id[pid] = full or pid

    all_weekly, all_rankings = [], []

    for season in SEASONS:
        print(f"\nSeason {season}")
        season_rows = []
        for week in range(1, 19):
            raw = get_json(
                f"https://api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular"
            )
            records = parse_weekly_records(raw)
            kept = 0
            for pid, stats in records:
                pos = position_by_id.get(pid)
                if pos not in {"QB", "RB", "WR", "TE"}:
                    continue
                season_rows.append({
                    "season": season,
                    "week": week,
                    "player_id": pid,
                    "player_name": name_by_id.get(pid, pid),
                    "position": pos,
                    "fantasy_points": score_stats(stats, scoring),
                })
                kept += 1
            print(f"  Week {week:2d}: {kept:4d} rows")

        season_df = pd.DataFrame(season_rows)
        dup = season_df.duplicated(["season", "week", "player_id"], keep=False)
        if dup.any():
            raise SystemExit("FAIL: duplicate player-week rows before engine.")

        print("  Running frozen WoRP engine...")
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

    weekly = pd.concat(all_weekly, ignore_index=True)
    rankings = pd.concat(all_rankings, ignore_index=True)

    # Reconcile BEFORE analysis.
    sum_weekly = (
        weekly.groupby(["season", "player_id"], as_index=False)["weekly_worp"]
        .sum()
        .rename(columns={"weekly_worp": "weekly_sum"})
    )
    recon = rankings[["season", "player_id", "worp"]].merge(
        sum_weekly, on=["season", "player_id"], how="left", validate="one_to_one"
    )
    recon["abs_diff"] = (recon["worp"] - recon["weekly_sum"].fillna(0)).abs()
    max_diff = float(recon["abs_diff"].max())
    print(f"\nReconciliation max diff: {max_diff:.12f}")
    if max_diff > 1e-8:
        raise SystemExit("FAIL: season WoRP != sum weekly WoRP.")
    print("PASS: season/weekly reconciliation.")

    wr_r = rankings[rankings["position"] == "WR"].copy()
    wr_w = weekly[weekly["position"] == "WR"].copy()
    wr_r["pos_rank"] = (
        wr_r.groupby("season")["worp"].rank(method="first", ascending=False).astype(int)
    )
    wr_w = wr_w.merge(
        wr_r[["season", "player_id", "pos_rank", "games", "worp"]],
        on=["season", "player_id"], how="left", validate="many_to_one"
    )

    player_rows = []
    for (season, pid), g in wr_w.groupby(["season", "player_id"], sort=False):
        g = g.sort_values("week")
        first = g.iloc[0]
        vals = g["weekly_worp"].astype(float)
        games = int(first["games"]) if pd.notna(first["games"]) else len(g)
        positive_weeks = int((vals > 0).sum())
        player_rows.append({
            "season": int(season),
            "player_id": pid,
            "player_name": first["player_name"],
            "pos_rank": int(first["pos_rank"]),
            "games": games,
            "season_worp": float(first["worp"]),
            "positive_weeks": positive_weeks,
            "positive_week_pct": positive_weeks / games if games > 0 else np.nan,
            "top2_positive_share": top_n_positive_share(vals, n=2),
            "weeks_to_75pct_positive": weeks_to_fraction_positive(vals, frac=0.75),
        })

    player_metrics = pd.DataFrame(player_rows)

    # Save caches BEFORE any later diagnostics so a late failure never wastes the engine run.
    weekly.to_csv(CACHE_WEEKLY, index=False)
    rankings.to_csv(CACHE_RANKINGS, index=False)
    player_metrics.to_csv(CACHE_PLAYER, index=False)
    print("\nCACHE SAVED BEFORE TIER ANALYSIS:")
    print(f"  {CACHE_WEEKLY.name}")
    print(f"  {CACHE_RANKINGS.name}")
    print(f"  {CACHE_PLAYER.name}")
    return player_metrics


def line_fit_sse(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    n = len(x)
    if n < 2:
        return np.inf, np.nan, np.nan
    X = np.column_stack([np.ones(n), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ beta
    sse = float(np.sum((y - pred) ** 2))
    return sse, float(beta[0]), float(beta[1])


def best_piecewise_linear(x, y, max_segments=5, min_seg=8):
    """
    Dynamic programming over contiguous rank points.
    Chooses segment count by BIC.
    Each segment has intercept+slope. Breakpoint count also gets penalized.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    if n < min_seg:
        raise ValueError("Not enough points for segmentation.")

    # precompute cost for every valid [i:j)
    cost = {}
    fits = {}
    for i in range(n):
        for j in range(i + min_seg, n + 1):
            sse, a, b = line_fit_sse(x[i:j], y[i:j])
            cost[(i, j)] = sse
            fits[(i, j)] = (a, b)

    results = []

    for k in range(1, max_segments + 1):
        # dp[s][j] = best SSE covering first j points with s segments
        dp = [dict() for _ in range(k + 1)]
        back = [dict() for _ in range(k + 1)]

        for j in range(min_seg, n + 1):
            if (0, j) in cost:
                dp[1][j] = cost[(0, j)]
                back[1][j] = 0

        for s in range(2, k + 1):
            min_j = s * min_seg
            for j in range(min_j, n + 1):
                best = np.inf
                best_i = None
                i_min = (s - 1) * min_seg
                i_max = j - min_seg
                for i in range(i_min, i_max + 1):
                    if i not in dp[s - 1] or (i, j) not in cost:
                        continue
                    val = dp[s - 1][i] + cost[(i, j)]
                    if val < best:
                        best = val
                        best_i = i
                if best_i is not None:
                    dp[s][j] = best
                    back[s][j] = best_i

        if n not in dp[k]:
            continue

        sse = max(dp[k][n], 1e-12)
        # 2 params per segment + (k-1) breakpoint locations
        p = 2 * k + (k - 1)
        bic = n * math.log(sse / n) + p * math.log(n)

        # reconstruct
        boundaries = []
        segments = []
        j = n
        for s in range(k, 0, -1):
            i = back[s][j]
            a, b = fits[(i, j)]
            segments.append({
                "start_idx": i,
                "end_idx": j,
                "start_rank": int(x[i]),
                "end_rank": int(x[j - 1]),
                "intercept": a,
                "slope_per_rank": b,
                "slope_per_12_ranks": b * 12,
            })
            if i > 0:
                boundaries.append(int(x[i]))
            j = i

        segments.reverse()
        boundaries = sorted(boundaries)
        results.append({
            "k": k,
            "sse": sse,
            "bic": bic,
            "boundaries": boundaries,
            "segments": segments,
        })

    return min(results, key=lambda z: z["bic"]), results


def cluster_breakpoints(rows, tolerance=5):
    """
    Greedy clusters over breakpoints from different metrics.
    Returns clusters with center + metric support.
    """
    pts = sorted(rows, key=lambda r: r["break_rank"])
    clusters = []
    for row in pts:
        placed = False
        for c in clusters:
            if abs(row["break_rank"] - c["center"]) <= tolerance:
                c["rows"].append(row)
                c["center"] = float(np.median([z["break_rank"] for z in c["rows"]]))
                placed = True
                break
        if not placed:
            clusters.append({"center": float(row["break_rank"]), "rows": [row]})
    return clusters


print("=" * 110)
print("WOOKIEE WR NATURAL TIERS AUDIT V1")
print("=" * 110)
print("Question: natural WoRP/recurrence tiers vs arbitrary 12-player blocks.")
print("Secondary hypothesis: does a deep fungibility zone exist?")
print("NO market / waiver / Captura / trade / roster-construction modeling.")

if CACHE_PLAYER.exists():
    print(f"\nUsing cache: {CACHE_PLAYER.name}")
    player_metrics = pd.read_csv(CACHE_PLAYER)
else:
    player_metrics = build_player_metrics()

need = {
    "season","player_id","player_name","pos_rank","season_worp",
    "positive_week_pct","top2_positive_share","weeks_to_75pct_positive"
}
missing = need - set(player_metrics.columns)
if missing:
    raise SystemExit(f"ERRO: player metrics missing columns: {sorted(missing)}")

x = player_metrics[player_metrics["pos_rank"].between(1, MAX_RANK)].copy()

# Rank profile = mean across seasons; retain N for sample visibility.
profile = (
    x.groupby("pos_rank")
    .agg(
        seasons=("season", "nunique"),
        season_worp=("season_worp", "mean"),
        positive_week_pct=("positive_week_pct", "mean"),
        top2_positive_share=("top2_positive_share", "mean"),
        weeks_to_75pct_positive=("weeks_to_75pct_positive", "mean"),
    )
    .reset_index()
    .sort_values("pos_rank")
)

# Need continuous rank range for segmentation.
profile = profile[profile["seasons"] >= 2].copy()

for m in METRICS:
    profile[m + "_smooth"] = (
        profile[m]
        .rolling(SMOOTH_WINDOW, center=True, min_periods=3)
        .median()
    )

profile.to_csv(PROFILE_OUT, index=False)

print("\n" + "=" * 110)
print("1. RANK PROFILE")
print("=" * 110)
print(f"Ranks available: WR{int(profile['pos_rank'].min())}-WR{int(profile['pos_rank'].max())}")
print(f"Rows: {len(profile)} | rolling median window={SMOOTH_WINDOW}")
print("\nSelected ranks:")
selected = profile[profile["pos_rank"].isin(
    [1,6,12,18,24,30,36,42,48,54,60,66,72,78,84,90,96]
)].copy()
print(
    selected[
        ["pos_rank","seasons","season_worp","positive_week_pct",
         "top2_positive_share","weeks_to_75pct_positive"]
    ].to_string(
        index=False,
        formatters={
            "season_worp": lambda v: f"{v:.3f}",
            "positive_week_pct": lambda v: f"{100*v:.1f}%",
            "top2_positive_share": lambda v: f"{100*v:.1f}%",
            "weeks_to_75pct_positive": lambda v: f"{v:.2f}",
        }
    )
)

# Segment separately by metric.
segment_rows = []
break_rows = []
model_rows = []

print("\n" + "=" * 110)
print("2. NATURAL BREAKPOINTS — METRIC BY METRIC")
print("=" * 110)

for metric in METRICS:
    col = metric + "_smooth"
    d = profile[["pos_rank", col]].dropna().copy()
    best, models = best_piecewise_linear(
        d["pos_rank"].to_numpy(),
        d[col].to_numpy(),
        max_segments=MAX_SEGMENTS,
        min_seg=MIN_SEGMENT,
    )

    print(f"\n{metric}")
    print(f"  Best K by BIC: {best['k']}")
    print(f"  Breakpoints: {best['boundaries'] if best['boundaries'] else 'NONE'}")
    print(f"  BIC: {best['bic']:.2f}")

    for model in models:
        model_rows.append({
            "metric": metric,
            "k": model["k"],
            "bic": model["bic"],
            "sse": model["sse"],
        })

    for b in best["boundaries"]:
        break_rows.append({"metric": metric, "break_rank": int(b)})

    for i, seg in enumerate(best["segments"], start=1):
        row = {"metric": metric, "segment": i, **seg}
        segment_rows.append(row)
        print(
            f"    S{i}: WR{seg['start_rank']}-WR{seg['end_rank']} "
            f"| slope/12 ranks={seg['slope_per_12_ranks']:+.4f}"
        )

segments_df = pd.DataFrame(segment_rows)
breaks_df = pd.DataFrame(break_rows)
segments_df.to_csv(SEGMENTS_OUT, index=False)
breaks_df.to_csv(BREAKS_OUT, index=False)

# Consensus breakpoint clusters.
print("\n" + "=" * 110)
print("3. BREAKPOINT CONSENSUS (±5 ranks)")
print("=" * 110)

if break_rows:
    clusters = cluster_breakpoints(break_rows, tolerance=5)
    cluster_rows = []
    for c in clusters:
        metrics = sorted(set(r["metric"] for r in c["rows"]))
        ranks = sorted(r["break_rank"] for r in c["rows"])
        support = len(metrics)
        center = int(round(c["center"]))
        cluster_rows.append({
            "center_rank": center,
            "support_metrics": support,
            "metrics": ",".join(metrics),
            "raw_breaks": ",".join(map(str, ranks)),
        })
    cluster_df = pd.DataFrame(cluster_rows).sort_values(
        ["support_metrics","center_rank"], ascending=[False, True]
    )
    print(cluster_df.to_string(index=False))
else:
    cluster_df = pd.DataFrame()
    print("No breakpoints selected by BIC.")

# Tail flatness audit.
# Change per 12 ranks normalized by overall WR1-WR90 metric range.
print("\n" + "=" * 110)
print("4. TAIL FLATNESS AUDIT")
print("=" * 110)
print("normalized_change_12 = |linear change per +12 ranks| / WR1-WR90 metric range")
print("Interpretation helper only: <=10% = relatively flat for that metric.")

base = profile[profile["pos_rank"].between(1, 90)].copy()
ranges = {}
for metric in METRICS:
    col = metric + "_smooth"
    vals = base[col].dropna()
    ranges[metric] = float(vals.max() - vals.min()) if len(vals) else np.nan

tail_rows = []
for start in [36, 42, 48, 54, 60]:
    d = profile[profile["pos_rank"].between(start, 90)].copy()
    if len(d) < 12:
        continue

    row = {"tail_start": start, "tail_end": 90}
    flat_count = 0

    for metric in METRICS:
        col = metric + "_smooth"
        q = d[["pos_rank", col]].dropna()
        _, _, slope = line_fit_sse(q["pos_rank"], q[col])
        change12 = slope * 12
        rng = ranges[metric]
        norm = abs(change12) / rng if np.isfinite(rng) and rng > 0 else np.nan

        row[f"{metric}_slope12"] = change12
        row[f"{metric}_norm12"] = norm

        if np.isfinite(norm) and norm <= 0.10:
            flat_count += 1

    row["flat_metrics_le_10pct"] = flat_count
    tail_rows.append(row)

tail_df = pd.DataFrame(tail_rows)
tail_df.to_csv(TAIL_OUT, index=False)

display_cols = ["tail_start", "tail_end", "flat_metrics_le_10pct"]
for metric in METRICS:
    display_cols.append(f"{metric}_norm12")

print(
    tail_df[display_cols].to_string(
        index=False,
        formatters={
            c: (lambda v: f"{100*v:.1f}%")
            for c in display_cols if c.endswith("_norm12")
        }
    )
)

# Candidate deep-fungibility start = earliest tested start where >=3/4 metrics are flat.
candidates = tail_df[tail_df["flat_metrics_le_10pct"] >= 3]
candidate_start = int(candidates["tail_start"].min()) if len(candidates) else None

print("\n" + "=" * 110)
print("5. GATE")
print("=" * 110)

strong_clusters = []
if len(cluster_df):
    strong_clusters = cluster_df[cluster_df["support_metrics"] >= 2]["center_rank"].tolist()

print(f"Consensus breakpoint clusters supported by >=2 metrics: {strong_clusters or 'NONE'}")
print(f"Earliest candidate tail start with >=3/4 relatively-flat metrics: {candidate_start or 'NONE'}")

if strong_clusters and candidate_start is not None:
    print("\nRESULT: ADVANCE")
    print("There is evidence for natural regime changes AND a candidate deep flat/fungible zone.")
    print("Do NOT freeze exact tier boundaries yet; inspect stability and economic magnitude first.")
elif strong_clusters:
    print("\nRESULT: ADVANCE CAUTIOUSLY")
    print("Natural regime changes appear, but no robust deep-flat zone passed the helper threshold.")
elif candidate_start is not None:
    print("\nRESULT: PARK NATURAL-TIER LABELS / ADVANCE TAIL TEST")
    print("Tail flatness appears, but breakpoint consensus is weak.")
else:
    print("\nRESULT: PARK")
    print("No strong evidence that discrete natural tiers beat treating WR value as a continuous curve.")

print("\nSaved:")
for p in [PROFILE_OUT, SEGMENTS_OUT, BREAKS_OUT, TAIL_OUT]:
    print(f"  {p.name}")

print("\nSTOP RULE:")
print("Do not infer trade strategy, roster concentration, waiver replacement or Captura from this audit.")
