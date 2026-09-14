from pathlib import Path

SRC = Path("app_v0_8_5.py")
DST = Path("app_v0_9_0.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_8_5.py not found. Run build_worp_lab_v0_8_5.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.8.5', 'UI V0.9.0')
s = s.replace('WoRP-Lab/0.8.5', 'WoRP-Lab/0.9.0')
s = s.replace('WoRP Lab UI V0.8.5', 'WoRP Lab UI V0.9.0')

# V0.9.0 changes the publication editor, not Engine V0.2.1.
# Evidence -> decision thesis -> Top 5.
old = '''    structural_insights = final_cards[:5]\n'''
if old not in s:
    raise SystemExit("STOP: V0.8.5 publication line not found")

new = r'''    # -------------------------------------------------------------------------
    # V0.9.0 DECISION-THESIS EDITOR
    # -------------------------------------------------------------------------
    # The frontend publishes manager decisions, not independent metrics. Evidence
    # that points to the same positional roster-construction decision is absorbed
    # into one thesis before the final Top 5 is selected.
    pool = []
    seen = set()
    for c in list(final_cards) + list(candidates) + list(story_candidates):
        sid = c.get("story_id")
        if not sid or sid in seen:
            continue
        seen.add(sid)
        if float(c.get("materiality", 0.0) or 0.0) < 0.90:
            continue
        if float(c.get("confidence", 0.0) or 0.0) < 0.90:
            continue
        if float(c.get("actionability", 0.0) or 0.0) < 1.00:
            continue
        if sid in {"flex_depth_absorption", "format_te_demand"}:
            continue
        if "editorial_score" not in c:
            c["editorial_score"] = (
                float(c.get("materiality", 0.0)) * 0.40 +
                float(c.get("confidence", 0.0)) * 0.25 +
                float(c.get("actionability", 0.0)) * 0.35
            )
        pool.append(c)

    ids = {c.get("story_id") for c in pool}

    # Canonical theses already synthesized upstream absorb supporting evidence.
    absorbed = set()
    if "rb_top_and_depth_synth" in ids:
        absorbed.update({
            "crosspos_elite_preference", "crosspos_elite_priority",
            "crosspos_equivalence_rb_wr", "crosspos_flex_preference",
            "elite_then_depth:RB",
        })
        # RB-vs-TE equivalence is also supporting evidence for the same broad
        # RB depth thesis when RB is the leading side of that card.
        for c in pool:
            if (c.get("family") == "cross_position_equivalence"
                    and c.get("position") == "RB"):
                absorbed.add(c.get("story_id"))

    if "wr_elite_and_midrange_synth" in ids:
        absorbed.update({"elite_then_depth:WR", "cheap_midrange:WR"})

    # QB: if format demand and/or a prior QB synthesis exists, waiting-cost and
    # elite-depth QB facts support that same lineup-construction decision rather
    # than consuming additional cards.
    qb_anchor = None
    for preferred in ("qb_roster_construction_synth", "format_qb_demand"):
        qb_anchor = next((c for c in pool if c.get("story_id") == preferred), None)
        if qb_anchor is not None:
            break
    if qb_anchor is not None:
        qb_support = [
            c for c in pool
            if c.get("position") == "QB"
            and c.get("story_id") in {"waiting_cost:QB", "elite_then_depth:QB"}
        ]
        absorbed.update({c.get("story_id") for c in qb_support})
        if qb_anchor.get("story_id") == "format_qb_demand" and qb_support:
            support = max(qb_support, key=lambda c: float(c.get("editorial_score", 0.0) or 0.0))
            ev = support.get("evidence", {}) or {}
            start = int(ev.get("start", 0) or 0)
            end = int(ev.get("end", 0) or 0)
            drop = float(ev.get("drop", 0.0) or 0.0)
            base_detail = str(qb_anchor.get("detail", ""))
            extra = ""
            if start > 0 and end > start and drop > 0:
                extra = f" Historically, moving from QB{start} to QB{end} also gives up {drop:.2f} WoRP."
            qb_anchor = dict(qb_anchor)
            qb_anchor["story_id"] = "qb_roster_construction_synth"
            qb_anchor["family"] = "roster_construction"
            qb_anchor["title"] = "QB requires both starting depth and timely access here"
            qb_anchor["detail"] = base_detail + extra
            qb_anchor["materiality"] = max(float(qb_anchor.get("materiality", 0.0)), 1.45)
            qb_anchor["confidence"] = max(float(qb_anchor.get("confidence", 0.0)), 1.30)
            qb_anchor["actionability"] = max(float(qb_anchor.get("actionability", 0.0)), 1.55)
            qb_anchor["editorial_score"] = 1.448
            absorbed.add("format_qb_demand")
            pool.append(qb_anchor)

    # RB elite priority + elite-depth are the same decision even when the stronger
    # top+depth synthesis did not trigger.
    rb_elite = next((c for c in pool if c.get("story_id") == "crosspos_elite_priority" and c.get("position") == "RB"), None)
    rb_depth = next((c for c in pool if c.get("story_id") == "elite_then_depth:RB"), None)
    if rb_elite is not None and rb_depth is not None and "rb_top_and_depth_synth" not in ids:
        eve = rb_depth.get("evidence", {}) or {}
        head = float(eve.get("head_drop", 0.0) or 0.0)
        end = int(eve.get("head_end", 8) or 8)
        frontier = int(eve.get("frontier", 0) or 0)
        merged = dict(rb_elite)
        merged["story_id"] = "rb_elite_access_synth"
        merged["family"] = "roster_construction"
        merged["title"] = "Prioritize elite RB access"
        merged["detail"] = (
            str(rb_elite.get("detail", "")) +
            (f" RB1 to RB{end} also loses {head:.2f} WoRP" if head > 0 else "") +
            (f" before replacement near RB{frontier}." if frontier > 0 else ".")
        )
        merged["materiality"] = max(float(rb_elite.get("materiality", 0.0)), 1.50)
        merged["confidence"] = max(float(rb_elite.get("confidence", 0.0)), 1.30)
        merged["actionability"] = max(float(rb_elite.get("actionability", 0.0)), 1.55)
        merged["editorial_score"] = 1.475
        absorbed.update({"crosspos_elite_priority", "elite_then_depth:RB"})
        pool.append(merged)

    thesis_pool = [c for c in pool if c.get("story_id") not in absorbed]

    # One semantic thesis per story ID, strongest representation wins.
    best = {}
    for c in thesis_pool:
        sid = c.get("story_id")
        if sid not in best or float(c.get("editorial_score", 0.0)) > float(best[sid].get("editorial_score", 0.0)):
            best[sid] = c
    thesis_pool = list(best.values())

    # Rank after synthesis. Do not force positional diversity; five strongest
    # distinct manager decisions win.
    thesis_pool = sorted(
        thesis_pool,
        key=lambda c: (float(c.get("editorial_score", 0.0)), float(c.get("score", 0.0))),
        reverse=True,
    )

    structural_insights = thesis_pool[:5]
'''

s = s.replace(old, new, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_9_0.py created")
print("Engine V0.2.1 math unchanged")
print("Structural Insights now publish decision theses rather than metric-level cards")
print("RB, WR, and QB supporting evidence is absorbed before Top-5 ranking")
print("No forced positional diversity and no new WoRP/market/predictive claim introduced")
