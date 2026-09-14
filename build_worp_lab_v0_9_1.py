from pathlib import Path

SRC = Path("app_v0_9_0.py")
DST = Path("app_v0_9_1.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_9_0.py not found. Run build_worp_lab_v0_9_0.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.9.0', 'UI V0.9.1')
s = s.replace('WoRP-Lab/0.9.0', 'WoRP-Lab/0.9.1')
s = s.replace('WoRP Lab UI V0.9.0', 'WoRP Lab UI V0.9.1')

# V0.9.1 — close the one remaining publication bug in the V0.9.0 thesis editor.
# If a canonical QB roster-construction synthesis exists, format_qb_demand is
# supporting evidence for that thesis and must not survive as a second card.
old = '''    qb_anchor = None\n    for preferred in ("qb_roster_construction_synth", "format_qb_demand"):\n        qb_anchor = next((c for c in pool if c.get("story_id") == preferred), None)\n        if qb_anchor is not None:\n            break\n    if qb_anchor is not None:\n'''
new = '''    qb_anchor = None\n    for preferred in ("qb_roster_construction_synth", "format_qb_demand"):\n        qb_anchor = next((c for c in pool if c.get("story_id") == preferred), None)\n        if qb_anchor is not None:\n            break\n    if qb_anchor is not None:\n        # The format-demand card is evidence inside the canonical QB thesis.\n        # V0.9.0 absorbed waiting/elite support but forgot this source card when\n        # qb_roster_construction_synth already existed upstream.\n        if qb_anchor.get("story_id") == "qb_roster_construction_synth":\n            absorbed.add("format_qb_demand")\n'''
if old not in s:
    raise SystemExit("STOP: V0.9.0 QB thesis block not found")
s = s.replace(old, new, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_9_1.py created")
print("Engine V0.2.1 math unchanged")
print("Canonical QB roster-construction thesis now absorbs format_qb_demand")
print("No new metric, story architecture, market, waiver, or predictive claim introduced")
