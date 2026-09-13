#!/usr/bin/env python3
"""
WOOKIEE CAPTURE QUALITY AUDIT V0.1

Question
--------
Among positive-WoRP player-weeks that were FREE and temporally classified as
CAPTURABLE, how much of the captured WoRP came with meaningful underlying
opportunity/volume versus low-volume/spike production?

This is DESCRIPTIVE. It does not yet define "good waiver", "startable", FAAB
value, or manager decision quality.

Inputs
------
- wookiee_2023_2025_weekly_worp.csv
- wookiee_free_capturability_temporal_detail_v0_2.csv
- Sleeper weekly stats (same source used by prior audits)

Volume definitions
------------------
QB: pass attempts + carries
RB: carries + targets
WR/TE: targets

Absolute volume bands are position-specific and deliberately descriptive:
QB: LOW <25, MID 25-34, HIGH 35+
RB: LOW <8, MID 8-14, HIGH 15+
WR/TE: LOW <4, MID 4-6, HIGH 7+

For WR/TE, an additional target-volume view is reported because target
opportunity is more directly interpretable for pass-catchers.

TD/spike decomposition
----------------------
We do NOT call a TD a "bad" outcome. We simply report:
- WoRP share from weeks with >=1 TD
- WoRP share from weeks with 0 TD
- median volume within each group

This lets us see whether FREE capture value is concentrated in:
1) high-volume opportunity,
2) low-volume production,
3) TD/spike weeks.

No universal threshold for "quality" is imposed in V0.1.
"""

import json
import urllib.request
from pathlib import Path
import pandas as pd

WORP = Path("wookiee_2023_2025_weekly_worp.csv")
CAP = Path("wookiee_free_capturability_temporal_detail_v0_2.csv")

LEAGUES = {
    2023: "950220100039311360",
    2024: "1050961255520923648",
    2025: "1182581249532833792",
}

POS = {"QB", "RB", "WR", "TE"}


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "WoRPLab/0.2.6"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_stats(raw):
    if isinstance(raw, dict):
        return [(str(pid), st or {}) for pid, st in raw.items()]

    out = []
    for rec in raw or []:
        if not isinstance(rec, dict) or rec.get("player_id") is None:
            continue
        st = rec.get("stats")
        if st is None:
            st = {
                k: v
                for k, v in rec.items()
                if k not in {"player_id", "team", "opponent", "game_id"}
            }
        out.append((str(rec["player_id"]), st or {}))
    return out


def val(st, *keys):
    for key in keys:
        if key in st:
            try:
                return float(st.get(key) or 0)
            except Exception:
                return 0.0
    return 0.0


def volume_band(position, volume):
    if position == "QB":
        if volume < 25:
            return "LOW"
        if volume < 35:
            return "MID"
        return "HIGH"

    if position == "RB":
        if volume < 8:
            return "LOW"
        if volume < 15:
            return "MID"
        return "HIGH"

    if volume < 4:
        return "LOW"
    if volume < 7:
        return "MID"
    return "HIGH"


