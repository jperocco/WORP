# WoRP Lab — Roster Construction Research Handoff

Date: 2026-09-14
Status: PAUSED / READY TO RESUME

## Product objective

The purpose of this research is not to mathematically classify every player into a perfect state. The product objective is to recommend an ideal roster-construction model from the league format, then alert the user when fluid player-state changes cause the roster to drift away from that model.

Canonical pipeline:

**league format → lineup demand → required Scoring Depth → point where additional positional capital loses lineup utility → remaining roster capacity demands Optionality**

The eventual product should answer questions such as:
- How much productive/lineup depth should this format carry at QB/RB/WR/TE?
- When is an additional player at a position still useful Scoring Depth?
- When has the roster crossed into Non-Scoring capacity, where the hurdle becomes optionality/state-change upside rather than ordinary lineup coverage?
- When a player changes state, has the roster become overweight in an upper layer and should the manager KEEP / START / TRADE / RECYCLE?

The goal is a useful roster-construction recommendation, not false mathematical precision.

## Canonical three fluid states

The states are functional and fluid, not permanent player classes.

1. **STARTER** — principal productive capital; expected normal lineup core.
2. **SCORING BENCH** — reserve productive capital; players deliberately rostered because they have a meaningful expectation of entering the lineup during normal seasonal operation (injury, bye, matchup, legitimate competition/rotation).
3. **NON-SCORING BENCH** — optional capital; low normal lineup-use expectation, rostered primarily for a meaningful state-change opportunity.

Typical transition:

**NON-SCORING → SCORING BENCH → STARTER**

and players can later move back down.

A **Promotion Event** is a transition/new-information event, not a fourth state.

Important: "Scoring Bench" does NOT mean bench points are captured. **WoRP is captured only when the player is actually STARTED.**

## Asset-value logic

WoRP measures sporting value, not trade/market value.

A state change can create two different forms of value:
1. sporting/lineup value, measurable through WoRP if the player is started;
2. asset/market appreciation, which requires a separate valuation layer and must not be inferred from WoRP alone.

Conceptual optionality cycle:

**acquire cheap optionality → wait for state change → capture production and/or asset appreciation → retain/start/trade promoted value → recycle roster capacity into new optionality**

This cycle is a product hypothesis, not yet proof that waiver cycling is always optimal.

## Critical roster-context principle — QB1 + QB1 + QB1

Do NOT force player names, fixed ranks or ordinal depth-chart labels into the state model.

The state depends on the relationship between:
- economic quality of the assets;
- number and eligibility of starting slots;
- competition among similar assets;
- expected temporal lineup use.

Example in Superflex with two QB-eligible lineup spots:
- QB1 + QB1 + QB1: the third QB is NOT automatically Non-Scoring. Three similarly valuable assets may be competing for two lineup spots. This is lineup ambiguity / Scoring Depth / Lineup Capture territory.
- QB1 + QB1 + deeply contingent QB: the third QB is much more plausibly Non-Scoring optionality.
- QB15 + QB18 + QB22: do not classify QB22 as Non-Scoring merely because he is the third QB. Similar assets may all belong to the competitive scoring layer.

Canonical principle:

**relative economic quality + eligible slots + competition + expected use → functional roster state**

not:

**player name/rank → fixed state**

Slot eligibility ultimately matters more than traditional slot names. FLEX is shared RB/WR/TE demand; Superflex is shared QB/RB/WR/TE eligibility.

## Current WR hypothesis

The working hypothesis is intentionally product-oriented rather than a demand for an exact mathematical threshold.

WR may deserve substantial roster capital in the **Scoring** layer because leagues can demand many WR/FLEX starters and useful lineup coverage.

But WR may lose relative attractiveness once the roster reaches the **Non-Scoring** layer. The question is not whether a deep WR can ever emerge; it is whether that Non-Scoring roster spot has better optionality elsewhere.

