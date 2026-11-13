from pathlib import Path

SRC = Path("app_v0_6_3.py")
DST = Path("app_v0_7_0.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_6_3.py not found")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.6.3', 'UI V0.7.0')
s = s.replace('WoRP-Lab/0.6', 'WoRP-Lab/0.7')
s = s.replace('V0.6.3: concept-first positional curve + click-to-hide legend + automatic structural insights.', 'V0.7.0: league-specific structural tiers + actionable insights.')
s = s.replace('[24, 36, 50],\n        index=2,', '[24, 36, 50, 72, 96],\n        index=3,')

start = s.index('    # Deterministic presentation-layer insights from the historical curve.')
end = s.index('    audit = {', start)
new_logic = '''    # Product layer V0.7.0: tier-first structural insights.
    # Tiers are discovered from the curve itself. Fixed 12-player buckets are not used.
    # Engine V0.2.1 is unchanged.
    def _segment_sse(values, a, b):
        import numpy as np
        y = np.asarray(values[a:b], dtype=float)
        if len(y) <= 1:
            return 0.0
        x = np.arange(len(y), dtype=float)
        coef = np.polyfit(x, y, 1)
        pred = coef[0] * x + coef[1]
        return float(((y - pred) ** 2).sum())

    def _discover_tiers(pos, max_rank=96, min_size=8, max_segments=5):
        import math
        import numpy as np
        x = curve[curve["position"] == pos].sort_values("position_rank").copy()
        x = x[x["position_rank"] <= max_rank].reset_index(drop=True)
        n = len(x)
        if n < min_size * 2:
            return []
        vals = x["three_year_worp_avg"].to_numpy(float)
        sse = [[None] * (n + 1) for _ in range(n)]
        for a in range(n):
            for b in range(a + min_size, n + 1):
                sse[a][b] = _segment_sse(vals, a, b)
        best_model = None
        for k in range(2, min(max_segments, n // min_size) + 1):
            inf = float("inf")
            dp = [[inf] * (n + 1) for _ in range(k + 1)]
            prev = [[None] * (n + 1) for _ in range(k + 1)]
            for b in range(min_size, n + 1):
                if sse[0][b] is not None:
                    dp[1][b] = sse[0][b]
            for seg in range(2, k + 1):
                for b in range(seg * min_size, n + 1):
                    for a in range((seg - 1) * min_size, b - min_size + 1):
                        if dp[seg - 1][a] < inf and sse[a][b] is not None:
                            v = dp[seg - 1][a] + sse[a][b]
                            if v < dp[seg][b]:
                                dp[seg][b] = v
                                prev[seg][b] = a
            rss = max(dp[k][n], 1e-12)
            # 2 params per line + k-1 breakpoints; BIC selects complexity.
            p = 2 * k + (k - 1)
            bic = n * math.log(rss / n) + p * math.log(n)
            if best_model is None or bic < best_model[0]:
                cuts = [n]
                b = n
                for seg in range(k, 1, -1):
                    a = prev[seg][b]
                    cuts.append(a)
                    b = a
                cuts.append(0)
                cuts = sorted(cuts)
                best_model = (bic, cuts)
        if best_model is None:
            return []
        cuts = best_model[1]
        out = []
        names = ["Elite Tier", "High-Value Tier", "Core Tier", "Compressed Tier", "Deep Tier"]
        for i, (a, b) in enumerate(zip(cuts[:-1], cuts[1:])):
            seg = x.iloc[a:b]
            if seg.empty:
                continue
            lo = int(seg["position_rank"].min())
            hi = int(seg["position_rank"].max())
            first = float(seg.iloc[0]["three_year_worp_avg"])
            last = float(seg.iloc[-1]["three_year_worp_avg"])
            slope = (last - first) / max(hi - lo, 1)
            out.append({"tier": names[min(i, len(names)-1)], "from": lo, "to": hi,
                        "start": first, "end": last, "slope": slope})
        return out

    tier_rows = []
    for _pos in ["QB", "RB", "WR", "TE"]:
        for _t in _discover_tiers(_pos):
            tier_rows.append({"position": _pos, **_t})
    tier_df = pd.DataFrame(tier_rows)

    insights = []
    for pos in ["QB", "RB", "WR", "TE"]:
        pt = tier_df[tier_df["position"] == pos].copy() if not tier_df.empty else pd.DataFrame()
        if pt.empty:
            continue
        first = pt.iloc[0]
        last = pt.iloc[-1]
        first_label = f"{first['tier']} ({pos}{int(first['from'])}–{pos}{int(first['to'])})"
        last_label = f"{last['tier']} ({pos}{int(last['from'])}–{pos}{int(last['to'])})"
        elite_drop = float(first["start"] - first["end"])
        deep_drop = float(last["start"] - last["end"])
        if elite_drop > 0:
            insights.append({
                "position": pos,
                "priority": elite_drop,
                "title": f"{pos}: value is concentrated in {first_label}",
                "detail": f"This tier loses {elite_drop:.2f} WoRP from top to bottom. Treat the top of the position as meaningfully different from the broader depth behind it."
            })
        insights.append({
            "position": pos,
            "priority": 0.5,
            "title": f"{pos}: {last_label} is broad and compressed",
            "detail": f"Across this tier the curve changes only {deep_drop:.2f} WoRP. Differences inside the tier are small historically; do not turn its lower boundary into a hard waiver cutoff."
        })
    insight_df = pd.DataFrame(insights)

'''
s = s[:start] + new_logic + s[end:]

