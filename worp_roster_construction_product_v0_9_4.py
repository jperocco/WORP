"""Product bridge for league-native Roster Construction.

Exact historical envelopes remain authoritative when available. Formats without
an exact row receive a lower-confidence envelope derived from their own slot
eligibility, active roster capacity, team count, and league-native WoRP curve.
No nearest-format substitution is performed.
"""

from __future__ import annotations

from itertools import product
import math

import pandas as pd


POSITIONS = ("QB", "RB", "WR", "TE")


def recover_v0_32_ranges(product_ranges=None, v0_24_envelopes=None):
    """Return V0.32 ranges, rebuilding them from local V0.24 when necessary.

    Research CSVs were intentionally local outputs and were not committed with
    the scripts. A user's established WoRP workspace may therefore contain the
    populated V0.24 envelope but an absent or header-only V0.32 product file.
    This applies the frozen V0.32 aggregation exactly; it does not recompute or
    approximate the underlying research.
    """
    if product_ranges is not None and not product_ranges.empty:
        return product_ranges.copy()
    if v0_24_envelopes is None or v0_24_envelopes.empty:
        return pd.DataFrame()

    required = {"format_key", "scoring_total"}
    for p in POSITIONS:
        required.update({f"{p}_low_050", f"{p}_high_050"})
    missing = required - set(v0_24_envelopes.columns)
    if missing:
        raise ValueError(f"V0.24 envelope missing columns: {sorted(missing)}")

    rows = []
    for fmt, group in v0_24_envelopes.groupby("format_key", sort=True):
        totals = pd.to_numeric(group["scoring_total"], errors="coerce").dropna()
        if totals.empty:
            continue
        row = {
            "format_key": fmt,
            "scoring_core_low": int(totals.min()),
            "scoring_core_high": int(totals.max()),
        }
        for p in POSITIONS:
            lows = pd.to_numeric(group[f"{p}_low_050"], errors="coerce").dropna()
            highs = pd.to_numeric(group[f"{p}_high_050"], errors="coerce").dropna()
            if lows.empty or highs.empty:
                raise ValueError(f"V0.24 envelope has no {p} bounds for {fmt}")
            row[f"{p}_low"] = int(lows.min())
            row[f"{p}_high"] = int(highs.max())
        rows.append(row)
    return pd.DataFrame(rows)


def format_key(teams, qb, rb, wr, te, flex, superflex, tep=False):
    start_n = sum(map(int, (qb, rb, wr, te, flex, superflex)))
    return (
        f"{int(teams)}T "
        + ("SF " if int(superflex) > 0 else "1QB ")
        + f"Start{start_n} QB{int(qb)} RB{int(rb)} WR{int(wr)} TE{int(te)} "
        + f"FLEX{int(flex)} SFLEX{int(superflex)}"
        + (" TEP" if bool(tep) else "")
    )


def _can_fill(counts, fixed, flex, superflex):
    if any(counts[p] < fixed[p] for p in POSITIONS):
        return False
    remaining = {p: counts[p] - fixed[p] for p in POSITIONS}

    for flex_rb in range(flex + 1):
        for flex_wr in range(flex - flex_rb + 1):
            flex_te = flex - flex_rb - flex_wr
            flex_need = {"RB": flex_rb, "WR": flex_wr, "TE": flex_te}
            if any(remaining[p] < flex_need[p] for p in ("RB", "WR", "TE")):
                continue
            after_flex = remaining.copy()
            for p in ("RB", "WR", "TE"):
                after_flex[p] -= flex_need[p]
            if sum(after_flex.values()) >= superflex:
                return True
    return False


def _last_positive_rank(curve, position):
    x = curve[curve["position"].eq(position)].copy()
    x["position_rank"] = pd.to_numeric(x["position_rank"], errors="coerce")
    x["three_year_worp_avg"] = pd.to_numeric(
        x["three_year_worp_avg"], errors="coerce"
    )
    x = x[x["position_rank"].notna() & x["three_year_worp_avg"].gt(0)]
    return int(x["position_rank"].max()) if not x.empty else 0


