# WoRP Lab — Structural Insights Intelligence Backlog

Status: ACTIVE PRODUCT PRIORITY

## Product objective

The current priority of WoRP Lab is the intelligence/editorial layer of the frontend.

The frozen WoRP Engine V0.2.1, positional curve, Player Board and Value Cliffs are infrastructure. The product question is:

> What does this specific league tell a fantasy manager about roster construction?

The frontend remains clean: exactly five high-value Structural Insights. Research complexity stays behind the editor.

## Non-negotiable guardrails

- Engine V0.2.1 math stays frozen unless a separate engine-validation project is explicitly opened.
- Exactly five Structural Insights in the main frontend.
- Value Cliffs remains the senior analytical layer below the five cards.
- One economic story can occupy at most one card.
- Do not force one card per position.
- Do not force the same five templates across leagues.
- Every card must have a plausible roster-construction implication.
- Statistical truth is insufficient: an insight must be decision-material.
- Ranges beyond the league-native replacement frontier cannot drive a headline Structural Insight.
- Compression is not automatically fungibility, FREE availability, waiver value, capturability or identifiability.
- Market Capture and Lineup Capture are distinct concepts.
- Do not claim a dynamic waiver strategy is superior to rostered depth; that has not been validated.
- Do not convert historical ex-post results into predictive claims.
- Slot eligibility, not conventional slot naming, defines lineup demand. Nonstandard formats such as SFB must be first-class structures.

---

## Editorial pipeline target

Current simplified pipeline:

`historical league WoRP -> positional curve -> metric candidates -> candidate ranking -> five cards`

Target pipeline:

`evidence -> structural hypotheses -> roster-construction stories -> materiality test -> semantic dedupe -> Top 5`

Metrics are evidence. They are not automatically stories.

---

# TASK 1 — Roster Construction Story Engine

### Hypothesis
A story-first candidate layer will produce more useful and less repetitive insights than selecting raw metrics such as cliff, compression and rank value independently.

### Inputs
- league-specific historical positional curve
- league-native replacement frontier by position
- slot eligibility structure
- scoring settings
- Value Cliffs

### Candidate story vocabulary
Examples, not mandatory templates:
- elite concentration
- stars-and-depth curve
- persistent scarcity
- useful depth
- cheap marginal upgrades / compression
- expensive waiting
- format-driven positional demand
- lineup-absorbable depth
- potentially blocked depth
- replacement-sensitive roster construction

### Expected output
A structured set of candidate stories, each containing:
- economic claim
- supporting evidence
- affected position(s)
- relevant rank range(s)
- roster-construction implication
- materiality score
- confidence score
- actionability score
- semantic story ID

### PASS
Across materially different league formats, the candidate pool contains genuinely different economic stories rather than the same templates with different positions/numbers.

### Main risk
Renaming metrics as stories without actually synthesizing multiple pieces of evidence.

---

# TASK 2 — Whole-Curve Shape Detection

### Hypothesis
The editor should discover economically meaningful regions from the shape of the curve instead of depending on arbitrary windows such as 1-8, 8-20 or 20-40.

### Inputs
- full positional rank/WoRP curve
- local slopes / marginal WoRP loss
- change points / slope changes
- replacement frontier
- historical stability across selected seasons

### Logic candidate
Detect:
- steep head
- slope changes
- progressive compression
- meaningful cliffs
- low marginal-value regions
- transitions before replacement

Rank ranges are generated as evidence after detecting the shape.

### Expected output
For each position, a small set of empirically detected curve regimes with actual rank ranges.

### PASS
The same algorithm can describe structurally different curves without relying on fixed rank windows, and changing an arbitrary rank constant is no longer capable of changing the headline conclusion.

### Main risk
Over-segmentation. Mathematical breakpoints must not automatically receive semantic tier names.

---

# TASK 3 — Slot Eligibility / Lineup Capacity Model

### Hypothesis
Economic depth only matters to roster construction to the extent that the league's legal lineup can absorb it.

### Inputs
- Sleeper roster positions
- fixed positional slots
- FLEX eligibility
- SUPER_FLEX / QB-eligible eligibility
- teams
- positional replacement frontiers

### Required distinction
- fixed slots
- non-QB FLEX-eligible slots
- QB-eligible flexible slots

### Expected output
League-specific starting capacity / eligibility pressure for QB, RB, WR and TE without assuming conventional 1QB/SF structures.

