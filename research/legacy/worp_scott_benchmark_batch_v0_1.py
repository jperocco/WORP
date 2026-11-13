#!/usr/bin/env python3
"""WoRP Lab — Scott WAR screenshot benchmark, batch side.

Purpose
-------
Generate our league-native 2023-2025 positional WoRP curves/checkpoints for the
20 Sleeper leagues whose Scott Connor 3-Year WAR screenshots were supplied.
This script does NOT attempt to OCR/pixel-fit Scott's screenshots and does NOT
pretend WAR and WoRP share an absolute scale. It produces the WoRP side of a
structural benchmark: shape, positional ordering, crossovers, cliffs and tail.

The same exact Sleeper configuration is calculated once and reused when two
screenshots correspond to structurally identical league settings.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pandas as pd

from sleeper_native_loader import load_sleeper_player_weeks, fetch_player_map, validate_weekly_contract
from worp_engine import LeagueSettings, calculate_season_worp

API = "https://api.sleeper.app/v1"
SEASONS = (2023, 2024, 2025)
CHECKPOINTS = (1, 5, 10, 20, 30, 40, 50)
POSITIONS = ("QB", "RB", "WR", "TE")
N_SIMS = 8000
SEED = 7

# Current league IDs matching the supplied screenshot filenames.
LEAGUES = {
    "academicos_do_fantasy": ("Acadêmicos do Fantasy", "1312089080602828800"),
    "AML": ("AML", "1312028651251863552"),
    "Americas League": ("America’s League", "1312859125763289088"),
    "BBuster": ("B.BUSTER", "1312443027570036736"),
    "Boss Thinks We're Working": ("Boss Thinks We’re Working SF Dynasty", "1313173772383043584"),
    "BRFFZAPL1": ("BRFFZAP L1", "1312024863770185728"),
    "Broke Dinasty Kings": ("Broke Dynasty Kings", "1312114098133037056"),
    "chernoleague": ("ChernoLeague", "1312079620211736576"),
    "ddlistenerleague4": ("DD Listener League 4", "1312093861622861824"),
    "dodge": ("Dodge, Duck, Dip, Dive & Dynasty", "1312890633362358272"),
    "dynastyaddicions3": ("Dynasty Addictions- #3", "1312187667143725056"),
    "Dynasty Mojuls": ("Dynasty Mojuls", "1333562166342590464"),
    "Dyno Dudes": ("Dyno Dudes", "1313526173799546880"),
    "E Street Legends": ("E Street Legends", "1313025869052149760"),
    "fun_house": ("$5 Fun House Dynasty", "1312478163749572608"),
    "goldeneye": ("Golden Eye", "1312032924173873152"),
    "Guardians of the Gridiron": ("Guardians of The Gridiron", "1312305081911091200"),
    "imoffendedyouracist": ("$50 Im offened you racist 2025", "1314446153420374016"),
    "las_vegas_dinasty": ("Las Vegas Dynasty Invitational", "1312271444629012480"),
    "ligademilao": ("Liga de Milão", "1312119459971891200"),
}


def sleeper_get(path: str):
    req = urllib.request.Request(API + path, headers={"User-Agent": "WoRP-Lab-Scott-Benchmark/0.1"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def counts(roster_positions):
    out = {}
    for p in roster_positions or []:
        out[p] = out.get(p, 0) + 1
    return out


def config_signature(league):
    # Exact calculation identity: team count + starter eligibility + scoring.
    c = counts(league.get("roster_positions", []))
    structural = {
        "teams": int(league.get("total_rosters", 0)),
        "QB": c.get("QB", 0),
        "RB": c.get("RB", 0),
        "WR": c.get("WR", 0),
        "TE": c.get("TE", 0),
        "FLEX": c.get("FLEX", 0),
        "SUPER_FLEX": c.get("SUPER_FLEX", 0),
        "scoring": league.get("scoring_settings", {}),
    }
    return json.dumps(structural, sort_keys=True, separators=(",", ":"))


def calculate_curve(league, player_map):
    c = counts(league.get("roster_positions", []))
    sc = league.get("scoring_settings", {})
    settings = LeagueSettings(
        teams=int(league.get("total_rosters", 0)),
        qb=int(c.get("QB", 0)),
        rb=int(c.get("RB", 0)),
        wr=int(c.get("WR", 0)),
        te=int(c.get("TE", 0)),
        flex=int(c.get("FLEX", 0)),
        superflex=int(c.get("SUPER_FLEX", 0)),
        ppr=float(sc.get("rec", 0.0)),
        te_premium=float(sc.get("bonus_rec_te", 0.0)),
    )

    all_weeks, _ = load_sleeper_player_weeks(
        seasons=SEASONS,
        scoring_settings=sc,
        player_map=player_map,
    )
    validate_weekly_contract(all_weeks)

    frames = []
    for season in SEASONS:
        season_df = all_weeks[all_weeks["season"] == season].copy()
        _, ranking = calculate_season_worp(
            season_df,
            settings,
            replacement_band=6,
            n_sims=N_SIMS,
            seed=SEED,
        )
        ranking = ranking[ranking["position"].isin(POSITIONS)].copy()
        ranking["season"] = season
        ranking["position_rank"] = (
            ranking.groupby("position")["worp"]
            .rank(method="first", ascending=False)
            .astype(int)
        )
        frames.append(ranking[["season", "position", "position_rank", "worp"]])

    source = pd.concat(frames, ignore_index=True)
    curve = (
        source.groupby(["position", "position_rank"], as_index=False)["worp"]
        .mean()
        .rename(columns={"worp": "three_year_worp_avg"})
    )
    return curve[curve["position_rank"] <= 50].copy()


def main():
    print("=" * 100)
    print("SCOTT WAR × WORP — BATCH BENCHMARK V0.1")
    print("20 supplied screenshot leagues | WoRP side only | 2023-2025")
    print("=" * 100)

    resolved = []
    for screenshot_key, (expected_name, league_id) in LEAGUES.items():
        league = sleeper_get(f"/league/{league_id}")
        if not league:
            raise RuntimeError(f"League not found: {expected_name} ({league_id})")
        sig = config_signature(league)
        resolved.append((screenshot_key, expected_name, league_id, league, sig))
        c = counts(league.get("roster_positions", []))
        starters = sum(v for k, v in c.items() if k not in {"BN", "IR", "TAXI"})
        print(
            f"Resolved: {expected_name} | {league_id} | {league.get('total_rosters')}T | "
            f"Start{starters} | SF={c.get('SUPER_FLEX',0)} | TE={c.get('TE',0)}"
        )

    unique = {}
    for row in resolved:
        unique.setdefault(row[4], row[3])
    print(f"\n20 screenshots collapse to {len(unique)} exact calculation configurations.")

    player_map = fetch_player_map()
    curve_by_sig = {}
    for i, (sig, league) in enumerate(unique.items(), start=1):
        print(f"\n[{i}/{len(unique)}] Calculating unique league-native WoRP configuration...")
        curve_by_sig[sig] = calculate_curve(league, player_map)

    detail_rows = []
    checkpoint_rows = []
    for screenshot_key, expected_name, league_id, league, sig in resolved:
        curve = curve_by_sig[sig]
        c = counts(league.get("roster_positions", []))
        starters = sum(v for k, v in c.items() if k not in {"BN", "IR", "TAXI"})
        for r in curve.itertuples(index=False):
            detail_rows.append({
                "screenshot_key": screenshot_key,
                "league_name": expected_name,
                "league_id": league_id,
                "teams": league.get("total_rosters"),
                "starters": starters,
                "sf_slots": c.get("SUPER_FLEX", 0),
                "te_slots": c.get("TE", 0),
                "position": r.position,
                "position_rank": int(r.position_rank),
                "three_year_worp_avg": float(r.three_year_worp_avg),
            })
        cp = curve[curve["position_rank"].isin(CHECKPOINTS)].copy()
        for r in cp.itertuples(index=False):
            checkpoint_rows.append({
                "screenshot_key": screenshot_key,
                "league_name": expected_name,
                "league_id": league_id,
                "position_rank": int(r.position_rank),
                "position": r.position,
                "three_year_worp_avg": float(r.three_year_worp_avg),
            })

    detail = pd.DataFrame(detail_rows)
    checkpoints = pd.DataFrame(checkpoint_rows)
    detail.to_csv("worp_scott_benchmark_curves_v0_1.csv", index=False)
    checkpoints.to_csv("worp_scott_benchmark_checkpoints_v0_1.csv", index=False)

    print("\n" + "=" * 100)
    print("CHECKPOINTS — OUR WORP")
    print("=" * 100)
    for key, (name, _) in LEAGUES.items():
        x = checkpoints[checkpoints["screenshot_key"] == key]
        pivot = x.pivot(index="position_rank", columns="position", values="three_year_worp_avg")
        print(f"\n{name} [{key}]")
        print(pivot.reindex(columns=list(POSITIONS)).round(3).to_string())

    print("\nCreated: worp_scott_benchmark_curves_v0_1.csv")
    print("Created: worp_scott_benchmark_checkpoints_v0_1.csv")
    print("\nReading contract:")
    print("- Do NOT compare Scott WAR and WoRP as if they share an absolute scale.")
    print("- Compare shape, positional ordering, crossovers, cliffs, tail/compression and response to format.")
    print("- Screenshot evidence is structural/range-level; do not manufacture decimal precision from pixels.")
    print("- Only decision-material divergences deserve follow-up.")


if __name__ == "__main__":
    main()
