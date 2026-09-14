from pathlib import Path

SRC = Path("app_v0_8_2.py")
DST = Path("app_v0_8_3.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_8_2.py not found. Run build_worp_lab_v0_8_2.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.8.2', 'UI V0.8.3')
s = s.replace('WoRP-Lab/0.8.2', 'WoRP-Lab/0.8.3')
s = s.replace('WoRP Lab UI V0.8.2', 'WoRP Lab UI V0.8.3')

# -----------------------------------------------------------------------------
# V0.8.3 — RESERVE DEDUPE HOTFIX
# Engine V0.2.1 math untouched.
#
# V0.8.2 correctly removed crosspos_flex_preference from the main candidate
# list when rb_top_and_depth_synth existed, but the V0.8.1 reserve could add it
# back because it was not included in the has_rb_synth blocked_ids set.
# -----------------------------------------------------------------------------

old = '''        if has_rb_synth:\n            blocked_ids.update({\n                "crosspos_elite_preference", "crosspos_elite_priority",\n                "crosspos_equivalence_rb_wr", "elite_then_depth:RB",\n            })\n'''
new = '''        if has_rb_synth:\n            blocked_ids.update({\n                "crosspos_elite_preference", "crosspos_elite_priority",\n                "crosspos_equivalence_rb_wr", "crosspos_flex_preference",\n                "elite_then_depth:RB",\n            })\n'''

if old not in s:
    raise SystemExit("STOP: V0.8.2 RB reserve block not found")

s = s.replace(old, new, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_8_3.py created")
print("Engine V0.2.1 math unchanged")
print("Reserve can no longer reintroduce redundant RB FLEX-preference story")
print("No new WoRP metric, ADP, market-price, waiver, or predictive claim introduced")