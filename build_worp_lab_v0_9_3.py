from pathlib import Path

SRC = Path("app_v0_9_2.py")
DST = Path("app_v0_9_3.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_9_2.py not found. Run build_worp_lab_v0_9_2.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.9.2', 'UI V0.9.3')
s = s.replace('WoRP-Lab/0.9.2', 'WoRP-Lab/0.9.3')
s = s.replace('WoRP Lab UI V0.9.2', 'WoRP Lab UI V0.9.3')

fn_marker = '''def calculate_league_intelligence_cached(\n'''
helper = r'''def build_lineup_economics(curve, teams, qb, rb, wr, te, flex, superflex):
    """League-native, player-free slot economics from historical WoRP ranks."""
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

    for pos in ("QB", "RB", "WR", "TE"):
        for slot_i in range(fixed[pos]):
            vals, lo, hi = block(pos, slot_i)
            rows.append({"slot": pos if fixed[pos] == 1 else f"{pos}{slot_i+1}", "slot_type": pos,
                         "rank_range": f"{pos}{lo}–{pos}{hi}",
                         "avg_worp": float(vals.mean()) if len(vals) else float("nan"), "shares": {pos: 1.0}})

    def flexible_slot(label, eligible):
        scores, ranges = {}, {}
        for pos in eligible:
            vals, lo, hi = block(pos, used_layers[pos])
            ranges[pos] = f"{pos}{lo}–{pos}{hi}"
            scores[pos] = max(float(vals.mean()), 0.0) if len(vals) else 0.0
        total = sum(scores.values())
        shares = {p: (scores[p] / total if total > 0 else 0.0) for p in eligible}
        avg_worp = sum(shares[p] * scores[p] for p in eligible) if total > 0 else float("nan")
        rows.append({"slot": label, "slot_type": label.split(" ")[0],
                     "rank_range": " · ".join(ranges[p] for p in eligible),
                     "avg_worp": avg_worp, "shares": shares})
        for pos, share in shares.items():
            if share >= 0.10:
                used_layers[pos] += 1

    for i in range(int(flex)):
        flexible_slot(f"FLEX {i+1}", ["RB", "WR", "TE"])
    for i in range(int(superflex)):
        flexible_slot(f"SUPER_FLEX {i+1}", ["QB", "RB", "WR", "TE"])
    return rows


'''
if fn_marker not in s:
    raise SystemExit("STOP: calculate function marker not found")
s = s.replace(fn_marker, helper + fn_marker, 1)

ui_marker = '''        # V0.9.2 — league-native Roster Construction product layer.\n'''
lineup_ui = r'''        # Derive product inputs from the selected Sleeper league here, where
        # league/counts/sc are actually in scope. Do not depend on local names
        # from the calculation function.
        _teams = int(league.get("total_rosters", 0) or 0)
        _qb = int(counts.get("QB", 0)); _rb = int(counts.get("RB", 0))
        _wr = int(counts.get("WR", 0)); _te = int(counts.get("TE", 0))
        _flex = int(counts.get("FLEX", 0)); _superflex = int(counts.get("SUPER_FLEX", 0))
        _sc = league.get("scoring_settings", {}) or {}

        st.markdown("##### Lineup Economics")
        st.caption("How this league's starting slots pull from each position historically. Fixed slots are position-locked; flexible slots follow league-native WoRP rank layers.")
        try:
            lineup_rows = build_lineup_economics(curve, _teams, _qb, _rb, _wr, _te, _flex, _superflex)
            if lineup_rows:
                display_rows = []
                for lr in lineup_rows:
                    shares = lr.get("shares", {})
                    mix = " · ".join(f"{p} {100*v:.0f}%" for p, v in sorted(shares.items(), key=lambda kv: kv[1], reverse=True) if v >= 0.01) or "No material edge"
                    display_rows.append({"Slot": lr["slot"], "Historical mix": mix,
                                         "WoRP layer": round(lr["avg_worp"], 2) if pd.notna(lr["avg_worp"]) else "—",
                                         "Rank evidence": lr["rank_range"]})
                st.dataframe(pd.DataFrame(display_rows), hide_index=True, use_container_width=True)
                st.caption("Shares describe positional pressure inside eligible slots; they are not lineup recommendations. Rank blocks scale with league team count — no fixed 12-player bucket assumption.")
        except Exception as exc:
            st.caption(f"Lineup Economics unavailable: {exc}")

'''
if ui_marker not in s:
    raise SystemExit("STOP: V0.9.2 Roster Construction marker not found")
s = s.replace(ui_marker, lineup_ui + ui_marker, 1)

# V0.9.2's Roster Construction UI was also injected into a scope where the
# calculation locals teams/qb/.../sc do not exist. Rebind those references to
# the selected league inputs established above.
s = s.replace('start_n = int(qb) + int(rb) + int(wr) + int(te) + int(flex) + int(superflex)',
              'start_n = _qb + _rb + _wr + _te + _flex + _superflex')
s = s.replace('tep = float(sc.get("bonus_rec_te", 0.0)) > 0', 'tep = float(_sc.get("bonus_rec_te", 0.0)) > 0')
s = s.replace('f"{int(teams)}T "', 'f"{_teams}T "')
s = s.replace('(\"SF \" if int(superflex) > 0 else \"1QB \")', '("SF " if _superflex > 0 else "1QB ")')
s = s.replace('f"Start{start_n} QB{int(qb)} RB{int(rb)} WR{int(wr)} TE{int(te)} "',
              'f"Start{start_n} QB{_qb} RB{_rb} WR{_wr} TE{_te} "')
s = s.replace('f"FLEX{int(flex)} SFLEX{int(superflex)}"', 'f"FLEX{_flex} SFLEX{_superflex}"')

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_9_3.py created")
print("FIX: Lineup Economics uses selected league inputs in UI scope")
print("FIX: Roster Construction uses the same selected league inputs")
print("Engine V0.2.1 and V0.32 research outputs unchanged")
