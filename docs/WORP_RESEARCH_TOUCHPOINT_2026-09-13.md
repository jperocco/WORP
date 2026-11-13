# WoRP Lab — Research Touchpoint — 2026-09-13

## Purpose
This file is a project-state handoff. It is not a chat transcript. It records what has been demonstrated, what has failed, what remains open, and the methodological boundaries that must not be crossed implicitly.

## Canonical project state
- Core WoRP Engine V0.2.1 remains frozen.
- Product UI reached V0.6.3.
- Historical WoRP is descriptive, not predictive.
- Replacement remains format-derived.
- Current research branch is the Wookiee / roster-construction investigation.

## Structural WR findings already accepted
- Fixed 12-player WR buckets do not map cleanly to economic regimes.
- Very strong top-end concentration, especially around WR1–8.
- Progressive compression through the middle.
- Strong evidence of a low marginal-value tail around WR55/60+.
- Important guardrail: compression / flatness is NOT the same as fungibility, FREE, waiver, capturable, identifiable, or executable replacement.

## Realized value location
STARTED / BENCHED / FREE reconstruction established that positive realized WoRP exists in the FREE market.

WR-specific historical finding:
- 170 positive-WoRP FREE WR player-weeks in the STARTED/BENCHED/FREE audit.
- FREE positive WR WoRP existed, but that alone did not establish capturability or predictability.

## Temporal capturability
General temporal reconstruction residual error was 9/435 = 2.1%, below the project 4% STOP threshold, therefore accepted as PASS.

FREE capturability V0.2:
- 506 FREE positive candidates across positions.
- 495 CAPTURABLE.
- 11 AMBIGUOUS.
- ambiguity rate 2.17% -> PASS.
- 97.75% of observed positive FREE WoRP was temporally compatible with availability before production under the audit definition.

Guardrail:
CAPTURABLE does not mean acquired, identified, started, or manager-realized.

## Capture Quality
Capture Quality V0.1 showed that capturable value is not simply obvious opportunity.

Overall capturable-positive player-weeks:
- 495 player-weeks.
- 23.106847 WoRP.
- low-volume cases were common.
- TD/spike production was meaningful.

For WR specifically:
- 0–2 targets: 36 positive capturable PW, 16.3% of WR capturable WoRP.
- 3–6 targets: 104 PW, 52.9%.
- 7+ targets: 29 PW, 30.8%.

Do not interpret these buckets as waiver thresholds.

## Ex-ante identifiability
Ex-Ante Identifiability V0.1 used only prior information:
- previous 1-week opportunity.
- previous 3 available-week mean / max.
- no target-week usage in signal construction.

PASS on coverage:
- 495 capturable positive PW.
- 15 no-prior-sample.
- 3.03% no-prior-sample -> PASS.

Key result:
Most capturable positive-WoRP winners had low or zero prior usage under the descriptive bands. This prevented us from calling MID/HIGH an actionable threshold.

## Denominator / discrimination audit
The denominator audit added all observed FREE target player-weeks, including failures.

Overall:
- 17,398 FREE target player-weeks.
- 488 positive-WoRP successes.
- 16,910 non-positive failures.
- no-prior-sample rate 2.15% -> PASS.

Discrimination:
- MID+HIGH: 359 FREE PW, 76 hits, 21.17% hit rate, 0.01149 WoRP/FREE PW.
- ZERO+LOW: 16,665 FREE PW, 408 hits, 2.45% hit rate, 0.00111 WoRP/FREE PW.
- hit-rate lift: 8.65x.
- WoRP-rate lift: 10.38x.

WR-specific hit rates:
- ZERO: 0.54%.
- LOW: 5.85%.
- MID: 16.40%.
- HIGH: 26.09%.

Interpretation:
Prior usage signal is genuinely discriminative ex ante. This still does NOT establish a waiver threshold or a player-selection policy.

## Continuous WR prior-signal curve
Continuous signal audit removed the arbitrary MID/HIGH framing and examined prior signal continuously.

WR exact examples:
- signal 0.0 -> 0.60% hit rate.
- 1.0 -> 3.95%.
- 2.0 -> 9.83%.
- 3.0 -> 12.43%.
- 4.0 -> 17.65%.
- 6.0 -> 20.00% on small sample.

Rolling local curve showed the largest descriptive increases around prior signal 2–4.

Interpretation:
There is an empirical bend / candidate region around 2–4 prior opportunities/targets for FREE WRs.
This is NOT yet a waiver threshold.

## Executable WR waiver policy V0.1 — important failure
First executable policy tested:
- one WR waiver slot.
- every week choose the observed FREE WR with the highest prior signal.
- use only prior information for selection.
- start that selected WR immediately.
- evaluate full realized weekly WoRP, including zero/negative outcomes.

Results:
- thresholds 2+ and 3+: 51/51 selection weeks.
- 11 positive-WoRP starts, 40 negative.
- 21.6% positive hit rate.
- realized WoRP total: -1.1873.
- WoRP per selection: -0.0233.
- 4+ was only slightly different and still negative.

Interpretation:
The naive policy FAILED.

Critical distinction discovered:
SIGNAL DISCRIMINATES does NOT imply HIGHEST SIGNAL RANKS THE BEST PLAYER.

Also, ACQUIRE and START may be separate decisions. Immediate-start may be the wrong execution model.

This failure should NOT be interpreted as disproving the broader roster-construction hypothesis.

## Major conceptual correction from user
The broader hypothesis is NOT primarily:
"Can a FREE player generate positive WoRP?"

