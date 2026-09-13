from pathlib import Path

SRC = Path("app_v0_7_6.py")
DST = Path("app_v0_7_6_1.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_7_6.py not found. Run build_worp_lab_v0_7_6.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.7.6', 'UI V0.7.6.1')
s = s.replace('WoRP-Lab/0.7.6', 'WoRP-Lab/0.7.6.1')
s = s.replace('WoRP Lab UI V0.7.6', 'WoRP Lab UI V0.7.6.1')

needle = '    structural_insights = candidates[:5]\n\n    audit = {'
replacement = '''    structural_insights = candidates[:5]\n\n    # Backward-compatible frontend contract: downstream UI/session-state code\n    # still consumes a DataFrame named insight_df. Story Engine V0.7.6 changed\n    # candidate semantics, not the public return shape.\n    insight_df = pd.DataFrame(structural_insights)\n\n    audit = {'''

if needle not in s:
    raise SystemExit("STOP: V0.7.6 Structural Insights output marker not found")

s = s.replace(needle, replacement, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_7_6_1.py created")
print("Engine V0.2.1 math unchanged")
print("Hotfix only: restores insight_df DataFrame contract for downstream UI")
print("Story Engine logic unchanged")
