from pathlib import Path

SRC = Path("app_v0_9_4.py")
DST = Path("app_v0_9_5.py")
if not SRC.exists():
    raise SystemExit("STOP: app_v0_9_4.py not found")

s = SRC.read_text(encoding="utf-8")
s = (s.replace("UI V0.9.4", "UI V0.9.5")
       .replace("WoRP-Lab/0.9.4", "WoRP-Lab/0.9.5"))

anchor = "\ndef build_lineup_scoring_share(player_weeks, teams, qb, rb, wr, te, flex, superflex):\n"
if anchor not in s:
    raise SystemExit("STOP: Lineup Share helper not found")

helper = r'''
def _dna_bucket(setting):
    """Map Sleeper scoring settings to readable QB scoring sources."""
    key = str(setting).lower()
    if key in {"pass_td", "pass_2pt"}:
        return "Passing TDs"
    if key in {"pass_yd", "pass_cmp", "pass_att", "pass_fd"}:
        return "Passing volume"
    if key.startswith("rush_"):
        return "Rushing"
    if key in {"pass_int", "sack", "fum_lost", "fumbles_lost"} or key.startswith("fum"):
        return "Turnovers & sacks"
    if key.startswith("bonus_"):
        return "Bonuses"
    return "Other scoring"


def build_qb_scoring_dna(player_weeks, teams):
    """Describe the historical sources that separate elite QB seasons.

    This is a deterministic descriptive layer over exact league-scored points.
    It does not use WoRP, player names, projections, or Monte Carlo.
    """
    component_cols = [c for c in player_weeks.columns if c.startswith("component__")]
    qbs = player_weeks[player_weeks["position"].eq("QB")].copy()
    if qbs.empty or not component_cols:
        return None
    for col in component_cols:
        qbs[col] = pd.to_numeric(qbs[col], errors="coerce").fillna(0.0)
    season = (qbs.groupby(["season", "player_id"], as_index=False)
              .agg(fantasy_points=("fantasy_points", "sum"),
                   games=("week", "nunique"),
                   **{c: (c, "sum") for c in component_cols}))
    season = season[season["games"] >= 8].copy()
    if len(season) < 8:
        return None
    season["ppg"] = season["fantasy_points"] / season["games"]
    for col in component_cols:
        season[col] = season[col] / season["games"]
    # Twelve is a transparent descriptive tier, kept constant across seasons;
    # the comparison tier scales only when a season lacks enough qualifiers.
    elite_n = min(12, max(4, int(teams)))
    parts = []
    for _, year in season.groupby("season"):
        year = year.sort_values("ppg", ascending=False).reset_index(drop=True)
        if len(year) < elite_n + 4:
            continue
        elite = year.iloc[:elite_n]
        next_end = min(len(year), elite_n * 2 + 4)
        next_tier = year.iloc[elite_n:next_end]
        if next_tier.empty:
            continue
        rows = []
        for col in component_cols:
            bucket = _dna_bucket(col.replace("component__", ""))
            rows.append((bucket, float(elite[col].mean() - next_tier[col].mean())))
        part = pd.DataFrame(rows, columns=["source", "gap_ppg"]).groupby("source", as_index=False)["gap_ppg"].sum()
        part["season"] = int(year["season"].iloc[0])
        part["elite_ppg"] = float(elite["ppg"].mean())
        part["next_ppg"] = float(next_tier["ppg"].mean())
        parts.append(part)
    if not parts:
        return None
    by_season = pd.concat(parts, ignore_index=True)
    summary = (by_season.groupby("source", as_index=False)
               .agg(gap_ppg=("gap_ppg", "mean"))
               .sort_values("gap_ppg", ascending=False))
    total_gap = float((by_season.groupby("season")["elite_ppg"].first() - by_season.groupby("season")["next_ppg"].first()).mean())
    return {
        "summary": summary,
        "total_gap": total_gap,
        "elite_n": elite_n,
        "next_label": f"QB{elite_n + 1}–QB{elite_n * 2 + 4}",
        "seasons": int(by_season["season"].nunique()),
    }

'''
s = s.replace(anchor, "\n" + helper + anchor, 1)

marker = "        # V0.9.2 — league-native Roster Construction product layer."
if marker not in s:
    raise SystemExit("STOP: Roster Construction marker not found")

ui = r'''        st.markdown("##### QB Scoring DNA")
        st.caption("What historically separates the best qualifying QB seasons from the next tier under this league's exact scoring. This explains scoring, not player evaluation or projection.")
        try:
            dna = build_qb_scoring_dna(_pw, _teams)
            if dna is None:
                st.caption("QB Scoring DNA needs at least eight qualifying QB seasons in each historical year.")
            else:
                sources = dna["summary"].copy()
                sources = sources[sources["gap_ppg"].abs() >= 0.05]
                positive = sources[sources["gap_ppg"] > 0]
                top = positive.iloc[0] if not positive.empty else None
                if top is not None:
                    st.markdown(
                        f"**Historical QB edge:** {top['source']} is the largest measured source of separation "
                        f"between the top {dna['elite_n']} qualifying QB seasons and {dna['next_label']}."
                    )
                dna_cards=[]
                for _, row in sources.iterrows():
                    sign="+" if row["gap_ppg"] >= 0 else ""
                    dna_cards.append(
                        f'<div class="dna-card"><div class="dna-source">{row["source"]}</div>'
                        f'<div class="dna-gap">{sign}{row["gap_ppg"]:.1f}</div><div class="dna-unit">PPG vs next tier</div></div>'
                    )
                st.markdown("""<style>
                .dna-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:8px 0 8px 0}
                .dna-card{border-left:4px solid #ff4b4b;border-radius:10px;padding:13px 14px;background:rgba(255,75,75,.06);min-height:94px}
                .dna-source{font-size:14px;font-weight:650;opacity:.85}.dna-gap{font-size:29px;font-weight:800;line-height:1.2;margin-top:6px}.dna-unit{font-size:12px;opacity:.68}
                </style>""", unsafe_allow_html=True)
                st.markdown('<div class="dna-grid">'+''.join(dna_cards)+'</div>', unsafe_allow_html=True)
                st.caption(
                    f"{window_label} · {dna['seasons']} seasons · qualifying QB seasons require 8+ games. "
                    f"Total elite-to-next-tier gap: {dna['total_gap']:+.1f} PPG. Components use Sleeper stat × scoring-setting contributions; they may not sum exactly because the comparison is averaged by season."
                )
        except Exception as exc:
            st.caption(f"QB Scoring DNA unavailable: {exc}")

'''
s = s.replace(marker, ui + marker, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_9_5.py created")
print("Scoring DNA added as a deterministic QB scoring explainer; WoRP engine untouched")
