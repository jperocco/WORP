from pathlib import Path

SRC = Path("app_v0_8_4.py")
DST = Path("app_v0_8_5.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_8_4.py not found. Run build_worp_lab_v0_8_4.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.8.4', 'UI V0.8.5')
s = s.replace('WoRP-Lab/0.8.4', 'WoRP-Lab/0.8.5')
s = s.replace('WoRP Lab UI V0.8.4', 'WoRP Lab UI V0.8.5')

# -----------------------------------------------------------------------------
# V0.8.5 — FINAL PUBLICATION-GATE WR SYNTHESIS HOTFIX
# Engine V0.2.1 math untouched.
#
# V0.8.4 attempted WR synthesis before the final publication contract, but the
# visible Top 5 still contained both WR evidence cards. This hotfix operates on
# the actual five cards immediately before publication, so the merge cannot be
# undone by later editorial/reserve logic.
# -----------------------------------------------------------------------------

old = '''    structural_insights = candidates[:5]\n'''
if old not in s:
    raise SystemExit("STOP: final structural_insights publication line not found")

new = r'''    # V0.8.5 final publication gate.
    # Work on the actual visible five cards. If both WR evidence cards survived
    # every earlier editorial stage, merge them here into one roster-construction
    # story and fill the freed slot only with an already-generated distinct story.
    final_cards = list(candidates[:5])
    final_ids = {c.get("story_id") for c in final_cards}

    if {
        "elite_then_depth:WR",
        "cheap_midrange:WR",
    }.issubset(final_ids):
        elite_wr = next(c for c in final_cards if c.get("story_id") == "elite_then_depth:WR")
        cheap_wr = next(c for c in final_cards if c.get("story_id") == "cheap_midrange:WR")
        eve = elite_wr.get("evidence", {}) or {}
        evm = cheap_wr.get("evidence", {}) or {}

        head_drop = float(eve.get("head_drop", 0.0) or 0.0)
        head_end = int(eve.get("head_end", 8) or 8)
        frontier = int(eve.get("frontier", evm.get("frontier", 0)) or 0)
        mid_start = int(evm.get("start", 0) or 0)
        mid_end = int(evm.get("end", 0) or 0)
        cost10 = float(evm.get("cost_per_10", 0.0) or 0.0)

        if head_drop > 0 and mid_start > 0 and mid_end > mid_start:
            merged = {
                "story_id": "wr_elite_and_midrange_synth",
                "family": "roster_construction",
                "position": "WR",
                "score": 6.00,
                "materiality": 1.70,
                "confidence": 1.40,
                "actionability": 1.60,
                "editorial_score": 1.585,
                "title": "Pay for elite WR access; be selective in the middle",
                "detail": (
                    f"WR1 to WR{head_end} loses {head_drop:.2f} WoRP, so the top of the position has carried real historical separation. "
                    f"But between WR{mid_start} and WR{mid_end}, moving 10 ranks changes only about {cost10:.2f} WoRP. "
                    + (f"With replacement near WR{frontier}, " if frontier > 0 else "")
                    + "this league has rewarded securing elite WR access more than paying repeatedly for small mid-range upgrades."
                ),
                "evidence": {
                    "head_drop": head_drop,
                    "head_end": head_end,
                    "mid_start": mid_start,
                    "mid_end": mid_end,
                    "cost_per_10": cost10,
                    "frontier": frontier,
                },
            }

            # Preserve the earlier of the two WR cards as the position of the
            # synthesized story, remove both evidence cards, and keep ordering
            # stable for every other visible recommendation.
            first_idx = min(
                i for i, c in enumerate(final_cards)
                if c.get("story_id") in {"elite_then_depth:WR", "cheap_midrange:WR"}
            )
            final_cards = [
                c for c in final_cards
                if c.get("story_id") not in {"elite_then_depth:WR", "cheap_midrange:WR"}
            ]
            final_cards.insert(first_idx, merged)

            # Fill only from already-generated editorial candidates. Do not
            # reintroduce evidence absorbed by a synthesis or generic format facts.
            visible_ids = {c.get("story_id") for c in final_cards}
            blocked_ids = {
                "elite_then_depth:WR", "cheap_midrange:WR",
                "flex_depth_absorption", "format_te_demand",
            }
            if "rb_top_and_depth_synth" in visible_ids:
                blocked_ids.update({
                    "crosspos_elite_preference", "crosspos_elite_priority",
                    "crosspos_equivalence_rb_wr", "crosspos_flex_preference",
                    "elite_then_depth:RB",
                })
            if "qb_roster_construction_synth" in visible_ids:
                blocked_ids.update({
                    "format_qb_demand", "elite_then_depth:QB", "waiting_cost:QB",
                })

            reserve = []
            for c in list(candidates) + list(story_candidates):
                sid = c.get("story_id")
                if sid in visible_ids or sid in blocked_ids:
                    continue
                if float(c.get("materiality", 0.0) or 0.0) < 0.90:
                    continue
                if float(c.get("confidence", 0.0) or 0.0) < 0.90:
                    continue
                if float(c.get("actionability", 0.0) or 0.0) < 1.00:
                    continue
                if "editorial_score" not in c:
                    c["editorial_score"] = (
                        float(c.get("materiality", 0.0)) * 0.40 +
                        float(c.get("confidence", 0.0)) * 0.25 +
                        float(c.get("actionability", 0.0)) * 0.35
                    )
                reserve.append(c)

            reserve = sorted(
                reserve,
                key=lambda c: (float(c.get("editorial_score", 0.0)), float(c.get("score", 0.0))),
                reverse=True,
            )
            for c in reserve:
                if len(final_cards) >= 5:
                    break
                sid = c.get("story_id")
                if sid in visible_ids:
                    continue
                final_cards.append(c)
                visible_ids.add(sid)

    structural_insights = final_cards[:5]
'''

# Replace only the final publication assignment. V0.8.4 contains one live
# structural_insights assignment inherited from the V0.8.1 reserve contract.
s = s.replace(old, new, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_8_5.py created")
print("Engine V0.2.1 math unchanged")
print("WR synthesis now runs on the actual final Top-5 publication set")
print("Freed fifth slot can be filled only by an existing distinct material story")
print("No new WoRP metric, ADP, market-price, waiver, or predictive claim introduced")
