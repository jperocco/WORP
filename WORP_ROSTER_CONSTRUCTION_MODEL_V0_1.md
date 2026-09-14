# WoRP Lab — Roster Construction Model V0.1

Date: 2026-09-14
Status: WORKING MODEL

## Purpose

Define a product-oriented roster-construction model that translates league format into a recommended allocation of roster capital across three fluid functional layers:

1. STARTERS
2. SCORING BENCH
3. NON-SCORING BENCH / OPTIONALITY

This model is not a mathematically exact player-state classifier. It is a decision framework for answering:

> Given this league's lineup and scoring structure, how much productive depth should the manager buy at each position before additional roster spots should be treated primarily as optionality inventory?

The product objective is to recommend an ideal roster shape and then alert the user when player-state changes materially push the roster away from that shape.

---

## 1. Core product equation

**league format → eligible lineup demand → scoring-depth demand → diminishing lineup utility → optionality hurdle**

The model must be league-native. There is no universal QB2, WR60 or RB50 cutoff that automatically defines a state.

The same player/rank can have a different functional state in:
- 1QB vs Superflex;
- 2WR vs 3WR;
- shallow FLEX vs FLEX-heavy;
- 1TE vs 2TE;
- standard TE scoring vs TEP;
- shallow vs deep roster sizes.

---

## 2. Functional layers

### STARTERS
Principal productive capital.

Expected normal lineup core for the specific league format.

### SCORING BENCH
Reserve productive capital.

Players rostered because there is a meaningful expectation they will enter the lineup during normal seasonal operation: bye, injury, matchup, rotation, legitimate competition, or flexible-slot demand.

Important: bench points are not captured. WoRP is captured only when the player is actually STARTED.

### NON-SCORING BENCH / OPTIONALITY
Optional capital.

Players with low normal expected lineup use whose main reason to occupy a roster spot is asymmetric upside from a meaningful state change.

Examples of possible state-change paths:
- backup RB inherits a concentrated workload;
- backup QB becomes an NFL starter;
- young/deep player earns a materially larger role;
- injury/depth-chart change moves an asset into the Scoring layer.

A player can move fluidly between layers. A Promotion Event is a transition, not a permanent label.

---

## 3. What V0.1 should optimize

V0.1 does NOT try to solve one global mathematical optimum.

It should produce, by position and format:

### A. Scoring Depth Zone
The region where carrying another player at a position still has meaningful expected lineup utility.

This can be justified by some combination of:
- eligible starting-slot demand;
- replacement frontier / relevant WoRP curve;
- historical lineup-use frequency;
- lineup ambiguity among similarly useful assets;
- injury/bye/rotation coverage;
- FLEX/SF competition.

### B. Transition Zone
The region where another player at the position may still have some lineup utility but the marginal benefit is falling sharply.

This is a decision zone, not an exact rank cutoff.

### C. Optionality Zone
The region where an additional player at the position should no longer be justified mainly by ordinary lineup depth.

At this point the player must clear a higher optionality hurdle:
- plausible path to a meaningful state change;
- magnitude of value created after promotion;
- likelihood that the resulting production can actually be captured in the lineup;
- potential market-value appreciation, if/when a separate valuation layer exists.

---

## 4. Positional working hypotheses

These are hypotheses to calibrate, not conclusions.

### QB
QB roster construction is driven strongly by eligible-slot count and quality distribution.

Key principle: **QB1 + QB1 + QB1**.

Three similarly useful QBs competing for two QB-eligible lineup spots may all belong to the competitive Scoring layer. The third QB is not automatically Non-Scoring simply because he is third on a roster.

Conversely, a clearly contingent QB behind two stable superior QBs may be Optionality.

Therefore QB state depends on:
**relative economic quality + QB-eligible slots + competition + expected use**.

1QB and SF must be treated differently.

### RB
Working hypothesis: RB may become attractive in the Optionality layer because some state changes transfer workload more mechanically and rapidly than at WR.

A backup RB can move from low expected use to high-value Scoring/Starter state after one depth-chart injury or workload change.

This does not mean every backup RB is good optionality; the product should care about the shape and plausibility of the promotion path.

### WR
Working hypothesis: WR can deserve substantial capital in the Scoring layer but lose relative priority once the roster reaches the Non-Scoring layer.

Reasons under investigation:
- WR/FLEX-heavy formats create legitimate scoring-depth demand;
- several WRs may be lineup-useful across a season;
- deep WR production can be difficult to capture because similar WRs compete for limited lineup spots;
- opportunity after one injury ahead may diffuse across multiple receivers rather than transfer cleanly;
- the deep WR economic tail is compressed;
- once ordinary lineup coverage is satisfied, another deep WR may have lower optionality value than an alternative position/archetype.

The model should therefore seek a **format-dependent WR cut zone / hurdle**, not a universal WR rank cutoff.

### TE
Elite TE may close the position in some formats; 2TE/TEP can radically increase scoring-depth demand.

TE optionality cannot be interpreted from V0.4's low captured-WoRP sample alone. That result is a flag for further audit, not a conclusion.

---

## 5. Evidence already available to V0.1

### A. League-native WoRP curves
The engine already gives league-specific positional WoRP curves and replacement frontiers.

These define the economic shape of positional supply and where marginal value compresses.

