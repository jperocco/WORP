"""Describe reference support, without interpreting pool sizes as quotas."""
from pathlib import Path
import argparse
import pandas as pd


def summarize(folder):
    pool = pd.read_csv(folder / "pool_reference_support.csv")
    detail = pd.read_csv(folder / "marginal_reference_detail.csv")
    counts = pool.pivot(index=["season", "week", "roster_id"],
                        columns="position", values="eligible_owned")
    records = []
    # The eight/nine capacity is the user's current case, not a model cutoff.
    for budget in (8, 9):
        for qb in range(budget + 1):
            rb = budget - qb
            eligible = counts.QB.ge(qb) & counts.RB.ge(rb)
            adjacent = counts.QB.ge(qb + 1) & counts.RB.ge(rb) if rb else eligible & False
            for season in (2023, 2024, 2025, "ALL"):
                select = counts.index.get_level_values("season") == season if season != "ALL" else [True] * len(counts)
                n = int(sum(select))
                records.append({"season": season, "budget": budget, "qb_options": qb,
                                "rb_options": rb, "total_roster_weeks": n,
                                "feasible_owned_pool_weeks": int(eligible[select].sum()),
                                "adjacent_split_common_weeks": int(adjacent[select].sum())})
    splits = pd.DataFrame(records)
    splits.to_csv(folder / "allocation_support.csv", index=False)
    # First-slot QB/RB comparisons use identical cohort keys, never different
    # denominators. Overlapping observations remain descriptive, not IID tests.
    first = detail[detail.slot.eq(1)].pivot(
        index=["season", "week", "roster_id"], columns="position",
        values="mean_four_week_increment").dropna(subset=["QB", "RB"])
    paired = first.groupby("season")[["QB", "RB"]].mean()
    paired["paired_roster_weeks"] = first.groupby("season").size()
    paired.to_csv(folder / "first_slot_paired_summary.csv")
    print("POOL SIZE (MEDIAN / MAX), NOT RECOMMENDED COUNTS")
    print(pool.groupby("position").eligible_owned.agg(["median", "max"]).to_string())
    print("PAIRED FIRST-SLOT HINDSIGHT CEILING")
    print(paired.to_string())
    print("EIGHT/NINE-SLOT ALLOCATION SUPPORT")
    print(splits[splits.season.eq("ALL")].to_string(index=False))
    print(f"Total cohorts: {len(counts)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    summarize(args.folder)
