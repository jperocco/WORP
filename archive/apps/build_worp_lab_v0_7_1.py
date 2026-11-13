from pathlib import Path

SRC = Path("app_v0_6_3.py")
DST = Path("app_v0_7_1.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_6_3.py not found")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.6.3', 'UI V0.7.1')
s = s.replace('WoRP-Lab/0.6', 'WoRP-Lab/0.7.1')
s = s.replace(
    'V0.6.3: concept-first positional curve + click-to-hide legend + automatic structural insights.',
    'V0.7.1: five league-specific Structural Insights. Clean, actionable, historical.'
)

start = s.index('    # Deterministic presentation-layer insights from the historical curve.')
end = s.index('    audit = {', start)
new_logic = '''    # Product layer V0.7.1: V1 philosophy, richer evidence underneath.
    # Generate many measured candidates, publish exactly five after editorial ranking.
    # No research/backoffice vocabulary. Engine V0.2.1 unchanged.
    def _value_at(pos, rank):
        row = curve[(curve["position"] == pos) & (curve["position_rank"] == int(rank))]
        if row.empty:
            return None
        return float(row.iloc[0]["three_year_worp_avg"])

    positions = ["QB", "RB", "WR", "TE"]
    candidates = []

    # 1) Elite concentration: rank 1 -> rank 8. Uses a narrow top window instead of fixed 12-player tiers.
    elite = []
    for pos in positions:
        v1, v8 = _value_at(pos, 1), _value_at(pos, 8)
        if v1 is not None and v8 is not None:
            elite.append((pos, v1 - v8, v1, v8))
    if elite:
        pos, gap, v1, v8 = max(elite, key=lambda z: z[1])
        candidates.append({
            "family": "elite_concentration", "position": pos,
            "score": gap * 1.35,
            "title": f"Prioritize elite {pos}",
            "detail": f"{pos} loses {gap:.2f} WoRP from {pos}1 to {pos}8 — the steepest elite drop in this league."
        })

    # 2) Top-12 retention: which position stays strongest deepest into its traditional starter-quality range.
    depth = []
    for pos in positions:
        v12 = _value_at(pos, 12)
        if v12 is not None:
            depth.append((pos, v12))
    if depth:
        pos, v12 = max(depth, key=lambda z: z[1])
        candidates.append({
            "family": "top12_depth", "position": pos,
            "score": max(v12, 0) * 0.85,
            "title": f"{pos} depth holds up",
            "detail": f"Even {pos}12 carries {v12:.2f} WoRP, the strongest value retention at rank 12."
        })

    # 3) Sharpest meaningful five-rank cliff already calculated from the same league curve.
    if not cliff_df.empty:
        r = cliff_df.sort_values("worp_drop", ascending=False).iloc[0]
        pos = str(r["position"])
        a, b = int(r["cliff_start_rank"]), int(r["cliff_end_rank"])
        drop = float(r["worp_drop"])
        candidates.append({
            "family": "cliff", "position": pos,
            "score": drop * 1.15,
            "title": f"Don’t trade down through {pos}{a}–{pos}{b} lightly",
            "detail": f"That five-rank stretch costs {drop:.2f} WoRP — the sharpest short-range drop on the board."
        })

    # 4) Middle-curve compression: rank 20 -> 40 normalized per 10 ranks.
    middle = []
    for pos in positions:
        v20, v40 = _value_at(pos, 20), _value_at(pos, 40)
        if v20 is not None and v40 is not None:
            middle.append((pos, (v20 - v40) / 2.0, v20, v40))
    if middle:
        pos, cost10, v20, v40 = min(middle, key=lambda z: z[1])
        candidates.append({
            "family": "middle_compression", "position": pos,
            "score": max(0.0, 0.9 - cost10),
            "title": f"Be selective paying for mid-range {pos} upgrades",
            "detail": f"From {pos}20 to {pos}40, each 10 ranks costs only about {cost10:.2f} WoRP on average."
        })

    # 5) Deep compression: rank 50 -> 72. This is economic compression only, never a waiver/fungibility claim.
    deep = []
    for pos in positions:
        v50, v72 = _value_at(pos, 50), _value_at(pos, 72)
        if v50 is not None and v72 is not None:
            cost = v50 - v72
            deep.append((pos, cost, v50, v72))
    if deep:
        pos, cost, v50, v72 = min(deep, key=lambda z: z[1])
        candidates.append({
            "family": "deep_compression", "position": pos,
            "score": max(0.0, 0.75 - cost),
            "title": f"Deep {pos} value is compressed",
            "detail": f"The {pos}50–{pos}72 range spans just {cost:.2f} WoRP. Small rank upgrades here have carried limited historical value."
        })

    # 6) Positive-value depth as a secondary candidate, deliberately de-emphasized.
    positive_depth = []
    for pos in positions:
        x = curve[(curve["position"] == pos) & (curve["three_year_worp_avg"] > 0)]
        if not x.empty:
            rank = int(x["position_rank"].max())
            value = float(x.loc[x["position_rank"].idxmax(), "three_year_worp_avg"])
            positive_depth.append((pos, rank, value))
    if positive_depth:
        pos, rank, value = max(positive_depth, key=lambda z: z[1])
        candidates.append({
            "family": "positive_depth", "position": pos,
            "score": 0.25,
            "title": f"{pos} offers the deepest positive-value pool",
            "detail": f"Historical WoRP stays positive deepest at {pos}{rank}. Treat this as depth context, not a hard waiver line."
        })

    # Editorial layer: materiality + balance + redundancy.
    # First take strongest candidate per family, then cap any one position at two cards.
    ranked = sorted(candidates, key=lambda d: d["score"], reverse=True)
    chosen, family_seen, pos_count = [], set(), {}
    for item in ranked:
        if item["family"] in family_seen:
            continue
        pos = item["position"]
        if pos_count.get(pos, 0) >= 2:
            continue
        chosen.append(item)
        family_seen.add(item["family"])
        pos_count[pos] = pos_count.get(pos, 0) + 1
        if len(chosen) == 5:
            break

    # Fill to exactly five if the position cap prevented it; still no duplicate families.
    if len(chosen) < 5:
        for item in ranked:
            if item["family"] in family_seen:
                continue
            chosen.append(item)
            family_seen.add(item["family"])
            if len(chosen) == 5:
                break

    insight_df = pd.DataFrame(chosen[:5])

'''
s = s[:start] + new_logic + s[end:]

