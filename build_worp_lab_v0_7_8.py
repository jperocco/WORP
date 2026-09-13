from pathlib import Path

SRC = Path("app_v0_7_7.py")
DST = Path("app_v0_7_8.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_7_7.py not found. Run build_worp_lab_v0_7_7.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.7.7', 'UI V0.7.8')
s = s.replace('WoRP-Lab/0.7.7', 'WoRP-Lab/0.7.8')
s = s.replace('WoRP Lab UI V0.7.7', 'WoRP Lab UI V0.7.8')

# -----------------------------------------------------------------------------
# V0.7.8 — CROSS-POSITION EQUIVALENCE + DECISION-ONLY FORMAT STORIES
# Engine V0.2.1 math is untouched.
#
# Two product changes only:
# 1) Stop forcing cross-position analysis into the same positional rank.
#    Find economically equivalent ranks across FLEX-eligible positions.
# 2) Pure format facts do not earn a Top-5 card. Format may support a story, but
#    the story must end in a roster-construction decision.
# -----------------------------------------------------------------------------

marker = '''    # Rank by the explicit editorial dimensions first; score breaks close ties.\n'''
if marker not in s:
    raise SystemExit("STOP: V0.7.7 editorial ranking marker not found")

insert = r'''    # -------------------------------------------------------------------------
    # V0.7.8 CROSS-POSITION EQUIVALENCE ENGINE
    # Question: at the same WoRP level, how deep into another eligible position's
    # curve can a manager go? Example shape: RB40 ~= WR20.
    #
    # This is stronger than same-rank comparison because FLEX decisions are made
    # between players, not between labels such as RB20 and WR20.
    # -------------------------------------------------------------------------
    def _equivalent_rank(pos, target_worp, max_rank=None):
        f = _frontier_rank(pos)
        if f is None:
            return None
        stop = int(f if max_rank is None else min(f, int(max_rank)))
        best = None
        for r in range(1, stop + 1):
            v = _value_at(pos, r)
            if v is None:
                continue
            diff = abs(float(v) - float(target_worp))
            if best is None or diff < best[0]:
                best = (diff, r, float(v))
        return best

    # Search FLEX-compatible skill positions for the strongest economically useful
    # rank equivalence. Stay before replacement and away from near-zero tail noise.
    equivalence_candidates = []
    if int(flex) > 0:
        skill_positions = ["RB", "WR", "TE"]
        for target_pos in skill_positions:
            target_frontier = _frontier_rank(target_pos)
            if target_frontier is None:
                continue

            # Start at rank 8 so this is not merely another elite card. Stop at
            # 80% of the target frontier to keep the comparison roster-relevant.
            target_end = max(8, int(round(target_frontier * 0.80)))
            for target_rank in range(8, target_end + 1):
                target_worp = _value_at(target_pos, target_rank)
                if target_worp is None or target_worp < 0.20:
                    continue

                for source_pos in skill_positions:
                    if source_pos == target_pos:
                        continue
                    eq = _equivalent_rank(source_pos, target_worp)
                    if eq is None:
                        continue
                    diff, source_rank, source_worp = eq

                    # We care about the powerful case: the same economic value
                    # survives materially deeper in one position's curve.
                    rank_gap = int(source_rank) - int(target_rank)
                    if rank_gap < 6:
                        continue

                    # Approximate equivalence guardrail. Allow a little more
                    # tolerance at high WoRP, but do not equate visibly different
                    # values simply because ranks are far apart.
                    tolerance = max(0.08, abs(float(target_worp)) * 0.12)
                    if diff > tolerance:
                        continue

                    rank_multiple = float(source_rank) / max(float(target_rank), 1.0)
                    equivalence_candidates.append({
                        "source_pos": source_pos,
                        "source_rank": int(source_rank),
                        "source_worp": float(source_worp),
                        "target_pos": target_pos,
                        "target_rank": int(target_rank),
                        "target_worp": float(target_worp),
                        "rank_gap": rank_gap,
                        "rank_multiple": rank_multiple,
                        "worp_diff": float(diff),
                    })

    if equivalence_candidates:
        # Prefer large rank leverage at a still-material WoRP level. This makes a
        # statement such as RB40 ~= WR20 more valuable than tiny tail equivalence.
        equivalence_candidates.sort(
            key=lambda x: (
                x["rank_gap"] * min(x["target_worp"], 1.5),
                x["rank_multiple"],
                -x["worp_diff"],
            ),
            reverse=True,
        )
        eq = equivalence_candidates[0]

        _add_story(
            "crosspos_rank_equivalence", "cross_position_equivalence", eq["source_pos"],
            5.00 + min(eq["rank_gap"] / 20.0, 1.0),
            f"{eq['source_pos']} value survives much deeper than {eq['target_pos']}",
            (
                f"{eq['source_pos']}{eq['source_rank']} ({eq['source_worp']:.2f} WoRP) is roughly equivalent to "
                f"{eq['target_pos']}{eq['target_rank']} ({eq['target_worp']:.2f} WoRP). "
                f"The same historical value appears about {eq['rank_gap']} positional ranks deeper at {eq['source_pos']}. "
                f"When {eq['source_pos']} and {eq['target_pos']} compete for FLEX or roster capital, do not treat the deeper "
                f"{eq['source_pos']} rank as automatically less valuable."
            ),
            1.60, 1.30, 1.55,
            {"source_position": eq["source_pos"], "source_rank": eq["source_rank"],
             "source_worp": eq["source_worp"], "target_position": eq["target_pos"],
             "target_rank": eq["target_rank"], "target_worp": eq["target_worp"],
             "rank_gap": eq["rank_gap"], "rank_multiple": eq["rank_multiple"],
             "worp_diff": eq["worp_diff"]},
        )

        # The equivalence story is a richer version of the generic same-rank FLEX
        # preference. Keep elite priority, but avoid spending two cards on the same
        # RB-vs-WR middle-of-curve message.
        candidates = [
            c for c in candidates
            if c.get("story_id") != "crosspos_flex_preference"
        ]

    # -------------------------------------------------------------------------
    # DECISION-ONLY FORMAT GATE
    # Format is evidence, not a headline. A card that merely says TEP/SF/FLEX
    # changes demand does not earn Top 5 unless it resolves into a concrete roster
    # decision. Current TE-format card is the known weak case from V0.7.7.
    # -------------------------------------------------------------------------
    candidates = [
        c for c in candidates
        if c.get("story_id") != "format_te_demand"
    ]

    # Add the new equivalence story through the same semantic-story contract.
    best_by_story = {}
    for c in candidates + [
        c for c in story_candidates
        if c.get("family") == "cross_position_equivalence"
    ]:
        sid = c["story_id"]
        if sid not in best_by_story or c["score"] > best_by_story[sid]["score"]:
            best_by_story[sid] = c
    candidates = list(best_by_story.values())

'''

s = s.replace(marker, insert + marker, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_7_8.py created")
print("Engine V0.2.1 math unchanged")
print("Cross-position equivalence engine added")
print("Equivalent WoRP ranks can now generate stories such as RB40 ~= WR20")
print("Generic same-rank FLEX preference is suppressed when a stronger equivalence story exists")
print("Pure TE-format fact card removed from Top-5 candidate pool")
print("Format remains evidence; Top-5 requires a roster-construction consequence")