### PASS
SFB/home/nonstandard leagues are interpreted from eligibility correctly without special-case league-name logic.

### Main risk
Double-counting flexible slots as guaranteed positional demand. Eligibility is capacity, not observed positional allocation.

---

# TASK 4 — Roster Utilization Pressure

### Hypothesis
A position can be economically deep while the lineup either can or cannot absorb that depth. This distinction should create useful roster-construction stories.

### Inputs
- relevant player pool before replacement
- slot eligibility capacity
- positional curve
- league format

### Candidate concept
`relevant positional supply relative to legal lineup capacity`

This is not yet a final formula.

### Expected output
Candidates such as:
- this league can absorb WR depth into starting lineups
- additional QB depth faces tighter lineup capacity
- TE depth is more/less usable because of TE/FLEX eligibility

### PASS
The metric distinguishes at least two league formats where the same positional curve would imply different roster-utilization pressure.

### Main risk
Calling legal eligibility actual historical utilization. Capacity and realized lineup usage must remain distinct.

---

# TASK 5 — Capital Efficiency

### Hypothesis
Roster construction should focus on where moving up the positional curve buys meaningful WoRP and where rank upgrades buy little.

### Inputs
- marginal WoRP curve
- detected curve regimes
- replacement frontier

### Scope
Sporting value only. No ADP, rookie picks, trade calculators or market prices unless a separate valuation layer is opened.

### Expected output
Candidates such as:
- protect access to the expensive part of the WR curve
- small upgrades in this mid-range historically buy little WoRP
- waiting through this regime has a high sporting cost

### PASS
Each candidate expresses an economically material marginal delta inside a roster-relevant region and can plausibly change a roster-construction choice.

### Main risk
Treating positional rank itself as acquisition cost.

---

# TASK 6 — Market Depth vs Lineup Depth

### Hypothesis
Economic/player-pool depth and usable lineup depth are separate dimensions and their interaction can be more informative than either alone.

### Inputs
- positional relevant pool
- replacement frontier
- lineup eligibility capacity
- later, only if validated, FREE/market availability evidence

### Expected output
A 2D structural classification such as:
- deep market + high lineup capacity
- deep market + constrained lineup capacity
- shallow market + high lineup demand
- shallow market + constrained lineup capacity

### PASS
The classification changes meaningfully across league formats and does not equate market depth with waiver availability.

### Main risk
Using the word "market" to imply FREE availability before the market-capture layer is validated league-specifically.

---

# TASK 7 — Lineup Capture Translation

### Hypothesis
Research on produced WoRP versus capturable WoRP can inform the product, but only after being translated into league-specific structural evidence.

### Existing research that motivates the task
- REAL/Manager vs ORACLE/Teto perfeito Lineup Capture V0.3: validation PASS.
- Full-Roster / Blocked-WoRP V0.5: validation PASS.
- Overall structural blockage was small in that audit; QB accounted for a disproportionate share of blocked positive WoRP.
- These historical audit results must NOT be pasted into every league's frontend.

### Inputs needed for productization
- league-specific slot eligibility
- positional relevant supply
- lineup capacity
- potentially roster-state data if a realized capture product is later opened

### Expected output
Structural candidates such as:
- depth here is easier for this lineup to absorb
- additional value here faces more lineup blockage risk

### PASS
A card can be generated from the current league's structure without importing the old audit's aggregate percentages as universal truths.

### Main risk
Calling hindsight gap manager error or projecting old realized roster behavior onto a different league.

---

# TASK 8 — Blocked Value Risk

### Hypothesis
Once useful positional supply exceeds legal lineup absorption, additional rostered value may have declining realizability.

### Inputs
- slot eligibility model
- relevant player pool
- positional WoRP curve
- validated method for allocating flexible capacity across positions

### Expected output
A candidate risk measure for redundant depth, especially where eligibility is constrained.

### PASS
The measure responds correctly to format changes (for example adding/removing QB-eligible or FLEX capacity) while holding the underlying curve constant.

### Main risk
Assuming a player is blocked simply because a theoretical positional count exceeds fixed slots; flexible-slot competition is interpositional.

---

# TASK 9 — Materiality Gate

### Hypothesis
Many statistically valid observations should never reach the frontend because they cannot change a meaningful roster-construction decision.

### Inputs
Every candidate story from the Story Engine.

### Required questions
1. Is the evidence before/at the league-native replacement frontier?
2. Is the WoRP delta economically non-trivial?
3. Does the conclusion change a plausible roster decision?
4. Is it distinct from already stronger stories?
5. Is confidence sufficient for a headline card?

