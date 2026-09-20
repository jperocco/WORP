"""Paired marginal opportunity for one extra roster place, all four positions.

Retrospective owned-pool diagnostic, not an acquisition model or product quota.
Uses frozen native weekly WoRP already cached by the multi-league diagnostic.
"""
import argparse
import json
from itertools import combinations
from pathlib import Path
import numpy as np
import pandas as pd
from worp_optionality_capacity_audit import POS, compositions, oracle, positive_oracle_ids


def marginal_options(base, candidates, future, legal):
    """Average *individual* additions to the same baseline, not their sum.

    Each candidate is retained across the complete evaluation window. Selection
    is uniform over the prior-owned pool, never the best future performer.
    """
    if set(base) & set(candidates):
        raise ValueError("Candidate already belongs to baseline")
    baseline = sum(oracle(base, week, legal) for week in future)
    values = [sum(oracle(set(base) | {pid}, week, legal) for week in future) - baseline
              for pid in sorted(candidates)]
    return np.asarray(values, dtype=float)


def run(source, out):
    out.mkdir(parents=True, exist_ok=True)
    cache = source / "cache"
    manifest = pd.read_csv(source / "selected_league_seasons.csv", dtype={"league_id": str})
    pmap = json.loads((cache / "players.json").read_text())
    records, paired, support = [], [], []
    for row in manifest.itertuples():
        lid = row.league_id
        slots = json.loads(row.roster_positions)
        legal = compositions(slots)
        weekly = pd.read_csv(cache / f"weekly_{lid}.csv", dtype={"player_id": str})
        if weekly.duplicated(["week", "player_id"]).any():
            raise ValueError(f"Duplicate weekly rows: {lid}")
        outcomes = {int(w): {r.player_id: (r.position, max(0., float(r.weekly_worp)))
                           for r in g.itertuples()} for w, g in weekly.groupby("week")}
        snaps = {w: json.loads((cache / f"matchups_{lid}_{w}.json").read_text()) for w in range(1, 19)}
        history = {}
        for w, entries in snaps.items():
            for entry in entries:
                owned = {str(pid) for pid in entry.get("players") or []}
                used = {str(pid) for pid in entry.get("starters") or []}
                used |= positive_oracle_ids(owned, outcomes[w], legal)
                history[w, entry["roster_id"]] = owned, used
        for week in range(4, 16):
            for snap in snaps[week-1]:
                rid = snap["roster_id"]
                prior = [history.get((w, rid)) for w in range(max(1, week-5), week)]
                if any(x is None for x in prior):
                    raise ValueError(f"Missing history: {lid}/{rid}/{week}")
                owned = prior[-1][0]
                eligible = {pid for pid in owned & prior[-2][0] & prior[-3][0]
                            if not any(pid in used for _, used in prior)}
                position = {pid: pmap.get(pid, {}).get("position") for pid in owned}
                eligible = {pid for pid in eligible if position[pid] in POS}
                base = {pid for pid in owned-eligible if position[pid] in POS}
                common = dict(league_id=lid, season=row.season, stratum=row.stratum,
                              roster_id=rid, week=week, baseline_size=len(base), active_capacity=len(slots))
                # Full snapshot capacity check avoids silently selecting from an
                # over-capacity roster; IR/taxi identities remain unavailable.
                valid = len(owned) <= len(slots) and len(base)+1 <= len(slots)
                support.append({**common, "owned_count": len(owned), "capacity_eligible": valid})
                if not valid:
                    continue
                future = [outcomes[w] for w in range(week, week+4)]
                means = {}
                for pos in POS:
                    pool = {pid for pid in eligible if position[pid] == pos}
                    if not pool:
                        continue
                    gains = marginal_options(base, pool, future, legal)
                    means[pos] = (float(gains.mean()), float((gains >= .50).mean()))
                    records.append({**common, "position": pos,
                                    "baseline_position_count": sum(position[pid] == pos for pid in base),
                                    "candidate_count": len(pool), "mean_gain": means[pos][0],
                                    "chance_gain_ge_050": means[pos][1]})
                for a, b in combinations(POS, 2):
                    if a in means and b in means:
                        paired.append({**common, "position_a": a, "position_b": b,
                                       "gain_a": means[a][0], "gain_b": means[b][0],
                                       "delta_a_minus_b": means[a][0]-means[b][0],
                                       "tail_delta_a_minus_b": means[a][1]-means[b][1]})
        print(f"PASS {lid}: {len(paired)} paired rows", flush=True)
    for name, rows in (("marginal_detail", records), ("paired_detail", paired), ("support", support)):
        pd.DataFrame(rows).to_csv(out / f"{name}.csv", index=False)
    df = pd.DataFrame(paired)
    keys = ["stratum", "position_a", "position_b"]
    league = df.groupby(keys+["league_id", "season"], as_index=False).agg(
        cohorts=("week", "size"), gain_a=("gain_a", "mean"), gain_b=("gain_b", "mean"),
        delta=("delta_a_minus_b", "mean"), tail_delta=("tail_delta_a_minus_b", "mean"))
    league.to_csv(out / "paired_league_means.csv", index=False)
    summary = league.groupby(keys, as_index=False).agg(
        league_seasons=("league_id", "size"), seasons=("season", "nunique"), cohorts=("cohorts", "sum"),
        gain_a=("gain_a", "mean"), gain_b=("gain_b", "mean"), delta=("delta", "mean"),
        min_league_delta=("delta", "min"), max_league_delta=("delta", "max"),
        tail_delta=("tail_delta", "mean"))
    summary.to_csv(out / "paired_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("research/optionality_multileague"))
    parser.add_argument("--out", type=Path, default=Path("research/optionality_four_positions"))
    args = parser.parse_args()
    run(args.source, args.out)
