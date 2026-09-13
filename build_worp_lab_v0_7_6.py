from pathlib import Path

SRC = Path("app_v0_7_5.py")
DST = Path("app_v0_7_6.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_7_5.py not found. Run build_worp_lab_v0_7_5.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.7.5', 'UI V0.7.6')
s = s.replace('WoRP-Lab/0.7.5', 'WoRP-Lab/0.7.6')
s = s.replace('WoRP Lab UI V0.7.5', 'WoRP Lab UI V0.7.6')

# -----------------------------------------------------------------------------
# V0.7.6 — TASK 1: STORY-FIRST STRUCTURAL INSIGHTS
# Engine V0.2.1 math is untouched.
# This step changes candidate architecture: metrics become evidence for economic
# roster-construction stories. It deliberately does NOT attempt Task 2 whole-
# curve segmentation or research-gated Lineup Capture productization yet.
# -----------------------------------------------------------------------------

start = s.index('    candidates = []\n', s.index('    # Product layer'))
end = s.index('    audit = {', start)

new_editor = r'''    # -------------------------------------------------------------------------
    # Product layer V0.7.6 — STORY-FIRST EDITOR
    # Evidence -> structural hypothesis -> roster-construction story -> ranking.
    # A metric is never itself a headline. Engine V0.2.1 remains descriptive.
    # -------------------------------------------------------------------------
    story_candidates = []

    def _add_story(story_id, family, position, score, title, detail,
                   materiality, confidence, actionability, evidence=None):
        # Explicit product contract: every candidate must carry a decision story,
        # not merely a statistic. Scores are editorial ranking inputs, not claims.
        story_candidates.append({
            "story_id": str(story_id),
            "family": str(family),
            "position": str(position),
            "score": float(score),
            "materiality": float(materiality),
            "confidence": float(confidence),
            "actionability": float(actionability),
            "title": str(title),
            "detail": str(detail),
            "evidence": evidence or {},
        })

    # STORY A — ELITE CONCENTRATION + CHEAPER DEPTH
    # Synthesize head steepness and later marginal cost into one economic story.
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
            materiality = min(2.0, head)
            confidence = min(1.5, 0.80 + ratio * 0.12)
            actionability = 1.35
            _add_story(
                f"elite_then_depth:{pos}", "elite_depth", pos,
                materiality + confidence + actionability,
                f"Protect access to elite {pos}",
                (
                    f"The top of {pos} is expensive: {pos}1 to {pos}{elite_end} loses {head:.2f} WoRP. "
                    f"After that, the curve gets cheaper before replacement near {pos}{f}. "
                    "Prioritize access to the elite tier; be more selective paying for smaller upgrades behind it."
                ),
                materiality, confidence, actionability,
                {"head_drop": head, "head_end": elite_end, "frontier": f, "slope_ratio": ratio},
            )

    # STORY B — EXPENSIVE WAITING / PERSISTENT SCARCITY
    # The window scales with this league's own replacement frontier. This remains
    # a supporting heuristic until Task 2 replaces windows with whole-curve shape.
    runway = []
    for pos in positions:
        f = _frontier_rank(pos)
        if f is None or f < 12:
            continue
        a = min(8, max(1, int(round(f * 0.20))))
        b = min(f, max(a + 5, int(round(f * 0.70))))
        if b <= a:
            continue
        drop = _window_value(pos, a, b)
        if drop is not None:
            per10 = drop / max(1, b - a) * 10.0
            runway.append((pos, a, b, drop, per10, f))
    if runway:
        pos, a, b, drop, per10, f = max(runway, key=lambda z: z[4])
        if drop > 0:
            _add_story(
                f"waiting_cost:{pos}", "scarcity", pos,
                1.10 + min(per10, 2.0) * 0.85,
                f"Waiting at {pos} has been expensive",
                (
                    f"Across the relevant {pos} pool, moving from {pos}{a} to {pos}{b} gives up {drop:.2f} WoRP "
                    f"before replacement near {pos}{f}. This is a position where waiting has carried a real sporting cost."
                ),
                min(1.6, drop), 1.05, 1.25,
                {"start": a, "end": b, "drop": drop, "per10": per10, "frontier": f},
            )

    # STORY C — CHEAP MID-RANGE UPGRADES / CAPITAL EFFICIENCY PREVIEW
    # Sporting WoRP only: rank is NOT acquisition price. Keep the claim narrowly
    # about the historical marginal value purchased by moving up this curve.
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
            cost10 = drop / max(1, b - a) * 10.0
            compressions.append((pos, a, b, cost10, drop, f))
    if compressions:
        pos, a, b, cost10, drop, f = min(compressions, key=lambda z: z[3])
        if cost10 >= 0:
            cheapness = max(0.0, 1.25 - cost10)
            _add_story(
                f"cheap_midrange:{pos}", "capital_efficiency", pos,
                0.90 + cheapness,
                f"Mid-range {pos} upgrades buy relatively little WoRP",
                (
                    f"Between {pos}{a} and {pos}{b}, moving 10 ranks costs about {cost10:.2f} WoRP. "
                    "Historically, small upgrades in this part of the relevant pool have produced limited marginal value."
                ),
                min(1.2, cheapness + 0.35), 0.95, 1.10,
                {"start": a, "end": b, "cost_per_10": cost10, "frontier": f},
            )

    # STORY D — FORMAT-DRIVEN QB DEMAND
    # V0.7.5 slot-eligibility semantics are preserved. This story describes legal
    # starting capacity; it does not pretend every eligible slot will contain a QB.
    if int(superflex) > 0:
        f = _frontier_rank("QB")
        fixed_qb_per_team = int(qb)
        sf_per_team = int(superflex)
        qb_eligible_per_team = fixed_qb_per_team + sf_per_team
        qb_eligible_leaguewide = int(teams) * qb_eligible_per_team
        if f is not None:
            if fixed_qb_per_team == 0:
                title = "QB demand is created by flexible starter eligibility"
                detail = (
                    f"There are no fixed QB slots, but each team has {sf_per_team} QB-eligible flexible "
                    f"slot{'s' if sf_per_team != 1 else ''}. Historical replacement sits near QB{f}. "
                    "Build QB depth around where QBs can legally start, not around a traditional QB-slot count."
                )
            else:
                title = "QB depth is part of the starting lineup in this format"
                detail = (
                    f"Each team has {qb_eligible_per_team} QB-eligible starting slots "
                    f"({fixed_qb_per_team} fixed + {sf_per_team} flexible), while historical replacement sits near QB{f}. "
                    "Treat QB depth as lineup construction, not merely bench insurance."
                )
            pressure = max(0.0, f - qb_eligible_leaguewide) / max(int(teams), 1)
            _add_story(
                "format_qb_demand", "format_demand", "QB",
                3.20 + min(pressure, 2.0) * 0.20,
                title, detail,
                1.30, 1.30, 1.45,
                {"fixed_qb_per_team": fixed_qb_per_team, "sf_per_team": sf_per_team,
                 "qb_eligible_leaguewide": qb_eligible_leaguewide, "frontier": f},
            )

    # STORY E — FLEX ABSORPTION OF RB/WR/TE DEPTH
    # This is the first roster-utilization bridge, but deliberately limited to
    # legal capacity. It does NOT claim observed lineup capture or manager behavior.
    if int(flex) >= 3:
        wr_f, rb_f, te_f = _frontier_rank("WR"), _frontier_rank("RB"), _frontier_rank("TE")
        if wr_f is not None and rb_f is not None:
            flexible_capacity = int(flex)
            deeper_pos, deeper_f = ("WR", wr_f) if wr_f >= rb_f else ("RB", rb_f)
            _add_story(
                "flex_depth_absorption", "lineup_capacity", deeper_pos,
                2.75 + min(flexible_capacity, 8) * 0.10,
                "This lineup can turn skill-position depth into starters",
                (
                    f"Each team has {flexible_capacity} RB/WR/TE-eligible FLEX slot{'s' if flexible_capacity != 1 else ''}. "
                    f"Historical replacement reaches roughly WR{wr_f} and RB{rb_f}. "
                    "In this format, useful skill-position depth has more paths into the starting lineup instead of being automatically treated as bench depth."
                ),
                1.15, 1.20, 1.35,
                {"flex_per_team": flexible_capacity, "wr_frontier": wr_f,
                 "rb_frontier": rb_f, "te_frontier": te_f},
            )

    # STORY F — TE FORMAT DEMAND
    if int(te) >= 2 or float(sc.get("bonus_rec_te", 0.0)) > 0:
        f = _frontier_rank("TE")
        if f is not None:
            premium = float(sc.get("bonus_rec_te", 0.0))
            if int(te) >= 2 and premium > 0:
                title = "TE demand is reinforced by both lineup and scoring"
            elif int(te) >= 2:
                title = "Two-TE lineups deepen usable TE demand"
            else:
                title = "TE premium changes where TE value matters"
            _add_story(
                "format_te_demand", "format_demand", "TE",
                2.80 + min(int(te), 2) * 0.10 + (0.15 if premium > 0 else 0.0),
                title,
                (
                    f"Historical TE replacement sits near TE{f} under this league's scoring and lineup structure. "
                    "Evaluate TE depth against this league's demand rather than a generic 1TE format."
                ),
                1.10, 1.20, 1.25,
                {"te_slots": int(te), "te_premium": premium, "frontier": f},
            )

    # STORY G — RELEVANT VALUE CLIFF AS A ROSTER DECISION
    # Value Cliffs remains separately visible. Only the strongest pre-replacement
    # cliff may become a card, and only if it adds a distinct economic story.
    relevant_cliffs = []
    if cliff_df is not None and not cliff_df.empty:
        for _, r in cliff_df.iterrows():
            pos = str(r["position"])
            a, b = int(r["cliff_start_rank"]), int(r["cliff_end_rank"])
            if _relevant(pos, b):
                relevant_cliffs.append((pos, a, b, float(r["worp_drop"])))
    if relevant_cliffs:
        pos, a, b, drop = max(relevant_cliffs, key=lambda z: z[3])
        if drop >= 0.55:
            _add_story(
                f"cliff:{pos}", "cliff", pos,
                1.40 + drop,
                f"Avoid crossing the {pos}{a}–{pos}{b} value cliff cheaply",
                (
                    f"That short move gives up {drop:.2f} WoRP, the sharpest relevant cliff on this league's board. "
                    "If moving down through it, demand compensation for the historical value lost."
                ),
                min(1.6, drop), 1.15, 1.30,
                {"start": a, "end": b, "drop": drop},
            )

    # -------------------------------------------------------------------------
    # TASK-1 EDITORIAL GATE
    # This is intentionally simple and inspectable. Later backlog tasks will add
    # formal materiality, whole-curve segmentation and richer semantic dedupe.
    # -------------------------------------------------------------------------
    # One economic story ID = one candidate. If duplicate evidence created the
    # same story, retain the strongest version.
    best_by_story = {}
    for c in story_candidates:
        sid = c["story_id"]
        if sid not in best_by_story or c["score"] > best_by_story[sid]["score"]:
            best_by_story[sid] = c
    candidates = list(best_by_story.values())

    # Prevent the known QB duplication: when the league format itself explains
    # QB starting demand, a generic QB waiting-cost card is supporting evidence,
    # not a second headline story.
    if any(c["story_id"] == "format_qb_demand" for c in candidates):
        candidates = [
            c for c in candidates
            if not (c["position"] == "QB" and c["story_id"].startswith("waiting_cost:"))
        ]

    # Same principle for TE: format-driven demand outranks a generic mid-range TE
    # compression card when both would mostly tell the manager how to price TE in
    # this league. Value Cliffs remains separately visible below the cards.
    if any(c["story_id"] == "format_te_demand" for c in candidates):
        candidates = [
            c for c in candidates
            if not (c["position"] == "TE" and c["story_id"].startswith("cheap_midrange:"))
        ]

    # If a position already has the synthesized elite+depth story, suppress a
    # cliff card when that cliff is entirely inside the elite range; it is evidence
    # for the same story, not another card.
    elite_story_positions = {
        c["position"] for c in candidates if c["story_id"].startswith("elite_then_depth:")
    }
    filtered = []
    for c in candidates:
        if c["story_id"].startswith("cliff:") and c["position"] in elite_story_positions:
            ev = c.get("evidence", {})
            if int(ev.get("end", 999)) <= 8:
                continue
        filtered.append(c)
    candidates = filtered

    # Rank by the explicit editorial dimensions first; score breaks close ties.
    for c in candidates:
        c["editorial_score"] = (
            c["materiality"] * 0.40 +
            c["confidence"] * 0.25 +
            c["actionability"] * 0.35
        )

    candidates = sorted(
        candidates,
        key=lambda c: (c["editorial_score"], c["score"]),
        reverse=True,
    )

    # Exactly five cards remains the product contract. If fewer than five strong
    # story candidates exist, use the strongest remaining evidence rather than
    # fabricate a new semantic claim.
    structural_insights = candidates[:5]

'''

s = s[:start] + new_editor + s[end:]

# V0.7.4/V0.7.5 code after the candidate block may still construct the final
# cards from `candidates`. Replace only a direct old assignment if present so the
# story-first selection above remains authoritative.
s = s.replace('    structural_insights = candidates[:5]\n\n    audit = {',
              '    structural_insights = candidates[:5]\n\n    audit = {', 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_7_6.py created")
print("Engine V0.2.1 math unchanged")
print("TASK 1: Structural Insights now use a story-first candidate architecture")
print("Each candidate carries materiality, confidence, actionability and semantic story_id")
print("Known QB format/scarcity and TE format/compression duplicate stories are suppressed")
print("Lineup-capacity language is eligibility-only; no Lineup Capture result is generalized")
print("Task 2 whole-curve segmentation remains intentionally deferred")