old_ui_start = s.index('        st.markdown("##### Structural insights")')
old_ui_end = s.index('        st.markdown("##### Value cliffs")', old_ui_start)
new_ui = '''        st.markdown("##### What this league is telling you")
        st.caption("Five historical, league-specific roster signals. Built to inform decisions — not project players.")

        if insight_df is not None and not insight_df.empty:
            for _, insight in insight_df.head(5).iterrows():
                st.markdown(f"**{insight['title']}**  \\n{insight['detail']}")
        else:
            st.caption("No Structural Insights available for this curve.")

'''
s = s[:old_ui_start] + new_ui + s[old_ui_end:]

# Remove raw cliff table/checkpoint backoffice from the main product tab.
cliff_start = s.index('        st.markdown("##### Value cliffs")')
players_start = s.index('    with tab_players:', cliff_start)
s = s[:cliff_start] + s[players_start:]

s = s.replace('["POSITIONAL CURVE", "PLAYER BOARD", "METHODOLOGY"]', '["STRUCTURAL INSIGHTS", "PLAYER BOARD", "METHODOLOGY"]')
s = s.replace(
    'WoRP Lab UI V0.6.3 · Sleeper-native scoring · Engine V0.2.1 frozen.',
    'WoRP Lab UI V0.7.1 · Five actionable Structural Insights · Sleeper-native scoring · Engine V0.2.1 frozen.'
)
s = s.replace('V0.6.2 changes', 'V0.7.1 changes')

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_7_1.py created")
print("Engine V0.2.1 unchanged")
print("Frontend: exactly five editorial Structural Insights; no tier wall; no research backoffice")
