# WoRP Lab — Three-Layer Roster Construction Hypothesis V1

Status: RESEARCH HYPOTHESIS — NOT PRODUCT TRUTH

## Objective

Test whether league-specific roster construction can be described through three functional layers rather than fixed positional depth rules.

## Layer 1 — STARTERS

The lineup-base: players expected to occupy starting slots under normal conditions.

This layer must respect the league's actual slot-eligibility graph. In Superflex, for example, QB capture paths differ from 1QB; FLEX slots are shared eligibility rather than assigned positional capacity.

## Layer 2 — SCORING BENCH

Bench players deliberately rostered because there is a reasonable expectation that they will enter the lineup during normal seasonal operation: bye weeks, short injuries, matchup decisions, legitimate competition for a starting spot, or other recurring lineup needs.

"Scoring" does not mean that bench points themselves are captured. WoRP is captured only when the player is actually started. The label means the player belongs to the planned scoring capacity of the roster.

The size of this layer must be discovered empirically, not assumed. In a start-11 format, do not predeclare that four, five, or any other number of scoring-bench players is optimal.

Candidate diagnostic: after the nominal starter layer, measure how frequently successive roster-depth levels enter the optimal legal lineup (ORACLE / Teto perfeito). Look for a meaningful utilization decline/cliff rather than imposing a fixed bench count.

## Layer 3 — NON-SCORING / CONTINGENT BENCH

Players not normally expected to enter the lineup. Their roster value depends primarily on observable changes of state that can transform their expected role/value.

Examples of the concept:
- backup NFL QB becomes starter;
- backup RB inherits major workload after starter absence;
- other role/depth-chart changes that create a material week-to-week opportunity jump.

The research question is which positions and player archetypes produce these state changes most often, how large the resulting WoRP opportunity is, and how identifiable the change is before kickoff.

This layer is not automatically waiver/free. A contingent player may already be rostered. NON-SCORING/CONTINGENT is a roster-function concept, not a market-availability label.

## Central construction hypothesis

Roster construction may be represented as:

**Starting Capacity + Planned Scoring Depth + Contingent Upside**

Once a league's normal scoring-depth requirement is satisfied, marginal roster spots may be better evaluated by their contingent upside rather than by accumulating additional players with low normal lineup utilization.

This is a hypothesis to test, not a conclusion.

## Research sequence

### Stage A — Find the Scoring-Bench frontier

Using actual league format, rosters and weekly outcomes:

1. Build the optimal legal lineup from each roster-week (ORACLE).
2. Rank/organize roster depth using a legitimate pre-week or season-level economic ordering without using target-week outcome to define the ordering.
3. Measure for each depth level / economically meaningful tier:
   - eligible roster-weeks;
   - ORACLE lineup-hit weeks;
   - lineup-hit rate;
   - persistence of lineup-hit status;
   - positive WoRP produced outside ORACLE;
   - positive WoRP selected by ORACLE.
4. Search for a meaningful utilization decline/cliff after the starter layer.
5. Do not force a universal bench count or equal-sized positional tiers.

Purpose: estimate how much planned scoring depth a specific league can economically use.

### Stage B — Decompose the frontier by position

After a league-level frontier is visible, analyze QB, WR, RB and TE behavior.

QB: Superflex is the primary informative case, with 1QB as structural contrast. Test persistent elite occupancy versus ambiguous competition among similarly valued QBs.

WR: test whether deeper WR tiers remain frequently lineup-worthy but create weekly selection ambiguity.

RB: use as contrast/control for the hypothesis that state changes can create large, more legible workload/value jumps.

TE: test persistent elite occupancy, FLEX paths and contingent role changes under actual eligibility.

### Stage C — Identify contingent-upside behavior

For players outside normal planned scoring depth, detect week-to-week state changes and measure:
- baseline lineup-hit frequency;
- frequency of material role/opportunity jumps;
- magnitude of WoRP change after the jump;
- whether the change was knowable before kickoff;
- duration/persistence of the changed state.

Only after this stage can the project compare which positions/archetypes are best suited to contingent roster spots.

## Existing evidence that motivates, but does not prove, this framework

Prior full-roster audit V0.5 found that only ~5.9% of owned positive WoRP was structurally blocked by the optimal legal lineup. QB had the largest blocked share (~12.0%), while WR/RB/TE were much lower. For WR, missed-lineup positive WoRP was substantially larger than structurally blocked positive WoRP.

Therefore the research should not assume that bench depth is broadly wasteful. The important unresolved problem is how often depth is normally usable, how difficult it is to select, and when contingent state changes create a better use of marginal roster spots.

## Guardrails

- Captured WoRP requires the player to be in the actual lineup.
- ORACLE selection is an ex-post structural diagnostic, not actual capture.
- ORACLE frequency is not manager skill and not ex-ante predictability.
- Legal eligibility is not realized positional allocation.
- FLEX belongs to its eligibility set, not automatically to WR/RB/TE.
- NON-SCORING BENCH is not synonymous with FREE, waiver, fungible, replacement or valueless.
- SCORING BENCH size must be discovered by league/format, not hard-coded.
- Do not assume RB contingent upside beats WR/QB/TE; test it.
- Do not assume season rank alone defines roster layer.
- Do not use target-week outcomes as pregame signals.
- Do not translate this into production recommendations until validated across materially different formats.

## Product destination if validated

The long-term product goal is individualized roster-construction guidance by league, potentially answering:

1. how much normal scoring depth the format can use;
2. where additional depth begins to have low normal lineup utilization;
3. which positions/archetypes historically provide the strongest identifiable contingent upside for remaining roster spots.

The frontend should express this in manager language, not research labels such as ORACLE.
