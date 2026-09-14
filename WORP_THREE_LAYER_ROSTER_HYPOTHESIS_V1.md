# WoRP Lab — Three-Layer Roster Construction Hypothesis V1

Status: RESEARCH HYPOTHESIS — NOT PRODUCT TRUTH

## Objective

Test whether league-specific roster construction can be described through three **fluid functional states** rather than fixed positional depth rules.

The three layers are not permanent player classifications. A player can move between them as role, opportunity, health, depth chart and roster context change.

## Layer 1 — STARTERS

The lineup-base: players expected to occupy starting slots under normal conditions.

This layer must respect the league's actual slot-eligibility graph. In Superflex, for example, QB capture paths differ from 1QB; FLEX slots are shared eligibility rather than assigned positional capacity.

## Layer 2 — SCORING BENCH

Bench players deliberately rostered because there is a reasonable expectation that they will enter the lineup during normal seasonal operation: bye weeks, short injuries, matchup decisions, legitimate competition for a starting spot, or other recurring lineup needs.

"Scoring" does not mean that bench points themselves are captured. WoRP is captured only when the player is actually started. The label means the player belongs to the planned scoring capacity of the roster.

The size of this layer must be discovered empirically, not assumed. In a start-11 format, do not predeclare that four, five, or any other number of scoring-bench players is optimal.

## Layer 3 — NON-SCORING / CONTINGENT BENCH

Players not normally expected to enter the lineup. Their roster value depends primarily on observable changes of state that can transform their expected role/value.

Examples:
- backup NFL QB becomes starter;
- backup RB inherits major workload after starter absence;
- other role/depth-chart changes that create a material week-to-week opportunity jump.

This layer is not automatically waiver/free. A contingent player may already be rostered. NON-SCORING/CONTINGENT is a roster-function state, not a market-availability label.

## States are fluid

A player may follow a path such as:

**NON-SCORING → SCORING BENCH → STARTER**

and later move back down the stack.

The research therefore should not attempt to permanently label players as one of the three types. It should identify the player's current functional state and meaningful transitions between states.

## Promotion Event

A **Promotion Event** is not a fourth roster layer. It is an event that materially changes a player's expected role or usefulness and can move the asset upward through the roster states.

Examples include injury ahead of the player, a depth-chart promotion, becoming an NFL starting QB, or another durable opportunity change.

A promotion can create two distinct forms of value:

1. **Sporting value / WoRP opportunity** — if the player becomes lineup-worthy and is actually started, his WoRP can be captured.
2. **Asset-value opportunity** — the player's dynasty/trade value may increase even if the manager does not need to start him.

These must remain analytically separate. WoRP can measure the sporting side. Trade/market appreciation requires a separate valuation layer and must not be inferred from WoRP alone.

## Roster recycling hypothesis

If a NON-SCORING player experiences a durable Promotion Event, the roster may gain surplus productive depth or asset value. That can create an opportunity to:

**PROMOTE / START / KEEP / TRADE → free or reallocate roster capacity → acquire another contingent option**

Conceptually:

**acquire cheap optionality → wait for state change → capture production and/or asset appreciation → retain or trade promoted value → recycle roster spot into new optionality**

This is a hypothesis to test, not a proven strategy.

## Central construction hypothesis

Roster construction may be represented as:

**Starting Capacity + Planned Scoring Depth + Contingent Optionality**

The manager needs both production and roster asset accumulation. Once normal scoring-depth requirements are satisfied, marginal roster spots may be better evaluated by their probability and magnitude of useful state change rather than simply by accumulating additional low-utilization scoring depth.

The eventual league-specific question is:

> After satisfying Starter + Scoring Bench needs, which positions/archetypes offer the best combination of promotion probability, post-promotion sporting value, identifiability before kickoff, persistence of the new state, and — in a separate valuation layer — asset appreciation?

## Research sequence

### Stage A — Estimate normal scoring-depth demand

Using actual league format, rosters and weekly outcomes, characterize how many players beyond the lineup core are recurrently consumed by normal lineup operation.

Do not force a universal bench count or arbitrary frequency cutoff. Initial Wookiee utilization work showed a gradual curve rather than an obvious cliff, so frequency alone cannot define the layers.

### Stage B — Detect state transitions

Identify players moving from low expected lineup utilization into materially higher opportunity states. Measure:
- baseline lineup utilization;
- size of opportunity change;
- duration/persistence of the promoted state;
- subsequent lineup-worthiness;
- WoRP produced after promotion;
- WoRP actually captured when started;
- whether the state change was identifiable before kickoff.

### Stage C — Compare promotion behavior by position/archetype

QB: Superflex primary case, 1QB structural contrast. Test backup-to-starter transitions and ambiguity among multiple usable QBs.

RB: test injury/depth-chart driven workload jumps and whether they create relatively legible promotion events.

WR: test whether state changes are smaller/more gradual or whether specific archetypes generate durable promotion events.

TE: test elite-slot persistence, FLEX paths and opportunity changes under actual eligibility.

Do not assume any positional ordering before measurement.

### Stage D — Add asset valuation separately

Only after sporting state transitions are validated should the project introduce dynasty market/trade valuation data to test whether promotion events also create monetizable asset appreciation.

This layer is necessary to study SELL / HOLD / RECYCLE decisions. WoRP alone cannot establish trade value.

## Existing evidence that motivates, but does not prove, this framework

Prior full-roster audit V0.5 found that only ~5.9% of owned positive WoRP was structurally blocked by the optimal legal lineup. QB had the largest blocked share (~12.0%), while WR/RB/TE were much lower. For WR, missed-lineup positive WoRP was substantially larger than structurally blocked positive WoRP.

The first utilization-frequency audit also found no obvious cliff after the nominal Start-11 boundary: utilization declined gradually through roster depth. Therefore a fixed "11 + N" definition should not be imposed from frequency alone.

These findings motivate a state-transition framework rather than a static bench-depth classification.

## Guardrails

- Captured WoRP requires the player to be in the actual lineup.
- ORACLE selection is an ex-post structural diagnostic, not actual capture.
- ORACLE frequency is not manager skill and not ex-ante predictability.
- Legal eligibility is not realized positional allocation.
- FLEX belongs to its eligibility set, not automatically to WR/RB/TE.
- NON-SCORING BENCH is not synonymous with FREE, waiver, fungible, replacement or valueless.
- The three roster layers are states, not permanent player labels.
- A Promotion Event is a transition, not a fourth layer.
- SCORING BENCH size must be discovered by league/format, not hard-coded.
- Do not assume RB contingent upside beats WR/QB/TE; test it.
- Do not use target-week outcomes as pregame signals.
- WoRP measures sporting value, not dynasty market/trade price.
- Asset appreciation and sell/recycle decisions require a separate valuation layer.
- Do not translate this into production recommendations until validated across materially different formats.

## Product destination if validated

The long-term product goal is individualized roster-construction guidance by league, potentially answering:

1. how much normal scoring depth the format can use;
2. how much roster capacity can be allocated to contingent optionality;
3. which positions/archetypes produce the strongest identifiable and persistent Promotion Events;
4. when a promoted player should strengthen the scoring layers versus, after a separate valuation analysis, become a candidate for value recycling.

The frontend should express this in manager language, not research labels such as ORACLE.