### Expected output
PASS / BACKOFFICE / REJECT classification.

### PASS
Examples like deep RB50-RB72 compression cannot consume a Top-5 card when that region is outside relevant roster construction.

### Main risk
Creating a universal materiality cutoff in WoRP without validation.

---

# TASK 10 — Semantic Story Dedupe

### Hypothesis
Metric-family dedupe is insufficient. Two different calculations can tell the same economic story.

### Inputs
- semantic story ID
- position(s)
- rank regimes
- roster implication
- supporting evidence

### Example
`Superflex increases QB demand` + `QB scarcity carries deeper` may both support one story:

> This format sustains QB demand deep into the relevant pool.

### Expected output
One synthesized card using the strongest complementary evidence rather than two cards.

### PASS
No two Top-5 cards would be reasonably summarized by a manager as "these are telling me the same thing."

### Main risk
Over-deduping genuinely distinct stories that happen to involve the same position.

---

# TASK 11 — Cross-Position Contrast Engine

### Hypothesis
The most actionable structural conclusions often come from relative opportunity cost across positions, not absolute WoRP at one rank.

### Inputs
- marginal curves by position
- curve regimes
- replacement frontiers
- lineup eligibility

### Candidate comparisons
- where waiting is most expensive
- where compression begins earliest
- where elite concentration is strongest
- where relevant depth is most/least absorbable
- where replacement pressure is strongest

### Expected output
Comparative stories that explain why a manager should allocate scarce roster/draft/trade attention differently across positions.

### PASS
No conclusion relies only on a statement such as "QB12 has high WoRP"; relative scarcity/depth must be demonstrated against the relevant alternatives and format.

### Main risk
Comparing raw ranks that represent different lineup demand across positions.

---

# TASK 12 — Top-5 Editorial Diversity

### Hypothesis
Five cards should cover different decision dimensions, not mechanically different positions.

### Candidate story dimensions
- elite / concentration
- depth / compression
- format / eligibility
- utilization / capture
- replacement / capital efficiency

These are diversity dimensions, not mandatory quotas.

### Selection objective
Maximize:
- materiality
- confidence
- actionability
- league specificity
- informational diversity

while minimizing:
- semantic redundancy
- deep-tail noise
- backoffice jargon
- false precision

### PASS
Two materially different leagues can produce visibly different Top-5 sets, and each five-card set reads as a coherent roster-construction brief rather than a metric report.

### Main risk
Forcing diversity when the league genuinely has several dominant conclusions from one structural phenomenon.

---

# Deferred / research-gated product concepts

## Market Capture / waiver
Research has established that historically positive FREE production was often timing-compatible/capturable and that prior usage signals discriminate future hits. The first naive executable WR waiver policy nevertheless failed on absolute WoRP.

Therefore:
- do not publish "waiver is enough";
- do not equate compression with waiver supply;
- do not claim `WR1* + WR1* + waiver` is proven;
- dynamic replacement remains a research candidate.

## Ex-ante lineup selection
Simple prior-WoRP ex-ante baselines underperformed real managers in V0.6, and availability did not explain the full manager advantage in V0.6A. Do not put Robô/Oracle/Manager research terminology in the frontend.

## Valuation layer
Future picks, ADP and trade-market prices are outside current Structural Insights scope. Capital Efficiency here means sporting WoRP cost along the curve, not market acquisition price.

---

# Recommended implementation order

Phase A — foundation
1. Story Engine
2. Whole-Curve Shape Detection
3. Slot Eligibility / Lineup Capacity

Phase B — roster-construction intelligence
4. Roster Utilization Pressure
5. Capital Efficiency
6. Market Depth vs Lineup Depth

Phase C — capture translation
7. Lineup Capture Translation
8. Blocked Value Risk

Phase D — editor
9. Materiality Gate
10. Semantic Story Dedupe
11. Cross-Position Contrast
12. Top-5 Editorial Diversity

## STOP rule
When an exception/divergence/residual under investigation falls below 4% of the relevant universe, explicitly assess whether it can still change a product/roster decision before spending more research time.

## Definition of success
WoRP Lab should not merely describe a curve. Its five Structural Insights should feel like a concise, league-specific roster-construction brief whose conclusions are traceable to historical WoRP evidence, legal lineup structure and validated capture concepts — without exposing the research backoffice or overstating what has been proven.
