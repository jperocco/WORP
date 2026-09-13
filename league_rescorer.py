import pandas as pd

CORE_DEFAULTS = {
    "pass_yd": 0.04,
    "pass_td": 4.0,
    "pass_int": -2.0,
    "rush_yd": 0.10,
    "rush_td": 6.0,
    "rec": 0.0,
    "rec_yd": 0.10,
    "rec_td": 6.0,
    "fum_lost": -2.0,
    "pass_2pt": 2.0,
    "rush_2pt": 2.0,
    "rec_2pt": 2.0,
    "bonus_rec_te": 0.0,
}

COLUMN_MAP = {
    "pass_yd": ["passing_yards"],
    "pass_td": ["passing_tds"],
    "pass_int": ["interceptions"],
    "rush_yd": ["rushing_yards"],
    "rush_td": ["rushing_tds"],
    "rec": ["receptions"],
    "rec_yd": ["receiving_yards"],
    "rec_td": ["receiving_tds"],
    "fum_lost": ["fumbles_lost"],
    "pass_2pt": ["passing_2pt_conversions", "passing_2pt_conversion"],
    "rush_2pt": ["rushing_2pt_conversions", "rushing_2pt_conversion"],
    "rec_2pt": ["receiving_2pt_conversions", "receiving_2pt_conversion"],
}

UNSUPPORTED_PREFIXES = ("bonus_", "pass_fd", "rush_fd", "rec_fd")
SUPPORTED_BONUS_KEYS = {"bonus_rec_te"}

def _first_existing(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def detect_unsupported_offensive_scoring(scoring):
    unsupported = []
    for key, raw in (scoring or {}).items():
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value == 0:
            continue
        if key in CORE_DEFAULTS or key in SUPPORTED_BONUS_KEYS:
            continue

        defensive_or_kicking = (
            key.startswith(("pts_allow_", "yds_allow_", "def_", "st_", "fg", "xp",
                            "sack", "safe", "blk_kick"))
            or key in {"int", "ff", "fum_rec", "def_td"}
        )
        if defensive_or_kicking:
            continue

        if key.startswith(UNSUPPORTED_PREFIXES):
            unsupported.append((key, value))
        elif any(token in key for token in ("pass", "rush", "rec", "fum")):
            unsupported.append((key, value))
    return unsupported

def rescore_weekly_dataframe(df, scoring):
    out = df.copy()
    sc = dict(CORE_DEFAULTS)
    sc.update({k: float(v) for k, v in (scoring or {}).items()
               if k in CORE_DEFAULTS and v is not None})

    missing = []
    total = pd.Series(0.0, index=out.index)

    for sleeper_key, candidates in COLUMN_MAP.items():
        col = _first_existing(out, candidates)
        coeff = float(sc.get(sleeper_key, 0.0))
        if col is None:
            if coeff != 0:
                missing.append((sleeper_key, candidates))
            continue
        total = total + pd.to_numeric(out[col], errors="coerce").fillna(0.0) * coeff

    te_bonus = float(sc.get("bonus_rec_te", 0.0))
    if te_bonus:
        rec_col = _first_existing(out, COLUMN_MAP["rec"])
        if rec_col is None:
            missing.append(("bonus_rec_te", COLUMN_MAP["rec"]))
        else:
            is_te = out["position"].astype(str).eq("TE")
            total = total + (
                pd.to_numeric(out[rec_col], errors="coerce").fillna(0.0)
                * te_bonus
                * is_te.astype(float)
            )

    if missing:
        detail = ", ".join(f"{k}→{cands}" for k, cands in missing)
        raise ValueError(
            "Cannot rescore this league from the current weekly dataset; "
            f"missing required stat columns: {detail}"
        )

    out["fantasy_points"] = total.round(6)

    audit = {
        "ppr": float(sc.get("rec", 0.0)),
        "te_premium": te_bonus,
        "pass_td": float(sc.get("pass_td", 0.0)),
        "pass_int": float(sc.get("pass_int", 0.0)),
        "unsupported": detect_unsupported_offensive_scoring(scoring),
    }
    return out, audit

def build_rank_average(rankings, seasons=(2023, 2024, 2025), top_n=50):
    frames = []
    for season, ranking in rankings.items():
        x = ranking.copy()
        x = x[x["position"].isin(["QB", "RB", "WR", "TE"])].copy()
        x["position_rank_curve"] = (
            x.groupby("position")["worp"]
             .rank(method="first", ascending=False)
             .astype(int)
        )
        x = x[x["position_rank_curve"] <= top_n]
        x["season"] = season
        frames.append(x[["season", "position", "position_rank_curve", "worp"]])

    all_rows = pd.concat(frames, ignore_index=True)
    curve = (
        all_rows.groupby(["position", "position_rank_curve"], as_index=False)
        .agg(three_year_worp_avg=("worp", "mean"),
             seasons_present=("season", "nunique"))
    )
    curve = curve[curve["seasons_present"] == len(seasons)].copy()
    return curve.sort_values(["position", "position_rank_curve"])
