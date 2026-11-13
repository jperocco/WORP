# WoRP Lab — Roster Construction Research Handoff

Date: 2026-09-15
Status: ACTIVE — LEAGUE-NATIVE MARGINAL ROSTER ECONOMICS

## NON-NEGOTIABLE PRODUCT PRINCIPLE — LEAGUE ADAPTABILITY

**WoRP is league-native before it is Wookiee-native.**

Wookiee is a reference/test league, not the definition of the product. A WoRP result that only works for Wookiee is not a finished WoRP result.

Priority zero for every current and future model:

> **The engine and its recommendations must adapt to each league's format, team count, scoring, starting-slot structure/eligibility, roster size, replacement environment, and other economically material league-specific settings.**

The correct architecture is:

**league settings → league-native WoRP/replacement economics → marginal WoRP vs capturable alternative → roster construction → roster diagnostic.**

Raw positional ranks are historical/diagnostic evidence only until translated into league-native economics. Wookiee remains useful for regression and behavioral audits but must never silently become the assumed league format.

## Product objective

WoRP Lab is a sporting-performance product. It does NOT model trade prices, picks, ADP, market value, or asset valuation.

Current product hierarchy:

0. **League adaptability / league-native economics — absolute priority.**
1. WoRP / league economic map.
2. What This League Is Telling You.
3. Value Cliffs.
4. Roster Construction — current research priority.
5. Roster Diagnostic — next product layer after construction logic is sufficiently validated.
6. Research-to-editor automation / Top-5 publication bridge — LAST backlog item.

## GOVERNING ROSTER-CONSTRUCTION PRINCIPLE — MARGINAL WoRP, NOT ABSOLUTE HURDLES

Do **not** treat 0.25, 0.50, 0.75, or any other WoRP landmark as an absolute roster-construction threshold. Those values are sensitivity probes into the curve, not semantic definitions of materiality.

The relevant roster-construction question is the **delta between production that must be secured and production that can realistically be obtained deeper in the league's player pool**.

Canonical example from the product discussion:

> If WR28 produces 0.25 WoRP and a realistically capturable WR110-level alternative produces 0.15 WoRP, the roster-construction advantage of securing WR28 is not 0.25 WoRP. The relevant marginal advantage is approximately 0.10 WoRP, subject to frequency, identification, timing, and capture.

Conversely, if a high-end player produces 1.50 WoRP and the realistic deep alternative produces 0.15, the large marginal delta is structurally difficult to replace and should matter greatly to roster construction.

Therefore the primary question becomes:

> **In THIS league and position, at what point does the marginal WoRP gained by securing additional rostered production converge toward the WoRP realistically capturable from deeper alternatives?**

When that delta becomes decision-immaterial, additional scoring depth may cease to buy meaningful competitive advantage even if both players still have positive absolute WoRP.

This is the rigorous form of the earlier `WR1* + WR1* + waiver` provocation. It is a hypothesis to test, NOT a proven roster recipe and NOT a literal instruction to roster only two WRs.

### What must be measured together

For each league/position/economic region:
1. WoRP produced by the secured/higher region.
2. WoRP available in deeper alternatives.
3. **Marginal WoRP delta** between them.
4. Frequency/density of deep alternatives capable of producing the relevant impact.
5. Whether those alternatives are actually FREE/available at the relevant time.
6. Whether they are **ex-ante identifiable and capturable before the production occurs**.
7. Persistence and lineup capture once acquired.

A deep player producing 0.15 in hindsight is not automatically a substitute for a rostered 0.25 player. There must be enough alternative supply and enough ex-ante capturability for the substitution to be economically real.

## Materiality principle

Optimize research for decision-material deltas, not mathematically nonzero production. Small differences such as 0.061 vs 0.045 WoRP are operationally zero vs zero unless evidence shows they compound into meaningful weekly/season impact.

Before spending research time on a difference, ask:

> **Could this marginal difference plausibly change how a manager builds a roster, sets a lineup, or wins meaningful weeks/seasons?**

If no, classify it as noise and STOP. Do not optimize thresholds by tiny increments. If a residual technical dispute affects less than 4% of the relevant universe and cannot change the decision, trigger STOP.

**Economic zero is a delta concept, not necessarily absolute WoRP = 0.000.** A player can have positive WoRP while the advantage of securing that player over a realistic alternative is economically zero.

## Roster Construction — simplified states

1. **STARTER** — normal productive lineup core.
2. **SCORING DEPTH** — additional rostered production whose marginal advantage over realistic alternatives remains materially useful.
3. **NON-SCORING OPTIONALITY** — roster capacity where securing ordinary scoring production no longer buys enough marginal advantage; justified primarily by meaningful state-change opportunity.

Preferred sequence:

