from pathlib import Path

SRC = Path("app_v0_9_1.py")
DST = Path("app_v0_9_2.py")
RANGES = Path("worp_roster_construction_product_ranges_v0_32.csv")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_9_1.py not found. Build through V0.9.1 first.")
if not RANGES.exists():
    raise SystemExit("STOP: V0.32 product ranges not found. Run worp_roster_construction_closeout_v0_32.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.9.1', 'UI V0.9.2')
s = s.replace('WoRP-Lab/0.9.1', 'WoRP-Lab/0.9.2')
s = s.replace('WoRP Lab UI V0.9.1', 'WoRP Lab UI V0.9.2')

# Product integration only. V0.32 ranges are frozen empirical outputs; this
# builder does not recompute or refine Roster Construction.
marker = '    with tab_players:'
if marker not in s:
    raise SystemExit("STOP: player-tab marker not found in V0.9.1")

insert = r'''        # V0.9.2 — league-native Roster Construction product layer.
        # No player identity and no asset-value inference. The independent
        # positional ranges are constraints inside a whole-core envelope; they
        # must never be summed into an exact quota.
        st.markdown("##### Roster Construction")
        st.caption("League-native Scoring Core ranges. Use these as construction envelopes, not exact quotas or player rankings.")

        try:
            rc = pd.read_csv("worp_roster_construction_product_ranges_v0_32.csv")
            # Reconstruct the exact-format key used by the frozen research from
            # the current league inputs. This deliberately abstains rather than
            # mapping an unsupported format to a nearby one.
            start_n = int(qb) + int(rb) + int(wr) + int(te) + int(flex) + int(superflex)
            tep = float(sc.get("bonus_rec_te", 0.0)) > 0
            fmt_key = (
                f"{int(teams)}T "
                + ("SF " if int(superflex) > 0 else "1QB ")
                + f"Start{start_n} QB{int(qb)} RB{int(rb)} WR{int(wr)} TE{int(te)} "
                + f"FLEX{int(flex)} SFLEX{int(superflex)}"
                + (" TEP" if tep else "")
            )
            hit = rc[rc["format_key"] == fmt_key]
            if hit.empty:
                st.caption("Roster Construction: exact format not yet supported by the frozen empirical envelope. No nearest-format substitution is made.")
            else:
                r = hit.iloc[0]
                st.markdown(
                    f"**Scoring Core: {int(r['scoring_core_low'])}–{int(r['scoring_core_high'])}**  \\n"
                    f"QB {int(r['QB_low'])}–{int(r['QB_high'])} · "
                    f"RB {int(r['RB_low'])}–{int(r['RB_high'])} · "
                    f"WR {int(r['WR_low'])}–{int(r['WR_high'])} · "
                    f"TE {int(r['TE_low'])}–{int(r['TE_high'])}"
                )
                st.caption(
                    "Independent positional lows/highs are decision-equivalent constraints, not additive quotas. "
                    "Once meaningful Scoring capacity is satisfied, remaining roster capacity belongs to Non-Scoring optionality."
                )
        except Exception as exc:
            st.caption(f"Roster Construction unavailable: {exc}")

'''
s = s.replace(marker, insert + marker, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_9_2.py created")
print("Engine V0.2.1 math unchanged")
print("V0.32 league-native Roster Construction ranges integrated")
print("Exact-format only; unsupported formats abstain")
print("No player names, asset value, buy/sell/drop, or new threshold introduced")
