"""League-reading layer built on top of a league-native WoRP curve.

This module is deliberately editorial: it translates already-calculated WoRP
into structural construction guidance.  It never changes the frozen engine,
projects players, assigns market prices, or turns role targets into rigid
roster quotas.
"""

from __future__ import annotations

import pandas as pd


POSITIONS = ("QB", "RB", "WR", "TE")
VALUE = "three_year_worp_avg"


def _prepared_curve(curve: pd.DataFrame) -> pd.DataFrame:
    required = {"position", "position_rank", VALUE}
    missing = required - set(curve.columns)
    if missing:
        raise ValueError(f"League reading curve missing columns: {sorted(missing)}")

    out = curve[list(required)].copy()
    out["position_rank"] = pd.to_numeric(out["position_rank"], errors="coerce")
    out[VALUE] = pd.to_numeric(out[VALUE], errors="coerce")
    out = out[out["position"].isin(POSITIONS)].dropna()
    out = out.sort_values(["position", "position_rank"])
    if out.empty:
        raise ValueError("League reading requires at least one ranked position curve.")
    return out


def _value_at(curve: pd.DataFrame, position: str, rank: int):
    row = curve[(curve.position.eq(position)) & (curve.position_rank.eq(rank))]
    return None if row.empty else float(row.iloc[0][VALUE])


def _frontier(curve: pd.DataFrame, position: str) -> int:
    x = curve[(curve.position.eq(position)) & (curve[VALUE].gt(0))]
    return 0 if x.empty else int(x.position_rank.max())


def _equivalent_rank(curve: pd.DataFrame, source: str, target_value: float):
    x = curve[(curve.position.eq(source)) & (curve[VALUE].gt(0))].copy()
    if x.empty:
        return None
    x["distance"] = (x[VALUE] - float(target_value)).abs()
    return x.sort_values(["distance", "position_rank"]).iloc[0]


def _anchors(frontier: int) -> list[int]:
    """Keep familiar middle-depth checkpoints only when the curve supports them."""
    return [rank for rank in (12, 18, 24) if rank <= int(frontier)]


def build_league_reading(
    curve: pd.DataFrame,
    teams: int,
    qb: int,
    rb: int,
    wr: int,
    te: int,
    flex: int,
    superflex: int,
    scoring: dict | None = None,
    rbwr_flex: int = 0,
) -> dict:
    """Return a transparent league-reading model from an existing WoRP curve.

    The result distinguishes a demonstrated RB-led shared-FLEX economy from a
    generic FLEX-heavy format.  The blueprint is expressed as role coverage,
    not as a hard positional roster quota.
    """
    curve = _prepared_curve(curve)
    scoring = scoring or {}
    frontiers = {p: _frontier(curve, p) for p in POSITIONS}

    rows = []
    for rank in _anchors(frontiers["RB"]):
        rb_value = _value_at(curve, "RB", rank)
        if rb_value is None:
            continue
        row = {"RB rank": f"RB{rank}", "RB WoRP": rb_value}
        for target in ("WR", "TE"):
            match = _equivalent_rank(curve, target, rb_value)
            if match is not None:
                row[f"Comparable {target}"] = f"{target}{int(match.position_rank)}"
                row[f"{target} WoRP"] = float(match[VALUE])
                row[f"{target} rank"] = int(match.position_rank)
        rows.append(row)

    equivalences = pd.DataFrame(rows)
    rb_wr_gaps = []
    if not equivalences.empty and "WR rank" in equivalences:
        for _, row in equivalences.iterrows():
            rb_rank = int(str(row["RB rank"]).replace("RB", ""))
            rb_wr_gaps.append(rb_rank - int(row["WR rank"]))

    elite_ranks = range(1, min(8, frontiers["RB"], frontiers["WR"]) + 1)
    elite_deltas = []
    for rank in elite_ranks:
        rb_value, wr_value = _value_at(curve, "RB", rank), _value_at(curve, "WR", rank)
        if rb_value is not None and wr_value is not None:
            elite_deltas.append(rb_value - wr_value)
    elite_edge = sum(elite_deltas) / len(elite_deltas) if elite_deltas else 0.0
    median_gap = float(pd.Series(rb_wr_gaps).median()) if rb_wr_gaps else 0.0

    restricted_flex = int(rbwr_flex)
    rb_led = (
        (int(flex) + restricted_flex) >= 2
        and len(rb_wr_gaps) >= 2
        and median_gap >= 5
        and elite_edge > 0
    )
    tep = float(scoring.get("bonus_rec_te", 0.0) or 0.0) > 0
    start_n = int(qb) + int(rb) + int(wr) + int(te) + int(flex) + restricted_flex + int(superflex)

    if rb_led:
        headline = "RB-led RB/WR-constrained FLEX economy" if restricted_flex else "RB-led shared-FLEX economy"
        thesis = (
            "RB holds its advantage at the top and through the RB/WR competition for flexible lineup capacity. "
            "Build enough usable RB roles to win flexible slots; do not spend the next "
            "valuable roster spot on a marginal WR merely because WR is a fixed slot."
        )
        rb_detail = (
            f"{int(rb)} fixed RB slot{'s' if int(rb) != 1 else ''} + {restricted_flex} RB/WR-only flex slot{'s' if restricted_flex != 1 else ''} in the lineup + two FLEX-winning RB roles + one resilience role. "
            "These are role targets, not a six-RB quota."
        )
    else:
        headline = "RB/WR-constrained plus shared-FLEX economy" if restricted_flex else "Shared-FLEX economy without a proven RB override"
        thesis = (
            "Flexible lineup capacity creates RB/WR demand in restricted slots and RB/WR/TE demand in shared slots, but this curve does not show "
            "enough RB-over-WR separation to hard-code the next roster spot as RB."
        )
        rb_detail = (
            "Cover the fixed RB requirement, then compare RB, WR and TE directly at the "
            "same WoRP tier before allocating another scoring role."
        )

    blueprint = [
        {
            "Layer": "QB",
            "Role architecture": (
                f"{int(qb) + int(superflex)} starter-quality access "
                + ("plus a survival option" if int(superflex) else "without overpaying for bench-only depth")
            ),
            "Why": "Superflex makes QB availability a lineup input, not only insurance." if int(superflex) else "QB depth is evaluated after the fixed starting requirement.",
        },
        {
            "Layer": "RB",
            "Role architecture": rb_detail,
            "Why": "RB earns the next slot only when the interpositional curve demonstrates the edge.",
        },
        {
            "Layer": "WR",
            "Role architecture": f"{int(wr)} fixed WR role{'s' if int(wr) != 1 else ''}; add depth only when it beats the RB/TE alternative.",
            "Why": "A fixed WR slot is not proof that every marginal WR upgrade is the best use of roster capital.",
        },
        {
            "Layer": "TE",
            "Role architecture": "One required TE role plus a second FLEX-capable option." if tep else "Meet the required TE role; compare additional TE only in the shared FLEX market.",
            "Why": "TE premium expands the set of players that can win a shared FLEX slot." if tep else "Without premium, TE competes through the same shared-slot test.",
        },
    ]

    return {
        "headline": headline,
        "thesis": thesis,
        "rb_led": rb_led,
        "elite_rb_wr_edge": elite_edge,
        "median_rb_wr_rank_gap": median_gap,
        "frontiers": frontiers,
        "equivalences": equivalences.drop(columns=[c for c in ("WR rank", "TE rank") if c in equivalences], errors="ignore"),
        "blueprint": pd.DataFrame(blueprint),
        "start_n": start_n,
    }
