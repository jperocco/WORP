#!/usr/bin/env python3
"""WoRP Lab V0.28.1 — validate live league-native player economics.

This is a fail-closed audit of the V0.28 player and summary CSVs. It checks
structural integrity, algebraic identities, league coverage, summary
reconciliation, same-economics reproducibility, cross-economics sensitivity,
and optionally recomputes a deterministic sample of leagues from source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

import worp_roster_diagnostic_live_economics_v0_28 as v28
from sleeper_native_loader import (
    fetch_player_map,
    load_sleeper_player_weeks,
    validate_weekly_contract,
)
from worp_engine import calculate_season_worp


LIVE = Path("worp_roster_diagnostic_live_economics_v0_28.csv")
SUMMARY = Path("worp_roster_diagnostic_live_economics_summary_v0_28.csv")
PREFLIGHT = Path("worp_roster_diagnostic_live_preflight_v0_27.csv")
OUT = Path("worp_roster_diagnostic_live_economics_validation_v0_28_1.csv")
TOL = 1e-9
POSITIONS = {"QB", "RB", "WR", "TE"}
REQUIRED = {
    "league_id", "league_name", "format_key", "player_id", "player_name",
    "position", "pos_rank", "weeks", "season_worp", "mean_weekly_worp",
}


def audit(rows: list[dict], check: str, status: str, detail: str) -> None:
    rows.append({"check": check, "status": status, "detail": detail})


def economic_signature(league: dict) -> str:
    payload = {
        "teams": int(league.get("total_rosters") or 0),
        "roster_positions": league.get("roster_positions") or [],
        "scoring_settings": league.get("scoring_settings") or {},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def metadata(live: pd.DataFrame, rows: list[dict]) -> pd.DataFrame:
    records = []
    for league_id in sorted(live["league_id"].astype(str).unique()):
        try:
            league = v28.league(league_id)
            records.append({
                "league_id": league_id,
                "economics_key": economic_signature(league),
            })
        except Exception as exc:
            audit(rows, "LEAGUE_METADATA", "FAIL", f"{league_id}: {exc!r}")
    return pd.DataFrame(records)


def recompute_league(league_id: str, player_map, n_sims: int) -> pd.DataFrame:
    league = v28.league(league_id)
    scoring = league.get("scoring_settings") or {}
    weekly, _ = load_sleeper_player_weeks(
        [v28.SEASON], scoring, player_map=player_map
    )
    validate_weekly_contract(weekly)
    calculated, ranks = calculate_season_worp(
        weekly,
        v28.settings(league),
        replacement_band=6,
        n_sims=n_sims,
        seed=7,
    )
    aggregate = (
        calculated[calculated.position.isin(v28.POS)]
        .groupby(["player_id", "player_name", "position"], as_index=False)
        .agg(
            weeks=("week", "nunique"),
            season_worp=("weekly_worp", "sum"),
            mean_weekly_worp=("weekly_worp", "mean"),
        )
    )
    aggregate = aggregate.merge(
        ranks[["player_id", "position", "pos_rank"]].drop_duplicates(
            ["player_id", "position"]
        ),
        on=["player_id", "position"],
        how="left",
    )
    user = v28.get("/user/" + v28.USERNAME)
    rosters = v28.get("/league/" + league_id + "/rosters")
    mine = next(
        (r for r in rosters if str(r.get("owner_id")) == str(user["user_id"])),
        None,
    )
    if not mine:
        raise RuntimeError("user roster not found during deep check")
    player_ids = {str(x) for x in (mine.get("players") or [])}
    aggregate["player_id"] = aggregate["player_id"].astype(str)
    return aggregate[aggregate.player_id.isin(player_ids)].copy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deep-check-leagues", type=int, default=3)
    parser.add_argument("--n-sims", type=int, default=1500)
    args = parser.parse_args()
    checks: list[dict] = []

    missing_files = [str(p) for p in (LIVE, SUMMARY, PREFLIGHT) if not p.exists()]
    if missing_files:
        raise SystemExit("Missing required files: " + ", ".join(missing_files))

    live = pd.read_csv(LIVE, dtype={"league_id": str, "player_id": str})
    summary = pd.read_csv(SUMMARY, dtype={"league_id": str})
    preflight = pd.read_csv(PREFLIGHT, dtype={"league_id": str})

    missing_columns = sorted(REQUIRED - set(live.columns))
    audit(
        checks,
        "SCHEMA",
        "FAIL" if missing_columns else "PASS",
        "missing=" + ",".join(missing_columns) if missing_columns else "all required columns present",
    )
    if missing_columns:
        pd.DataFrame(checks).to_csv(OUT, index=False)
        raise SystemExit("V0.28.1 FAIL: schema mismatch")

    ready = set(preflight.loc[preflight.status.eq("READY"), "league_id"].astype(str))
    observed = set(live["league_id"].astype(str))
    coverage_ok = ready == observed
    audit(
        checks,
        "READY_LEAGUE_COVERAGE",
        "PASS" if coverage_ok else "FAIL",
        f"ready={len(ready)} observed={len(observed)} missing={sorted(ready-observed)} extra={sorted(observed-ready)}",
    )

    duplicate_n = int(live.duplicated(["league_id", "player_id"]).sum())
    audit(checks, "PLAYER_UNIQUENESS", "PASS" if duplicate_n == 0 else "FAIL", f"duplicate rows={duplicate_n}")

    invalid_positions = sorted(set(live.position.astype(str).str.upper()) - POSITIONS)
    audit(checks, "POSITIONS", "PASS" if not invalid_positions else "FAIL", f"invalid={invalid_positions}")

    numeric_columns = ["pos_rank", "weeks", "season_worp", "mean_weekly_worp"]
    numeric = live[numeric_columns].apply(pd.to_numeric, errors="coerce")
    finite = numeric.notna().all().all() and numeric.applymap(math.isfinite).all().all()
    audit(checks, "FINITE_NUMERICS", "PASS" if finite else "FAIL", f"invalid cells={int(numeric.isna().sum().sum())}")

    ranks = numeric["pos_rank"]
    weeks = numeric["weeks"]
    domain_ok = bool((ranks.ge(1) & ranks.mod(1).eq(0) & weeks.ge(1) & weeks.mod(1).eq(0)).all())
    audit(checks, "RANK_WEEK_DOMAIN", "PASS" if domain_ok else "FAIL", "pos_rank and weeks must be positive integers")

    identity_error = (
        numeric["season_worp"] - numeric["mean_weekly_worp"] * numeric["weeks"]
    ).abs()
    identity_ok = bool(identity_error.le(TOL).all())
    audit(checks, "SEASON_MEAN_IDENTITY", "PASS" if identity_ok else "FAIL", f"max_abs_error={identity_error.max():.3g}")

    probability_bound = numeric["mean_weekly_worp"].abs().le(1 + TOL) & numeric["season_worp"].abs().le(numeric["weeks"] + TOL)
    audit(checks, "WORP_PROBABILITY_BOUNDS", "PASS" if probability_bound.all() else "FAIL", f"violations={int((~probability_bound).sum())}")

    duplicate_ranks = int(live.duplicated(["league_id", "position", "pos_rank"]).sum())
    audit(checks, "POSITIONAL_RANK_UNIQUENESS", "PASS" if duplicate_ranks == 0 else "FAIL", f"duplicate ranks={duplicate_ranks}")

    expected_summary = (
        live.groupby(["league_id", "league_name", "format_key", "position"], as_index=False)
        .agg(
            rostered_players=("player_id", "size"),
            best_pos_rank=("pos_rank", "min"),
            worst_pos_rank=("pos_rank", "max"),
            rostered_season_worp=("season_worp", "sum"),
        )
    )
    keys = ["league_id", "league_name", "format_key", "position"]
    comparison = expected_summary.merge(summary, on=keys, how="outer", suffixes=("_expected", "_actual"), indicator=True)
    summary_ok = comparison._merge.eq("both").all()
    for column in ["rostered_players", "best_pos_rank", "worst_pos_rank", "rostered_season_worp"]:
        left = pd.to_numeric(comparison.get(column + "_expected"), errors="coerce")
        right = pd.to_numeric(comparison.get(column + "_actual"), errors="coerce")
        summary_ok = summary_ok and bool((left - right).abs().fillna(float("inf")).le(TOL).all())
    audit(checks, "SUMMARY_RECONCILIATION", "PASS" if summary_ok else "FAIL", f"groups={len(comparison)}")

    meta = metadata(live, checks)
    enriched = live.merge(meta, on="league_id", how="left")
    same_groups = enriched.groupby(["economics_key", "player_id", "position"], dropna=False)
    same_inconsistent = 0
    comparable_same = 0
    for _, group in same_groups:
        if len(group) < 2:
            continue
        comparable_same += 1
        if (
            group.season_worp.max() - group.season_worp.min() > TOL
            or group.pos_rank.nunique() != 1
            or group.weeks.nunique() != 1
        ):
            same_inconsistent += 1
    audit(
        checks,
        "SAME_ECONOMICS_REPRODUCIBILITY",
        "PASS" if same_inconsistent == 0 else "FAIL",
        f"comparable_player_groups={comparable_same} inconsistent={same_inconsistent}",
    )

    cross = enriched.groupby(["player_id", "position"])
    comparable_cross = 0
    varied_cross = 0
    for _, group in cross:
        if group.economics_key.nunique() < 2:
            continue
        comparable_cross += 1
        if group.season_worp.max() - group.season_worp.min() > TOL or group.pos_rank.nunique() > 1:
            varied_cross += 1
    sensitivity_status = "PASS" if comparable_cross > 0 and varied_cross > 0 else "WARN"
    audit(
        checks,
        "CROSS_ECONOMICS_SENSITIVITY",
        sensitivity_status,
        f"comparable_players={comparable_cross} varied={varied_cross}",
    )

    if args.deep_check_leagues > 0:
        sample_ids = sorted(observed)[: args.deep_check_leagues]
        player_map = fetch_player_map()
        for league_id in sample_ids:
            try:
                fresh = recompute_league(league_id, player_map, args.n_sims)
                saved = live[live.league_id.eq(league_id)].copy()
                merged = saved.merge(
                    fresh,
                    on=["player_id", "position"],
                    how="outer",
                    suffixes=("_saved", "_fresh"),
                    indicator=True,
                )
                common = merged[merged._merge.eq("both")]
                membership_changed = int(merged._merge.ne("both").sum())
                if common.empty:
                    audit(checks, "DEEP_RECOMPUTE", "FAIL", f"{league_id}: no overlapping rostered players")
                    continue
                worp_error = (common.season_worp_saved - common.season_worp_fresh).abs().max()
                mean_error = (common.mean_weekly_worp_saved - common.mean_weekly_worp_fresh).abs().max()
                rank_error = int(common.pos_rank_saved.ne(common.pos_rank_fresh).sum())
                numeric_ok = worp_error <= TOL and mean_error <= TOL and rank_error == 0
                status = "FAIL" if not numeric_ok else ("WARN" if membership_changed else "PASS")
                audit(
                    checks,
                    "DEEP_RECOMPUTE",
                    status,
                    f"{league_id}: overlap={len(common)} roster_delta={membership_changed} max_worp_error={worp_error:.3g} max_mean_error={mean_error:.3g} rank_errors={rank_error}",
                )
            except Exception as exc:
                audit(checks, "DEEP_RECOMPUTE", "FAIL", f"{league_id}: {exc!r}")

    result = pd.DataFrame(checks)
    result.to_csv(OUT, index=False)
    failures = int(result.status.eq("FAIL").sum())
    warnings = int(result.status.eq("WARN").sum())
    verdict = "PASS" if failures == 0 else "FAIL"

    print("V0.28.1 LIVE ECONOMICS VALIDATION")
    print(result.to_string(index=False))
    print(f"\nVERDICT: {verdict} | failures={failures} | warnings={warnings}")
    print(f"Created:\n- {OUT}")
    print("\nREADING CONTRACT")
    print("- PASS authorizes the next frozen Scoring-core/envelope gate; it does not classify players by itself.")
    print("- WARN records limited comparative evidence or live roster drift; it does not conceal a failed invariant.")
    print("- FAIL blocks the next gate until the named invariant is explained or corrected.")


if __name__ == "__main__":
    main()
