from pathlib import Path

SRC = Path("app_v0_9_3.py")
DST = Path("app_v0_9_4.py")
if not SRC.exists():
    raise SystemExit("STOP: app_v0_9_3.py not found")

s = SRC.read_text(encoding="utf-8")
s = (
    s.replace("UI V0.9.3", "UI V0.9.4")
     .replace("WoRP-Lab/0.9.3", "WoRP-Lab/0.9.4")
     .replace("WoRP Lab UI V0.9.3", "WoRP Lab UI V0.9.4")
)

# V0.9.4 intentionally preserves the observed lineup reconstruction introduced
# in V0.9.3. It must not replace actual roster/week slot placement with an
# aggregate optimal-lineup or fantasy-points model.
DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_9_4.py created")
print("Observed league x roster x week Lineup Economics preserved")
print("No aggregate optimal-lineup or rank-based substitute")
print("Engine V0.2.1 and frozen Roster Construction unchanged")
