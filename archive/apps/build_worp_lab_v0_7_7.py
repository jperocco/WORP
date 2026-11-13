from pathlib import Path

SRC = Path("app_v0_7_6_1.py")
DST = Path("app_v0_7_7.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_7_6_1.py not found. Run build_worp_lab_v0_7_6_1.py first.")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.7.6.1', 'UI V0.7.7')
s = s.replace('WoRP-Lab/0.7.6.1', 'WoRP-Lab/0.7.7')
s = s.replace('WoRP Lab UI V0.7.6.1', 'WoRP Lab UI V0.7.7')

# -----------------------------------------------------------------------------
# V0.7.7 — CROSS-POSITION DECISION ENGINE
# Engine V0.2.1 math is untouched.
# Goal: turn same-range positional WoRP differences into actual roster decisions.
# This step adds interpositional evidence for draft/trade/FLEX decisions and
# suppresses repetitive same-message elite cards when a stronger cross-position
# story exists.
# -----------------------------------------------------------------------------

marker = '''    # Rank by the explicit editorial dimensions first; score breaks close ties.\n'''
if marker not in s:
    raise SystemExit("STOP: V0.7.6 editorial ranking marker not found")

insert = r'''    # -------------------------------------------------------------------------
    # V0.7.7 CROSS-POSITION DECISION ENGINE
    # Compare positions only where the decision is economically comparable.
    # - Elite draft/trade capital: RB/WR/TE same positional rank band.
    # - FLEX decisions: only RB/WR/TE, because they share FLEX eligibility.
    # This does NOT assume rank itself is market price; it compares historical
    # WoRP produced by similarly ranked positional assets in this league.
    # -------------------------------------------------------------------------
    def _avg_rank_band(pos, a, b):
        vals = []
        for r in range(int(a), int(b) + 1):
            v = _value_at(pos, r)
            if v is not None:
                vals.append(float(v))
        return (sum(vals) / len(vals)) if vals else None

    # 1) ELITE INTERPOSITIONAL PRIORITY
    # Replace several "protect elite X" cards with one decision if one skill
    # position clearly generates more WoRP across the same elite rank band.
    elite_band_end = 8
    elite_scores = []
    for pos in ["RB", "WR", "TE"]:
        f = _frontier_rank(pos)
        if f is None or f < elite_band_end:
            continue
        avg = _avg_rank_band(pos, 1, elite_band_end)
        if avg is not None:
            elite_scores.append((pos, avg))

    if len(elite_scores) >= 2:
        elite_scores = sorted(elite_scores, key=lambda z: z[1], reverse=True)
        win_pos, win_avg = elite_scores[0]
        second_pos, second_avg = elite_scores[1]
        elite_edge = win_avg - second_avg

        # Materiality gate: do not manufacture a preference from noise.
        if elite_edge >= 0.12:
            _add_story(
                "crosspos_elite_priority", "cross_position", win_pos,
                4.50 + min(elite_edge, 1.0),
                f"At the elite tier, prioritize {win_pos} over {second_pos}",
                (
                    f"Across {win_pos}1–{win_pos}{elite_band_end}, {win_pos} averages {win_avg:.2f} WoRP versus "
                    f"{second_avg:.2f} for {second_pos}1–{second_pos}{elite_band_end}. "
                    f"For similarly ranked elite assets in this league, {win_pos} has delivered about {elite_edge:.2f} more WoRP per player. "
                    "That makes the position the stronger structural target when draft or trade capital is comparable."
                ),
                min(1.8, 1.10 + elite_edge), 1.25, 1.50,
                {"rank_start": 1, "rank_end": elite_band_end,
                 "winner": win_pos, "runner_up": second_pos,
                 "winner_avg": win_avg, "runner_up_avg": second_avg,
                 "avg_edge": elite_edge},
            )

            # The cross-position card now carries the elite decision. Keep only
            # elite intra-position cards that tell a genuinely different story.
            candidates = [
                c for c in candidates
                if not (
                    c["story_id"].startswith("elite_then_depth:")
                    and c["position"] in {"RB", "WR", "TE"}
                )
            ]

    # 2) FLEX INTERPOSITIONAL PREFERENCE
    # Compare RB/WR/TE at several same-rank anchors inside the shared relevant
    # pool. Require a stable winner, not a single-rank accident.
    if int(flex) > 0:
        flex_positions = []
        for pos in ["RB", "WR", "TE"]:
            f = _frontier_rank(pos)
            if f is not None and f >= 12:
                flex_positions.append((pos, f))

        if len(flex_positions) >= 2:
            common_frontier = min(f for _, f in flex_positions)
            raw_anchors = [
                max(8, int(round(common_frontier * 0.30))),
                max(9, int(round(common_frontier * 0.45))),
                max(10, int(round(common_frontier * 0.60))),
                max(11, int(round(common_frontier * 0.75))),
            ]
            anchors = sorted({min(common_frontier, a) for a in raw_anchors})

            wins = {p: 0 for p, _ in flex_positions}
            values_by_pos = {p: [] for p, _ in flex_positions}

            for r in anchors:
                rank_values = []
                for p, _ in flex_positions:
                    v = _value_at(p, r)
                    if v is not None:
                        values_by_pos[p].append(float(v))
                        rank_values.append((p, float(v)))
                if len(rank_values) >= 2:
                    rank_values.sort(key=lambda z: z[1], reverse=True)
                    wins[rank_values[0][0]] += 1

            avg_values = []
            for p, vals in values_by_pos.items():
                if vals:
                    avg_values.append((p, sum(vals) / len(vals)))

            if len(avg_values) >= 2 and anchors:
                avg_values.sort(key=lambda z: z[1], reverse=True)
                flex_win, flex_win_avg = avg_values[0]
                flex_second, flex_second_avg = avg_values[1]
                flex_edge = flex_win_avg - flex_second_avg
                stable_wins = wins.get(flex_win, 0)
                required_wins = max(2, (len(anchors) // 2) + 1)

                if stable_wins >= required_wins and flex_edge >= 0.10:
                    rank_text = ", ".join(str(x) for x in anchors)
                    _add_story(
                        "crosspos_flex_preference", "cross_position", flex_win,
                        4.10 + min(flex_edge, 0.8),
                        f"For comparable FLEX-range assets, lean {flex_win} over {flex_second}",
                        (
                            f"At shared rank checkpoints ({rank_text}), {flex_win} leads the eligible skill positions in "
                            f"{stable_wins} of {len(anchors)} comparisons and averages about {flex_edge:.2f} more WoRP than {flex_second}. "
                            f"When similarly ranked {flex_win}/{flex_second} options compete for flexible lineup capital, "
                            f"this league's historical structure favors {flex_win}."
                        ),
                        min(1.6, 1.00 + flex_edge), 1.20, 1.45,
                        {"anchors": anchors, "winner": flex_win, "runner_up": flex_second,
                         "winner_avg": flex_win_avg, "runner_up_avg": flex_second_avg,
                         "avg_edge": flex_edge, "wins": wins,
                         "common_frontier": common_frontier},
                    )

    # Newly added cross-position stories must participate in the same semantic
    # story-ID contract as the rest of the editor.
    best_by_story = {}
    for c in candidates + [c for c in story_candidates if c["family"] == "cross_position"]:
        sid = c["story_id"]
        if sid not in best_by_story or c["score"] > best_by_story[sid]["score"]:
            best_by_story[sid] = c
    candidates = list(best_by_story.values())

'''

s = s.replace(marker, insert + marker, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_7_7.py created")
print("Engine V0.2.1 math unchanged")
print("Cross-position decision engine added")
print("Elite RB/WR/TE are compared on the same rank band with a materiality gate")
print("FLEX-eligible RB/WR/TE are compared at shared relevant-rank checkpoints")
print("Stable interpositional preference can replace repetitive elite positional cards")
print("No market-price equivalence or waiver conclusion is assumed")
