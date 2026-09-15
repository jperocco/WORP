"""Rebuild WoRP Lab V0.9.4 without consuming stale generated V0.9.3/V0.9.4 apps.

The normal generated-app chain is intentionally not committed. This recovery
builder recreates the last clean editorial base from committed V0.6.3, then
adds the approved V0.9.4 Lineup Economics and preserves the frozen V0.32
Roster Construction presentation. Existing generated apps are overwritten;
source builders and the frozen engine are not modified.
"""

from pathlib import Path
import subprocess
import sys


BASE_BUILDERS = [
    "build_worp_lab_v0_7_0.py",
    "build_worp_lab_v0_7_1.py",
    "build_worp_lab_v0_7_2.py",
    "build_worp_lab_v0_7_3.py",
    "build_worp_lab_v0_7_4.py",
    "build_worp_lab_v0_7_5.py",
    "build_worp_lab_v0_7_6.py",
    "build_worp_lab_v0_7_6_1.py",
    "build_worp_lab_v0_7_7.py",
    "build_worp_lab_v0_7_8.py",
    "build_worp_lab_v0_7_9.py",
    "build_worp_lab_v0_8_0.py",
    "build_worp_lab_v0_8_1.py",
    "build_worp_lab_v0_8_2.py",
    "build_worp_lab_v0_8_3.py",
    "build_worp_lab_v0_8_4.py",
    "build_worp_lab_v0_8_5.py",
    "build_worp_lab_v0_9_0.py",
    "build_worp_lab_v0_9_1.py",
]


for builder in BASE_BUILDERS:
    if not Path(builder).exists():
        raise SystemExit(f"STOP: committed base builder missing: {builder}")
    subprocess.run([sys.executable, builder], check=True)


src = Path("app_v0_9_1.py")
dst = Path("app_v0_9_4.py")
if not src.exists():
    raise SystemExit("STOP: clean V0.9.1 base was not generated")

s = src.read_text(encoding="utf-8")
s = s.replace("UI V0.9.1", "UI V0.9.4")
s = s.replace("WoRP-Lab/0.9.1", "WoRP-Lab/0.9.4")
s = s.replace("WoRP Lab UI V0.9.1", "WoRP Lab UI V0.9.4")

calculate_marker = "@st.cache_data(show_spinner=False)\ndef calculate_league_intelligence_cached("
if calculate_marker not in s:
    raise SystemExit("STOP: clean calculation marker not found")
s = s.replace(
    calculate_marker,
    "from worp_lineup_economics_v0_9_4 import build_lineup_scoring_share\n\n"
    + calculate_marker,
    1,
)

player_tab_marker = "    with tab_players:"
if player_tab_marker not in s:
    raise SystemExit("STOP: clean player-tab marker not found")

product_ui = r'''        _teams=int(league.get("total_rosters",0) or 0)
        _qb=int(counts.get("QB",0)); _rb=int(counts.get("RB",0)); _wr=int(counts.get("WR",0)); _te=int(counts.get("TE",0))
        _flex=int(counts.get("FLEX",0)); _superflex=int(counts.get("SUPER_FLEX",0)); _sc=league.get("scoring_settings",{}) or {}

        st.markdown("##### Lineup Economics")
        st.caption("How much of this league's expected starting-lineup scoring comes from each slot — and which positions fill flexible slots.")
        try:
            _pw,_ = load_sleeper_player_weeks([2023,2024,2025], _sc, player_map=fetch_player_map())
            lineup_rows=build_lineup_scoring_share(_pw,_teams,_qb,_rb,_wr,_te,_flex,_superflex)
            cards=[]
            for lr in lineup_rows:
                occ=lr['occupancy']
                is_flexible=lr['slot'].startswith('FLEX') or lr['slot'].startswith('SUPER_FLEX')
                mix=(''.join(f'<span>{p} {100*v:.0f}%</span>' for p,v in sorted(occ.items(),key=lambda kv:kv[1],reverse=True)) if is_flexible else '')
                cards.append(
                    f'<div class="ls-card"><div class="ls-slot">{lr["slot"]}</div>'
                    f'<div class="ls-share">{100*lr["lineup_share"]:.1f}%</div>'
                    f'<div class="ls-label">of expected lineup scoring</div>'
                    f'<div class="ls-pts">{lr["points_week"]:.1f} pts/week</div>'
                    f'<div class="ls-mix">{mix}</div></div>'
                )
            st.markdown("""<style>
            .ls-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:8px 0 16px 0}
            .ls-card{border:1px solid rgba(128,128,128,.35);border-radius:14px;padding:16px 14px;text-align:center;min-height:164px;background:rgba(128,128,128,.04)}
            .ls-slot{font-weight:700;font-size:15px;margin-bottom:10px}.ls-share{font-weight:800;font-size:34px;line-height:1.05}.ls-label{font-size:11px;opacity:.62;margin-top:4px}.ls-pts{font-size:16px;margin:10px 0 8px}.ls-mix{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;font-size:12px;opacity:.72;line-height:1.45;min-height:18px}
            </style>""",unsafe_allow_html=True)
            st.markdown('<div class="ls-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)
            st.caption("Historical 2023–25 average under this league's exact Sleeper scoring. Share is fantasy-point contribution to the expected starting lineup; flexible-slot mix is modeled positional occupancy. WoRP is not used in this panel.")
        except Exception as exc:
            st.caption(f"Lineup Economics unavailable: {exc}")

        # Frozen V0.32 presentation. Universal derived-format support remains
        # the next task after V0.9.4 visual validation.
        st.markdown("##### Roster Construction")
        st.caption("League-native Scoring Core ranges. Use these as construction envelopes, not exact quotas or player rankings.")
        try:
            rc=pd.read_csv("worp_roster_construction_product_ranges_v0_32.csv")
            start_n=_qb+_rb+_wr+_te+_flex+_superflex
            tep=float(_sc.get("bonus_rec_te",0.0))>0
            fmt_key=(f"{_teams}T "+("SF " if _superflex>0 else "1QB ")
                     +f"Start{start_n} QB{_qb} RB{_rb} WR{_wr} TE{_te} "
                     +f"FLEX{_flex} SFLEX{_superflex}"+(" TEP" if tep else ""))
            hit=rc[rc["format_key"]==fmt_key]
            if hit.empty:
                st.caption("Roster Construction: exact format not yet supported by the frozen empirical envelope. No nearest-format substitution is made.")
            else:
                r=hit.iloc[0]
                st.markdown(
                    f"**Scoring Core: {int(r['scoring_core_low'])}–{int(r['scoring_core_high'])}**  \n"
                    f"QB {int(r['QB_low'])}–{int(r['QB_high'])} · RB {int(r['RB_low'])}–{int(r['RB_high'])} · "
                    f"WR {int(r['WR_low'])}–{int(r['WR_high'])} · TE {int(r['TE_low'])}–{int(r['TE_high'])}"
                )
                st.caption("Independent positional lows/highs are decision-equivalent constraints, not additive quotas. Once meaningful Scoring capacity is satisfied, remaining roster capacity belongs to Non-Scoring optionality.")
        except Exception as exc:
            st.caption(f"Roster Construction unavailable: {exc}")

'''

s = s.replace(player_tab_marker, product_ui + player_tab_marker, 1)
dst.write_text(s, encoding="utf-8")
compile(s, str(dst), "exec")

print("PASS: clean app_v0_9_4.py created")
print("Ignored stale generated V0.9.2/V0.9.3/V0.9.4 apps")
print("Lineup Economics: slot cards + lineup scoring share + pts/week + FLEX/SF mix")
print("WoRP Engine V0.2.1 unchanged")

