"""League-native Lineup Economics for WoRP Lab V0.9.4.

This module describes expected starting-lineup fantasy-point anatomy. It does
not consume, approximate, or display WoRP.
"""

from __future__ import annotations

import math

import pandas as pd


POSITIONS = ("QB", "RB", "WR", "TE")


def build_lineup_scoring_share(
    player_weeks,
    teams,
    qb,
    rb,
    wr,
    te,
    flex,
    superflex,
):
    """Return expected points and lineup share for each starting-slot layer.

    Each season/week supplies `teams` vacancies per layer. Fixed positional
    layers are filled first, then FLEX and SUPER_FLEX layers are filled in
    eligibility order from the best remaining weekly fantasy-point scores.
    Flexible-slot composition counts the positions of those modeled occupants.
    """
    required = {"season", "week", "position", "fantasy_points"}
    missing = required - set(player_weeks.columns)
    if missing:
        raise ValueError(f"Lineup Economics missing columns: {sorted(missing)}")

    teams = int(teams)
    if teams <= 0:
        raise ValueError("Lineup Economics requires a positive team count.")

    fixed = {"QB": int(qb), "RB": int(rb), "WR": int(wr), "TE": int(te)}
    flex = int(flex)
    superflex = int(superflex)
    if any(value < 0 for value in (*fixed.values(), flex, superflex)):
        raise ValueError("Starting-slot counts cannot be negative.")

    slot_names = []
    for pos in POSITIONS:
        for layer in range(fixed[pos]):
            slot_names.append(pos if fixed[pos] == 1 else f"{pos}{layer + 1}")
    slot_names.extend(f"FLEX {layer + 1}" for layer in range(flex))
    slot_names.extend(f"SUPER_FLEX {layer + 1}" for layer in range(superflex))
    if not slot_names:
        raise ValueError("Lineup Economics requires at least one starting slot.")

    acc = {name: {"weekly_points": [], "positions": []} for name in slot_names}
    data = player_weeks.copy().reset_index(drop=True)
    data["fantasy_points"] = pd.to_numeric(data["fantasy_points"], errors="coerce")
    data = data[
        data["position"].isin(POSITIONS) & data["fantasy_points"].notna()
    ].copy()
    data["_row_id"] = range(len(data))

    if data.empty:
        raise ValueError("Lineup Economics received no valid QB/RB/WR/TE weeks.")

    tie_columns = ["fantasy_points", "position"]
    ascending = [False, True]
    if "player_id" in data.columns:
        tie_columns.append("player_id")
        ascending.append(True)

    for (_, _), week in data.groupby(["season", "week"], sort=True):
        week = week.sort_values(tie_columns, ascending=ascending)
        used = set()

        for pos in POSITIONS:
            positional = week[week["position"] == pos]
            for layer in range(fixed[pos]):
                name = pos if fixed[pos] == 1 else f"{pos}{layer + 1}"
                winners = positional.iloc[layer * teams : (layer + 1) * teams]
                if winners.empty:
                    continue
                acc[name]["weekly_points"].append(float(winners["fantasy_points"].mean()))
                acc[name]["positions"].extend(winners["position"].tolist())
                used.update(winners["_row_id"].tolist())

        def fill_flexible(name, eligible):
            pool = week[
                week["position"].isin(eligible) & ~week["_row_id"].isin(used)
            ]
            winners = pool.sort_values(tie_columns, ascending=ascending).head(teams)
            if winners.empty:
                return
            acc[name]["weekly_points"].append(float(winners["fantasy_points"].mean()))
            acc[name]["positions"].extend(winners["position"].tolist())
            used.update(winners["_row_id"].tolist())

        for layer in range(flex):
            fill_flexible(f"FLEX {layer + 1}", ("RB", "WR", "TE"))
        for layer in range(superflex):
            fill_flexible(f"SUPER_FLEX {layer + 1}", POSITIONS)

    rows = []
    for name in slot_names:
        weekly_points = acc[name]["weekly_points"]
        points_week = float(pd.Series(weekly_points, dtype=float).mean()) if weekly_points else math.nan
        positions = acc[name]["positions"]
        mix = (
            pd.Series(positions, dtype=str).value_counts(normalize=True).to_dict()
            if positions
            else {}
        )
        rows.append({"slot": name, "points_week": points_week, "occupancy": mix})

    finite_points = [row["points_week"] for row in rows if math.isfinite(row["points_week"])]
    total = sum(finite_points)
    if not math.isfinite(total) or total <= 0:
        raise ValueError("Expected starting-lineup points must sum to a positive value.")

    for row in rows:
        row["lineup_share"] = (
            row["points_week"] / total if math.isfinite(row["points_week"]) else 0.0
        )
    return rows
