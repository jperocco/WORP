# WoRP Lab — Lineup Capture Hypothesis V1

Status: RESEARCH HYPOTHESIS — NOT PRODUCT TRUTH

## Core definition

**Captured WoRP = WoRP produced by a player while that player is in the fantasy lineup.**

If the player produces WoRP on the bench, that WoRP was not captured.

Rostered value, produced value and captured value are therefore distinct.

## Central hypothesis

The roster-construction value of depth depends not only on how much WoRP a player can produce, but on how often that production can enter the lineup and how ambiguous the weekly start/sit decision is.

A useful first diagnostic is ex-post lineup-worthiness frequency:

> For a player/tier, in how many weeks would that player belong to the optimal legal lineup (Oracle / Teto perfeito)?

This is a structural diagnostic, not an ex-ante prediction and not manager-error measurement.

## Candidate states

### AUTO-START
A player/tier occupies an eligible lineup slot with high week-to-week persistence. Additional same-position depth may have limited capture opportunity unless another eligible slot exists or the auto-start player becomes unavailable.

### COMPETITION / AMBIGUITY
Multiple rostered players of similar economic quality compete for fewer eligible lineup spots. Positive WoRP can be produced on the bench because the correct weekly choice changes or is difficult to identify.

### BLOCKED
A player's positive WoRP has little legal/structural route into the lineup because stronger players persistently occupy the available eligible spots.

These are hypotheses/states to measure, not fixed rank labels.

## Positional intuition to test — do not assume as result

### QB
1QB and Superflex must be treated differently through slot eligibility.

In 1QB, an elite persistent starter can close the normal QB capture path for a backup.

In Superflex, two elite persistent QBs (example concept: Josh Allen + Lamar Jackson) can occupy both QB-eligible starting paths nearly every week, making QB3 WoRP difficult to capture.

If instead a roster has several non-elite, similarly valued QBs competing for one or two QB-eligible spots, the issue becomes weekly ambiguity rather than simple blockage.

Therefore Superflex does not eliminate capture difficulty; it can shift the point at which capture difficulty begins.

### WR
WR is the primary ambiguity hypothesis.

Suggested path: measure, by economically meaningful tier/range, how frequently a player at that level belongs to the Oracle lineup. Example question: if a player is season-level WR20, in how many weeks was he actually lineup-worthy under the optimal legal lineup?

Then examine persistence and competition: does a tier provide steady lineup value, or does its positive WoRP arrive in weeks that are difficult to distinguish from bench weeks?

Do not equate season rank or positive season WoRP with captured weekly WoRP.

### RB
RB is proposed as a contrast/control, not a presumed conclusion.

Fantasy intuition: situational depth may become easier to capture when role changes are observable. Example concept: Ashton Jeanty starts and a backup such as Mike Washington sits; if Jeanty is unavailable and the backup receives a major workload increase, a large week-to-week rank jump (e.g. RB60-type baseline to RB20-type usable week) may be easier to identify and start.

The research must test whether RB positive depth production is in fact more episodic but more identifiable/capturable than comparable WR depth production.

### TE
An elite persistent TE can occupy the dedicated TE slot almost every week. Backup TE value may therefore be blocked unless FLEX eligibility, bye/injury, or relative FLEX value creates a legal lineup path.

TE should be analyzed after QB/WR and the RB contrast establish the framework.

## Research design

### Stage 1 — Ex-post structural frequency

Use actual league roster/slot eligibility and weekly player outcomes.

For each player-week and relevant season-level tier/range, determine whether the player belongs to the optimal legal lineup (Oracle / Teto perfeito).

Primary outputs:
- lineup-hit weeks / eligible weeks
- lineup-hit rate
- persistence/stability of lineup-hit status across weeks
- positive WoRP produced while outside the Oracle lineup
- number and quality of same-position competitors for eligible slots

Aggregate by position and empirically useful tier/range. Do not force equal 12-player tiers.

Stage 1 answers: **where does lineup capture become structurally difficult?**

### Stage 2 — Ex-ante identifiability

Only after Stage 1 identifies meaningful ambiguity regions, test whether lineup-worthy weeks could be distinguished before games using legitimate prior information.

Potential evidence can include prior role/usage and availability signals, but target-week outcomes cannot be used as pregame information.

Stage 2 answers: **how identifiable/capturable was the value before kickoff?**

## Critical distinctions

- Oracle lineup frequency != manager skill.
- Oracle lineup frequency != ex-ante identifiability.
- Rostered WoRP != captured WoRP.
- Positive WoRP != lineup-worthy every week.
- Legal slot eligibility != realized lineup utilization.
- Blockage != ambiguity.
- Superflex != automatic capture of all QB depth.
- RB role-change intuition is a hypothesis to test, not a baked-in advantage.
- WR ambiguity intuition is a hypothesis to test, not a baked-in disadvantage.

## First experiment

Start with **QB + WR together** because both expose competition for lineup spots but with different slot structures. Use RB next as a contrast/control. TE closes the positional comparison.

The first experiment should remain descriptive/ex-post and should not attempt to prove a waiver strategy, market availability, manager error or predictive start/sit model.

## Product gate

Nothing from this hypothesis enters the five Structural Insights until the research shows a league-specific, decision-material pattern that survives validation.

If validated, the product translation should use manager language such as depth being frequently usable, frequently blocked, or creating weekly start/sit ambiguity — never Oracle/Robot/backoffice terminology.
