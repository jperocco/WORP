# WoRP Lab — Frontend Touchpoint V4

Date: 2026-09-13
Status: final planned frontend iteration for this session

## Product state

- Core WoRP Engine remains **V0.2.1 frozen**.
- Main work is improving the **Structural Insights** product layer, not rebuilding the engine.
- V0.7.3 improved story-level deduplication and restored **Value Cliffs**, but still exposed two product problems:
  1. some insights used economically irrelevant deep ranges (example: RB50+), outside normal roster-construction decisions;
  2. the five cards still risked looking too similar across materially different league formats.
- The V0.7.3 Performance profile did not become a useful user-facing diagnostic and is removed from the final-session build.

## What the Monte Carlo is actually doing

Historical player production is observed, not simulated. Monte Carlo in Engine V0.2.1 is used to convert observed weekly fantasy points into a win-probability delta:

**Weekly WoRP = P(win with player) − P(win with positional replacement)**

The engine samples complete roster/opponent contexts from observed weekly starter-level scoring pools. Therefore Monte Carlo is part of the current WoRP definition, not a forecast of player production.

However, repeated recomputation is unnecessary when the inputs that determine the historical result have not changed.

## V0.7.4 performance contract

V0.7.4 does **not** alter Engine V0.2.1 math.

Instead, it adds a persistent exact-result cache at the **season ranking** level, keyed by:

- Engine version
- teams
- QB / RB / WR / TE / FLEX / SUPER_FLEX roster structure
- exact Sleeper scoring JSON
- historical season
- simulation count
- seed
- replacement band

Implications:

- First-ever calculation for a new scoring/format/season combination can still be expensive because Engine V0.2.1 must run.
- Once computed, that season ranking is persisted locally and can be reused across any league with the same actual scoring/format configuration.
- If all three requested seasons are warm, the app can skip both Sleeper historical loading and Monte Carlo entirely for the Structural Insights calculation.
- Changing a 3-year window should only require calculating seasons that are not already persisted.
- This preserves the existing WoRP definition exactly while eliminating unnecessary repeated historical simulation.

A future research task, if reopened, can test whether the Monte Carlo win-probability transform itself can be replaced by an exact or analytically equivalent method. That is **not** part of V0.7.4 because it would require engine-level validation.

## V0.7.4 editorial contract

### 1. Replacement-frontier relevance gate

The five headline Structural Insights may not use arbitrary deep rank ranges simply because the curve exists there.

For each position, the editor derives a league-native historical relevance frontier from the engine's observed `avg_replacement_effective_rank` across the selected seasons.

A candidate headline whose comparison range extends beyond that position's replacement frontier is suppressed from the Top 5.

This is a product relevance gate, **not** a universal waiver threshold.

It specifically prevents low-value headline stories such as "RB50–RB72 is compressed" when those ranks are already outside the economically relevant roster-construction region for that league.

### 2. League differentiation is mandatory

The Structural Insights editor must not merely fill the same five templates with different numbers.

Candidate stories now include format-dependent families that only exist when supported by the selected league:

- **Superflex:** QB demand can extend materially beyond nominal fixed QB slots.
- **2TE / TEP:** TE replacement depth and curve structure are interpreted against the league's deeper TE demand.
- **Flex-heavy formats:** mid-range WR/RB depth can become starting-lineup supply rather than ordinary bench depth.

These compete with curve-derived stories such as:

- stars-and-depth curve shape;
- relevant short-range cliffs;
- scarcity runway toward replacement;
- mid-curve compression;
- replacement-frontier contrast.

The editor still publishes at most five cards and limits position/story redundancy.

### 3. Curve shape before fixed windows

V0.7.3 showed that fixed comparisons such as QB8→QB20 can manufacture a conclusion even when another part of the curve tells a different story.

V0.7.4 scales comparison windows to each position's own league-native replacement frontier. Fixed rank windows are evidence only when they fall naturally inside the relevant pool.

### 4. Value Cliffs stays

**Value Cliffs remains directly below the five Structural Insights.**

It is the senior analytical layer: the five cards summarize; Value Cliffs exposes the marginal short-range WoRP deltas for users who want to inspect the evidence.

Value Cliffs may show deeper raw curve information than the Top 5 relevance gate because it is an analytical table, not a headline recommendation layer.

## Explicit methodology guardrails retained

- WoRP is descriptive/historical, not predictive.
- Compression ≠ waiver.
- Flat tail ≠ fungibility.
- Replacement is league-native, not a universal fixed positional rank.
- A rank boundary is not a roster-construction conclusion by itself.
- Do not infer `WR1* + WR1* + waiver` as proven.
- Do not force equal-sized tiers or semantic tier names from mathematical segmentation.
- Structural Insights must be actionable, concise, non-redundant, and league-specific.
- Value Cliffs is evidence, not an automatic headline generator.

## Files / next local steps

New builder:

`build_worp_lab_v0_7_4.py`

Expected generated app:

`app_v0_7_4.py`

V0.7.4 is intended to be the **last frontend build for this session**. After it is generated and smoke-tested, stop iteration unless a blocking bug appears.
