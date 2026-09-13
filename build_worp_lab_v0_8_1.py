from pathlib import Path

SRC = Path("app_v0_8_0.py")
DST = Path("app_v0_8_1.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_8_0.py not found. Run build_worp_lab_v0_8_0.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.8.0', 'UI V0.8.1')
s = s.replace('WoRP-Lab/0.8.0', 'WoRP-Lab/0.8.1')
s = s.replace('WoRP Lab UI V0.8.0', 'WoRP Lab UI V0.8.1')

# -----------------------------------------------------------------------------
# V0.8.1 — STORY SYNTHESIS HOTFIX + EDITORIAL RESERVE
# Engine V0.2.1 math untouched.
#
# Fixes:
# 1) V0.8.0 looked for the old elite story_id (crosspos_elite_preference), while
#    the live V0.8.0 candidate is crosspos_elite_priority. That prevented the
#    intended RB top+depth synthesis from ever firing.
# 2) If synthesis/dedupe leaves fewer than five cards, backfill only from already
#    generated, material, non-redundant story evidence. No new metric/claim.
# -----------------------------------------------------------------------------

old = 'if c.get("story_id") == "crosspos_elite_preference"\n        and c.get("position") == "RB"'
new = 'if c.get("story_id") in {"crosspos_elite_preference", "crosspos_elite_priority"}\n        and c.get("position") == "RB"'
if old not in s:
    raise SystemExit("STOP: V0.8.0 elite synthesis matcher not found")
s = s.replace(old, new, 1)

old_remove = '''                if c.get("story_id") not in {\n                    "crosspos_elite_preference",\n                    "crosspos_equivalence_rb_wr",\n                }\n'''
new_remove = '''                if c.get("story_id") not in {\n                    "crosspos_elite_preference",\n                    "crosspos_elite_priority",\n                    "crosspos_equivalence_rb_wr",\n                }\n'''
if old_remove not in s:
    raise SystemExit("STOP: V0.8.0 synthesis removal set not found")
s = s.replace(old_remove, new_remove, 1)

# Insert a conservative reserve after final candidate sorting and before the
# product's structural_insights = candidates[:5] contract.
marker = '''    # Exactly five cards remains the product contract. If fewer than five strong\n    # story candidates exist, use the strongest remaining evidence rather than\n    # fabricate a new semantic claim.\n    structural_insights = candidates[:5]\n'''
if marker not in s:
    raise SystemExit("STOP: final structural_insights marker not found")

replacement = r'''    # V0.8.1 editorial reserve.
    # Synthesis can correctly collapse two cards into one and leave only four.
    # When that happens, look only at stories the engine/editor already generated.
    # Do NOT backfill generic format facts or evidence that belongs to a published
    # synthesized thesis. The reserve is therefore conservative by construction.
    if len(candidates) < 5:
        published_ids = {c.get("story_id") for c in candidates}
        published_families = {(c.get("family"), c.get("position")) for c in candidates}
        has_qb_synth = "qb_roster_construction_synth" in published_ids
        has_rb_synth = "rb_top_and_depth_synth" in published_ids

        blocked_ids = {
            "flex_depth_absorption",   # format fact without enough economic specificity
            "format_te_demand",       # format alone is evidence, not a Top-5 story
        }
        if has_qb_synth:
            blocked_ids.update({
                "format_qb_demand", "elite_then_depth:QB", "waiting_cost:QB"
            })
        if has_rb_synth:
            blocked_ids.update({
                "crosspos_elite_preference", "crosspos_elite_priority",
                "crosspos_equivalence_rb_wr", "elite_then_depth:RB",
            })

        reserve = []
        for c in story_candidates:
            sid = c.get("story_id")
            if sid in published_ids or sid in blocked_ids:
                continue
            # A reserve card still has to clear a basic decision-quality floor.
            if float(c.get("materiality", 0.0) or 0.0) < 0.90:
                continue
            if float(c.get("confidence", 0.0) or 0.0) < 0.90:
                continue
            if float(c.get("actionability", 0.0) or 0.0) < 1.00:
                continue
            # Avoid spending a second card on the same family+position unless the
            # story itself is semantically different and no alternative survives.
            fam_pos = (c.get("family"), c.get("position"))
            if fam_pos in published_families:
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
            if len(candidates) >= 5:
                break
            candidates.append(c)
            published_ids.add(c.get("story_id"))
            published_families.add((c.get("family"), c.get("position")))

    # Exactly five remains the product target, but we still refuse to fabricate a
    # sixth-rate claim merely to fill space. The regression harness will expose
    # any league that still has fewer than five material, distinct stories.
    structural_insights = candidates[:5]
'''

s = s.replace(marker, replacement, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_8_1.py created")
print("Engine V0.2.1 math unchanged")
print("Fixed V0.8.0 RB synthesis story_id mismatch")
print("RB elite + RB/WR depth evidence can now synthesize as designed")
print("Conservative editorial reserve added for <5-card cases")
print("Generic FLEX and TE format facts are not reserve fillers")
print("No new WoRP metric, ADP, market-price, waiver, or predictive claim introduced")