**league-native WoRP distribution → league-native replacement/availability environment → marginal WoRP vs capturable alternatives → useful scoring depth → remaining roster capacity becomes optionality → diagnose roster.**

Do not derive a perfect state classifier before answering the economic question.

## `WR1* + WR1* + waiver` — protocolled hypothesis

The historical shorthand is preserved as a research provocation only.

It means:

> After securing the WRs that create genuinely large and difficult-to-replace WoRP deltas, does spending additional roster capacity to secure ordinary WR depth buy enough marginal WoRP compared with realistically capturable deep WR alternatives?

It does **not** mean:
- exactly two WRs are always optimal;
- WR28 is waiver-level;
- WR110 is always available;
- any deep WR is fungible with WR28;
- a hindsight deep hit was ex-ante capturable;
- the same construction applies across league formats.

The hypothesis must be league-native and may prove true for WR in some formats, false in others, and different for QB/RB/TE.

## League-Native Material Production Frontier V0.2 — VALIDATED

V0.2 tested six materially different environments across 2016–2025 and passed the adaptability sanity checks:
- 10T 1QB Start8;
- 12T 1QB Start8;
- 12T 1QB Start11;
- 12T SF Start11;
- 12T SF 2TE/TEP Start11;
- 14T SF Start10.

The frontier moved materially with team count, starting depth, Superflex, and 2TE/TEP. Shared-slot competition also moved RB/WR/TE economics rather than preserving Wookiee-fixed positional ranks.

Examples at the 0.50 sensitivity landmark:
- QB: 12T 1QB Start8 QB10 → 12T SF Start11 QB34.
- TE: 12T SF Start11 TE14.5 → 12T SF 2TE/TEP Start11 TE25.
- WR: 10T 1QB Start8 WR30 → 12T 1QB Start11 WR58.

Conclusion: **league adaptability passed as a structural prerequisite.** Raw rank cutlines must still never be universalized.

## Roster Construction Frontier V0.3 — VALID DIAGNOSTIC, NOT A DECISION RULE

V0.3 compares each sensitivity-landmark frontier with that league's effective aggregate replacement rank. It is useful for describing how far material production extends above/below replacement.

However, its 0.25/0.50/0.75 landmarks must NOT be promoted into absolute roster thresholds. The V0.3 outputs are curve probes and diagnostic evidence only.

At 0.50, examples of material reserve versus replacement were:
- 12T 1QB Start8: QB -5.5, RB -0.5, TE -6.0, WR -4.5.
- 12T SF Start11: QB +6.5, RB +1.0, TE -8.0, WR -6.0.
- 14T SF Start10: QB +9.0, RB +1.0, TE -6.5, WR -4.5.

Do not interpret these as exact roster counts. The next research layer must compare **marginal WoRP against realistic deep/capturable alternatives**.

## Historical WoRP evidence

Historical WoRP covers 2016–2025. V0.1 remains a format-agnostic baseline demonstrating repeatable decay/compression zones. Examples:
- QB31–35 0.581; QB36–40 0.352; QB41–45 0.109; QB46–50 0.023.
- RB31–35 0.611; RB36–40 0.481; RB41–45 0.347; RB46–50 0.216; RB51–55 0.130; RB56–60 0.047.
- WR31–35 0.761; WR36–40 0.601; WR41–45 0.499; WR46–50 0.410; WR51–55 0.318; WR56–60 0.245; WR61–65 0.170; WR71–75 0.044.
- TE21–25 0.644; TE26–30 0.421; TE31–35 0.281; TE36–40 0.168; TE41–45 0.065.

These are evidence about curve shape, NOT universal roster/waiver cutlines.

## Capturability guardrails

Keep these concepts separate:
- produced WoRP ≠ captured WoRP;
- FREE ≠ WAIVER;
- capturable ≠ captured;
- hindsight production ≠ ex-ante identifiability;
- compression ≠ fungibility;
- replacement ≠ availability;
- a deep alternative is economically substitutable only if its impact is sufficiently frequent, available, identifiable, and capturable at the relevant time.

Market Capture = can identify/acquire a FREE player before production.
Lineup Capture = once rostered, can choose the correct starter(s) ex ante.
WoRP captured = WoRP from the player actually in lineup. Not started = not captured.

## Optionality and roster-spot recycling

Asset valuation remains OUT OF SCOPE.

When a Non-Scoring player changes into a meaningfully higher sporting state, the manager gains capacity to act. If promotion/retention/trade/consolidation frees a roster spot, that spot can be recycled into another optionality bet.

What matters:
- probability of meaningful state change;
- magnitude after change;
- persistence;
- speed/time to meaningful state change;
- ability to recycle roster capacity.

A **clogger** is a Non-Scoring roster asset that consumes roster capacity too long without meaningful state change.

## Sleeper readonly — role and limitation