Structural reasons being investigated:
1. A deep RB can sometimes receive a concentrated workload from one state change ahead of him.
2. A backup QB can become an NFL starter, especially valuable in formats with QB-eligible demand.
3. Deep WR opportunity often does not transfer as mechanically after one player ahead disappears; target redistribution can be diffuse.
4. WR has meaningful produced-vs-captured WoRP friction: a WR can produce useful value while still being benched because of lineup ambiguity.
5. Deep WR economics are compressed in the tail; many deep WR assets can be economically similar.
6. Therefore a purely Non-Scoring WR should face a higher **optionality hurdle rate** than a WR who still provides meaningful Scoring Depth.

Do NOT translate this into an arbitrary universal WR rank cutoff. The desired product output is closer to an economically meaningful **cut zone / hurdle** that changes with league format.

## What the product eventually needs

For each position and league format, estimate:

**How far should the manager buy Scoring Depth, and after what region should additional roster capacity primarily be allocated for Optionality?**

This can produce guidance like:
- position X still adds useful lineup/scoring depth here;
- additional position X exposure beyond this region has declining lineup utility;
- Non-Scoring capacity should now prioritize assets with stronger asymmetric state-change paths.

Precision should be sufficient for roster decisions, not optimized for its own sake.

## Research completed before the current pause

### Promotion Event / Episode work

V0.1–V0.3.1 established an empirical object for low-use-to-active transitions.

V0.3.1 fixed onset timing by separating trigger week from active start week. All 239 episodes found an active onset after the fix. Promotion episodes remain ex-post utilization/performance shapes, NOT validated historical NFL injury/depth-chart/news events.

The research can measure:
- duration of active episode;
- positive WoRP produced;
- positive WoRP captured when actually STARTED;
- produced-but-not-captured value.

### V0.4 — Non-Scoring Exposure Proxy

Script: `wookiee_non_scoring_exposure_audit_v0_4.py`

The audit intentionally calls its state definition a proxy, not a final semantic classifier.

Primary L5 definition:
- rostered player-week;
- at least two prior observations;
- zero REAL starts in recent lookback;
- zero ORACLE selections in recent lookback;
- target-week outcomes excluded from classification.

Primary results:
- 5,162 proxy exposure player-weeks;
- 144 promotion-episode triggers;
- 2.7896% descriptive promotion-trigger rate per exposure-week;
- 144/239 V0.3.1 episodes matched the primary proxy.

Position results, L5:
- QB: 1,319 exposures; 32 triggers; 2.43%; produced WoRP / 100 exposure weeks 0.6400; captured 0.2924.
- RB: 1,447; 40; 2.76%; produced 0.3780; captured 0.0881.
- TE: 500; 13; 2.60%; produced 0.3146; captured 0.0020.
- WR: 1,896; 59; 3.11%; produced 0.3848; captured 0.1289.

Sensitivity was reasonably stable across 3/5/8-week lookbacks:
- QB: 2.40% / 2.43% / 2.47%
- RB: 2.88% / 2.76% / 2.41%
- TE: 2.19% / 2.60% / 2.60%
- WR: 3.28% / 3.11% / 3.04%

Interpretation: useful evidence that the transition phenomenon survives reasonable lookback changes. These are still proxy rates, not true probabilities of semantic Non-Scoring assets promoting.

Important emerging observation: produced WoRP and captured WoRP differ materially. Do not rank optionality by raw produced WoRP alone.

TE's extremely low captured WoRP in the small promoted sample is an audit flag, not a product conclusion.

## V0.5 / V0.5.1 — exploratory path now FROZEN

`wookiee_promotion_roster_context_audit_v0_5.py` attempted to classify promotion context using same-position stronger-player counts versus observed position capacity.

It produced 131/144 events in a "competition" bucket and only 13 in a "room" bucket. This binary construction was too coarse and did not reliably express the QB1 + QB1 + QB1 concept.

A V0.5.1 script was then created to explore continuous distance to the roster's observed capacity frontier. **Do not continue tuning this path by inertia.** The research direction was corrected before treating V0.5.1 as the next canonical step.