It is closer to:
"How much WoRP do I lose by replacing a marginal rostered / last-flex player with a dynamically sourced FREE player?"

A waiver option can be strategically useful even if its absolute WoRP is negative, provided its DELTA versus the marginal rostered alternative is small.

Therefore FREE vs FREE is the wrong primary comparison for roster construction.

The relevant comparisons are likely:
- FREE vs BENCHED marginal asset.
- FREE vs last FLEX spot.
- FREE vs the marginal rostered depth player the manager would otherwise carry.

## Central roster-construction question
The user’s motivating construction is:

WR1* + WR1* + dynamic replacement
vs
WR3*-type depth across WR slots.

But this must NOT be simplified into "two top-12 WRs plus any waiver WR."

The economic hypothesis is:
- concentrate value in stronger upper-tier assets;
- outsource one or more marginal lineup slots to dynamic replacement;
- compare the WoRP cost of outsourced marginal slots with the value of carrying rostered depth.

## Waiver / replacement capacity
A new central question is:

How many marginal lineup slots can be supplied by replacement before the WoRP delta becomes materially worse?

Possible answer space:
- zero replacement slots supported -> hypothesis fails.
- one supported -> concentration + one outsourced slot may work.
- two supported -> more aggressive construction may work.
- more slots -> increasingly difficult because the market must supply the 2nd/3rd-best replacement options, not just the best one.

This should be measured as a capacity curve, not assumed.

## Interpositional correction
A FLEX slot is not a WR slot.

The correct replacement market for FLEX is interpositional:
- RB
- WR
- TE

Therefore the project should NOT build a "WR Waiver Capacity Curve" as the main roster-construction answer.
It should build a format-aware INTERPOSITIONAL REPLACEMENT CAPACITY CURVE.

The question becomes:

Given the league format, how many marginal lineup slots can be supplied dynamically by the FREE market, from any eligible position, before the delta versus rostered alternatives becomes materially large?

This keeps the analysis consistent with the core WoRP philosophy that replacement is format-derived.

## Boundary: WoRP vs roster valuation
This project is now approaching roster construction, but there is a methodological boundary.

WoRP can answer:
- what is the sporting / lineup cost in WoRP of outsourcing a marginal slot?
- how does that cost change for the 1st, 2nd, 3rd outsourced slot?
- which positions supply that replacement capacity in a given format?

WoRP alone CANNOT answer:
- what does it cost in trade value, startup ADP, auction dollars, or future picks to upgrade WR20 to WR8?
- whether selling a depth asset for future picks is profitable.
- how much market capital is released by carrying less depth.

Those questions require a separate roster-valuation / market-value layer.

DO NOT silently import future-pick values, trade charts, ADP prices, or external player-market valuations into the WoRP engine.

The next clean step is to finish the WoRP-side question first:
REPLACEMENT CAPACITY and MARGINAL WoRP DELTA.

Only after that should the project consciously decide whether to add a separate Roster Construction / Valuation layer to model reinvestment of saved roster capital.

## Current next audit
Interpositional Replacement Capacity V0.1 is the next structural audit.

Reference fixture currently being tested:
- 12 teams
- 2 RB mandatory
- 3 WR mandatory
- 2 TE mandatory
- 2 FLEX
- FLEX eligible: RB / WR / TE

Purpose:
- compare interpositional FREE supply against the marginal aggregate FLEX layer.
- test 1 dynamic replacement slot per team and 2 dynamic replacement slots per team.
- measure which positions actually supply FREE capacity.

Important limitation:
Current STARTED/BENCHED/FREE detail does not preserve literal historical FLEX slot labels, so the initial audit reconstructs the aggregate FLEX layer economically. This is a structural hindsight-capacity audit, NOT yet an executable ex-ante policy.

## Methodological guardrails to preserve
- realized WoRP != predictive value.
- FREE != waiver.
- capturable != acquired.
- capturable != identifiable.
- identifiable != executable.
- signal discrimination != ranking quality.
- target volume != route/snap structural role.
- compression != fungibility.
- flat tail != replacement market.
- negative absolute WoRP does not automatically mean a replacement strategy is bad; roster construction depends on DELTA versus the alternative occupying the same slot.
- do not declare a WR rank such as WR60/72/80 to be the waiver threshold.
- do not declare 2/3/4 prior targets to be a final waiver threshold.
- do not mix future-pick or trade-market valuation into the WoRP layer unless a separate valuation model is explicitly created.

## Research sequence from here
1. Interpositional structural replacement capacity.
2. Marginal delta for 1st / 2nd / possibly additional outsourced slots.
3. If structural capacity survives, rebuild ex-ante acquisition/start execution for the interpositional replacement pool.
4. Compare executable replacement output with the actual marginal rostered / FLEX alternative.
5. Only then determine how many replacement slots the format supports.
6. After the WoRP-side result is stable, decide whether to build a separate market-value / roster-construction layer for reinvestment of saved capital.

## Current status labels
- Economic WR curve: PASS.
- STARTED/BENCHED/FREE: PASS.
- Temporal reconstruction: PASS.
- FREE capturability V0.2: PASS.
- Capture Quality V0.1: PASS.
- Ex-Ante Identifiability V0.1: PASS.
- Denominator / Discrimination V0.1: PASS.
- Continuous Signal Curve V0.1: PASS as descriptive signal-shape audit.
- Naive highest-signal WR immediate-start policy: FAIL as a policy.
- Broader concentration + dynamic replacement hypothesis: OPEN.
- Interpositional replacement capacity: NEXT.
