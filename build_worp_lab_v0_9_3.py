from pathlib import Path

SRC = Path("app_v0_9_2.py")
DST = Path("app_v0_9_3.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_9_2.py not found. Run build_worp_lab_v0_9_2.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.9.2', 'UI V0.9.3')
s = s.replace('WoRP-Lab/0.9.2', 'WoRP-Lab/0.9.3')
s = s.replace('WoRP Lab UI V0.9.2', 'WoRP Lab UI V0.9.3')

# -----------------------------------------------------------------------------
# V0.9.3 — LINEUP ECONOMICS
# Descriptive bridge: exact league slots + historical league-scored positional
# ranks -> observed positional occupation of each successive flexible slot.
# No fixed groups of 12: team count determines the rank block for each layer.
# This does not alter Engine V0.2.1 or Roster Construction V0.32.
# -----------------------------------------------------------------------------
fn_marker = '''def calculate_league_intelligence_cached(
'''
helper = r'''def build_lineup_economics(curve, teams, qb, rb, wr, te, flex, superflex):
    """Return slot-level historical lineup economics from the league-native curve.

    Fixed slots consume their own positional rank layers first. Each successive
    FLEX/SUPER_FLEX layer then compares the next team-sized rank block among
    eligible positions. Shares are based on positive marginal WoRP within that
    layer; if all eligible marginal WoRP is non-positive, the layer abstains.
    This is descriptive demand, not a player projection or roster prescription.
    """
    import numpy as np

    teams = int(teams)
    fixed = {"QB": int(qb), "RB": int(rb), "WR": int(wr), "TE": int(te)}
    used_layers = fixed.copy()
    rows = []

    def block(pos, layer):
        lo = layer * teams + 1
        hi = (layer + 1) * teams
        x = curve[(curve["position"] == pos) & (curve["position_rank"].between(lo, hi))]
        vals = x["three_year_worp_avg"].dropna().astype(float)
        return vals, lo, hi

    # Fixed slots: their league-wide rank layer is position-locked.
    for pos in ("QB", "RB", "WR", "TE"):
        for slot_i in range(fixed[pos]):
            vals, lo, hi = block(pos, slot_i)
            rows.append({
                "slot": pos if fixed[pos] == 1 else f"{pos}{slot_i + 1}",
                "slot_type": pos,
                "layer": slot_i + 1,
                "eligible": pos,
                "rank_range": f"{pos}{lo}–{pos}{hi}",
                "avg_worp": float(vals.mean()) if len(vals) else float("nan"),
                "shares": {pos: 1.0},
            })

    def flexible_slot(label, eligible):
        scores = {}
        ranges = {}
        for pos in eligible:
            vals, lo, hi = block(pos, used_layers[pos])
            ranges[pos] = f"{pos}{lo}–{pos}{hi}"
            # Positive marginal WoRP only: tiny/negative tails do not manufacture
            # lineup demand. Mean is used to keep this rank-level and player-free.
            scores[pos] = max(float(vals.mean()), 0.0) if len(vals) else 0.0
        total = sum(scores.values())
        shares = {p: (scores[p] / total if total > 0 else 0.0) for p in eligible}
        # Expected slot WoRP is a descriptive mixture of eligible rank blocks.
        avg_worp = sum(shares[p] * scores[p] for p in eligible) if total > 0 else float("nan")
        rows.append({
            "slot": label,
            "slot_type": label.split(" ")[0],
            "layer": len([r for r in rows if r["slot_type"] == label.split(" ")[0]]) + 1,
            "eligible": "/".join(eligible),
            "rank_range": " · ".join(ranges[p] for p in eligible),
            "avg_worp": avg_worp,
            "shares": shares,
        })
        # Advance the layer only for the position(s) economically occupying the
        # slot. Fractional shares are descriptive; a meaningful share advances
        # that position's next candidate block for the following flex layer.
        for pos, share in shares.items():
            if share >= 0.10:
                used_layers[pos] += 1

    for i in range(int(flex)):
        flexible_slot(f"FLEX {i + 1}", ["RB", "WR", "TE"])
    for i in range(int(superflex)):
        flexible_slot(f"SUPER_FLEX {i + 1}", ["QB", "RB", "WR", "TE"])

    return rows


'''
if fn_marker not in s:
    raise SystemExit("STOP: calculate function marker not found")
s = s.replace(fn_marker, helper + fn_marker, 1)

# Insert immediately before Roster Construction so the product reads:
# league economics -> lineup economics -> roster construction.
ui_marker = '''        # V0.9.2 — league-native Roster Construction product layer.
'''
lineup_ui = r'''        st.markdown("##### Lineup Economics")
        st.caption(
            "How this league's starting slots pull from each position historically. "
            "Fixed slots are position-locked; flexible slots follow league-native WoRP rank layers."
        )
        try:
            lineup_rows = build_lineup_economics(
                curve, teams, qb, rb, wr, te, flex, superflex
            )
            if lineup_rows:
                # Compact table: readable first, no wall of research diagnostics.
                display_rows = []
                for lr in lineup_rows:
                    shares = lr.get("shares", {})
                    mix = " · ".join(
                        f"{p} {100*v:.0f}%" for p, v in sorted(
                            shares.items(), key=lambda kv: kv[1], reverse=True
                        ) if v >= 0.01
                    ) or "No material edge"
                    display_rows.append({
                        "Slot": lr["slot"],
                        "Historical mix": mix,
                        "WoRP layer": (round(lr["avg_worp"], 2) if pd.notna(lr["avg_worp"]) else "—"),
                        "Rank evidence": lr["rank_range"],
                    })
                st.dataframe(pd.DataFrame(display_rows), hide_index=True, use_container_width=True)
                st.caption(
                    "Shares describe positional pressure inside eligible slots; they are not lineup recommendations. "
                    "Rank blocks scale with league team count — no fixed 12-player bucket assumption."
                )
        except Exception as exc:
            st.caption(f"Lineup Economics unavailable: {exc}")

'''
if ui_marker not in s:
    raise SystemExit("STOP: V0.9.2 Roster Construction marker not found")
s = s.replace(ui_marker, lineup_ui + ui_marker, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_9_3.py created")
print("Engine V0.2.1 math unchanged")
print("Lineup Economics inserted before Roster Construction")
print("Team-count-scaled rank layers; no fixed groups-of-12 assumption")
print("Slot eligibility preserved: FLEX=RB/WR/TE; SUPER_FLEX=QB/RB/WR/TE")
print("No player names, projections, asset value, or new Roster Construction threshold")
