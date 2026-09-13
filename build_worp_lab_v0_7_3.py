from pathlib import Path

SRC = Path("app_v0_7_2.py")
DST = Path("app_v0_7_3.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_7_2.py not found. Run build_worp_lab_v0_7_2.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.7.2', 'UI V0.7.3')
s = s.replace('WoRP-Lab/0.7.2', 'WoRP-Lab/0.7.3')
s = s.replace('WoRP Lab UI V0.7.2', 'WoRP Lab UI V0.7.3')

# -----------------------------------------------------------------------------
# 1) PERFORMANCE PROFILING ONLY — no engine math changes.
# -----------------------------------------------------------------------------
if 'import time\n' not in s:
    s = s.replace('import json\n', 'import json\nimport time\n', 1)

fn_marker = '''def calculate_league_intelligence_cached(
    teams, qb, rb, wr, te, flex, superflex, scoring_json,
    seasons=(2023, 2024, 2025), n_sims=4000, seed=7
):
    from worp_engine import LeagueSettings, calculate_season_worp
'''
fn_repl = '''def calculate_league_intelligence_cached(
    teams, qb, rb, wr, te, flex, superflex, scoring_json,
    seasons=(2023, 2024, 2025), n_sims=4000, seed=7
):
    from worp_engine import LeagueSettings, calculate_season_worp
    t_calc0 = time.perf_counter()
'''
if fn_marker not in s:
    raise SystemExit("STOP: calculate function marker not found")
s = s.replace(fn_marker, fn_repl, 1)

load_marker = '''    all_weeks, endpoint_log = load_scored_history_cached(tuple(seasons), scoring_json)

    rankings = {}

    for season_i in seasons:
'''
load_repl = '''    all_weeks, endpoint_log = load_scored_history_cached(tuple(seasons), scoring_json)
    t_after_load = time.perf_counter()

    rankings = {}
    engine_timings = []

    for season_i in seasons:
'''
if load_marker not in s:
    raise SystemExit("STOP: cached history marker not found")
s = s.replace(load_marker, load_repl, 1)

engine_marker = '''        weekly, ranking = calculate_season_worp(
            season_df,
            settings,
            replacement_band=6,
            n_sims=int(n_sims),
            seed=int(seed),
        )

        ranking = ranking.copy()
'''
engine_repl = '''        t_engine0 = time.perf_counter()
        weekly, ranking = calculate_season_worp(
            season_df,
            settings,
            replacement_band=6,
            n_sims=int(n_sims),
            seed=int(seed),
        )
        engine_timings.append((int(season_i), time.perf_counter() - t_engine0))

        ranking = ranking.copy()
'''
if engine_marker not in s:
    raise SystemExit("STOP: engine call marker not found")
s = s.replace(engine_marker, engine_repl, 1)

post_marker = '''    # Rank-average positional curve:
'''
post_repl = '''    t_after_engine = time.perf_counter()

    # Rank-average positional curve:
'''
if post_marker not in s:
    raise SystemExit("STOP: post-engine marker not found")
s = s.replace(post_marker, post_repl, 1)

# -----------------------------------------------------------------------------
# 2) STORY-LEVEL EDITORIAL SYNTHESIS.
# A position can have a steep elite head AND a flat next band. That is one shape,
# not two contradictory cards. Top-end cliff is evidence for that same story.
# -----------------------------------------------------------------------------
editor_start = '''    ranked = sorted(candidates, key=lambda d: d["score"], reverse=True)
    chosen, family_seen, pos_count = [], set(), {}
    elite_story_positions = set()
    for item in ranked:
'''
editor_end = '''    # Fill to exactly five if the position cap prevented it; still no duplicate families.
'''
if editor_start not in s or editor_end not in s:
    raise SystemExit("STOP: V0.7.2 editorial block not found")
start = s.index(editor_start)
end = s.index(editor_end, start)
new_editor = '''    # Story synthesis happens BEFORE ranking cards.
    # Example: steep WR1->WR8 + cheap WR8->WR20 = one "stars-and-depth" story.
    by_family = {c["family"]: c for c in candidates}
    synthesized = []
    consumed = set()

    elite_item = by_family.get("elite_concentration")
    depth_item = by_family.get("relative_depth")
    if elite_item and depth_item and elite_item["position"] == depth_item["position"]:
        pos = elite_item["position"]
        elite_gap = None
        wait_gap = None
        try:
            elite_gap = float(elite_item["detail"].split("loses ")[1].split(" WoRP")[0])
        except Exception:
            pass
        try:
            wait_gap = float(depth_item["detail"].split("only ")[1].split(" WoRP")[0])
        except Exception:
            pass
        if elite_gap is not None and wait_gap is not None:
            detail = (
                f"{pos} separates sharply at the very top ({elite_gap:.2f} WoRP from {pos}1 to {pos}8), "
                f"then gets much cheaper to wait ({wait_gap:.2f} from {pos}8 to {pos}20). "
                "Protect access to the stars; be more selective paying for the next tier down."
            )
        else:
            detail = (
                f"{pos} separates sharply at the very top, then the curve compresses. "
                "Protect access to the stars; be more selective paying for the next tier down."
            )
        synthesized.append({
            "family": "curve_shape",
            "position": pos,
            "score": max(elite_item["score"], depth_item["score"]) + 0.20,
            "title": f"{pos} is a stars-and-depth position",
            "detail": detail,
        })
        consumed.update({"elite_concentration", "relative_depth"})

    # If the sharpest 5-rank cliff is top-end at the same position as a synthesized
    # curve-shape/elite story, it is evidence for that story — not a second card.
    top_cliff_pos = None
    top_cliff_end = None
    if not cliff_df.empty:
        cr = cliff_df.sort_values("worp_drop", ascending=False).head(1)
        if not cr.empty:
            top_cliff_pos = str(cr.iloc[0]["position"])
            top_cliff_end = int(cr.iloc[0]["cliff_end_rank"])

    for c in candidates:
        if c["family"] in consumed:
            continue
        if c["family"] == "cliff" and top_cliff_end is not None and top_cliff_end <= 10:
            same_story = any(
                x["position"] == top_cliff_pos and x["family"] in {"curve_shape", "elite_concentration"}
                for x in synthesized
            )
            if same_story:
                continue
        synthesized.append(c)

    ranked = sorted(synthesized, key=lambda d: d["score"], reverse=True)
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
s = s[:start] + new_editor + s[end:]

# Add timing to audit without changing existing outputs.
audit_marker = '''        "endpoint_examples": {
            str(s): (urls[0] if urls else None)
            for s, urls in endpoint_log.items()
        },
    }
