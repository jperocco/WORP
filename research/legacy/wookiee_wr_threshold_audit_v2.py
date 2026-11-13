#!/usr/bin/env python3
"""
Wookiee WR Threshold Audit V2
PROVOCAÇÃO / NÃO ALTERA O ENGINE

Pergunta ÚNICA:
    Qual é a demanda estrutural semanal por WR no formato/scoring real da Wookiee?

Importante:
- Lê roster_positions e scoring_settings DIRETAMENTE da liga Sleeper.
- Calcula Fantasy Points com os stats semanais Sleeper e scoring real da liga.
- Usa select_aggregate_starters do worp_engine.py CONGELADO.
- Não altera worp_engine.py.
- Não define waiver.
- Não modela Captura.
- Não compara WR vs RB backup.

Janela:
    2023-2025 REG (as três temporadas já reconciliadas no audit Sleeper anterior)

League:
    Wookiee Moves — 1317417394439741440
"""

from pathlib import Path
from collections import Counter
import json
import sys
import urllib.request
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

LEAGUE_ID = "1317417394439741440"
SEASONS = [2023, 2024, 2025]
BASE = "https://api.sleeper.app/v1"

try:
    from worp_engine import LeagueSettings, select_aggregate_starters
except Exception as e:
    raise SystemExit(f"ERRO importando frozen engine: {e}")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "WoRP-Lab-Threshold-Audit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def normalize_roster_positions(roster_positions):
    c = Counter(roster_positions)

    # Sleeper uses FLEX / SUPER_FLEX in roster_positions.
    # BN, IR and TAXI are not starter demand.
    teams = 12
    return {
        "teams": teams,
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
    # Sleeper scoring contract:
    # Fantasy points = sum(scoring_settings[key] * player_stats[key])
    total = 0.0
    for key, weight in scoring.items():
        if not weight:
            continue
        try:
            total += float(weight) * float(stats.get(key, 0) or 0)
        except (TypeError, ValueError):
            pass
    return total


print("=" * 88)
print("WOOKIEE WR THRESHOLD AUDIT V2 — REAL SLEEPER FORMAT + SCORING")
print("=" * 88)

print("\nLoading Wookiee league object...")
league = get_json(f"{BASE}/league/{LEAGUE_ID}")
roster_positions = league.get("roster_positions") or []
scoring = league.get("scoring_settings") or {}

if not roster_positions:
    raise SystemExit("ERRO: Sleeper league object sem roster_positions.")
if not scoring:
    raise SystemExit("ERRO: Sleeper league object sem scoring_settings.")

fmt = normalize_roster_positions(roster_positions)

print(f"League: {league.get('name')}")
print(f"League ID: {LEAGUE_ID}")
print("Roster positions:", roster_positions)
print(
    "Parsed starters: "
    f"{fmt['qb']}QB {fmt['rb']}RB {fmt['wr']}WR {fmt['te']}TE "
    f"{fmt['flex']}FLEX {fmt['superflex']}SF"
)
print(f"Bench/IR/Taxi observed: {fmt['bench']} / {fmt['ir']} / {fmt['taxi']}")
print(f"Non-zero scoring keys: {sum(1 for v in scoring.values() if v)}")

# The frozen selector needs a LeagueSettings object.
# ppr/te_premium fields are irrelevant here because points are calculated
# directly from Sleeper scoring_settings before allocation.
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

expected_starters = fmt["teams"] * (
    fmt["qb"] + fmt["rb"] + fmt["wr"] + fmt["te"]
    + fmt["flex"] + fmt["superflex"]
)

# Player metadata for positions.
print("\nLoading Sleeper player metadata...")
players = get_json(f"{BASE}/players/nfl")
position_by_id = {}
name_by_id = {}
for pid, meta in players.items():
    pos = (meta or {}).get("position")
    if pos in {"QB", "RB", "WR", "TE"}:
        position_by_id[str(pid)] = pos
        name_by_id[str(pid)] = (
            (meta or {}).get("full_name")
            or (meta or {}).get("first_name", "") + " " + (meta or {}).get("last_name", "")
        ).strip()

weekly_rows = []
allocation_rows = []

for season in SEASONS:
    print(f"\nSeason {season}")
    # REG season lengths in this window = 18 NFL weeks.
    for week in range(1, 19):
        url = f"https://api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular"
        raw = get_json(url)

        rows = []
        for pid, stats in raw.items():
            pid = str(pid)
            pos = position_by_id.get(pid)
            if pos not in {"QB", "RB", "WR", "TE"}:
                continue
            fp = score_stats(stats or {}, scoring)
            rows.append({
                "player_id": pid,
                "player_name": name_by_id.get(pid, pid),
                "position": pos,
                "fantasy_points": fp,
            })

        g = pd.DataFrame(rows)
        if g.empty:
            print(f"  Week {week}: NO DATA — skipped")
            continue

        # Frozen engine call: actual LeagueSettings object, fixing V1 bug.
        selected = select_aggregate_starters(g, settings)

        if not isinstance(selected, pd.DataFrame):
            raise SystemExit(
                f"ERRO season={season} week={week}: "
                f"select_aggregate_starters returned {type(selected).__name__}, expected DataFrame."
            )

        counts = (
            selected["position"]
            .value_counts()
            .reindex(["QB", "RB", "WR", "TE"], fill_value=0)
        )
        total = int(counts.sum())

        if total != expected_starters:
            raise SystemExit(
                f"FAIL season={season} week={week}: "
                f"{total} aggregate starters; expected {expected_starters}."
            )

        wr_n = int(counts["WR"])
        weekly_rows.append({
            "season": season,
            "week": week,
            "wr_starters": wr_n,
            "wr_threshold_rank": wr_n,
        })
        allocation_rows.append({
            "season": season,
            "week": week,
            "QB": int(counts["QB"]),
            "RB": int(counts["RB"]),
            "WR": int(counts["WR"]),
            "TE": int(counts["TE"]),
            "total": total,
        })
        print(
            f"  Week {week:2d}: WR threshold WR{wr_n} "
            f"| allocation QB{int(counts['QB'])} RB{int(counts['RB'])} "
            f"WR{wr_n} TE{int(counts['TE'])}"
        )

weekly = pd.DataFrame(weekly_rows)
alloc = pd.DataFrame(allocation_rows)

if weekly.empty:
    raise SystemExit("ERRO: zero weeks audited.")

def pct(s, q):
    return float(s.quantile(q))

summary = pd.DataFrame([{
    "weeks": len(weekly),
    "min": float(weekly["wr_starters"].min()),
    "p25": pct(weekly["wr_starters"], .25),
    "median": pct(weekly["wr_starters"], .50),
    "mean": float(weekly["wr_starters"].mean()),
    "p75": pct(weekly["wr_starters"], .75),
    "max": float(weekly["wr_starters"].max()),
    "sd": float(weekly["wr_starters"].std(ddof=1)),
}])

season_rows = []
for season, s in weekly.groupby("season"):
    x = s["wr_starters"]
    season_rows.append({
        "season": season,
        "weeks": len(x),
        "min": x.min(),
        "p25": x.quantile(.25),
        "median": x.median(),
        "mean": x.mean(),
        "p75": x.quantile(.75),
        "max": x.max(),
    })
by_season = pd.DataFrame(season_rows)

dist = (
    weekly["wr_starters"].value_counts()
    .sort_index()
    .rename_axis("wr_starters")
    .reset_index(name="weeks")
)
dist["pct_weeks"] = dist["weeks"] / len(weekly) * 100

weekly.to_csv(ROOT / "wookiee_wr_threshold_weekly.csv", index=False)
summary.to_csv(ROOT / "wookiee_wr_threshold_summary.csv", index=False)
by_season.to_csv(ROOT / "wookiee_wr_threshold_by_season.csv", index=False)
dist.to_csv(ROOT / "wookiee_wr_threshold_distribution.csv", index=False)
alloc.to_csv(ROOT / "wookiee_starter_allocation_weekly.csv", index=False)

print("\n" + "=" * 88)
print("1. WR STRUCTURAL DEMAND — 2023-2025")
print("=" * 88)
print(summary.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

print("\n2. BY SEASON")
print(by_season.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

print("\n3. DISTRIBUTION")
print(dist.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

print("\n4. STARTER ALLOCATION SANITY CHECK")
print(
    alloc[["QB", "RB", "WR", "TE", "total"]]
    .agg(["min", "median", "mean", "max"])
    .to_string(float_format=lambda x: f"{x:.2f}")
)

print("\nSaved:")
print("  wookiee_wr_threshold_weekly.csv")
print("  wookiee_wr_threshold_summary.csv")
print("  wookiee_wr_threshold_by_season.csv")
print("  wookiee_wr_threshold_distribution.csv")
print("  wookiee_starter_allocation_weekly.csv")

print("\nGATE:")
print("Interpretar SOMENTE a concentração/estabilidade da demanda estrutural por WR.")
print("Nada de waiver, Captura, RB backup ou roster construction neste gate.")
