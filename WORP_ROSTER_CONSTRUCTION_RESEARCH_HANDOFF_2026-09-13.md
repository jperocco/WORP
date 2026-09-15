# WoRP Lab — Roster Construction Research Handoff

Date: 2026-09-15
Status: ACTIVE — HIERARCHY RESET

## NON-NEGOTIABLE PRODUCT PRINCIPLE — LEAGUE ADAPTABILITY

**WoRP is league-native before it is Wookiee-native.**

Wookiee is a reference/test league, not the definition of the product. A WoRP result that only works for Wookiee is not a finished WoRP result.

Priority zero for every current and future model:

> **The engine and its recommendations must adapt to each league's format, team count, scoring, starting-slot structure/eligibility, roster size, replacement environment, and other economically material league-specific settings.**

This requirement is ABOVE Roster Construction, Roster Diagnostic, and frontend/editor work. If a research result is expressed in raw positional ranks (for example RB35 or WR45), treat that as a historical baseline/diagnostic until it has been translated into league-native economics.

Do not ship universal raw-rank cutlines learned from a reference league or pooled NFL history when league format can materially move the frontier.

The correct architecture is:

**league settings → league-native WoRP/replacement economics → material production frontier → roster construction → roster diagnostic.**

Wookiee remains useful for regression, examples, and deep behavioral audits. It must never silently become the assumed league format.

## Product objective

WoRP Lab remains a sporting-performance product. It does NOT model trade prices, picks, ADP, market value, or asset valuation.

Current product hierarchy:

0. **League adaptability / league-native economics — absolute priority.**
1. WoRP / league economic map.
2. What This League Is Telling You.
3. Value Cliffs.
4. Roster Construction — primary research priority after adaptability is preserved.
5. Roster Diagnostic — next product layer after construction logic is sufficiently validated.
6. Research-to-editor automation / Top-5 publication bridge — LAST backlog item, not a current priority.

The main research goal is to turn each league's own economics into a decision-useful answer to:

> **In THIS league, how deep at each position does sporting production remain materially capable of helping win, with enough consistency and repeatability to matter?**

The product should prefer simple, decision-material boundaries/zones over mathematically elaborate state classifiers.

## New primary abstraction — Material Production Cutline

Roster Construction should first seek the positional region where WoRP stops being materially relevant to winning.

For each position **under the target league's economics**, ask:
- Where is WoRP magnitude still large enough to matter?
- How consistently does that impact occur?
- How repeatable is the result across seasons?
- At what economic depth does the distribution effectively become zero for normal winning production?

Raw historical rank questions such as RB35 or WR45 are useful discovery tools, not universal product answers.

**Economic zero does not mean mathematical WoRP = 0.000.** It means remaining differences are too small, too rare, or too unstable to plausibly change roster construction, weekly outcomes, or season-winning decisions.

## Governing materiality principle

Optimize research for large, decision-material impacts. Small differences such as 0.061 vs 0.045 WoRP are operationally zero vs zero unless there is evidence that they compound into a material weekly/season effect.

Before spending research time on a difference, ask:
> **Could this plausibly change how a manager builds a roster, sets a lineup, or wins meaningful weeks/seasons?**

If no, classify it as noise and STOP. Do not optimize thresholds by tiny increments. Seek robust zones where the decision changes. If a residual technical dispute affects less than 4% of the relevant universe and cannot change the decision, trigger STOP.

## Roster Construction — simplified hierarchy

The three fluid roster states remain useful operational language, but they are no longer the object that must be perfectly classified first.

1. **STARTER** — normal productive lineup core.
2. **SCORING DEPTH** — additional rostered production that still has a meaningful path to material lineup impact.
3. **NON-SCORING OPTIONALITY** — roster capacity below/outside normal material production, justified primarily by meaningful state-change opportunity.

Preferred sequence:

**league-native WoRP distribution → Material Production Cutline → eligible lineup demand → useful scoring depth → remaining roster capacity becomes optionality → diagnose roster against that structure.**

Do not derive a perfect Starter/Scoring/Non-Scoring classifier before answering the simpler economic question.

## Optionality and roster-spot recycling

