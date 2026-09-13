from pathlib import Path

SRC = Path("app_v0_7_8.py")
DST = Path("app_v0_7_9.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_7_8.py not found. Run build_worp_lab_v0_7_8.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.7.8', 'UI V0.7.9')
s = s.replace('WoRP-Lab/0.7.8', 'WoRP-Lab/0.7.9')
s = s.replace('WoRP Lab UI V0.7.8', 'WoRP Lab UI V0.7.9')

# -----------------------------------------------------------------------------
# V0.7.9 — DECISION-RELEVANCE EDITOR
# Engine V0.2.1 math untouched.
#
# Goals:
# 1) Prefer interpositional equivalences that map to frequent shared-slot
#    decisions, rather than simply the largest positional-rank gap.
# 2) Turn FLEX format facts into a position-specific economic consequence.
# 3) Collapse QB format-demand + elite-QB concentration into one QB roster story
#    when both are present.
# -----------------------------------------------------------------------------

marker = '''    # Rank by the explicit editorial dimensions first; score breaks close ties.\n'''
if marker not in s:
    raise SystemExit("STOP: editorial ranking marker not found in V0.7.8")

insert = r'''    # -------------------------------------------------------------------------
    # V0.7.9 DECISION-RELEVANCE EDITOR
    # -------------------------------------------------------------------------
    # Shared-slot decision relevance is an editorial prior, not a WoRP claim.
    # RB/WR decisions are most directly recurrent in FLEX roster construction;
    # TE participates too, but dedicated TE demand makes a pure rank-gap less
    # automatically transferable. We therefore reward shared FLEX competition
    # and material equivalence, while still allowing TE stories to win when the
    # economic evidence is clearly stronger.
    pair_relevance = {
        frozenset(("RB", "WR")): 1.00,
        frozenset(("RB", "TE")): 0.82,
        frozenset(("WR", "TE")): 0.82,
    }

    # Re-score equivalence candidates using decision relevance rather than raw
    # rank-gap spectacle. The V0.7.8 candidate stores the pair and equivalence
    # evidence; if field names evolve, use conservative defaults rather than
    # inventing evidence.
    for c in candidates:
        if c.get("family") != "cross_position_equivalence":
            continue
        ev = c.get("evidence", {}) or {}
        p1 = str(ev.get("position_a", ev.get("deeper_position", c.get("position", ""))))
        p2 = str(ev.get("position_b", ev.get("shallower_position", "")))
        relevance = pair_relevance.get(frozenset((p1, p2)), 0.70)
        gap = abs(float(ev.get("rank_gap", 0.0) or 0.0))
        worp_gap = abs(float(ev.get("worp_gap", 0.0) or 0.0))
        # Equivalence quality: smaller WoRP mismatch is better. Rank gap matters,
        # but only after decision relevance; huge gaps do not automatically win.
        equivalence_quality = max(0.0, 1.0 - min(worp_gap, 0.25) / 0.25)
        c["decision_relevance"] = relevance
        c["editorial_score"] = (
            c.get("materiality", 1.0) * 0.30 +
            c.get("confidence", 1.0) * 0.20 +
            c.get("actionability", 1.0) * 0.25 +
            relevance * 0.20 +
            equivalence_quality * 0.05
        )
        c["score"] = float(c.get("score", 0.0)) + relevance * 0.55 + min(gap, 20.0) * 0.01

    # Build a specifically RB-vs-WR equivalence candidate when both positions
    # share FLEX eligibility and a material cross-rank equivalence exists. This
    # prevents a larger but less recurrent RB-vs-TE rank gap from monopolizing
    # the equivalence slot merely because the number is bigger.
    if int(flex) > 0:
        rb_f = _frontier_rank("RB")
        wr_f = _frontier_rank("WR")
        if rb_f is not None and wr_f is not None:
            # Search the full relevant curves. For each deeper RB rank, find the
            # closest WR WoRP and retain a material, close equivalence. Avoid the
            # elite band already covered by the elite-priority story.
            rbwr_matches = []
            for rb_rank in range(9, int(rb_f) + 1):
                rb_val = _value_at("RB", rb_rank)
                if rb_val is None:
                    continue
                best = None
                for wr_rank in range(1, int(wr_f) + 1):
                    wr_val = _value_at("WR", wr_rank)
                    if wr_val is None:
                        continue
                    diff = abs(float(rb_val) - float(wr_val))
                    if best is None or diff < best[0]:
                        best = (diff, wr_rank, float(wr_val))
                if best is None:
                    continue
                diff, wr_rank, wr_val = best
                rank_gap = rb_rank - wr_rank
                # We want meaningful cross-rank equivalence, not RB17 ~= WR16.
                if rank_gap >= 6 and diff <= 0.08:
                    # Prefer a large but roster-relevant gap, with an anchor that
                    # remains inside both replacement frontiers.
                    strength = rank_gap * 0.08 + max(0.0, 0.08 - diff) * 4.0
                    rbwr_matches.append((strength, rb_rank, float(rb_val), wr_rank, wr_val, diff, rank_gap))

            if rbwr_matches:
                _, rb_rank, rb_val, wr_rank, wr_val, diff, rank_gap = max(rbwr_matches, key=lambda x: x[0])
                _add_story(
                    "crosspos_equivalence_rb_wr", "cross_position_equivalence", "RB",
                    5.15 + min(rank_gap, 20) * 0.03,
                    f"RB{rb_rank} has carried roughly WR{wr_rank} value",
                    (
                        f"RB{rb_rank} ({rb_val:.2f} WoRP) is roughly equivalent to WR{wr_rank} ({wr_val:.2f} WoRP). "
                        f"The same historical value survives about {rank_gap} positional ranks deeper at RB. "
                        "Because RB and WR compete directly for FLEX capacity, do not assume the deeper RB is the lesser roster asset."
                    ),
                    min(1.8, 1.05 + rank_gap * 0.025), 1.30, 1.60,
                    {"position_a": "RB", "position_b": "WR", "deeper_position": "RB",
                     "shallower_position": "WR", "deeper_rank": rb_rank,
                     "shallower_rank": wr_rank, "rank_gap": rank_gap,
                     "worp_a": rb_val, "worp_b": wr_val, "worp_gap": diff,
                     "shared_slot": "FLEX", "decision_relevance": 1.0},
                )

    # Rebuild story-ID map after adding the decision-relevant equivalence.
    best_by_story = {}
    for c in candidates + [c for c in story_candidates if c.get("story_id") == "crosspos_equivalence_rb_wr"]:
        sid = c["story_id"]
        if sid not in best_by_story or c.get("score", 0.0) > best_by_story[sid].get("score", 0.0):
            best_by_story[sid] = c
    candidates = list(best_by_story.values())

    # If a strong RB/WR equivalence exists, generic FLEX-capacity copy is no
    # longer allowed to consume a Top-5 slot. The equivalence itself explains
    # which depth the lineup can exploit and why.
    has_rbwr_equivalence = any(c.get("story_id") == "crosspos_equivalence_rb_wr" for c in candidates)
    if has_rbwr_equivalence:
        candidates = [c for c in candidates if c.get("story_id") != "flex_depth_absorption"]
        # Same-rank FLEX preference is also weaker evidence than cross-rank
        # economic equivalence; keep one economic story = one card.
        candidates = [c for c in candidates if c.get("story_id") != "crosspos_flex_preference"]

    # QB semantic synthesis: in SF, "QB depth is part of the lineup" and
    # "protect elite QB" can be two pieces of one roster-construction story.
    qb_format = next((c for c in candidates if c.get("story_id") == "format_qb_demand"), None)
    qb_elite = next((c for c in candidates if c.get("story_id") == "elite_then_depth:QB"), None)
    if qb_format is not None and qb_elite is not None:
        evf = qb_format.get("evidence", {}) or {}
        eve = qb_elite.get("evidence", {}) or {}
        fixed_qb = int(evf.get("fixed_qb_per_team", int(qb)))
        sf_qb = int(evf.get("sf_per_team", int(superflex)))
        eligible = fixed_qb + sf_qb
        frontier = evf.get("frontier", _frontier_rank("QB"))
        head_drop = float(eve.get("head_drop", 0.0) or 0.0)
        head_end = int(eve.get("head_end", 8) or 8)
        candidates = [
            c for c in candidates
            if c.get("story_id") not in {"format_qb_demand", "elite_then_depth:QB"}
        ]
        _add_story(
            "qb_roster_construction_synth", "roster_construction", "QB",
            4.75 + min(head_drop, 1.5) * 0.15,
            "QB requires both top-end access and starting depth here",
            (
                f"Each team can start a QB in {eligible} lineup slots, while historical replacement sits near QB{frontier}. "
                f"The QB1–QB{head_end} segment also loses {head_drop:.2f} WoRP. "
                "This format rewards securing a strong QB anchor without treating the second startable QB as mere bench insurance."
            ),
            1.45, 1.30, 1.55,
            {"qb_eligible_per_team": eligible, "frontier": frontier,
             "head_drop": head_drop, "head_end": head_end},
        )
        synth = [c for c in story_candidates if c.get("story_id") == "qb_roster_construction_synth"]
        candidates.extend(synth[-1:])

'''

s = s.replace(marker, insert + marker, 1)

# V0.7.9 ranking must respect a precomputed decision-relevance editorial score.
old_rank_block = '''    for c in candidates:\n        c["editorial_score"] = (\n            c["materiality"] * 0.40 +\n            c["confidence"] * 0.25 +\n            c["actionability"] * 0.35\n        )\n'''
new_rank_block = '''    for c in candidates:\n        if "editorial_score" not in c:\n            c["editorial_score"] = (\n                c["materiality"] * 0.40 +\n                c["confidence"] * 0.25 +\n                c["actionability"] * 0.35\n            )\n'''
if old_rank_block not in s:
    raise SystemExit("STOP: expected V0.7.8 editorial score block not found")
s = s.replace(old_rank_block, new_rank_block, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_7_9.py created")
print("Engine V0.2.1 math unchanged")
print("Decision-Relevance Editor added")
print("RB/WR cross-rank equivalence receives explicit shared-FLEX decision relevance")
print("Generic FLEX-capacity fact is suppressed when a stronger RB/WR equivalence exists")
print("QB format-demand + elite-QB stories are synthesized when both are present")
print("No ADP, market-price, waiver, or predictive claim introduced")
