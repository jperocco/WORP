from pathlib import Path

SRC = Path("app_v0_9_2.py")
DST = Path("app_v0_9_3.py")
if not SRC.exists():
    raise SystemExit("STOP: app_v0_9_2.py not found")

s = SRC.read_text(encoding="utf-8")
s = (
    s.replace("UI V0.9.2", "UI V0.9.3")
     .replace("WoRP-Lab/0.9.2", "WoRP-Lab/0.9.3")
     .replace("WoRP Lab UI V0.9.2", "WoRP Lab UI V0.9.3")
)

fn_marker = "def calculate_league_intelligence_cached(\n"
helper = r'''@st.cache_data(ttl=300)
def load_observed_lineup_economics(league_id, roster_positions):
    """Reconstruct actual Sleeper starter-slot occupancy.

    Sleeper returns `starters` in the same order as the league's non-bench
    `roster_positions`. No positional rank, WoRP average, or aggregate optimal
    lineup is inferred. Empty starter IDs remain vacancies.
    """
    from collections import Counter

    bench_slots = {"BN", "IR", "TAXI", "RESERVE"}
    supported_slots = {"QB", "RB", "WR", "TE", "FLEX", "SUPER_FLEX"}
    active_slots = [slot for slot in roster_positions if slot not in bench_slots]

    totals = Counter(active_slots)
    seen = Counter()
    labelled_slots = []
    for slot in active_slots:
        seen[slot] += 1
        label = slot if totals[slot] == 1 else f"{slot}{seen[slot]}"
        labelled_slots.append((slot, label))

    player_map = fetch_player_map()
    accum = {
        label: {"slot_type": slot, "opportunities": 0, "filled": 0, "positions": Counter()}
        for slot, label in labelled_slots
        if slot in supported_slots
    }
    observed_weeks = set()
    roster_weeks = 0

    for week in range(1, 19):
        matchups = sleeper_get(f"/league/{league_id}/matchups/{week}") or []
        if not matchups:
            continue
        observed_weeks.add(int(week))
        for matchup in matchups:
            starters = list(matchup.get("starters") or [])
            roster_weeks += 1
            for idx, (slot, label) in enumerate(labelled_slots):
                if slot not in supported_slots:
                    continue
                rec = accum[label]
                rec["opportunities"] += 1
                player_id = starters[idx] if idx < len(starters) else None
                if player_id in (None, 0, "0", ""):
                    continue
                player = player_map.get(str(player_id), {}) if isinstance(player_map, dict) else {}
                position = player.get("position")
                rec["filled"] += 1
                rec["positions"][position or "UNKNOWN"] += 1

    rows = []
    for slot, label in labelled_slots:
        if slot not in supported_slots:
            continue
        rec = accum[label]
        filled = int(rec["filled"])
        opportunities = int(rec["opportunities"])
        shares = {
            pos: count / filled
            for pos, count in rec["positions"].items()
        } if filled else {}
        rows.append({
            "slot": label.replace("SUPER_FLEX", "SUPERFLEX"),
            "shares": shares,
            "filled": filled,
            "vacant": opportunities - filled,
            "opportunities": opportunities,
        })

    return rows, {
        "weeks": sorted(observed_weeks),
        "roster_weeks": int(roster_weeks),
    }


'''
if fn_marker not in s:
    raise SystemExit("STOP: calculate marker not found")
s = s.replace(fn_marker, helper + fn_marker, 1)

ui_marker = "        # V0.9.2 — league-native Roster Construction product layer.\n"
ui = r'''        _teams=int(league.get("total_rosters",0) or 0)
        _qb=int(counts.get("QB",0)); _rb=int(counts.get("RB",0)); _wr=int(counts.get("WR",0)); _te=int(counts.get("TE",0))
        _flex=int(counts.get("FLEX",0)); _superflex=int(counts.get("SUPER_FLEX",0)); _sc=league.get("scoring_settings",{}) or {}
        st.markdown("##### Lineup Economics")
        st.caption("Observed starter-slot occupancy from this league's real Sleeper lineups — reconstructed by roster and week.")
        try:
            lineup_rows, lineup_audit = load_observed_lineup_economics(
                str(league.get("league_id")),
                tuple(league.get("roster_positions",[]) or []),
            )
            display=[]
            for lr in lineup_rows:
                mix=" · ".join(
                    f"{p} {100*v:.0f}%"
                    for p,v in sorted(lr["shares"].items(),key=lambda kv:kv[1],reverse=True)
                ) or "No filled observations"
                vacancy_rate=(lr["vacant"] / lr["opportunities"]) if lr["opportunities"] else 0.0
                display.append({
                    "Slot":lr["slot"],
                    "Observed occupancy":mix,
                    "Filled":lr["filled"],
                    "Vacant":lr["vacant"],
                    "Vacancy rate":f"{100*vacancy_rate:.1f}%",
                })
            if display and lineup_audit["roster_weeks"]:
                st.dataframe(pd.DataFrame(display),hide_index=True,use_container_width=True)
                weeks=lineup_audit["weeks"]
                week_label=(f"W{weeks[0]}–W{weeks[-1]}" if len(weeks)>1 else f"W{weeks[0]}") if weeks else "no weeks"
                st.caption(
                    f"Observed {lineup_audit['roster_weeks']} roster-weeks ({week_label}). "
                    "FLEX/SUPERFLEX shares use only players actually placed in those slots. "
                    "Empty slots remain vacancies; byes and manager lineup decisions are preserved."
                )
            else:
                st.caption("Lineup Economics: no observed Sleeper lineup weeks are available for this league yet. No synthetic substitute is shown.")
        except Exception as exc:
            st.caption(f"Lineup Economics unavailable: {exc}")

'''
if ui_marker not in s:
    raise SystemExit("STOP: RC marker not found")
s = s.replace(ui_marker, ui + ui_marker, 1)

# Keep Roster Construction tied to the selected league; its frozen empirical
# ranges and the V0.2.1 engine remain untouched.
s = s.replace(
    "start_n = int(qb) + int(rb) + int(wr) + int(te) + int(flex) + int(superflex)",
    "start_n = _qb + _rb + _wr + _te + _flex + _superflex",
)
s = s.replace('tep = float(sc.get("bonus_rec_te", 0.0)) > 0', 'tep = float(_sc.get("bonus_rec_te", 0.0)) > 0')
s = s.replace('f"{int(teams)}T "', 'f"{_teams}T "')
s = s.replace('("SF " if int(superflex) > 0 else "1QB ")', '("SF " if _superflex > 0 else "1QB ")')
s = s.replace(
    'f"Start{start_n} QB{int(qb)} RB{int(rb)} WR{int(wr)} TE{int(te)} "',
    'f"Start{start_n} QB{_qb} RB{_rb} WR{_wr} TE{_te} "',
)
s = s.replace('f"FLEX{int(flex)} SFLEX{int(superflex)}"', 'f"FLEX{_flex} SFLEX{_superflex}"')

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_9_3.py created")
print("Lineup Economics = observed Sleeper starters by league x roster x week")
print("FLEX/SUPERFLEX occupancy comes from actual slot placement")
print("Empty slots preserved as vacancies; no rank/WoRP synthetic substitute")
print("Engine V0.2.1 and frozen Roster Construction unchanged")