Asset valuation is OUT OF SCOPE.

When a Non-Scoring player changes into a meaningfully higher sporting state, the manager gains capacity to act. The player can be promoted, retained, traded, consolidated in a 2-for-1, or otherwise moved; if that action frees a roster spot, the manager can make another optionality bet.

The model does NOT need to know the trade price or quantify market appreciation.

What matters for Non-Scoring capacity:
- probability of meaningful state change;
- magnitude of sporting impact after the change;
- persistence of the new state;
- speed/time to meaningful state change;
- ability to recycle the roster spot into another bet after promotion/action.

### Clogger

A **clogger** is a Non-Scoring roster asset that consumes roster capacity for too long without generating a meaningful state change. Optionality should therefore care about large transitions and roster-time consumed to generate them, not merely the number of small positive outcomes.

## Sporting impact only

Do NOT add an Asset Value layer. Do NOT research trade prices, picks, ADP, market appreciation, or dynasty market valuation unless product scope is explicitly changed later.

## Sleeper readonly — role and limitation

Sleeper readonly is a major empirical source for Roster Construction and Roster Diagnostic. It can support reconstruction of league settings, roster structure, weekly rosters, starters/bench, and transaction/state changes for accessible leagues/seasons.

The existing 2023–2025 Wookiee dataset is an initial behavioral sample, NOT a structural ceiling and NOT the assumed target league.

Before generalizing behavior, inventory the league IDs / historical leagues actually accessible to the project. Use diversity of formats deliberately: team count, roster size, scoring, 1QB/SF, TE premium, number and eligibility of FLEX-type slots, etc.

Use Sleeper to study how real rosters allocate depth around **their league-native material production frontier**, how often below-frontier players cross it, time to state change/clogger behavior, realized lineup capture, and differences by format.

## Historical WoRP advantage and V0.1 status

Historical WoRP data cover 2016–2025. Material Production Cutline V0.1 has now been run successfully and is **VALIDATED AS A FORMAT-AGNOSTIC HISTORICAL BASELINE ONLY**.

It found stable cross-season raw-rank decay regions, including:
- QB: strong material production through roughly low/mid QB30s; rapid decay across QB36–45; near-zero around QB46–50+.
- RB: strong material production through roughly RB35; transition across roughly RB36–50; small/no normal impact deeper in the tail.
- WR: strong material production extends deeper, through roughly WR40–50 depending materiality hurdle; transition through roughly WR51–65; tail approaches economic zero later.
- TE: strong material production through roughly TE25–30; transition roughly TE31–40; near-zero deeper.

These are **NOT universal roster cutlines**. They are evidence that the material-frontier concept is empirically visible and cross-season repeatable in the historical WoRP distribution.

The next research step must test/adapt these frontiers under league-specific replacement and eligible-slot economics before they can become product recommendations.

## V0.1 evidence — 2016–2025

Five-rank cross-season bands show strong repeatability. Selected landmarks:
- QB31–35 median season-band WoRP 0.581; QB36–40 0.352; QB41–45 0.109; QB46–50 0.023.
- RB31–35 0.611; RB36–40 0.481; RB41–45 0.347; RB46–50 0.216; RB51–55 0.130; RB56–60 0.047.
- WR31–35 0.761; WR36–40 0.601; WR41–45 0.499; WR46–50 0.410; WR51–55 0.318; WR56–60 0.245; WR61–65 0.170; WR71–75 0.044.
- TE21–25 0.644; TE26–30 0.421; TE31–35 0.281; TE36–40 0.168; TE41–45 0.065.

At the 0.50 season-WoRP descriptive landmark, last ranks across 2016–25 were:
- QB: 30–36.
- RB: 32–39.
- WR: 40–47.
- TE: 20–32.

This supports transition **zones**, not exact universal ranks.

## Primary cutline tests

For each position/economic region evaluate:
1. **Magnitude** — WoRP large enough to matter?
2. **Consistency** — occurs often enough rather than isolated spikes?
3. **Repeatability** — recurs across seasons?
4. **Adaptability** — does the frontier move correctly when league settings/replacement/slot eligibility change?

