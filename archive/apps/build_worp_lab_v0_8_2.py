from pathlib import Path

SRC = Path("app_v0_8_1.py")
DST = Path("app_v0_8_2.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_8_1.py not found. Run build_worp_lab_v0_8_1.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.8.1', 'UI V0.8.2')
s = s.replace('WoRP-Lab/0.8.1', 'WoRP-Lab/0.8.2')
s = s.replace('WoRP Lab UI V0.8.1', 'WoRP Lab UI V0.8.2')

# -----------------------------------------------------------------------------
# V0.8.2 — SEMANTIC DEDUPE + ECONOMIC STORY PRIORITY
# Engine V0.2.1 math untouched.
#
# Fixes visible in the V0.8.1 regression harness:
# 1) Once RB top+depth synthesis is published, same-rank FLEX preference is
#    supporting evidence for the same thesis and must not consume another card.
# 2) Generic FLEX-capacity copy is a format fact. Remove it from Top-5 selection
#    and let an already-generated economic story win instead when available.
# -----------------------------------------------------------------------------

marker = '''    # V0.8.1 editorial reserve.\n'''
if marker not in s:
    raise SystemExit("STOP: V0.8.1 reserve marker not found")

insert = r'''    # -------------------------------------------------------------------------
    # V0.8.2 semantic editorial gate.
    # -------------------------------------------------------------------------
    published_ids_now = {c.get("story_id") for c in candidates}

    # One economic story = one card. If the RB synthesis already says RB wins at
    # the top AND through FLEX-relevant depth, the same-rank FLEX preference is
    # evidence for that story, not an additional recommendation.
    if "rb_top_and_depth_synth" in published_ids_now:
        candidates = [
            c for c in candidates
            if c.get("story_id") not in {
                "crosspos_flex_preference",
                "crosspos_elite_preference",
                "crosspos_elite_priority",
                "crosspos_equivalence_rb_wr",
            }
        ]

    # A raw statement that the lineup has several FLEX slots is useful evidence,
    # but not by itself a Top-5 economic story. Keep it in backoffice generation
    # and remove it from publication. The reserve below may promote an existing
    # curve/economic story instead; no new metric or claim is fabricated.
    candidates = [
        c for c in candidates
        if c.get("story_id") != "flex_depth_absorption"
    ]

'''

s = s.replace(marker, insert + marker, 1)

# Make sure the reserve can use an economic alternative after the generic FLEX
# fact was removed, but still never reintroduce the blocked format fact.
# (V0.8.1 already blocks flex_depth_absorption inside reserve.)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_8_2.py created")
print("Engine V0.2.1 math unchanged")
print("RB synthesis now suppresses redundant same-rank FLEX preference")
print("Generic FLEX-capacity fact removed from Top-5 publication")
print("Existing economic stories may fill the freed slot through the reserve")
print("No new WoRP metric, ADP, market-price, waiver, or predictive claim introduced")