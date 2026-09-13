#!/usr/bin/env python3
"""
WOOKIEE CONTINUOUS EX-ANTE SIGNAL CURVE V0.1

Goal:
Do NOT impose MID/HIGH as the answer.
Measure how next-week positive-WoRP probability and expected WoRP change
continuously with PRIOR usage among players observed FREE.

Input:
  wookiee_ex_ante_signal_denominator_detail_v0_1.csv

Outputs:
  wookiee_ex_ante_signal_curve_overall_v0_1.csv
  wookiee_ex_ante_signal_curve_position_v0_1.csv
  wookiee_ex_ante_signal_curve_wr_v0_1.csv

Guardrail:
This searches for empirical shape / candidate break regions.
It does NOT define "waiver", roster strategy, or prove
WR1* + WR1* + waiver > WR3* depth.
"""

from pathlib import Path
import numpy as np
import pandas as pd

SRC = Path("wookiee_ex_ante_signal_denominator_detail_v0_1.csv")

def make_curve(df, label):
    # max(prev week, prior-3 mean), exactly as denominator audit
    x = df[df["has_prior_sample"].astype(str).str.lower().isin(["true","1"])].copy()
    x["prior_signal"] = x[["prev1_opportunity","prev3_opportunity_mean"]].max(axis=1).fillna(0)

    # Integer-ish opportunity grid. For rolling estimates we use local windows
    # rather than declaring thresholds.
    max_sig = int(np.ceil(x["prior_signal"].quantile(.995)))
    rows = []
    for s in range(0, max_sig + 1):
        # local window +/-1 opportunity; expand to +/-2 if sparse
        z = x[(x.prior_signal >= s-1) & (x.prior_signal <= s+1)]
        if len(z) < 30:
            z = x[(x.prior_signal >= s-2) & (x.prior_signal <= s+2)]
        if len(z) == 0:
            continue
        hits = z["positive_worp"].astype(str).str.lower().isin(["true","1"]).sum()
        worp = pd.to_numeric(z["weekly_worp"], errors="coerce").fillna(0).clip(lower=0).sum()
        rows.append({
            "group": label,
            "prior_signal_center": s,
            "window_n": len(z),
            "positive_worp_cases": int(hits),
            "hit_rate": hits / len(z),
            "positive_worp_sum": worp,
            "worp_per_free_player_week": worp / len(z),
        })
    return pd.DataFrame(rows)

def exact_curve(df, label):
    x = df[df["has_prior_sample"].astype(str).str.lower().isin(["true","1"])].copy()
    x["prior_signal"] = x[["prev1_opportunity","prev3_opportunity_mean"]].max(axis=1).fillna(0)
    # half-opportunity bins preserve more shape while retaining sample sizes
    x["signal_bin"] = np.floor(x["prior_signal"] * 2) / 2
    rows = []
    for s, z in x.groupby("signal_bin"):
        hits = z["positive_worp"].astype(str).str.lower().isin(["true","1"]).sum()
        worp = pd.to_numeric(z["weekly_worp"], errors="coerce").fillna(0).clip(lower=0).sum()
        rows.append({
            "group": label,
            "prior_signal": s,
            "n": len(z),
            "hits": int(hits),
            "hit_rate": hits/len(z),
            "worp_per_free_player_week": worp/len(z),
        })
    return pd.DataFrame(rows).sort_values("prior_signal")

def main():
    print("="*108)
    print("WOOKIEE CONTINUOUS EX-ANTE SIGNAL CURVE V0.1")
    print("="*108)

    if not SRC.exists():
        raise FileNotFoundError(
            f"{SRC} not found. Run denominator audit V0.1 first."
        )

    d = pd.read_csv(SRC)
    d["weekly_worp"] = pd.to_numeric(d["weekly_worp"], errors="coerce").fillna(0)

    overall = make_curve(d, "ALL")
    pos_parts = []
    for p in ["QB","RB","WR","TE"]:
        pos_parts.append(make_curve(d[d.position == p], p))
    position = pd.concat(pos_parts, ignore_index=True)

    wr = exact_curve(d[d.position == "WR"], "WR")

    overall.to_csv("wookiee_ex_ante_signal_curve_overall_v0_1.csv", index=False)
    position.to_csv("wookiee_ex_ante_signal_curve_position_v0_1.csv", index=False)
    wr.to_csv("wookiee_ex_ante_signal_curve_wr_v0_1.csv", index=False)

    print("\nWR — EXACT PRIOR-SIGNAL CURVE")
    print("-"*108)
    # Human-readable: avoid pretending tiny bins are stable.
    wr_show = wr[wr.n >= 20].copy()
    print(wr_show.to_string(
        index=False,
        formatters={
            "prior_signal": "{:.1f}".format,
            "hit_rate": "{:.2%}".format,
            "worp_per_free_player_week": "{:.5f}".format,
        }
    ))

    print("\nWR — ROLLING LOCAL CURVE")
    print("-"*108)
    wrr = position[position.group == "WR"].copy()
    print(wrr.to_string(
        index=False,
        formatters={
            "hit_rate": "{:.2%}".format,
            "worp_per_free_player_week": "{:.5f}".format,
        }
    ))

    # Candidate inflection diagnostics only. No threshold declaration.
    stable = wrr[wrr.window_n >= 50].copy()
    if len(stable) >= 3:
        stable["hit_rate_delta"] = stable.hit_rate.diff()
        stable["worp_rate_delta"] = stable.worp_per_free_player_week.diff()
        top_hit = stable.nlargest(3, "hit_rate_delta")[
            ["prior_signal_center","window_n","hit_rate","hit_rate_delta"]
        ]
        top_worp = stable.nlargest(3, "worp_rate_delta")[
            ["prior_signal_center","window_n","worp_per_free_player_week","worp_rate_delta"]
        ]
        print("\nWR — CANDIDATE INFLECTION REGIONS (descriptive only; n>=50)")
        print("-"*108)
        print("Largest local hit-rate increases:")
        print(top_hit.to_string(index=False, formatters={
            "hit_rate":"{:.2%}".format,
            "hit_rate_delta":"{:+.2%}".format,
        }))
        print("\nLargest local expected-WoRP increases:")
        print(top_worp.to_string(index=False, formatters={
            "worp_per_free_player_week":"{:.5f}".format,
            "worp_rate_delta":"{:+.5f}".format,
        }))

    print("\nPASS: continuous prior-signal curve generated.")
    print("INTERPRETATION STOP:")
    print("A bend in this curve is only a candidate signal region.")
    print("It is NOT yet a waiver threshold and NOT yet a roster-construction result.")
    print("Next, any candidate region must be converted into an executable acquisition/start policy.")


if __name__ == "__main__":
    main()