def main():
    print("=" * 110)
    print("WOOKIEE CAPTURE QUALITY AUDIT V0.1")
    print("=" * 110)

    if not WORP.exists():
        raise FileNotFoundError(WORP)
    if not CAP.exists():
        raise FileNotFoundError(CAP)

    w = pd.read_csv(WORP)
    w["player_id"] = w["player_id"].astype(str)

    cap = pd.read_csv(CAP)
    cap["player_id"] = cap["player_id"].astype(str)

    # Only temporally CAPTURABLE + positive WoRP.
    cap = cap[
        (cap.capturability == "CAPTURABLE")
        & (cap.weekly_worp > 0)
    ].copy()

    base_cols = [
        "season",
        "week",
        "player_id",
        "player_name",
        "position",
        "weekly_worp",
        "fantasy_points",
    ]

    # Prefer the authoritative WoRP source for names/position/production.
    m = cap.merge(
        w[base_cols].drop_duplicates(
            ["season", "week", "player_id"]
        ),
        on=["season", "week", "player_id"],
        how="left",
        suffixes=("", "_worp"),
    )

    # Fill authoritative fields where available.
    for c in ["player_name", "position", "weekly_worp", "fantasy_points"]:
        wc = f"{c}_worp"
        if wc in m.columns:
            m[c] = m[wc].where(m[wc].notna(), m[c])

    # Same Sleeper weekly stats source used by previous audit.
    stats = []
    for season in LEAGUES:
        for week in range(1, 19):
            raw = get_json(
                f"https://api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular"
            )
            for pid, st in parse_stats(raw):
                stats.append(
                    {
                        "season": season,
                        "week": week,
                        "player_id": pid,
                        "carries": val(
                            st, "rush_att", "rushing_attempts", "carries"
                        ),
                        "targets": val(st, "rec_tgt", "targets"),
                        "receptions": val(st, "rec", "receptions"),
                        "pass_attempts": val(
                            st,
                            "pass_att",
                            "passing_attempts",
                            "attempts",
                        ),
                        "rush_yards": val(
                            st, "rush_yd", "rushing_yards"
                        ),
                        "rec_yards": val(
                            st, "rec_yd", "receiving_yards"
                        ),
                        "pass_yards": val(
                            st, "pass_yd", "passing_yards"
                        ),
                        "rush_tds": val(
                            st, "rush_td", "rushing_tds"
                        ),
                        "rec_tds": val(
                            st, "rec_td", "receiving_tds"
                        ),
                        "pass_tds": val(
                            st, "pass_td", "passing_tds"
                        ),
                    }
                )

    v = pd.DataFrame(stats).drop_duplicates(
        ["season", "week", "player_id"]
    )

    m = m.merge(
        v,
        on=["season", "week", "player_id"],
        how="left",
    )

    stat_cols = [
        "carries",
        "targets",
        "receptions",
        "pass_attempts",
        "rush_yards",
        "rec_yards",
        "pass_yards",
        "rush_tds",
        "rec_tds",
        "pass_tds",
    ]

    for c in stat_cols:
        m[c] = pd.to_numeric(m[c], errors="coerce").fillna(0)

    m["total_tds"] = (
        m.rush_tds + m.rec_tds + m.pass_tds
    )
    m["scrimmage_yards"] = (
        m.rush_yards + m.rec_yards
    )

    m["volume"] = 0.0
    m.loc[m.position == "QB", "volume"] = (
        m.pass_attempts + m.carries
    )
    m.loc[m.position == "RB", "volume"] = (
        m.carries + m.targets
    )
    m.loc[m.position.isin(["WR", "TE"]), "volume"] = (
        m.targets
    )

    m["volume_band"] = [
        volume_band(p, v)
        for p, v in zip(m.position, m.volume)
    ]

    m["zero_td"] = m.total_tds == 0
    m["has_td"] = m.total_tds > 0
    m["low_volume"] = m.volume_band == "LOW"
    m["mid_volume"] = m.volume_band == "MID"
    m["high_volume"] = m.volume_band == "HIGH"

    # ------------------------------------------------------------
    # OVERALL CAPTURE QUALITY
    # ------------------------------------------------------------
    total_worp = m.weekly_worp.sum()

    print(f"Capturable positive player-weeks: {len(m)}")
    print(f"Capturable WoRP: {total_worp:.6f}")

    def share(mask):
        return (
            m.loc[mask, "weekly_worp"].sum() / total_worp
            if total_worp
            else 0
        )

    overall = pd.DataFrame(
        [
            {
                "capturable_player_weeks": len(m),
                "capturable_worp": total_worp,
                "low_volume_player_week_share": m.low_volume.mean(),
                "mid_volume_player_week_share": m.mid_volume.mean(),
                "high_volume_player_week_share": m.high_volume.mean(),
                "low_volume_worp_share": share(m.low_volume),
                "mid_volume_worp_share": share(m.mid_volume),
                "high_volume_worp_share": share(m.high_volume),
                "zero_td_player_week_share": m.zero_td.mean(),
                "has_td_player_week_share": m.has_td.mean(),
                "zero_td_worp_share": share(m.zero_td),
                "has_td_worp_share": share(m.has_td),
                "median_volume": m.volume.median(),
                "p75_volume": m.volume.quantile(.75),
                "median_worp": m.weekly_worp.median(),
                "p75_worp": m.weekly_worp.quantile(.75),
            }
        ]
    )

    print("\nOVERALL CAPTURE QUALITY")
    print("-" * 110)
    print(
        overall.to_string(
            index=False,
            formatters={
                "capturable_worp": "{:.4f}".format,
                "low_volume_player_week_share": "{:.1%}".format,
                "mid_volume_player_week_share": "{:.1%}".format,
                "high_volume_player_week_share": "{:.1%}".format,
                "low_volume_worp_share": "{:.1%}".format,
                "mid_volume_worp_share": "{:.1%}".format,
                "high_volume_worp_share": "{:.1%}".format,
                "zero_td_player_week_share": "{:.1%}".format,
                "has_td_player_week_share": "{:.1%}".format,
                "zero_td_worp_share": "{:.1%}".format,
                "has_td_worp_share": "{:.1%}".format,
                "median_volume": "{:.1f}".format,
                "p75_volume": "{:.1f}".format,
                "median_worp": "{:.4f}".format,
                "p75_worp": "{:.4f}".format,
            },
        )
    )

    # ------------------------------------------------------------
    # POSITION
    # ------------------------------------------------------------
    position_rows = []

    for position in sorted(POS):
        x = m[m.position == position].copy()
        if x.empty:
            continue

        tw = x.weekly_worp.sum()

        for band in ["LOW", "MID", "HIGH"]:
            z = x[x.volume_band == band]
            position_rows.append(
                {
                    "position": position,
                    "volume_band": band,
                    "player_weeks": len(z),
                    "player_week_share": (
                        len(z) / len(x) if len(x) else 0
                    ),
                    "worp": z.weekly_worp.sum(),
                    "worp_share": (
                        z.weekly_worp.sum() / tw if tw else 0
                    ),
                    "median_worp": (
                        z.weekly_worp.median()
                        if len(z)
                        else float("nan")
                    ),
                    "median_volume": (
                        z.volume.median()
                        if len(z)
                        else float("nan")
                    ),
                    "td_worp_share": (
                        z.loc[z.has_td, "weekly_worp"].sum()
                        / z.weekly_worp.sum()
                        if z.weekly_worp.sum()
                        else 0
                    ),
                }
            )

    position_summary = pd.DataFrame(position_rows)

    print("\nPOSITION × VOLUME BAND")
    print("-" * 110)
    print(
        position_summary.to_string(
            index=False,
            formatters={
                "player_week_share": "{:.1%}".format,
                "worp": "{:.4f}".format,
                "worp_share": "{:.1%}".format,
                "median_worp": "{:.4f}".format,
                "median_volume": "{:.1f}".format,
                "td_worp_share": "{:.1%}".format,
            },
        )
    )

    # ------------------------------------------------------------
    # TD / NO-TD DECOMPOSITION
    # ------------------------------------------------------------
    td_rows = []

    for position in sorted(POS):
        x = m[m.position == position]
        if x.empty:
            continue

        tw = x.weekly_worp.sum()

        for label, mask in [
            ("NO_TD", x.total_tds == 0),
            ("HAS_TD", x.total_tds > 0),
        ]:
            z = x[mask]
            td_rows.append(
                {
                    "position": position,
                    "td_group": label,
                    "player_weeks": len(z),
                    "player_week_share": len(z) / len(x),
                    "worp": z.weekly_worp.sum(),
                    "worp_share": (
                        z.weekly_worp.sum() / tw if tw else 0
                    ),
                    "median_volume": (
                        z.volume.median()
                        if len(z)
                        else float("nan")
                    ),
                    "median_worp": (
                        z.weekly_worp.median()
                        if len(z)
                        else float("nan")
                    ),
                }
            )

    td_summary = pd.DataFrame(td_rows)

    print("\nPOSITION × TD / NO-TD")
    print("-" * 110)
    print(
        td_summary.to_string(
            index=False,
            formatters={
                "player_week_share": "{:.1%}".format,
                "worp": "{:.4f}".format,
                "worp_share": "{:.1%}".format,
                "median_volume": "{:.1f}".format,
                "median_worp": "{:.4f}".format,
            },
        )
    )

    # ------------------------------------------------------------
    # WR / TE TARGET QUALITY — direct opportunity lens
    # ------------------------------------------------------------
    passcatcher = m[m.position.isin(["WR", "TE"])].copy()

    if not passcatcher.empty:
        target_rows = []

        for position in ["WR", "TE"]:
            x = passcatcher[passcatcher.position == position]
            if x.empty:
                continue

            tw = x.weekly_worp.sum()

            for group, mask in [
                ("0-2_TARGETS", x.targets <= 2),
                ("3-6_TARGETS", x.targets.between(3, 6)),
                ("7+_TARGETS", x.targets >= 7),
            ]:
                z = x[mask]
                target_rows.append(
                    {
                        "position": position,
                        "target_band": group,
                        "player_weeks": len(z),
                        "player_week_share": len(z) / len(x),
                        "worp": z.weekly_worp.sum(),
                        "worp_share": (
                            z.weekly_worp.sum() / tw if tw else 0
                        ),
                        "median_targets": (
                            z.targets.median()
                            if len(z)
                            else float("nan")
                        ),
                        "median_worp": (
                            z.weekly_worp.median()
                            if len(z)
                            else float("nan")
                        ),
                        "td_worp_share": (
                            z.loc[z.has_td, "weekly_worp"].sum()
                            / z.weekly_worp.sum()
                            if z.weekly_worp.sum()
                            else 0
                        ),
                    }
                )

        target_summary = pd.DataFrame(target_rows)

        print("\nWR / TE TARGET OPPORTUNITY")
        print("-" * 110)
        print(
            target_summary.to_string(
                index=False,
                formatters={
                    "player_week_share": "{:.1%}".format,
                    "worp": "{:.4f}".format,
                    "worp_share": "{:.1%}".format,
                    "median_targets": "{:.1f}".format,
                    "median_worp": "{:.4f}".format,
                    "td_worp_share": "{:.1%}".format,
                },
            )
        )
    else:
        target_summary = pd.DataFrame()

    # ------------------------------------------------------------
    # YEAR STABILITY
    # ------------------------------------------------------------
    yearly_rows = []

    for season in sorted(m.season.unique()):
        x = m[m.season == season]
        tw = x.weekly_worp.sum()

        yearly_rows.append(
            {
                "season": season,
                "capturable_player_weeks": len(x),
                "capturable_worp": tw,
                "low_volume_worp_share": (
                    x.loc[x.low_volume, "weekly_worp"].sum() / tw
                    if tw else 0
                ),
                "high_volume_worp_share": (
                    x.loc[x.high_volume, "weekly_worp"].sum() / tw
                    if tw else 0
                ),
                "zero_td_worp_share": (
                    x.loc[x.zero_td, "weekly_worp"].sum() / tw
                    if tw else 0
                ),
                "has_td_worp_share": (
                    x.loc[x.has_td, "weekly_worp"].sum() / tw
                    if tw else 0
                ),
                "median_volume": x.volume.median(),
                "median_worp": x.weekly_worp.median(),
            }
        )

    yearly = pd.DataFrame(yearly_rows)

    print("\nYEAR STABILITY")
    print("-" * 110)
    print(
        yearly.to_string(
            index=False,
            formatters={
                "capturable_worp": "{:.4f}".format,
                "low_volume_worp_share": "{:.1%}".format,
                "high_volume_worp_share": "{:.1%}".format,
                "zero_td_worp_share": "{:.1%}".format,
                "has_td_worp_share": "{:.1%}".format,
                "median_volume": "{:.1f}".format,
                "median_worp": "{:.4f}".format,
            },
        )
    )

    # ------------------------------------------------------------
    # HUMAN CASES: largest capturable FREE weeks
    # ------------------------------------------------------------
    cases = m.sort_values("weekly_worp", ascending=False).head(50).copy()

    case_cols = [
        "season",
        "week",
        "player_name",
        "position",
        "weekly_worp",
        "fantasy_points",
        "volume",
        "volume_band",
        "targets",
        "carries",
        "receptions",
        "scrimmage_yards",
        "pass_yards",
        "total_tds",
    ]

    cases[case_cols].to_csv(
        "wookiee_capture_quality_human_cases_v0_1.csv",
        index=False,
    )

    print("\nTOP 20 CAPTURABLE FREE WoRP CASES")
    print("-" * 110)
    print(
        cases[case_cols].head(20).to_string(
            index=False,
            formatters={
                "weekly_worp": "{:.4f}".format,
                "fantasy_points": "{:.2f}".format,
                "volume": "{:.1f}".format,
                "targets": "{:.1f}".format,
                "carries": "{:.1f}".format,
                "receptions": "{:.1f}".format,
                "scrimmage_yards": "{:.1f}".format,
                "pass_yards": "{:.1f}".format,
                "total_tds": "{:.1f}".format,
            },
        )
    )

    # Save full detail and summaries.
    m.to_csv(
        "wookiee_capture_quality_detail_v0_1.csv",
        index=False,
    )
    overall.to_csv(
        "wookiee_capture_quality_overall_v0_1.csv",
        index=False,
    )
    position_summary.to_csv(
        "wookiee_capture_quality_position_v0_1.csv",
        index=False,
    )
    td_summary.to_csv(
        "wookiee_capture_quality_td_v0_1.csv",
        index=False,
    )
    if not target_summary.empty:
        target_summary.to_csv(
            "wookiee_capture_quality_targets_v0_1.csv",
            index=False,
        )
    yearly.to_csv(
        "wookiee_capture_quality_yearly_v0_1.csv",
        index=False,
    )

    print("\nPASS: descriptive capture-quality decomposition complete.")
    print("INTERPRETATION STOP:")
    print("This does NOT define a waiver threshold or manager decision quality.")
    print("It only decomposes capturable FREE WoRP by underlying weekly volume and TD/spike context.")


if __name__ == "__main__":
    main()
