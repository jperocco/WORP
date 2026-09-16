"""Reference-league marginal optionality audit; NOT a product quota allocator.

Freeze the target-week ownership snapshot for the evaluation. Eligibility uses
two prior consecutive observations and no actual/positive-oracle start over
the previous up-to-five calendar weeks. Compare random nested subsets from
that owned pool over four forward weeks, retaining the same baseline roster.
Future legal-lineup positive WoRP is a hindsight ceiling, not actual capture.
Missing weekly production contributes zero positive WoRP, not negative WoRP.
Ownership transaction timestamps are not audited: lagged usage eligibility
does not establish a fully ex-ante acquisition strategy. No player names or
player identifiers are written to aggregate outputs.
"""
from concurrent.futures import ThreadPoolExecutor
from itertools import product
from pathlib import Path
import argparse
import json
import urllib.request
import numpy as np
import pandas as pd

POS = ("QB", "RB", "WR", "TE")


def fetch(url):
    with urllib.request.urlopen(url, timeout=45) as response:
        return json.load(response)


def compositions(slots):
    fixed = {p: slots.count(p) for p in POS}
    flex, sf = slots.count("FLEX"), slots.count("SUPER_FLEX")
    unsupported = set(slots) - set(POS) - {"BN", "FLEX", "SUPER_FLEX"}
    if unsupported:
        raise ValueError(f"Unsupported slots: {unsupported}")
    size = sum(fixed.values()) + flex + sf
    legal = []
    for values in product(*(range(fixed[p], fixed[p] + flex + sf + 1) for p in POS)):
        if sum(values) != size or values[0] > fixed["QB"] + sf:
            continue
        legal.append(values)
    return np.array(legal, dtype=int)


def cumulative(ids, outcomes, position, pad):
    values = sorted((outcomes.get(pid, (None, 0))[1] for pid in ids
                     if outcomes.get(pid, (None, 0))[0] == position), reverse=True)
    values += [0.] * pad
    return np.r_[0., np.cumsum(values)][:pad + 1]


def oracle(ids, outcomes, legal):
    scores = np.zeros(len(legal))
    for j, p in enumerate(POS):
        scores += cumulative(ids, outcomes, p, int(legal[:, j].max()))[legal[:, j]]
    return float(scores.max())


def positive_oracle_ids(ids, outcomes, legal):
    scores = np.zeros(len(legal))
    for j, p in enumerate(POS):
        scores += cumulative(ids, outcomes, p, int(legal[:, j].max()))[legal[:, j]]
    chosen = legal[int(scores.argmax())]
    selected = set()
    for j, p in enumerate(POS):
        ordered = sorted((pid for pid in ids if outcomes.get(pid, (None, 0))[0] == p),
                         key=lambda pid: (-outcomes[pid][1], pid))
        selected.update(pid for pid in ordered[:chosen[j]] if outcomes[pid][1] > 0)
    return selected


