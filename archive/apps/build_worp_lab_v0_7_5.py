from pathlib import Path

SRC = Path("app_v0_7_4.py")
DST = Path("app_v0_7_5.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_7_4.py not found. Run build_worp_lab_v0_7_4.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.7.4', 'UI V0.7.5')
s = s.replace('WoRP-Lab/0.7.4', 'WoRP-Lab/0.7.5')
s = s.replace('WoRP Lab UI V0.7.4', 'WoRP Lab UI V0.7.5')

# -----------------------------------------------------------------------------
# V0.7.5 — FORMAT SEMANTICS ONLY
# Engine V0.2.1 math is untouched.
# Structural Insights must describe demand through SLOT ELIGIBILITY, not assume
# every league has traditional fixed positional starters.
# This matters for SFB/home/nonstandard formats with 0 fixed QB and multiple
# FLEX / SUPER_FLEX slots.
# -----------------------------------------------------------------------------

old_sf = '''    if int(superflex) > 0:
        f = _frontier_rank("QB")
        fixed_qb = int(teams) * int(qb)
        if f is not None and f > fixed_qb:
            candidates.append({
                "family": "format_superflex", "position": "QB",
                "score": 1.35 + min((f - fixed_qb) / max(int(teams), 1), 2.0) * 0.20,
                "title": "Superflex pushes QB demand beyond the nominal QB slots",
                "detail": (
                    f"This format has {fixed_qb} fixed QB starts league-wide, but the historical replacement frontier sits near QB{f}. "
                    "Treat QB depth as a structural requirement, not just bench insurance."
                ),
            })
'''
new_sf = '''    if int(superflex) > 0:
        f = _frontier_rank("QB")
        fixed_qb_per_team = int(qb)
        sf_per_team = int(superflex)
        qb_eligible_per_team = fixed_qb_per_team + sf_per_team
        qb_eligible_leaguewide = int(teams) * qb_eligible_per_team
        if f is not None:
            # Describe the actual choice architecture. A league may legitimately
            # have zero fixed QB slots (e.g. SFB/home formats) while still giving
            # each roster multiple QB-eligible starter slots.
            if fixed_qb_per_team == 0:
                title = "QB demand comes entirely from flexible eligibility"
                detail = (
                    f"There are no fixed QB starter slots, but each team has {sf_per_team} QB-eligible flexible "
                    f"slot{'s' if sf_per_team != 1 else ''} ({qb_eligible_leaguewide} league-wide). "
                    f"The historical QB replacement frontier sits near QB{f}. Read QB demand from slot eligibility, not from a traditional QB count."
                )
            else:
                title = "Superflex expands the QB-eligible starting pool"
                detail = (
                    f"Each team can start QBs in {qb_eligible_per_team} slot{'s' if qb_eligible_per_team != 1 else ''} "
                    f"({fixed_qb_per_team} fixed + {sf_per_team} flexible), or {qb_eligible_leaguewide} QB-eligible slots league-wide. "
                    f"The historical replacement frontier sits near QB{f}. Treat QB depth as a starting-lineup requirement, not just bench insurance."
                )
            candidates.append({
                "family": "format_superflex", "position": "QB",
                "score": 1.35 + min(max(f - qb_eligible_leaguewide, 0) / max(int(teams), 1), 2.0) * 0.20,
                "title": title,
                "detail": detail,
            })
'''
if old_sf not in s:
    raise SystemExit("STOP: V0.7.4 Superflex editorial block not found")
s = s.replace(old_sf, new_sf, 1)

old_flex = '''    if int(flex) >= 3:
        wr_f, rb_f = _frontier_rank("WR"), _frontier_rank("RB")
        if wr_f is not None and rb_f is not None:
            deeper_pos, deeper_f = ("WR", wr_f) if wr_f >= rb_f else ("RB", rb_f)
            candidates.append({
                "family": "format_flex", "position": deeper_pos,
                "score": 1.00 + int(flex) * 0.08,
                "title": "Flex-heavy lineups make depth a starting-lineup issue",
                "detail": (
                    f"With {int(flex)} FLEX spots per team, the observed replacement frontier extends to roughly WR{wr_f} and RB{rb_f}. "
                    "Judge mid-range depth as lineup supply, not merely bench depth."
                ),
            })
'''
new_flex = '''    if int(flex) >= 3:
        wr_f, rb_f = _frontier_rank("WR"), _frontier_rank("RB")
        if wr_f is not None and rb_f is not None:
            deeper_pos, deeper_f = ("WR", wr_f) if wr_f >= rb_f else ("RB", rb_f)
            # FLEX here means the engine's RB/WR/TE-eligible flex class. Keep it
            # explicitly separate from SUPER_FLEX/QB eligibility in the copy.
            candidates.append({
                "family": "format_flex", "position": deeper_pos,
                "score": 1.00 + int(flex) * 0.08,
                "title": "Flexible starter eligibility makes depth a lineup issue",
                "detail": (
                    f"Each team has {int(flex)} non-QB FLEX slot{'s' if int(flex) != 1 else ''} for RB/WR/TE, "
                    f"with historical replacement near WR{wr_f} and RB{rb_f}. "
                    "Judge mid-range depth as starting-lineup supply, not merely bench depth."
                ),
            })
'''
if old_flex not in s:
    raise SystemExit("STOP: V0.7.4 FLEX editorial block not found")
s = s.replace(old_flex, new_flex, 1)

# Make the methodology explicit without exposing research/backoffice vocabulary
# in the five headline cards.
method_needle = 'Engine V0.2.1 frozen.'
# Version replacements above are sufficient for the visible footer/caption.

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_7_5.py created")
print("Engine V0.2.1 math unchanged")
print("Format semantics: Structural Insights now distinguish fixed slots, non-QB FLEX, and QB-eligible SUPER_FLEX")
print("SFB/home formats with 0 fixed QB are treated as valid slot-eligibility structures, not parser errors")
print("Editorial dedupe and performance are intentionally unchanged in this step")