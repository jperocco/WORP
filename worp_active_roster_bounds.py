"""Conditional bounds, not reconstructed historical active identities."""
import json
from pathlib import Path
import pandas as pd


def active_bounds(owned, starters, positions, capacity, reserve_capacity):
    owned, starters = set(owned), set(starters) - {"0"}
    if not starters <= owned:
        raise ValueError("Starter absent from ownership snapshot")
    if capacity < 0 or reserve_capacity < 0:
        raise ValueError("Negative capacity")
    low, high = max(len(starters), len(owned)-reserve_capacity), min(capacity, len(owned))
    if low > high:
        raise ValueError("Snapshot incompatible with supplied capacity")
    result = {"active_min": low, "active_max": high,
              "nonactive_min": len(owned)-high, "nonactive_max": len(owned)-low}
    for pos in ("QB", "RB", "WR", "TE"):
        n = sum(positions.get(pid) == pos for pid in owned)
        fixed = sum(positions.get(pid) == pos for pid in starters)
        other_fixed = len(starters)-fixed
        result[pos+"_min"] = max(fixed, n-reserve_capacity)
        result[pos+"_max"] = min(n, capacity-other_fixed)
    return result


def run():
    source = Path("research/optionality_multileague")
    out = Path("research/active_roster_recovery")
    out.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(source/"selected_league_seasons.csv", dtype={"league_id": str})
    pmap = json.loads((source/"cache/players.json").read_text())
    positions = {pid: item.get("position") for pid, item in pmap.items()}
    rows = []
    for league in manifest.itertuples():
        settings = json.loads(league.settings)
        capacity = len(json.loads(league.roster_positions))
        reserve = int(settings.get("reserve_slots", 0))+int(settings.get("taxi_slots", 0))
        for week in range(3, 15):
            snapshots = json.loads((source/"cache"/f"matchups_{league.league_id}_{week}.json").read_text())
            for snap in snapshots:
                row = dict(league_id=league.league_id, season=league.season, week=week,
                           roster_id=snap["roster_id"], capacity=capacity, reserve_capacity=reserve)
                try:
                    row.update(active_bounds(snap["players"], snap["starters"], positions, capacity, reserve))
                    row["status"] = "conditional_bounds"
                except ValueError as exc:
                    row.update(status="incompatible", reason=str(exc))
                rows.append(row)
    frame = pd.DataFrame(rows)
    frame.to_csv(out/"weekly_bounds.csv", index=False)
    print(frame.status.value_counts().to_string())
    ok = frame[frame.status.eq("conditional_bounds")]
    print("Exact total count:", int(ok.active_min.eq(ok.active_max).sum()))
    print("All four positional counts exact:", int(pd.concat([ok[p+"_min"].eq(ok[p+"_max"]) for p in ("QB","RB","WR","TE")],axis=1).all(axis=1).sum()))


if __name__ == "__main__":
    run()