def _construction_value(curve, counts, teams):
    """Per-roster WoRP protected by a positional construction.

    A roster allocation of N players at a position corresponds to league-wide
    access through rank N * teams. Summing that league-native curve and dividing
    by team count yields a comparable per-roster structural value.
    """
    value = 0.0
    for position in POSITIONS:
        depth = int(counts[position]) * int(teams)
        x = curve[curve["position"].eq(position)].copy()
        x["position_rank"] = pd.to_numeric(x["position_rank"], errors="coerce")
        x["three_year_worp_avg"] = pd.to_numeric(
            x["three_year_worp_avg"], errors="coerce"
        )
        x = x[x["position_rank"].between(1, depth)].dropna(
            subset=["three_year_worp_avg"]
        )
        value += float(x["three_year_worp_avg"].sum()) / int(teams)
    return value


def derive_league_native_envelope(
    curve,
    teams,
    qb,
    rb,
    wr,
    te,
    flex,
    superflex,
    active_roster_size,
):
    """Derive a lower-confidence envelope from this league's own economy.

    The V0.19/V0.32 empirical closeout found the broad useful Scoring buffer
    most often at StartN +3..+5. For a format without exact historical support,
    that validated band is constrained by this league's own active roster size
    and positive-WoRP positional supply. Positional ranges are then enumerated
    jointly under the league's FLEX/SF eligibility; their bounds are non-additive.
    """
    required = {"position", "position_rank", "three_year_worp_avg"}
    missing = required - set(curve.columns)
    if missing:
        raise ValueError(f"Roster Construction curve missing columns: {sorted(missing)}")

    teams = int(teams)
    if teams <= 0:
        raise ValueError("Roster Construction requires a positive team count.")
    fixed = {"QB": int(qb), "RB": int(rb), "WR": int(wr), "TE": int(te)}
    flex, superflex = int(flex), int(superflex)
    start_n = sum(fixed.values()) + flex + superflex
    active_roster_size = max(start_n, int(active_roster_size))

    frontier = {p: _last_positive_rank(curve, p) for p in POSITIONS}
    # The per-roster ceiling is an expectation from league-wide positive-WoRP
    # supply. Preserve enough headroom to represent every legal starter mix.
    caps = {
        p: max(fixed[p], int(math.ceil(frontier[p] / teams)))
        for p in POSITIONS
    }
    caps["QB"] = max(caps["QB"], fixed["QB"] + superflex)
    for p in ("RB", "WR", "TE"):
        caps[p] = max(caps[p], fixed[p] + flex + superflex)

    feasible = []
    ranges = [range(fixed[p], caps[p] + 1) for p in POSITIONS]
    for values in product(*ranges):
        counts = dict(zip(POSITIONS, values))
        total = sum(values)
        if total > active_roster_size:
            continue
        if _can_fill(counts, fixed, flex, superflex):
            feasible.append((total, counts))
    if not feasible:
        raise ValueError("No legal Scoring Core construction for this league format.")

    max_economic_total = max(total for total, _ in feasible)
    low = min(active_roster_size, start_n + 3, max_economic_total)
    high = min(active_roster_size, start_n + 5, max_economic_total)
    low = max(start_n, low)
    high = max(low, high)
    in_range = [(total, counts) for total, counts in feasible if low <= total <= high]
    if not in_range:
        nearest_total = min(
            {total for total, _ in feasible}, key=lambda total: abs(total - low)
        )
        low = high = nearest_total
        in_range = [(total, counts) for total, counts in feasible if total == nearest_total]

    # Frozen V0.24 joint decision-equivalence view: absolute regret <= .05 and
    # at least 90% of the observed same-total protection spread retained.
    # The comparison is always within one Scoring-core total; no exact optimum
    # or cross-total positional quota is inferred.
    selected = []
    for total in sorted({total for total, _ in in_range}):
        candidates = [counts for candidate_total, counts in in_range if candidate_total == total]
        scored = [(counts, _construction_value(curve, counts, teams)) for counts in candidates]
        best = max(score for _, score in scored)
        worst = min(score for _, score in scored)
        spread = best - worst
        equivalent = []
        for counts, score in scored:
            regret = best - score
            protection = 1.0 if spread <= 1e-12 else 1.0 - regret / spread
            if regret <= 0.05 + 1e-12 and protection >= 0.90 - 1e-12:
                equivalent.append(counts)
        selected.extend(equivalent or [max(scored, key=lambda item: item[1])[0]])

    result = {
        "source": "LEAGUE_NATIVE_DERIVED",
        "confidence": "LOWER_VALIDATION",
        "scoring_core_low": int(low),
        "scoring_core_high": int(high),
        "format_key": None,
        "frontier": frontier,
        "decision_equivalence": "V0.24_ABS_050_PROTECTION_090",
    }
    for p in POSITIONS:
        result[f"{p}_low"] = min(counts[p] for counts in selected)
        result[f"{p}_high"] = max(counts[p] for counts in selected)
    return result


