from pathlib import Path

SRC = Path("app_v0_8_3.py")
DST = Path("app_v0_8_4.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_8_3.py not found. Run build_worp_lab_v0_8_3.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.8.3', 'UI V0.8.4')
s = s.replace('WoRP-Lab/0.8.3', 'WoRP-Lab/0.8.4')
s = s.replace('WoRP Lab UI V0.8.3', 'WoRP Lab UI V0.8.4')

# -----------------------------------------------------------------------------
# V0.8.4 — WR VERTICAL STORY SYNTHESIS
# Engine V0.2.1 math untouched.
#
# If elite WR concentration and cheap mid-range WR upgrades are both present,
# publish them as one roster-construction thesis instead of two separate cards.
# -----------------------------------------------------------------------------

marker = '''    # V0.8.1 editorial reserve.\n'''
if marker not in s:
    raise SystemExit("STOP: editorial reserve marker not found in V0.8.3")

insert = r'''    # -------------------------------------------------------------------------
    # V0.8.4 WR vertical synthesis.
    # -------------------------------------------------------------------------
    elite_wr = next((
        c for c in candidates
        if c.get("story_id") == "elite_then_depth:WR"
    ), None)
    cheap_wr = next((
        c for c in candidates
        if c.get("story_id") == "cheap_midrange:WR"
    ), None)

    if elite_wr is not None and cheap_wr is not None:
        eve = elite_wr.get("evidence", {}) or {}
        evm = cheap_wr.get("evidence", {}) or {}

        head_drop = float(eve.get("head_drop", 0.0) or 0.0)
        head_end = int(eve.get("head_end", 8) or 8)
        frontier = int(eve.get("frontier", evm.get("frontier", 0)) or 0)
        mid_start = int(evm.get("start", 0) or 0)
        mid_end = int(evm.get("end", 0) or 0)
        cost10 = float(evm.get("cost_per_10", 0.0) or 0.0)

        if head_drop > 0 and mid_start > 0 and mid_end > mid_start:
            candidates = [
                c for c in candidates
                if c.get("story_id") not in {
                    "elite_then_depth:WR",
                    "cheap_midrange:WR",
                }
            ]

            _add_story(
                "wr_elite_and_midrange_synth", "roster_construction", "WR",
                6.00,
                "Pay for elite WR access; be selective in the middle",
                (
                    f"WR1 to WR{head_end} loses {head_drop:.2f} WoRP, so the top of the position has carried real historical separation. "
                    f"But between WR{mid_start} and WR{mid_end}, moving 10 ranks changes only about {cost10:.2f} WoRP. "
                    + (f"With replacement near WR{frontier}, " if frontier > 0 else "")
                    + "this league has rewarded securing elite WR access more than paying repeatedly for small mid-range upgrades."
                ),
                1.70, 1.40, 1.60,
                {
                    "head_drop": head_drop,
                    "head_end": head_end,
                    "mid_start": mid_start,
                    "mid_end": mid_end,
                    "cost_per_10": cost10,
                    "frontier": frontier,
                },
            )
            synth = [
                c for c in story_candidates
                if c.get("story_id") == "wr_elite_and_midrange_synth"
            ]
            candidates.extend(synth[-1:])

'''

s = s.replace(marker, insert + marker, 1)

# Prevent the reserve from reintroducing the two WR evidence cards after
# successful synthesis.
old = '''        has_qb_synth = "qb_roster_construction_synth" in published_ids\n        has_rb_synth = "rb_top_and_depth_synth" in published_ids\n'''
new = '''        has_qb_synth = "qb_roster_construction_synth" in published_ids\n        has_rb_synth = "rb_top_and_depth_synth" in published_ids\n        has_wr_synth = "wr_elite_and_midrange_synth" in published_ids\n'''
if old not in s:
    raise SystemExit("STOP: reserve synth flags not found")
s = s.replace(old, new, 1)

old2 = '''        if has_rb_synth:\n            blocked_ids.update({\n                "crosspos_elite_preference", "crosspos_elite_priority",\n                "crosspos_equivalence_rb_wr", "crosspos_flex_preference",\n                "elite_then_depth:RB",\n            })\n'''
new2 = '''        if has_rb_synth:\n            blocked_ids.update({\n                "crosspos_elite_preference", "crosspos_elite_priority",\n                "crosspos_equivalence_rb_wr", "crosspos_flex_preference",\n                "elite_then_depth:RB",\n            })\n        if has_wr_synth:\n            blocked_ids.update({\n                "elite_then_depth:WR", "cheap_midrange:WR",\n            })\n'''
if old2 not in s:
    raise SystemExit("STOP: RB reserve block not found")
s = s.replace(old2, new2, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_8_4.py created")
print("Engine V0.2.1 math unchanged")
print("Elite WR concentration + mid-range WR compression can now synthesize into one card")
print("Reserve cannot reintroduce the two WR evidence cards after synthesis")
print("No new WoRP metric, ADP, market-price, waiver, or predictive claim introduced")