# Persist tiers in result/session state without changing engine outputs.
s = s.replace('return curve, player_summary, player_seasons, cliff_df, insight_df, audit', 'return curve, player_summary, player_seasons, cliff_df, insight_df, tier_df, audit')
s = s.replace('                insight_df,\n                audit,', '                insight_df,\n                tier_df,\n                audit,')
s = s.replace('            st.session_state["league_insights"] = insight_df\n            st.session_state["league_curve_audit"] = audit', '            st.session_state["league_insights"] = insight_df\n            st.session_state["league_tiers"] = tier_df\n            st.session_state["league_curve_audit"] = audit')
s = s.replace('    insight_df = st.session_state["league_insights"].copy()\n    audit =', '    insight_df = st.session_state["league_insights"].copy()\n    tier_df = st.session_state["league_tiers"].copy()\n    audit =')

old_ui_start = s.index('        st.markdown("##### Structural insights")')
old_ui_end = s.index('        st.markdown("##### Value cliffs")', old_ui_start)
new_ui = '''        st.markdown("##### Structural tiers")
        st.caption(
            "League-specific economic regimes discovered from the historical WoRP curve. "
            "Tier sizes are allowed to be asymmetric; every tier shows its actual rank range."
        )

        if tier_df is not None and not tier_df.empty:
            for pos in ["WR", "RB", "TE", "QB"]:
                pt = tier_df[tier_df["position"] == pos].copy()
                if pt.empty:
                    continue
                st.markdown(f"**{pos}**")
                cols = st.columns(len(pt))
                for col, (_, t) in zip(cols, pt.iterrows()):
                    label = f"{t['tier']} ({pos}{int(t['from'])}–{pos}{int(t['to'])})"
                    col.metric(label, f"{t['start']:.2f} → {t['end']:.2f} WoRP")

        st.markdown("##### What this league is telling you")
        st.caption("Simple, actionable reads from the tier structure. Historical, not predictive.")
        if insight_df is not None and not insight_df.empty:
            for _, insight in insight_df.sort_values("priority", ascending=False).iterrows():
                st.markdown(f"**{insight['title']}**  \\n{insight['detail']}")
        else:
            st.caption("No structural insights available for this curve.")

'''
s = s[:old_ui_start] + new_ui + s[old_ui_end:]

# Remove raw cliff table/checkpoint backoffice from the main product tab.
cliff_start = s.index('        st.markdown("##### Value cliffs")')
players_start = s.index('    with tab_players:', cliff_start)
s = s[:cliff_start] + '        st.caption("Exact rank values remain available in the chart tooltip; the product view prioritizes tiers over hard cut lines.")\n\n' + s[players_start:]

s = s.replace('["POSITIONAL CURVE", "PLAYER BOARD", "METHODOLOGY"]', '["STRUCTURAL INSIGHTS", "PLAYER BOARD", "METHODOLOGY"]')
s = s.replace('WoRP Lab UI V0.6.3 · Sleeper-native scoring · Engine V0.2.1 frozen.', 'WoRP Lab UI V0.7.0 · Tier-first Structural Insights · Sleeper-native scoring · Engine V0.2.1 frozen.')
s = s.replace('V0.6.2 changes', 'V0.7.0 changes')

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_7_0.py created")
print("Engine V0.2.1 unchanged")
print("Structural Insights: tier-first, ranges always in parentheses, no research backoffice")