# WoRP Lab — Frontend Touchpoint — 2026-09-13

## STOP / reprioritization

Research expansion is PAUSED. Immediate priority is the WoRP Lab frontend and Structural Insights product layer.

The WoRP Engine V0.2.1 remains frozen and unchanged. The research/backoffice remains useful as evidence, but must not leak into the product UI.

## Product north star

Return to the V1 philosophy:

- clean;
- exactly 5 headline insights;
- simple language;
- league-specific;
- actionable / ready to go;
- substantially more accurate than V1 because the new research informs selection underneath the hood.

The product question is: **What is this league teaching the fantasy manager?**

Not: show the research process, every detected pattern, or every numeric breakpoint.

## What failed in V0.7.0

The first V0.7.0 Structural Tiers frontend is NOT approved as product direction.

Observed failure modes:

1. Too many numbers and too much detail.
2. Backoffice/research logic exposed in the frontend.
3. A wall of tiers across every position instead of editorial prioritization.
4. Mathematical segments were automatically given semantic names they had not earned.
5. Implausible labels such as `High-Value Tier (WR9–WR53)` and `Core Tier (WR54–WR96)` demonstrate why segmentation cannot automatically become product semantics.
6. Excessive attention to WR because WR is the hardest research problem. The frontend must evaluate QB/RB/WR/TE together and surface only the most material league-level conclusions.
7. Rank-level precision was promoted into conclusions even when economically marginal. Example: the exact last rank slightly above zero WoRP is usually less useful than the broader shape of the curve.

## Hard frontend rules

### 1. Five insights only

Structural Insights should publish **exactly five** headline insights.

The backoffice may generate many candidates. The frontend must select the five most useful.

### 2. Editorial selection layer

Pipeline:

`many measured signals -> candidate insights -> materiality/confidence/actionability ranking -> redundancy filter -> Top 5`

A statistically detectable result does not automatically deserve frontend space.

### 3. Actionability over precision theater

Prefer conclusions such as:

- elite value separates unusually fast;
- a position retains useful depth;
- a middle/deep region is compressed;
- a format rewards scarce value;
- a positional curve gives the manager more/less flexibility.

Avoid promoting marginal exact cutoffs unless the cutoff materially changes a roster decision.

### 4. Tier syntax

When a tier is mentioned, the rank range MUST appear in parentheses.

Example syntax:

`Elite Tier (WR1–WR8)`

Never show a tier label without its range.

### 5. Tiers are asymmetric

Do not force 12-player buckets or equal-size tiers. A bottom tier may legitimately be very large.

But: a detected mathematical segment is NOT automatically a semantically validated tier.

### 6. No automatic semantic tier names

Do not assign `Elite`, `High-Value`, `Core`, `Compressed`, or `Deep` merely from segment order.

A tier name must be supported by its economic behavior and validated product logic.

Until that validation exists, use the underlying segmentation only as backoffice evidence for an insight.

### 7. No research vocabulary in product

Do not expose Oracle, REAL, EX-ANTE, robot, audit versions, research fixture, blocked-WoRP diagnostics, or other research diary terminology in Structural Insights.

### 8. Balanced positional editorial layer

WR may generate more research because it is difficult, but the product is not WR Lab.

Candidate insights must be compared across QB/RB/WR/TE. Five slots go to the five most decision-relevant conclusions for the selected league, not one slot per position and not the five strongest WR findings.

### 9. Historical, not predictive

WoRP remains descriptive. Product language may give roster-construction implications supported by the historical structure, but must not pretend to project individual future player outcomes.

## Reprioritized evidence

### Tier 1 — product-ready foundations

Highest priority for Structural Insights:

- exact Sleeper league scoring and roster format;
- frozen WoRP Engine V0.2.1;
- league-specific historical positional curves;
- elite concentration / steepness;
- relative positional depth;
- meaningful cliffs;
- progressive compression;
- low marginal-value regions;
- natural/asymmetric economic regimes when sufficiently validated;
- cross-position comparison of those structures.

### Tier 2 — useful backoffice evidence, not direct UI

Use to improve confidence and wording, not as cards:

- fixed-12 tier challenge;
- breakpoint studies;
- cents / economic magnitude;
- historical stability of curve shape;
- STARTED/BENCHED/FREE;
- temporal FREE capturability;
- capture quality;
- ex-ante signal discrimination;
- lineup capture / roster utilization findings.

### Tier 3 — research only / unresolved

Do not turn into actionable frontend claims yet:

- `WR1* + WR1* + waiver` as a proven strategy;
- compressed tail = fungibility;
- compressed tail = waiver availability;
- exact waiver threshold;
- number of lineup slots safely outsourced to waivers;
- simple prior-WoRP ex-ante selector as decision engine;
- intrinsic manager skill/unpredictability claims from Manager vs hindsight/ex-ante gaps.

## Important validated guardrails

- Compression != fungibility != FREE != waiver capturability != strategy.
- Exact bottom-rank boundaries are secondary when moving them does not change a decision.
- Do not force the waiver hypothesis; fully rostered depth may ultimately win.
- Research findings should influence the product only at the confidence level they earned.

## Desired Structural Insight form

Each of the five outputs should read approximately as:

**Actionable headline**  
One short sentence explaining the league-specific evidence and implication.

Numbers are supporting evidence, not the product itself. Use the minimum number needed to make the conclusion credible.

If a validated tier materially improves the insight, include it with mandatory parenthetical range syntax, e.g. `Elite Tier (WR1–WR8)`.

## Current product status

- Engine V0.2.1: frozen / valid.
- UI V0.6.3: prior clean baseline.
- UI V0.7.0: generated and runnable, but Structural Tiers presentation rejected as product direction.
- Next frontend target: **V0.7.1 — V1 philosophy + richer validated evidence underneath.**

## Immediate work order

1. Freeze new research expansion.
2. Use V0.6.3/V1-style clean presentation as UX reference.
3. Replace the V0.7.0 tier wall with a five-insight editorial engine.
4. Keep tier detection and research evidence backstage.
5. Validate semantic tier naming before allowing named tiers into generated copy.
6. Review the five generated insights for balance, materiality, redundancy, and actionability.
7. Only after the frontend is approved, resume deeper research.