def roster_construction_envelope(
    curve,
    historical_ranges,
    teams,
    qb,
    rb,
    wr,
    te,
    flex,
    superflex,
    active_roster_size,
    tep=False,
):
    key = format_key(teams, qb, rb, wr, te, flex, superflex, tep=tep)
    if historical_ranges is not None and not historical_ranges.empty:
        hit = historical_ranges[historical_ranges["format_key"].eq(key)]
        if not hit.empty:
            row = hit.iloc[0]
            result = {
                "source": "EXACT_HISTORICAL_SUPPORT",
                "confidence": "EMPIRICALLY_VALIDATED",
                "format_key": key,
            }
            for field in ("scoring_core_low", "scoring_core_high"):
                result[field] = int(row[field])
            for p in POSITIONS:
                result[f"{p}_low"] = int(row[f"{p}_low"])
                result[f"{p}_high"] = int(row[f"{p}_high"])
            return result

    result = derive_league_native_envelope(
        curve=curve,
        teams=teams,
        qb=qb,
        rb=rb,
        wr=wr,
        te=te,
        flex=flex,
        superflex=superflex,
        active_roster_size=active_roster_size,
    )
    result["format_key"] = key
    return result


def whole_roster_layers(envelope, active_roster_size, superflex):
    """Account for the complete active roster without inventing exact quotas.

    V0.7/V0.7.1 support directional optionality priority only: QB material-tail
    hits recurred in 3/3 seasons, RB in 2/3, WR produced zero >=.50 hits, and TE
    remained unresolved. Format changes how that direction is presented: SF
    makes QB optionality primary; in 1QB, RB is primary and QB is secondary.
    """
    active_roster_size = int(active_roster_size)
    scoring_low = int(envelope["scoring_core_low"])
    scoring_high = int(envelope["scoring_core_high"])
    if active_roster_size < scoring_high:
        raise ValueError("Active roster cannot be smaller than the Scoring Core.")

    optionality_low = active_roster_size - scoring_high
    optionality_high = active_roster_size - scoring_low
    is_sf = int(superflex) > 0
    return {
        "active_roster_size": active_roster_size,
        "scoring_core_low": scoring_low,
        "scoring_core_high": scoring_high,
        "optionality_low": optionality_low,
        "optionality_high": optionality_high,
        "primary_optionality": ("QB", "RB") if is_sf else ("RB",),
        "secondary_optionality": () if is_sf else ("QB",),
        "deprioritized_optionality": ("WR",),
        "unresolved_optionality": ("TE",),
        "evidence": {
            "QB": "material hits in 3/3 seasons",
            "RB": "material hits in 2/3 seasons",
            "WR": "zero >=0.50 four-week hits",
            "TE": "sparse / unresolved",
        },
    }