Guardrail: compression is not waiver/fungibility and replacement rank is not automatically the Scoring/Optionality boundary.

### B. Actual historical lineup-use research
Season-long counts showed no clean universal Scoring Bench size. Distinct starters per roster-season and start-frequency curves are useful evidence, but not a direct state classifier.

This supports using zones/heuristics rather than pretending there is a fixed universal bench count.

### C. Produced vs captured WoRP
Existing research shows that useful WoRP can be produced without being captured because the player remains benched.

This is central to roster construction: more productive assets are not always more useful if they create lineup ambiguity that the manager cannot reliably convert into starts.

### D. Promotion / Optionality research
V0.3.1 and V0.4 show that low-use assets can transition into active episodes and that promotion frequency is reasonably stable under 3/5/8-week lookbacks.

V0.4 L5 descriptive proxy rates:
- QB 2.43%
- RB 2.76%
- TE 2.60%
- WR 3.11%

These are not true semantic promotion probabilities.

More important for V0.1 is that promotion value differs from captured value:
- QB produced 0.6400 WoRP / 100 exposure weeks; captured 0.2924
- RB produced 0.3780; captured 0.0881
- TE produced 0.3146; captured 0.0020
- WR produced 0.3848; captured 0.1289

These numbers calibrate the optionality hurdle but do not by themselves rank positions.

---

## 6. First V0.1 product object

For each league, build a table conceptually like:

| Position | Starting demand | Scoring Depth recommendation | Transition zone | Optionality posture |
|---|---:|---|---|---|
| QB | format-derived | league-specific | league-specific | depends strongly on 1QB/SF and quality distribution |
| RB | format-derived | league-specific | league-specific | potentially strong asymmetric optionality |
| WR | format-derived | often deeper in FLEX-heavy formats | important cut zone | higher hurdle once lineup depth is satisfied |
| TE | format-derived | highly format/TEP dependent | league-specific | unresolved pending stronger optionality evidence |

V0.1 should not output fake precision. Acceptable outputs include ranges and confidence labels.

Example style:
- "Carry 5–6 WRs as expected scoring depth; WR exposure beyond that should justify itself primarily through optionality."
- "In this SF structure, three comparable QBs can still be productive depth; a fourth QB needs a much stronger state-change case."

Those are product statements only when supported by the league's actual slot demand and curve evidence.

---

## 7. Drift detection after the model exists

Once an ideal roster shape is defined, the product can monitor changes in state.

Example:
- roster target: 2 Starter/Scoring RBs + 2 Scoring Depth RBs + 2 Optionality assets;
- a Non-Scoring RB is promoted by a meaningful NFL role change;
- roster now contains one extra upper-layer asset;
- product alert: roster has become overweight in scoring capital relative to the target model;
- manager choices: KEEP / START / TRADE / RECYCLE.

The alert does not need to prove an exact mathematical state score. It needs a material, defensible change in role/value relative to the roster model.

---

## 8. V0.1 research sequence

### Step 1 — Format demand
For each test league, derive the eligible starting demand by position from lineup settings.

Do not assign FLEX/SF to a position in advance. Treat them as shared eligible demand.

### Step 2 — Scoring-depth evidence
Use league-native WoRP curves, replacement frontiers and historical lineup-use evidence to estimate where additional positional depth still has meaningful lineup utility.

Output a RANGE / ZONE, not a brittle point estimate.

### Step 3 — Optionality hurdle
For roster capacity beyond the Scoring Depth zone, use the Promotion research to compare the attractiveness of position/archetype types.

Primary considerations:
- path to state change;
- value created after promotion;
- capture friction;
- economic redundancy / tail compression.

### Step 4 — Cross-position allocation
Ask the actual product question:

> After satisfying Starter + Scoring Depth needs, where should the next bench spot go?

This is the first true roster-construction comparison.

### Step 5 — Validate across materially different league formats
At minimum:
- 1QB conventional;
- Superflex;
- FLEX-heavy;
- 2TE/TEP.

If the model recommends essentially the same roster shape across these formats, it has failed.

---

## 9. STOP rules

Stop and reassess if:
- a proposed cutoff changes little or nothing about the roster decision;
- the model is tuning rank boundaries without changing position allocation;
- a residual dispute affects <4% of the relevant universe and has no material decision impact;
- a metric is becoming more precise while the product recommendation remains unchanged;
- a proxy contradicts the relational roster-state concept (especially QB1 + QB1 + QB1).

The model exists to improve roster decisions, not to maximize methodological ornamentation.

---

## 10. Canonical next implementation task

Build the first **Roster Construction Worksheet** for the existing validation leagues using only already-supported evidence:

1. league format / slot eligibility;
2. league-native replacement frontier and WoRP curve;
3. observed historical lineup-use depth;
4. existing produced-vs-captured and promotion evidence.

For each position, output:
- Starting Demand;
- tentative Scoring Depth Zone;
- tentative Transition Zone;
- Optionality Hurdle: LOW / MEDIUM / HIGH;
- confidence;
- one plain-English reason.

Do not integrate this into the frontend yet. First inspect whether the resulting recommendations are materially different and intuitively coherent across the validation leagues.

If they are, the next product step is to connect roster-state drift alerts to this model.
