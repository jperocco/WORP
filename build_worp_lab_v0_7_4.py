from pathlib import Path

SRC = Path("app_v0_7_3.py")
DST = Path("app_v0_7_4.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_7_3.py not found. Run build_worp_lab_v0_7_3.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.7.3', 'UI V0.7.4')
s = s.replace('WoRP-Lab/0.7.3', 'WoRP-Lab/0.7.4')
s = s.replace('WoRP Lab UI V0.7.3', 'WoRP Lab UI V0.7.4')

# -----------------------------------------------------------------------------
# V0.7.4 FINAL SESSION BUILD
# 1) Preserve Engine V0.2.1 math.
# 2) Stop recomputing historical Monte Carlo for the same season + league
#    structure + scoring + simulation count. Persist exact season rankings.
# 3) Editorial relevance is bounded by the engine-native replacement frontier.
# 4) Candidate stories react to league format instead of always filling the same
#    five templates.
# -----------------------------------------------------------------------------

if 'import hashlib\n' not in s:
    s = s.replace('import json\n', 'import json\nimport hashlib\n', 1)

# Persistent season-result cache. Historical WoRP for a season is determined by
# historical weekly stats + scoring + roster format + engine settings; league_id
# itself is not part of the math.
calc_marker = '@st.cache_data(show_spinner=False)\ndef calculate_league_intelligence_cached('
cache_helper = '''ENGINE_CACHE_VERSION = "worp_engine_v0_2_1"
ENGINE_CACHE_DIR = Path.home() / ".worp_lab" / "season_rankings_v0_2_1"


def _season_ranking_cache_path(
    teams, qb, rb, wr, te, flex, superflex, scoring_json,
    season, n_sims, seed, replacement_band=6,
):
    payload = {
        "engine": ENGINE_CACHE_VERSION,
        "teams": int(teams), "qb": int(qb), "rb": int(rb), "wr": int(wr),
        "te": int(te), "flex": int(flex), "superflex": int(superflex),
        "scoring_json": scoring_json,
        "season": int(season), "n_sims": int(n_sims), "seed": int(seed),
        "replacement_band": int(replacement_band),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:24]
    ENGINE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return ENGINE_CACHE_DIR / f"{int(season)}_{digest}.pkl"


@st.cache_data(show_spinner=False)
def calculate_league_intelligence_cached('''
if calc_marker not in s:
    raise SystemExit("STOP: calculate cache marker not found")
s = s.replace(calc_marker, cache_helper, 1)

# Replace the V0.7.3 season-calculation loop. If all requested seasons already
# exist on disk, Sleeper history is not fetched and Monte Carlo is not rerun.
load_start = s.index('    all_weeks, endpoint_log = load_scored_history_cached(tuple(seasons), scoring_json)')
post_marker = '    t_after_engine = time.perf_counter()\n\n    # Rank-average positional curve:'
load_end = s.index(post_marker, load_start)
new_load = '''    rankings = {}
    engine_timings = []
    cache_hits = {}
    cache_paths = {}

    for season_i in seasons:
        cache_paths[int(season_i)] = _season_ranking_cache_path(
            teams, qb, rb, wr, te, flex, superflex, scoring_json,
            int(season_i), int(n_sims), int(seed), replacement_band=6,
        )

    missing_seasons = []
    for season_i in seasons:
        season_i = int(season_i)
        path = cache_paths[season_i]
        if path.exists():
            try:
                ranking = pd.read_pickle(path)
                rankings[season_i] = ranking
                cache_hits[season_i] = True
            except Exception:
                missing_seasons.append(season_i)
                cache_hits[season_i] = False
        else:
            missing_seasons.append(season_i)
            cache_hits[season_i] = False

    if missing_seasons:
        all_weeks, endpoint_log = load_scored_history_cached(tuple(seasons), scoring_json)
        t_after_load = time.perf_counter()
        for season_i in missing_seasons:
            season_df = all_weeks[all_weeks["season"] == int(season_i)].copy()
            t_engine0 = time.perf_counter()
            _weekly, ranking = calculate_season_worp(
                season_df,
                settings,
                replacement_band=6,
                n_sims=int(n_sims),
                seed=int(seed),
            )
            engine_timings.append((int(season_i), time.perf_counter() - t_engine0))
            ranking = ranking.copy()
            ranking["season"] = int(season_i)
            ranking["position_rank"] = (
                ranking.groupby("position")["worp"]
                .rank(method="first", ascending=False)
                .astype(int)
            )
            rankings[int(season_i)] = ranking
            try:
                ranking.to_pickle(cache_paths[int(season_i)])
            except Exception:
                pass
    else:
        # Fully warm historical configuration: no Sleeper fetch, no Monte Carlo.
        all_weeks = pd.DataFrame()
        endpoint_log = {}
        t_after_load = time.perf_counter()

    t_after_engine = time.perf_counter()

    # Rank-average positional curve:'''
s = s[:load_start] + new_load + s[load_end + len(post_marker):]

# Replace the complete editorial candidate engine with a league-aware version.
editor_start = s.index('    # Product layer V0.7.1:')
editor_end = s.index('    audit = {', editor_start)
new_editor = '''    # Product layer V0.7.4: league-aware story editor.
    # The engine remains descriptive/historical. The editor is allowed to publish
    # only economically relevant ranges at or before the observed replacement frontier.
    def _value_at(pos, rank):
        row = curve[(curve["position"] == pos) & (curve["position_rank"] == int(rank))]
        if row.empty:
            return None
        return float(row.iloc[0]["three_year_worp_avg"])

    positions = ["QB", "RB", "WR", "TE"]

    # Engine-native relevance frontier. This is NOT a universal positional cutoff:
    # it is derived from this league format and these historical seasons.
    frontier_samples = {p: [] for p in positions}
    for _season_i, _ranking in rankings.items():
        if "avg_replacement_effective_rank" not in _ranking.columns:
            continue
        for pos in positions:
            vals = pd.to_numeric(
                _ranking.loc[_ranking["position"] == pos, "avg_replacement_effective_rank"],
                errors="coerce",
            ).dropna()
            if not vals.empty:
                frontier_samples[pos].append(float(vals.median()))

    frontier_by_pos = {
        pos: (sum(vals) / len(vals) if vals else None)
        for pos, vals in frontier_samples.items()
    }

    def _frontier_rank(pos):
        f = frontier_by_pos.get(pos)
        return None if f is None else max(1, int(round(f)))

    def _relevant(pos, end_rank):
        f = _frontier_rank(pos)
        return f is None or int(end_rank) <= f

    def _window_value(pos, a, b):
        va, vb = _value_at(pos, a), _value_at(pos, b)
        if va is None or vb is None:
            return None
        return float(va - vb)

    candidates = []

    # A) Full curve-shape stories. Detect a steep head followed by materially
    # cheaper depth, rather than publishing two cards about the same position.
    for pos in positions:
        f = _frontier_rank(pos)
        if f is None or f < 12:
            continue
        elite_end = min(8, f)
        post_end = min(f, max(12, int(round(f * 0.45))))
        head = _window_value(pos, 1, elite_end)
        post = _window_value(pos, elite_end, post_end)
        if head is None or post is None or post_end <= elite_end:
            continue
        head_per_rank = head / max(1, elite_end - 1)
        post_per_rank = post / max(1, post_end - elite_end)
        ratio = head_per_rank / max(post_per_rank, 0.01)
        if head >= 0.70 and ratio >= 1.55:
            candidates.append({
                "family": "curve_shape", "position": pos,
                "score": head + min(ratio, 4.0) * 0.18,
                "title": f"{pos} is a stars-and-depth position",
                "detail": (
                    f"{pos} separates sharply at the top ({head:.2f} WoRP from {pos}1 to {pos}{elite_end}), "
                    f"then the curve gets cheaper before the league-specific replacement frontier near {pos}{f}. "
                    "Protect access to the stars; be more selective paying for the next step down."
                ),
            })

    # B) Relevant short-range cliff. Anything beyond replacement is excluded from
    # the five-card editor even though it may remain visible in Value Cliffs/data.
    relevant_cliffs = []
    if cliff_df is not None and not cliff_df.empty:
        for _, r in cliff_df.iterrows():
            pos = str(r["position"])
            a, b = int(r["cliff_start_rank"]), int(r["cliff_end_rank"])
            if _relevant(pos, b):
                relevant_cliffs.append((pos, a, b, float(r["worp_drop"])))
    if relevant_cliffs:
        pos, a, b, drop = max(relevant_cliffs, key=lambda z: z[3])
        candidates.append({
            "family": "cliff", "position": pos,
            "score": drop * 1.10,
            "title": f"Don’t trade down through {pos}{a}–{pos}{b} lightly",
            "detail": f"That five-rank stretch costs {drop:.2f} WoRP — the sharpest relevant short-range drop on this league’s board."
        })

    # C) League-relative waiting cost. Window scales with this position's own
    # replacement frontier instead of hard-coding QB8->QB20 for every league.
    runway = []
    for pos in positions:
        f = _frontier_rank(pos)
        if f is None or f < 12:
            continue
        a = min(8, max(1, int(round(f * 0.20))))
        b = max(a + 5, int(round(f * 0.70)))
        b = min(b, f)
        if b <= a:
            continue
        drop = _window_value(pos, a, b)
        if drop is not None:
            per10 = drop / (b - a) * 10.0
            runway.append((pos, a, b, drop, per10, f))
    if runway:
        pos, a, b, drop, per10, f = max(runway, key=lambda z: z[4])
        candidates.append({
            "family": "scarcity_runway", "position": pos,
            "score": per10 * 0.85,
            "title": f"{pos} scarcity carries deeper in this league",
            "detail": (
                f"From {pos}{a} to {pos}{b}, the curve gives up {drop:.2f} WoRP before replacement near {pos}{f}. "
                "Waiting through this part of the board has been relatively expensive."
            ),
        })

    # D) Mid-curve compression inside the relevant player pool only.
    compressions = []
    for pos in positions:
        f = _frontier_rank(pos)
        if f is None or f < 16:
            continue
        a = max(8, int(round(f * 0.35)))
        b = min(f, max(a + 6, int(round(f * 0.70))))
        if b <= a or not _relevant(pos, b):
            continue
        drop = _window_value(pos, a, b)
        if drop is not None:
            cost10 = drop / (b - a) * 10.0
            compressions.append((pos, a, b, cost10, f))
    if compressions:
        pos, a, b, cost10, f = min(compressions, key=lambda z: z[3])
        candidates.append({
            "family": "compression", "position": pos,
            "score": max(0.0, 0.95 - cost10),
            "title": f"Be selective paying for mid-range {pos} upgrades",
            "detail": (
                f"Inside the relevant pool ({pos}{a}–{pos}{b}), each 10 ranks costs only about {cost10:.2f} WoRP. "
                "Small rank upgrades here have carried limited historical value."
            ),
        })

    # E) Format-specific stories. These exist only when the league settings make
    # them relevant, which prevents every league from receiving the same five cards.
    if int(superflex) > 0:
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

    if int(te) >= 2 or float(sc.get("bonus_rec_te", 0.0)) > 0:
        f = _frontier_rank("TE")
        fixed_te = int(teams) * int(te)
        if f is not None:
            premium = float(sc.get("bonus_rec_te", 0.0))
            label = "2TE/TEP keeps more TE value in play" if int(te) >= 2 and premium > 0 else (
                "Two-TE lineups keep more TE value in play" if int(te) >= 2 else "TE premium changes the TE value curve"
            )
            candidates.append({
                "family": "format_te", "position": "TE",
                "score": 1.10 + min(max(f - fixed_te, 0) / max(int(teams), 1), 2.0) * 0.12,
                "title": label,
                "detail": (
                    f"The league-specific TE replacement frontier sits near TE{f}. "
                    "Read TE prices against this format’s deeper demand, not against a generic 1TE league."
                ),
            })

    if int(flex) >= 3:
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

    # F) Replacement-frontier contrast can surface a structurally unusual position.
    frontier_rows = [(p, _frontier_rank(p)) for p in positions if _frontier_rank(p) is not None]
    if frontier_rows:
        pos, f = max(frontier_rows, key=lambda z: z[1])
        candidates.append({
            "family": "replacement_frontier", "position": pos,
            "score": 0.70,
            "title": f"{pos} has the deepest relevant player pool in this format",
            "detail": f"The historical replacement frontier lands near {pos}{f}. Use that as league-specific depth context — not as a universal waiver line.",
        })

    # Editorial selection: one economic story per family, max two cards per position,
    # and suppress a cliff when a stronger same-position curve-shape story already
    # explains that exact top-end behavior.
    ranked = sorted(candidates, key=lambda d: d["score"], reverse=True)
    chosen, family_seen, pos_count = [], set(), {}
    curve_shape_positions = {c["position"] for c in ranked if c["family"] == "curve_shape"}

    for item in ranked:
        if item["family"] in family_seen:
            continue
        pos = item["position"]
        if item["family"] == "cliff" and pos in curve_shape_positions:
            # The raw cliff stays visible below; don't spend a second headline on it.
            continue
        if pos_count.get(pos, 0) >= 2:
            continue
        chosen.append(item)
        family_seen.add(item["family"])
        pos_count[pos] = pos_count.get(pos, 0) + 1
        if len(chosen) == 5:
            break

    # Fill only with distinct remaining stories. No deep/off-frontier fallback.
    if len(chosen) < 5:
        for item in ranked:
            if item["family"] in family_seen or item in chosen:
                continue
            pos = item["position"]
            if pos_count.get(pos, 0) >= 2:
                continue
            chosen.append(item)
            family_seen.add(item["family"])
            pos_count[pos] = pos_count.get(pos, 0) + 1
            if len(chosen) == 5:
                break

    insight_df = pd.DataFrame(chosen[:5])

'''
s = s[:editor_start] + new_editor + s[editor_end:]

# Audit: warm/cold season cache status. Keep timing internal; remove the broken
# frontend performance-profile expander from the product UI.
s = s.replace('        "rows": int(len(all_weeks)),', '        "rows": (int(len(all_weeks)) if not all_weeks.empty else None),')
audit_insert = '''        "engine_cache": {
            "version": ENGINE_CACHE_VERSION,
            "season_hits": {str(k): bool(v) for k, v in cache_hits.items()},
            "missing_seasons_computed": [int(x) for x in missing_seasons],
        },
'''
needle = '        "replacement_band": 6,\n'
if needle not in s:
    raise SystemExit("STOP: audit replacement-band marker not found")
s = s.replace(needle, needle + audit_insert, 1)

profile_start = s.find('    timing = audit.get("timing", {}) if isinstance(audit, dict) else {}')
if profile_start != -1:
    profile_end_marker = '    curve = curve[curve["position_rank"] <= int(top_n)].copy()'
    profile_end = s.index(profile_end_marker, profile_start)
    s = s[:profile_start] + profile_end_marker + s[profile_end + len(profile_end_marker):]

# Product copy: Monte Carlo is engine methodology, not something users should
# have to think about as the primary workflow. Keep the control available but
# explain that exact season/config results are persisted after first calculation.
old_help = 'help="4,000 is the standard product mode. 8,000 remains the validated control setting.",'
new_help = 'help="Historical results are persisted by scoring + format + season after the first calculation. 8,000 remains the validated control setting.",'
s = s.replace(old_help, new_help)

# Remove any stale performance caption if present.
s = s.replace('st.caption("Performance: 4,000 simulations is the standard product mode; 8,000 remains available for validated-control reruns. Repeated runs reuse cached historical Sleeper inputs.")\n', '')

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_7_4.py created")
print("Engine V0.2.1 math unchanged")
print("Performance: exact season rankings persist by scoring + format + season + simulation count")
print("Performance: warm configurations skip Sleeper history and Monte Carlo entirely")
print("Editorial: Structural Insights cannot use ranges beyond the league-native replacement frontier")
print("Editorial: format-specific SF / 2TE-TEP / flex-heavy stories can enter the Top 5")
print("Frontend: Value Cliffs retained; broken Performance profile removed")