The fourth test is mandatory before productization.

Do not define materiality by choosing a threshold that favors a position. Use distributional evidence and decision-scale sensitivity, then seek robust zones where roster decisions change.

## Relationship to previous big-impact research

V0.7 and V0.7.1 remain valid optionality evidence. Historical extension of the old 2023–25 Non-Scoring proxy is PAUSED.

At the pre-specified >=0.50 WoRP / next-four-complete-weeks replication hurdle:
- QB showed material-tail hits in all 3 observed seasons.
- RB showed rare material hits in 2/3 seasons.
- WR showed zero >=0.50 four-week post-shock sporting hits in all 3 seasons despite the largest exposure pool.
- TE remained unresolved/sparse.

Do not tune 0.50 vs nearby thresholds by inertia.

## Roster Diagnostic — second priority

Once league-native construction logic exists, diagnose the user's actual roster against it. Eventually answer:
- Is the roster underweight in materially useful scoring depth for THIS format?
- Is too much capacity below THIS league's material frontier?
- Are Non-Scoring spots consumed by slow-changing cloggers?
- Is optionality concentrated in positions/archetypes that rarely generate material state changes?
- Has a promotion/state change altered the optimal roster mix?

## Frozen / killed / backlog work

### KILL — Asset Value
No market-value layer, trade pricing, pick valuation, or ADP valuation.

### PAUSE — historical extension of old V0.7 Non-Scoring proxy
Revisit only if league-native cutline/construction research creates a specific need.

### FREEZE — Structural Insights editorial hotfix loop
V0.9.1 remains frozen unless a material defect appears.

### LAST BACKLOG — research-to-editor publication bridge
Deferred until underlying league-native roster-construction intelligence is stronger.

## Current product architecture

**League Settings → League-native WoRP Map → What This League Is Telling You → Value Cliffs → Roster Construction → My Roster Diagnostic**

The product should answer manager decisions, not expose research machinery.

## Methodological guardrails

- **Never universalize Wookiee. Adaptability is priority zero.**
- WoRP captured = WoRP from a player actually in lineup. Not started = not captured.
- Produced WoRP ≠ captured WoRP.
- Capturable ≠ captured.
- FREE ≠ WAIVER.
- Compression ≠ fungibility.
- FLEX/SF are shared eligible-slot demand, not position-owned slots.
- Relative improvement above low baseline does not automatically equal material impact.
- Statistical separation does not automatically equal decision materiality.
- Do not use tiny mean differences as roster-construction evidence.
- Raw rank cutline ≠ universal league-native cutline ≠ waiver threshold.
- Do not force waiver cycling as optimal.
- Do not force fixed player/rank labels onto fluid states.
- Seek large-impact frequency × magnitude × persistence × capture; for optionality also speed/time-to-state-change.
- Product precision should be sufficient to change a roster decision, not optimized for its own sake.

## Execution contract

1. Advance autonomously through research design, diagnosis, reversible methodological choices, code, and direct GitHub commits.
2. Stop and call user only when local/Terminal execution is truly required or a genuine conceptual fork would embed an unapproved assumption.
3. Do not ask for micro-confirmations.
4. Product question drives research; old numeric sequence does not.
5. Apply materiality STOP aggressively.
6. GitHub is source of truth for research contracts/scripts; local outputs are not automatically synchronized.
7. Do not claim a script/result is validated until required local computation passes.
8. **Every roster-construction result must pass a league-adaptability test before becoming product logic.**

## IMMEDIATE NEXT GOAL

### League-Native Material Production Frontier V0.2

Take the validated 2016–2025 raw historical cutline evidence and determine how the material production frontier transforms under materially different league formats.

The V0.2 research must explicitly vary or ingest:
- team count;
- scoring settings relevant to positional economics;
- starting-slot count and eligibility, including FLEX/SF shared demand;
- replacement environment;
- roster size where it affects practical depth/availability.

Use Wookiee only as one regression/reference case. Include materially different league configurations so the test can answer:

> **Does WoRP correctly move the QB/RB/WR/TE material frontier when the league itself changes?**

Only after this passes should raw historical rank regions become Roster Construction recommendations.