Decision:
- V0.5 and V0.5.1 are exploratory artifacts.
- They are not validated roster-state models.
- Do not use them for frontend/product claims.
- Do not resume endless threshold/frontier refinement unless a later product question specifically requires it.

## Why the direction changed

The research briefly became too focused on deriving mathematically perfect Starter / Scoring / Non-Scoring classifications.

That is not necessary for the product.

The three-state framework can be an operational roster-construction heuristic. The product needs a recommended allocation and useful drift alerts when player states change. It does not need to prove that a specific player has a mathematically exact state score.

This is the canonical correction of course.

## NEXT STEP WHEN RESUMING

Begin **Roster Construction Model V0.1**.

Do NOT resume V0.5 threshold tuning first.

Research question:

> **For each position and league format, how far should the manager buy Scoring Depth, and from what economic region should additional roster capacity primarily be evaluated as Optionality?**

Start with league-format/slot demand and existing WoRP curve evidence, then use Promotion/Produced/Captured evidence as calibration for the optionality hurdle.

The first version does not need a mathematically exact universal boundary. It should seek a decision-useful zone and explicitly represent uncertainty.

For WR specifically, test the hypothesis that:
- WR remains important through the Scoring Depth layer;
- once additional WRs no longer materially improve expected lineup coverage/competition, deep WRs should face a higher optionality hurdle;
- the relevant cut zone is format-dependent, not a universal WR rank;
- alternative positions/archetypes can become preferred Non-Scoring capital because of more asymmetric state-change paths.

## Existing methodological guardrails to preserve

- WoRP captured = WoRP from a player actually in the lineup. Not started = not captured.
- Produced WoRP ≠ captured WoRP.
- Market Capture ≠ Lineup Capture.
- WoRP ≠ trade price.
- Capturable ≠ captured.
- Compression ≠ fungibility.
- FREE ≠ WAIVER.
- Do not claim WR60/WR72/WR80 is a waiver threshold.
- Approximate WR economic tail around WR55/60+ is not a universal roster-state cutoff.
- FLEX/SF are shared eligible-slot demand, not position-owned slots.
- Oracle/Teto is ex-post usefulness, not ex-ante identifiability.
- Do not use target-week outcomes to define pre-week state.
- Do not force waiver cycling as optimal; test it.
- If a residual technical dispute falls below 4% of the relevant universe, trigger a relevance/STOP discussion before spending more research time.
- Product output should remain decision-oriented; research complexity belongs in the backoffice.

## Product context

The core WoRP Engine V0.2.1 is frozen. Structural Insights editor V0.9.1 passed its three-league harness and its editorial phase is frozen unless a material defect appears.

Current research is intended to improve the intelligence behind roster-construction guidance, not to reopen the engine or the frozen editorial hotfix loop.

Canonical product philosophy:

**evidence → structural hypothesis → roster-construction story → relevance test → dedupe → high-value actionable insight**

The product now needs the roster-construction intelligence layer more than another threshold-optimization exercise.

## Frontend access workflow — validated 2026-09-14

A local double-click launcher was created for the user:

`Abrir_WoRP_Lab.command`

Expected local repo path:

`~/Downloads/worp/worp_lab_v0_2_1`

Launcher behavior:
1. enters the local WoRP Lab directory;
2. runs `git pull --ff-only`;
3. selects the highest-version local `app_v0_*.py` using version sort;
4. launches it through Streamlit, preferring `python3.12` when available and falling back to `python3`.

The downloaded `.command` initially lacked executable permission. This was fixed once with:

`chmod +x /Users/jperocco/Downloads/Abrir_WoRP_Lab.command`

After that, double-clicking the launcher successfully opened the frontend.

Operational preference: for normal frontend access, prefer this launcher over making the user navigate through Terminal manually. If a future frontend version is committed and pulled locally, the launcher is designed to select the newest `app_v0_*.py` automatically.