Sleeper readonly can support league settings, roster structure, weekly rosters, starters/bench, and transactions/state changes for accessible leagues/seasons. Wookiee 2023–2025 is an initial behavioral sample, not a structural ceiling.

Use diverse accessible leagues to study whether deep alternatives are actually rostered/free, how often they become relevant, whether managers could identify/acquire them before production, lineup capture after acquisition, and how all of this changes with format.

Sleeper has no documented endpoint for arbitrary/random league discovery; breadth depends on accessible/discoverable league IDs.

## Previous big-impact research

V0.7/V0.7.1 remain valid optionality evidence, not absolute roster cutline evidence. The pre-specified >=0.50 next-four-complete-weeks hurdle was a replication test landmark, not a universal materiality definition.

Key 2023–2025 evidence:
- QB material-tail hits recurred all 3 seasons.
- RB rare material hits appeared 2/3 seasons.
- WR had zero >=0.50 four-week post-shock hits despite the largest exposure pool.
- TE remained sparse/unresolved.

Historical extension of the old Non-Scoring proxy remains PAUSED unless the marginal/capturability question creates a specific need.

## Roster Diagnostic

Once league-native construction logic exists, diagnose the user's roster against it:
- Is the roster securing genuinely difficult-to-replace WoRP?
- Is roster capacity being spent on players whose marginal advantage over capturable alternatives is negligible?
- Is optionality concentrated in positions/archetypes capable of large state changes?
- Are slow-changing cloggers consuming capacity?
- Has a state change altered the optimal roster mix?

## Frozen / killed / backlog

- **KILL — Asset Value:** no market-value layer, trade pricing, pick valuation, or ADP valuation.
- **PAUSE — historical extension of old Non-Scoring proxy:** only reopen for a specific marginal/capturability need.
- **FREEZE — Structural Insights editorial hotfix loop:** V0.9.1 frozen unless material defect.
- **LAST BACKLOG — research-to-editor publication bridge.**

## Current product architecture

**League Settings → League-native WoRP Map → What This League Is Telling You → Value Cliffs → Roster Construction → My Roster Diagnostic**

Value Cliffs and Roster Construction now share an economic intuition: what matters is not merely positive production but the **marginal advantage over the next realistically obtainable alternative**.

## Methodological guardrails

- Never universalize Wookiee.
- Never turn 0.25/0.50/0.75 into absolute roster thresholds by inertia.
- Analyze deltas and curve shape.
- Raw rank cutline ≠ league-native frontier ≠ waiver threshold.
- FLEX/SF are shared eligible-slot demand.
- Compression ≠ fungibility.
- FREE ≠ WAIVER.
- Capturable ≠ captured.
- Produced ≠ captured.
- Ex-ante identification is required for a deep alternative to count as practically substitutable.
- Relative improvement above a low baseline is not automatically material.
- Statistical separation is not automatically decision materiality.
- Small marginal WoRP differences are noise unless they change decisions/outcomes.
- Optionality = large-impact frequency × magnitude × persistence × capture × speed/time-to-state-change.
- Product precision should stop when additional precision cannot change a roster decision.

## Execution contract

1. Advance autonomously through research design, diagnosis, reversible methodological choices, code, and direct GitHub commits.
2. Stop and call user only when local/Terminal execution is truly required or a genuine conceptual fork would embed an unapproved assumption.
3. Do not ask for micro-confirmations.
4. Product question drives research; old numeric sequence does not.
5. Apply materiality STOP aggressively.
6. GitHub is source of truth for research contracts/scripts; local outputs are not automatically synchronized.
7. Do not claim a script/result is validated until required local computation passes.
8. Every roster-construction result must pass league-adaptability before becoming product logic.

## IMMEDIATE NEXT GOAL

### League-Native Marginal WoRP / Capturable Alternative Curve

Build the next research layer around this question:

> **For each league and position, how much WoRP is actually gained by securing progressively deeper rostered production compared with the best realistically available, ex-ante identifiable, capturable alternative?**

Research sequence:
1. Preserve V0.2/V0.3 as economic-curve diagnostics.
2. Define league-native deeper alternative pools from actual roster/availability states where possible, not arbitrary universal rank thresholds.
3. Measure marginal WoRP deltas from secured regions to those alternatives.
4. Measure density/frequency of alternatives capable of supplying similar production.
5. Apply timing and ex-ante capturability constraints.
6. Test persistence and lineup capture.
7. Identify robust zones where the marginal advantage of additional ordinary scoring depth becomes decision-immaterial.
8. Only then translate the result into Roster Construction recommendations and revisit the `WR1* + WR1* + waiver` hypothesis by format.

Do NOT begin by choosing an absolute WoRP threshold. The target is the **marginal curve relative to realistic alternatives**.
