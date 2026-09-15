# WoRP Lab — Roster Construction Research Handoff

Date: 2026-09-15
Status: ACTIVE — HIERARCHY RESET

## Product objective

WoRP Lab remains a sporting-performance product. It does NOT need to model trade prices, picks, ADP, market value, or asset valuation.

Current product hierarchy:

1. WoRP / league economic map.
2. What This League Is Telling You.
3. Value Cliffs.
4. Roster Construction — primary research priority.
5. Roster Diagnostic — next product layer after construction logic is sufficiently validated.
6. Research-to-editor automation / Top-5 publication bridge — LAST backlog item, not a current priority.

The main research goal is to turn league economics into a decision-useful answer to:

> **How deep at each position does sporting production remain materially capable of helping win, with enough consistency and repeatability to matter?**

The product should prefer simple, decision-material boundaries/zones over mathematically elaborate state classifiers.

## New primary abstraction — Material Production Cutline

Roster Construction should first seek the positional region where WoRP stops being materially relevant to winning.

For each position and league format, ask:

- Where is WoRP magnitude still large enough to matter?
- How consistently does that impact occur?
- How repeatable is the result across seasons?
- At what depth/rank does the distribution effectively become economic zero for normal winning production?

Examples of the question, NOT assumed answers:
- Does RB impact remain material through roughly RB35?
- Does WR impact remain material through roughly WR35, WR45, or somewhere else?
- Does the same cut region recur across seasons and formats?

**Economic zero does not mean mathematical WoRP = 0.000.** It means remaining differences are too small, too rare, or too unstable to plausibly change roster construction, weekly outcomes, or season-winning decisions.

The cutline should be discovered from the data, not assumed from conventional fantasy ranks.

## Governing materiality principle

Optimize research for large, decision-material impacts.

Small differences such as 0.061 vs 0.045 WoRP are operationally zero vs zero unless there is evidence that they compound into a material weekly/season effect.

Before spending research time on a difference, ask:

> **Could this plausibly change how a manager builds a roster, sets a lineup, or wins meaningful weeks/seasons?**

If no, classify it as noise and STOP.

Do not optimize thresholds by tiny increments. Seek robust zones where the decision changes.

If a residual technical dispute affects less than 4% of the relevant universe and cannot change the decision, trigger STOP rather than continue tuning.

## Roster Construction — simplified hierarchy

The three fluid roster states remain useful as operational language, but they are no longer the object that must be perfectly classified first.

1. **STARTER** — normal productive lineup core.
2. **SCORING DEPTH** — additional rostered production that still has a meaningful path to material lineup impact.
3. **NON-SCORING OPTIONALITY** — roster capacity below/outside normal material production, justified primarily by the possibility of a meaningful state change.

Preferred research sequence:

**WoRP distribution → Material Production Cutline → lineup/slot demand → useful scoring depth → remaining roster capacity becomes optionality → diagnose roster against that structure.**

Do not derive a perfect Starter/Scoring/Non-Scoring classifier before answering the simpler economic question.

## Optionality and roster-spot recycling

Asset valuation is OUT OF SCOPE.

The only value-generation concept required is:

> When a Non-Scoring player changes into a meaningfully higher sporting state, the manager gains capacity to act. The player can be promoted, retained, traded, consolidated in a 2-for-1, or otherwise moved; if that action frees a roster spot, the manager can make another optionality bet.

The model does NOT need to know the trade price or quantify market appreciation.

What matters for roster construction is the efficiency of Non-Scoring capacity:

- probability of meaningful state change;
- magnitude of sporting impact after the change;
- persistence of the new state;
- speed/time to meaningful state change;
- ability to recycle the roster spot into another bet after promotion/action.

### Clogger

A **clogger** is a Non-Scoring roster asset that consumes roster capacity for too long without generating a meaningful state change.

Therefore optionality should not be judged merely by number of small positive outcomes. The research should care about **large transitions and roster-time consumed to generate them**.

## Sporting impact only

WoRP measures sporting value.

Do NOT add an Asset Value layer to this project.
Do NOT research trade prices, picks, ADP, market appreciation, or dynasty market valuation unless the product scope is explicitly changed later.

A state change matters because it creates sporting usefulness and managerial capacity; the app does not need to price the resulting transaction.

## Sleeper readonly — role and limitation

Sleeper readonly is a major empirical source for Roster Construction and Roster Diagnostic.

It can support reconstruction of league settings, roster structure, weekly rosters, starters/bench, and transaction/state changes for accessible leagues/seasons.

This means the existing 2023–2025 Wookiee dataset is an initial sample, NOT a structural ceiling on roster-behavior research.

However, do not claim a universal multi-league sample before inventorying the league IDs / historical leagues actually accessible to the project. Sleeper provides the infrastructure; sample breadth must be measured.

Use Sleeper primarily after/alongside the WoRP economic cutline work to study:

- how real rosters allocate depth around the material production region;
- how often below-cutline players cross into material production;
- time to state change / clogger behavior;
- realized lineup capture after state changes;
- differences by league format, roster size, scoring, and slot eligibility.

## Historical WoRP advantage

Local project inventory confirms WoRP data covering 2016–2025, including weekly WoRP, rankings, normalized data, relevant universe, band sensitivity, and tier-by-season outputs.

Therefore the first Material Production Cutline study does NOT require Sleeper roster history.