def run(root, out, draws=64):
    out.mkdir(parents=True, exist_ok=True)
    history = pd.read_csv(root / "wookiee_inseason_roster_history_audit_v0_1.csv",
                          dtype={"league_id": str})
    leagues = history[["season", "league_id"]].drop_duplicates()
    weekly = pd.read_csv(root / "wookiee_2023_2025_weekly_worp.csv", dtype={"player_id": str})
    if weekly.duplicated(["season", "week", "player_id"]).any():
        raise ValueError("Duplicate weekly outcomes")
    outcomes = {}
    for (season, week), group in weekly.groupby(["season", "week"]):
        outcomes[int(season), int(week)] = {
            r.player_id: (r.position, max(0., float(r.weekly_worp)))
            for r in group.itertuples() if r.position in POS
        }
    rows, support, metadata = [], [], []
    rng = np.random.default_rng(7)
    for season, lid in leagues.itertuples(index=False, name=None):
        season = int(season)
        if season not in (2023, 2024, 2025):
            continue
        league = fetch(f"https://api.sleeper.app/v1/league/{lid}")
        legal = compositions(league["roster_positions"])
        metadata.append({"season": season, "league_id": lid,
                         "roster_positions": league["roster_positions"],
                         "scoring_settings": league["scoring_settings"]})
        def download(week):
            return week, fetch(f"https://api.sleeper.app/v1/league/{lid}/matchups/{week}")
        with ThreadPoolExecutor(max_workers=4) as executor:
            snapshots = dict(executor.map(download, range(1, 19)))
        history_rows = {}
        position_map = dict(zip(weekly.loc[weekly.season.eq(season), "player_id"],
                               weekly.loc[weekly.season.eq(season), "position"]))
        for week, snaps in snapshots.items():
            for snap in snaps:
                ids = {str(pid) for pid in snap.get("players") or []}
                starters = {str(pid) for pid in snap.get("starters") or []}
                optimal = positive_oracle_ids(ids, outcomes.get((season, week), {}), legal)
                history_rows[week, snap["roster_id"]] = (ids, starters | optimal)
        for week in range(3, 16):
            # Require full league-wide outcome coverage for all evaluation weeks.
            if not all((season, w) in outcomes for w in range(week, week + 4)):
                continue
            for snap in snapshots[week]:
                rid = snap["roster_id"]
                owned = {str(pid) for pid in snap.get("players") or []}
                previous = [history_rows.get((w, rid), (set(), set()))
                            for w in range(max(1, week - 5), week)]
                eligible = {pid for pid in owned
                            if pid in previous[-1][0] and pid in previous[-2][0]
                            and not any(pid in used for _, used in previous)}
                eligible = {pid for pid in eligible if position_map.get(pid) in POS}
                baseline = owned - eligible
                base = [oracle(baseline, outcomes[season, w], legal)
                        for w in range(week, week + 4)]
                for p in POS:
                    candidates = sorted(pid for pid in eligible if position_map[pid] == p)
                    n = len(candidates)
                    support.append({"season": season, "week": week, "roster_id": rid,
                                    "position": p, "eligible_owned": n})
                    if not n:
                        continue
                    gains = np.zeros((draws, n + 1))
                    for draw in range(draws):
                        order = rng.permutation(candidates)
                        selected = set(baseline)
                        for k, pid in enumerate(order, 1):
                            selected.add(pid)
                            gains[draw, k] = sum(
                                oracle(selected, outcomes[season, w], legal) - base[w - week]
                                for w in range(week, week + 4))
                    marginal = np.diff(gains, axis=1)
                    if marginal.min() < -1e-9:
                        raise AssertionError("Adding a player decreased positive lineup opportunity")
                    for k in range(1, n + 1):
                        rows.append({"season": season, "week": week, "roster_id": rid,
                                     "position": p, "slot": k, "eligible_owned": n,
                                     "mean_four_week_increment": marginal[:, k - 1].mean(),
                                     "mean_four_week_cumulative": gains[:, k].mean()})
        print(f"Finished {season}: {len(rows)} marginal observations", flush=True)
    detail = pd.DataFrame(rows)
    detail.to_csv(out / "marginal_reference_detail.csv", index=False)
    pd.DataFrame(support).to_csv(out / "pool_reference_support.csv", index=False)
    summary = detail.groupby(["season", "position", "slot"], as_index=False).agg(
        roster_weeks=("mean_four_week_increment", "size"),
        mean_four_week_increment=("mean_four_week_increment", "mean"),
        median_four_week_increment=("mean_four_week_increment", "median"))
    summary.to_csv(out / "marginal_reference_summary.csv", index=False)
    (out / "provenance.json").write_text(json.dumps({
        "source_leagues": metadata, "draws": draws, "seed": 7,
        "status": "REFERENCE_DIAGNOSTIC_NOT_PRODUCT_QUOTAS",
        "limitations": ["Wookiee only; no cross-format generalization",
            "Owned low-use pool, not an available acquisition pool",
            "Positive-WoRP legal-lineup hindsight ceiling, not actual capture",
            "Missing production rows contribute zero positive WoRP",
            "Overlapping four-week windows are not independent samples",
            "Slot support differs; summary means must not be ranked across slots",
            "Uniform subsets do not rank candidates using pregame information",
            "Scoring baseline is historical use-based, not the V0.32 envelope",
            "Single-position additions do not estimate joint QB/RB portfolio value"]
    }, indent=2) + "\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).parent)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=64)
    args = parser.parse_args()
    run(args.root, args.out, args.draws)
