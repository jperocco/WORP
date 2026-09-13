from pathlib import Path

SRC = Path("app_v0_7_1.py")
DST = Path("app_v0_7_2.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_7_1.py not found")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.7.1', 'UI V0.7.2')
s = s.replace('WoRP-Lab/0.7.1', 'WoRP-Lab/0.7.2')
s = s.replace('V0.7.1: five league-specific Structural Insights. Clean, actionable, historical.', 'V0.7.2: five league-specific Structural Insights + Value Cliffs + faster compute.')
s = s.replace('WoRP Lab UI V0.7.1 · Five actionable Structural Insights · Sleeper-native scoring · Engine V0.2.1 frozen.', 'WoRP Lab UI V0.7.2 · Five actionable Structural Insights · Value Cliffs · Engine V0.2.1 frozen.')

# PERFORMANCE: 4k default, optional 2k preview, 8k validated control.
old_mc = '''    n_sims_ui = st.selectbox(
        "Monte Carlo",
        [4000, 8000],
        index=1,
        help="8,000 is the validated control setting.",
    )'''
new_mc = '''    n_sims_ui = st.selectbox(
        "Monte Carlo",
        [2000, 4000, 8000],
        index=1,
        format_func=lambda x: {2000: "2,000 · Fast preview", 4000: "4,000 · Standard", 8000: "8,000 · Validated control"}[x],
        help="4,000 is the standard product mode. 8,000 remains the validated control setting.",
    )'''
if old_mc not in s:
    raise SystemExit("STOP: Monte Carlo control block not found")
s = s.replace(old_mc, new_mc)

marker = '''@st.cache_data(show_spinner=False)
def calculate_league_intelligence_cached('''
helper = '''@st.cache_data(ttl=86400, show_spinner=False)
def load_scored_history_cached(seasons, scoring_json):
    """Cache expensive Sleeper historical input preparation separately from Monte Carlo."""
    sc = json.loads(scoring_json)
    player_map = fetch_player_map()
    all_weeks, endpoint_log = load_sleeper_player_weeks(
        seasons=tuple(seasons),
        scoring_settings=sc,
        player_map=player_map,
    )
    validate_weekly_contract(all_weeks)
    return all_weeks, endpoint_log


@st.cache_data(show_spinner=False)
def calculate_league_intelligence_cached('''
if marker not in s:
    raise SystemExit("STOP: calculate cache marker not found")
s = s.replace(marker, helper, 1)

old_load = '''    player_map = fetch_player_map()
    all_weeks, endpoint_log = load_sleeper_player_weeks(
        seasons=seasons,
        scoring_settings=sc,
        player_map=player_map,
    )
    validate_weekly_contract(all_weeks)
'''
new_load = '''    # Base historical scoring/input prep is cached independently from Monte Carlo.
    all_weeks, endpoint_log = load_scored_history_cached(tuple(seasons), scoring_json)
'''
if old_load not in s:
    raise SystemExit("STOP: historical input block not found")
s = s.replace(old_load, new_load, 1)
s = s.replace('seasons=(2023, 2024, 2025), n_sims=8000, seed=7', 'seasons=(2023, 2024, 2025), n_sims=4000, seed=7')