'''
audit_repl = '''        "endpoint_examples": {
            str(s): (urls[0] if urls else None)
            for s, urls in endpoint_log.items()
        },
        "timing": {
            "historical_input_seconds": round(t_after_load - t_calc0, 3),
            "engine_total_seconds": round(t_after_engine - t_after_load, 3),
            "engine_by_season_seconds": {str(season): round(sec, 3) for season, sec in engine_timings},
            "postprocess_seconds": round(time.perf_counter() - t_after_engine, 3),
            "total_seconds": round(time.perf_counter() - t_calc0, 3),
        },
    }
'''
if audit_marker not in s:
    raise SystemExit("STOP: audit marker not found")
s = s.replace(audit_marker, audit_repl, 1)

# Performance profile lives in a collapsed senior/debug layer, not in the five cards.
result_marker = '''    audit = st.session_state["league_curve_audit"]

    curve = curve[curve["position_rank"] <= int(top_n)].copy()
'''
result_repl = '''    audit = st.session_state["league_curve_audit"]

    timing = audit.get("timing", {}) if isinstance(audit, dict) else {}
    if timing:
        with st.expander("Performance profile"):
            st.caption("Timing only. This does not change Engine V0.2.1 math.")
            perf_rows = [
                {"Stage": "Historical input / prep", "Seconds": timing.get("historical_input_seconds")},
                {"Stage": "WoRP Engine — all seasons", "Seconds": timing.get("engine_total_seconds")},
                {"Stage": "Post-processing / editorial", "Seconds": timing.get("postprocess_seconds")},
                {"Stage": "Total", "Seconds": timing.get("total_seconds")},
            ]
            st.dataframe(pd.DataFrame(perf_rows), hide_index=True, use_container_width=True)
            by_season = timing.get("engine_by_season_seconds", {})
            if by_season:
                st.caption("Engine by season: " + " · ".join(f"{k}: {v:.2f}s" for k, v in by_season.items()))

    curve = curve[curve["position_rank"] <= int(top_n)].copy()
'''
if result_marker not in s:
    raise SystemExit("STOP: result/audit marker not found")
s = s.replace(result_marker, result_repl, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_7_3.py created")
print("Engine V0.2.1 unchanged")
print("Editorial: same-position elite + post-elite depth can synthesize into one curve-shape story")
print("Editorial: top-end cliff is suppressed when it is evidence for the same story")
print("Performance: stage timings added for input/prep, engine by season, post-processing, total")