Use the 2016–2025 WoRP history first to answer:

> **At what positional depth does WoRP stop producing material winning impact with enough consistency and cross-season repeatability to treat deeper normal production as economic zero?**

Sleeper then becomes the behavioral/roster layer used to translate that economic frontier into construction and diagnostic guidance.

## Primary cutline tests

For each position/rank region, evaluate three things first:

1. **Magnitude** — is the WoRP large enough to matter?
2. **Consistency** — does material impact occur often enough rather than depending on isolated spikes?
3. **Repeatability** — does the economically relevant region recur across seasons rather than being a one-year artifact?

Do not force a universal exact rank if evidence supports a transition zone instead.

Do not define 'material' by choosing a threshold that favors a position. Use distributional evidence and decision-scale sensitivity, then look for a robust zone where the roster decision changes.

## Relationship to previous big-impact research

V0.7 and V0.7.1 remain valid evidence, but the prior attempt to broaden the 2023–2025 Non-Scoring proxy historically is PAUSED.

Validated V0.7/V0.7.1 finding at the pre-specified >=0.50 WoRP / next-four-complete-weeks replication hurdle:
- QB showed material-tail hits in all 3 observed seasons.
- RB showed rare material hits in 2/3 seasons.
- WR showed zero >=0.50 four-week post-shock sporting hits in all 3 seasons despite the largest exposure pool.
- TE remained unresolved/sparse.

This is useful optionality evidence, not the next research priority.

Do not spend time tuning 0.50 vs nearby thresholds or extending the old proxy by inertia.

The next research priority is the simpler and more fundamental **Material Production Cutline** using 2016–2025 WoRP history.

## Roster Diagnostic — second priority

Once a decision-useful construction model exists, diagnose a user's actual roster against it.

The diagnostic should eventually answer questions such as:
- Is the roster underweight in materially useful scoring depth?
- Is too much roster capacity sitting below the material cutline?
- Are Non-Scoring spots being consumed by slow-changing cloggers?
- Is the roster carrying optionality in positions/archetypes that rarely generate material state changes?
- Has a recent promotion/state change altered the optimal roster mix?

Do not build the diagnostic before the construction logic is sufficiently validated.

## Frozen / killed / backlog work

### KILL — Asset Value
No market-value layer. No trade pricing. No pick valuation. No ADP valuation.

### PAUSE — historical extension of the old V0.7 Non-Scoring proxy
Do not continue merely because it was the previous task. Revisit only if the cutline/construction research creates a specific need.

### FREEZE — Structural Insights editorial hotfix loop
V0.9.1 remains frozen unless a material defect appears.

### LAST BACKLOG — research-to-editor publication bridge
The automatic bridge from research evidence to Top-5 frontend cards is intentionally deferred. First improve the underlying roster-construction intelligence.

## Current product architecture

Keep the final product compact. Current intended architecture:

**League WoRP Map → What This League Is Telling You → Value Cliffs → Roster Construction → My Roster Diagnostic**

A future player/trade decision layer is not a current priority and must not require market valuation.

The product should answer manager decisions, not expose research machinery.

## Methodological guardrails to preserve

- WoRP captured = WoRP from a player actually in the lineup. Not started = not captured.
- Produced WoRP ≠ captured WoRP.
- Capturable ≠ captured.
- FREE ≠ WAIVER.
- Compression ≠ fungibility.
- FLEX/SF are shared eligible-slot demand, not position-owned slots.
- Relative improvement above a low baseline does not automatically equal material impact.
- Statistical separation does not automatically equal decision materiality.
- Do not use tiny mean differences as roster-construction evidence.
- Do not claim WR60/WR72/WR80 or any other rank as a waiver threshold without evidence.
- A material production cutline is NOT automatically a waiver threshold.
- Do not force waiver cycling as optimal.
- Do not force fixed player/rank labels onto fluid roster states.
- Research should seek large-impact frequency × magnitude × persistence × capture, and for optionality also speed/time-to-state-change.
- Product precision should be sufficient to change a roster decision, not optimized for its own sake.

## New execution contract

1. Development/research is currently resumed under this hierarchy.
2. Advance autonomously through research design, diagnosis, reversible methodological choices, code, and direct GitHub commits.
3. Stop and call the user only when:
   - the user truly needs to execute something locally / in Terminal; or
   - a genuine conceptual fork would embed an unapproved assumption into WoRP Lab.
4. Do not ask for micro-confirmations.
5. Do not continue an old research branch merely because it is next numerically.
6. Product question drives research: identify the decision → identify missing evidence → research only that evidence → incorporate if material.
7. Apply the materiality STOP aggressively. Noise does not earn research time.
8. GitHub is the source of truth for research contracts/scripts, but local outputs are not automatically synchronized.
9. Do not claim a script/result is validated until the user runs the required local computation and validation passes.

## IMMEDIATE NEXT GOAL

### Material Production Cutline V0.1

Use 2016–2025 historical WoRP to identify, for QB/RB/WR/TE, the positional depth/rank region after which normal sporting production ceases to generate material winning impact with sufficient consistency and repeatability.

The study should prioritize robust decision zones over exact arbitrary cutoffs.

Only after this economic frontier is understood should the research use Sleeper roster history to calibrate how real roster construction should allocate scoring depth versus Non-Scoring optionality around those frontiers.