# EDITORIAL: replace isolated rank-12 absolute value with relative marginal cost of waiting.
old_depth = '''    # 2) Top-12 retention: which position stays strongest deepest into its traditional starter-quality range.
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
'''
new_depth = '''    # 2) Relative depth/scarcity: cost of waiting from rank 8 to rank 20.
    # A high absolute WoRP at one rank does not prove scarcity if the whole curve stays high.
    wait_costs = []
    for pos in positions:
        v8, v20 = _value_at(pos, 8), _value_at(pos, 20)
        if v8 is not None and v20 is not None:
            wait_costs.append((pos, v8 - v20))
    if wait_costs:
        scarce_pos, scarce_cost = max(wait_costs, key=lambda z: z[1])
        deep_pos, deep_cost = min(wait_costs, key=lambda z: z[1])
        candidates.append({
            "family": "relative_scarcity", "position": scarce_pos,
            "score": scarce_cost * 0.95,
            "title": f"Waiting at {scarce_pos} gets expensive",
            "detail": f"From {scarce_pos}8 to {scarce_pos}20, the curve gives up {scarce_cost:.2f} WoRP — the largest marginal cost of waiting across positions."
        })
        candidates.append({
            "family": "relative_depth", "position": deep_pos,
            "score": max(0.0, 1.25 - deep_cost) * 0.85,
            "title": f"You can wait longer at {deep_pos}",
            "detail": f"From {deep_pos}8 to {deep_pos}20, the curve gives up only {deep_cost:.2f} WoRP — the smallest marginal cost of waiting across positions."
        })
'''
if old_depth not in s:
    raise SystemExit("STOP: V0.7.1 depth block not found")
s = s.replace(old_depth, new_depth)

# DEDUPE: elite concentration + top-end cliff at same position = one story.
old_editor = '''    ranked = sorted(candidates, key=lambda d: d["score"], reverse=True)
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
'''
new_editor = '''    ranked = sorted(candidates, key=lambda d: d["score"], reverse=True)
    chosen, family_seen, pos_count = [], set(), {}
    elite_story_positions = set()
    for item in ranked:
        if item["family"] in family_seen:
            continue
        pos = item["position"]
        if item["family"] == "elite_concentration":
            if pos in elite_story_positions:
                continue
            elite_story_positions.add(pos)
        elif item["family"] == "cliff":
            cr = cliff_df[cliff_df["position"] == pos].sort_values("worp_drop", ascending=False).head(1)
            if not cr.empty and int(cr.iloc[0]["cliff_end_rank"]) <= 10:
                if pos in elite_story_positions:
                    continue
                elite_story_positions.add(pos)
        if pos_count.get(pos, 0) >= 2:
            continue
        chosen.append(item)
        family_seen.add(item["family"])
        pos_count[pos] = pos_count.get(pos, 0) + 1
        if len(chosen) == 5:
            break
'''
if old_editor not in s:
    raise SystemExit("STOP: V0.7.1 editorial block not found")
s = s.replace(old_editor, new_editor)

# VALUE CLIFFS: restore the senior analytical layer directly below the five insights.
ui_marker = '''        else:
            st.caption("No Structural Insights available for this curve.")

'''
value_cliffs = '''        else:
            st.caption("No Structural Insights available for this curve.")

        st.markdown("##### Value Cliffs")
        st.caption("Where does waiting a few ranks cost the most WoRP? The five insights summarize; this table lets you inspect the marginal delta.")
        if cliff_df is not None and not cliff_df.empty:
            cliff_view = cliff_df.copy().sort_values("worp_drop", ascending=False)
            cliff_view["Range"] = cliff_view.apply(lambda r: f"{r['position']}{int(r['cliff_start_rank'])}–{r['position']}{int(r['cliff_end_rank'])}", axis=1)
            cliff_view["WoRP drop"] = cliff_view["worp_drop"].round(2)
            st.dataframe(
                cliff_view[["position", "Range", "WoRP drop"]].rename(columns={"position": "Position"}),
                hide_index=True,
                use_container_width=True,
            )

'''
if ui_marker not in s:
    raise SystemExit("STOP: Structural Insights UI marker not found")
s = s.replace(ui_marker, value_cliffs, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_7_2.py created")
print("Engine V0.2.1 unchanged")
print("Performance: 4k default, 2k preview, 8k validated control; Sleeper historical inputs cached 24h")
print("Editorial: rank-12 absolute depth removed; relative marginal cost used")
print("Editorial: overlapping elite/cliff stories deduplicated")
print("Frontend: Value Cliffs restored below Structural Insights")