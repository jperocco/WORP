# WoRP Lab — Product Status and Handoff

Date: 2026-09-16  
Status: ACTIVE REVIEW — V0.9.4.6 WITH HISTORICAL EVIDENCE RECOVERY FIX  
Authority: this document records the latest product decisions and supersedes older immediate-next-step notes where they conflict.

## Canonical version distinction

- **WoRP Engine V0.2.1** remains frozen.
- **Roster Construction V0.32** is the research closeout, not the current app version.
- **WoRP Lab V0.9.4** is the current product-integration target.

Do not treat the V0.32 research identifier as the version of the app.

## Roster Construction / Diagnostic — research status

Roster Construction research closed at V0.32.

V0.31 named-player membership was deliberately killed. WoRP does not need player names to solve Roster Construction or the structural diagnostic. The product layer is positional and league-native:

- Scoring Core = range;
- QB / RB / WR / TE = positional ranges or envelopes;
- independent positional bounds are not additive quotas;
- no named-player membership;
- no asset value, trade value, buy/sell/drop, or player-ranking interpretation.

V0.32 consolidates the structural result by format and retains V0.30 live validation with boundary-sensitive signals suppressed. There is no planned V0.33 research threshold exercise. The remaining work is product integration and presentation.

## Roster Construction — adaptability requirement

Roster Construction must appear for every league whose league-native economy WoRP can calculate. The historical sample is evidence and validation, not a product allowlist.

Required behavior:

1. **Exact historical support:** use the empirically validated envelope.
2. **No exact historical support:** derive the envelope from that league's own team count, scoring, slots, eligibility, roster structure, replacement environment, and WoRP curve; clearly signal the lower validation level.

Forbidden behavior:

- returning `unsupported` merely because the format is absent from the 29 historically validated formats;
- silently mapping a league to Wookiee;
- using a nearest-format fallback;
- presenting positional envelope highs as additive roster quotas.

## Lineup Economics — final product definition

Lineup Economics explains the anatomy of the selected league's starting lineup. It is not a WoRP panel.

Canonical display:

> **Slot → share of expected lineup fantasy points → fantasy points/week → FLEX/SF positional composition**

Example fixed slot:

> WR2  
> 8.0% of expected lineup scoring  
> 13.1 pts/week

Example flexible slot:

> FLEX 2  
> 6.0% of expected lineup scoring  
> 9.8 pts/week  
> WR 44% · RB 31% · TE 25%

Product requirements:

- use fantasy points recalculated with the exact Sleeper scoring settings of the selected league;
- use the agreed 2023–2025 scoring basis;
- render visual cards, not a methodology-heavy table;
- make the percentage the dominant number;
- show `pts/week` directly below it;
- show positional composition only for FLEX/SUPERFLEX or other multi-position slots;
- keep WoRP out of this panel even though WoRP remains the project's economic engine.

The panel must not contain:

- `WoRP layer`;
- WoRP ranges or WoRP-ratio pseudo-shares;
- `Rank evidence`;
- named players;
- `Observed occupancy`, `Filled`, `Vacant`, or `Vacancy rate`;
- inferred vacancies from incomplete historical lineup observations.

## Implementation history and rejected detour

- `8398102` corrected the earlier WoRP-ratio pseudo-share into flexible-slot vacancy occupancy. That methodology was subsequently rejected for this product panel.
- `fad788d` introduced the intended V0.9.4 direction: visual slot cards based on league-scored fantasy points, without WoRP in the panel.
- Later `observed lineup economics` changes and the `Filled / Vacant / Vacancy rate` table are a rejected detour and must not be treated as the approved product state.

Lineup Economics passed visual and numerical validation in V0.9.4.1 and is frozen. FLEX/SF shares below 0.5% are suppressed in V0.9.4.3 so rounded 0% labels are not published.

## Current implementation status

- `app_v0_9_4_6.py` is the launcher-compatible current app. The user's `Abrir_WoRP_Lab.command` selects the highest `app_v0_*.py` version automatically.
- Lineup Economics is frozen after visual and numerical validation.
- Roster Construction has two product paths: exact historical support and league-native derivation.
- A header-only/missing V0.32 product CSV is recovered in memory from the user's populated local V0.24 envelope using the frozen V0.32 aggregation.
- If neither populated V0.32 nor V0.24 research output exists locally, the app derives the envelope from the selected league without nearest-format substitution.
- Derived-format validation covers 1QB, Superflex, 2TE, active-roster capacity, and non-additive positional bounds.
- No nearest-format, Wookiee fallback, player-name membership, or new research threshold was introduced.
- Eleven automated tests pass: three for Lineup Economics and eight for Roster Construction.

## Whole-roster construction update

V0.9.4.5 closed the roster-size presentation gap by separating the complete active roster into two layers:

1. **Scoring Core:** the economically meaningful scoring range and its positional envelope.
2. **Optionality capacity:** every remaining active-roster slot after the Scoring Core.

The active roster is calculated from starting slots plus bench slots. Bench depth changes Optionality capacity, but does not mechanically inflate the Scoring Core. For example, with a Scoring Core of 14–16:

- active roster 16 → Optionality capacity 0–2;
- active roster 24 → Optionality capacity 8–10;
- active roster 25 → Optionality capacity 9–11.

Optionality evidence remains directional rather than an invented positional quota:

- Superflex: QB + RB are the primary optionality targets;
- 1QB: RB is primary and QB secondary;
- WR is deprioritized by the validated hurdle;
- TE remains unresolved.

V0.9.4.6 is a presentation-only release. It removes the light-gray backend/methodology captions from Roster Construction and leaves the calculations unchanged. The visible block now contains only Active roster, Scoring Core, positional core envelope, Optionality capacity, and positional priorities.

## Immediate next steps

1. User opens V0.9.4.6 through `Abrir_WoRP_Lab.command` and confirms the cleaned presentation.
2. Do not make another conceptual or methodological Roster Construction change with the fallback model.
3. Resume substantive review when the stronger model is available.
4. Then decide whether the directional Optionality presentation is sufficient for product freeze or needs a better user-facing representation without inventing exact quotas.
5. After Roster Construction is frozen, move to the structural, player-free Roster Diagnostic presentation.

## Execution guardrails

- GitHub is the source of truth.
- Do not call an output validated until the required local run passes.
- Do not reopen named-player membership for this layer.
- Do not reopen Roster Construction threshold research without a new decision-material failure.
- Apply the less-than-4% relevance STOP to residual technical disputes that cannot change a product decision.
- Keep WoRP and JJ Stats as separate projects and repositories.

## 2026-09-16 — Real V0.24 data recovery and format-key correction

This section supersedes conflicting validation claims and pause instructions above.

- User supplied the original V0.24 CSV: 58 format/total rows, 29 structural formats. It is now tracked under `data/worp_scoring_core_decision_equivalence_envelopes_v0_24.csv`. Keeping it under data avoids a pull collision with the user's previously generated root-level CSV.
- Concrete integration bug: research uses pipe-separated format keys with explicit TEP/noTEP, while the product generated space-separated keys and omitted noTEP. Matching now uses canonical research keys and accepts legacy product labels.
- Clean installs recover the frozen V0.32 aggregation from bundled V0.24 evidence when local outputs are absent or empty. Local populated research inputs retain precedence.
- All 29 real research formats now reach the historical path. Fourteen automated tests pass, including clean-install recovery and whole-roster accounting.
- For 12T SF Start11 QB1 RB2 WR2 TE2 FLEX3 SFLEX1 TEP, the supplied evidence yields Scoring Core 15–16; QB 2–4, RB 3–5, WR 4–7, TE 2–4. At active roster 24, optionality is 8–9. Positional endpoints are still non-additive.
- App launcher remains app_v0_9_4_6.py; the imported module and bundled data are updated. No new app build is required. Real local screenshot validation remains pending.

### Remaining methodological limits — do not call the product fully validated

The derived path's sum-of-positional-curves objective is not the legal-lineup Oracle-loss measure tested by V0.23/V0.24. Reusing .05/90% does not establish methodological equivalence. This path is unchanged by this release and still requires correction/review before product freeze. Structural-format matches also do not establish identical full scoring settings. Historical aggregated envelopes do not yet handle every capacity below their historical core high; do not silently clamp positional bounds and call them empirically validated.

Next: validate the recovered historical output in the user's app, then repair remaining translation/capacity cases without inventing optionality quotas or reopening research thresholds. QB/RB directional optionality evidence is preserved; the user-facing technical gray captions remain removed.

## 2026-09-16 — Optionality allocation investigation completed (reference diagnostic)

- User screenshot confirmed recovered historical display for the 3WR/1TE format: active roster 24, Scoring Core 15–16, QB2–3/RB3–5/WR5–7/TE2–4, optionality8–9. Local visual confirmation for this case is no longer pending.
- User requested complete numerical positional allocation. The illustrative 5QB/10RB/6WR/3TE proposal was explicitly withdrawn and is not implemented or validated.
- Ran a new diagnostic using Wookiee 2023–2025 actual Sleeper snapshots and existing native weekly WoRP: 468 roster-week cohorts, 4,749 marginal slot observations. Artifacts and methods are committed under research/optionality_capacity_reference/.
- Support for 2QB+6RB options: 44/468 cohorts; common support versus 3QB+5RB: 32/468 across seven roster-seasons. For nine options, comparing 2QB+7RB versus 3QB+6RB leaves 17/468 (3.6%) across six roster-seasons. These are owned-pool support counts, not proof of acquisition unavailability or quota optimality.
- First-slot paired QB/RB mean opportunity ordering changes across seasons. Means are small and measure a hindsight legal-lineup positive-WoRP ceiling, not material-tail events or realized capture. No exact allocation is established.
- The <4% relevance STOP applies to further micro-refinement of the nine-slot reference comparison. A multi-league, common-support joint-allocation study with acquisition/active-roster controls would be a material scope expansion; do not silently publish arbitrary quota defaults.
- App remains unchanged. Prior Scoring research and directional optionality evidence remain intact. This completed reference audit does not complete the user's requested numeric allocator.

## 2026-09-20 — Authorized multi-league optionality diagnostic completed

The user authorized expanding the calculations after the reference audit. This supersedes the earlier instruction to stop at that reference comparison.

- Completed 18 league-seasons from 2023–2025, across 1QB, SF/1TE and SF/2TE; exact Sleeper scoring and frozen engine. All selected runs completed without reported failures. Five focused tests pass.
- 2,544 roster-week cohorts; 500 adjacent equal-budget comparisons from 150 distinct roster-week cohorts. Overlapping weeks, multiple splits and simulation draws are not independent observations.
- For eight options, exchanging 2QB+6RB for 3QB+5RB changes mean four-week opportunity by −0.006398 in SF/1TE (19 paired cohorts, three league-seasons) and −0.024851 in SF/2TE (36 paired cohorts, five league-seasons). For nine options, the corresponding means favor the extra QB slightly but league-season signs vary; only nine and eight paired cohorts respectively. These units are summed positive-WoRP opportunity, not observed wins or a calibrated joint team win probability.
- Numerical results, code, tests, selection manifest and cache hashes are committed under research/optionality_multileague/ and worp_optionality_multileague.py. Raw public-data caches remain local; replay can download them again.
- This is a lagged owned-pool diagnostic, not a prospective acquisition policy. The baseline is prior-use based, not a validated V0.32 core tuple. IR/taxi eligibility is not disaggregated. Low-use WR/TE alternatives are not tested. These limits prevent translating the comparison into an exact whole-roster allocation.
- No arbitrary optionality quota was deployed. App stays V0.9.4.6; existing Engine/Core/Lineup Economics decisions remain unchanged.
- User supplied Scott Connor's “WAR Has Changed” article for evaluation. Recommendations from that review are proposals, not authorization to replace the engine or reintroduce named-player product membership.

## 2026-09-20 — Article distinction accepted; four-position calculation and capacity gate

User approved moving forward with the distinction between available opportunity and usable lineup contribution, preserving the frozen engine.

Implemented and ran worp_optionality_four_positions.py on the same 18 historical league-seasons. It compares adding one QB/RB/WR/TE separately to the same prior-use baseline, keeping each candidate across four weeks and respecting legal FLEX/SF competition. Ten tests pass across marginal and joint-allocation components. Code and results are in research/optionality_four_positions/.

A conservative capacity screen excludes historical ownership snapshots larger than active starting-plus-bench capacity. Only 97/2,544 cohorts (3.81%) pass; 94 provide a paired comparison, across seven league-seasons. This is a data limitation: snapshots do not sufficiently distinguish historical active/IR/taxi status, and passing the size screen alone does not prove active eligibility. The surviving sample is selected and cannot justify full-roster positional quotas.

The agreed below-4% relevance STOP is now explicit: discuss the decision value of reconstructing historical active availability before further refining this subset. Do not confuse this with discarding optionality, changing prior QB/RB conclusions, or claiming the numeric allocator is complete. Historical baseline/core translation and acquisition controls also remain unresolved.

Engine V0.2.1, Scoring Core research, Lineup Economics, and app V0.9.4.6 are unchanged. The new calculation is a research component, not a deployed product recommendation.

## 2026-09-20 — Active-roster bounds; correction of coverage STOP

The user authorized proceeding. The previous 3.81% survival rate was incorrectly treated as the residual-exception 4% rule: 96.19% missing coverage is central, not residual. That STOP is superseded.

Checked all 324 cached matchup schemas, official Sleeper endpoint documentation, and one live roster endpoint plus two transaction weeks. Matchups do not expose reserve/taxi assignments; the roster endpoint does not supply a documented weekly timeline, and probed transactions did not recover one. Do not backdate end-state reserve/taxi lists.

Implemented worp_active_roster_bounds.py and four passing tests. Conditional on the supplied capacities/settings, 2,538/2,544 roster-weeks admit active-count/positional bounds; six conflict and remain flagged. 360 compatible cases have an exact conditional active total; zero have all four positional counts determined. Results are in research/active_roster_recovery/.

This recovers count constraints, not historical active identities. Prior marginal calculations remain restricted sensitivity diagnostics, not validated active-roster recommendations. No artificial identities, quota defaults, or new thresholds were inserted. Engine/app unchanged.

Exact retrospective active-roster allocation remains blocked on dated reserve/taxi assignments in the checked sources. A simulated positional-portfolio allocator would be a separate explicit modeling choice, not an empirical recovery. Do not continue issuing tiny study variants as though they complete the requested full-roster numerical allocator.

## 2026-09-20 — Scott Connor archive and modeled portfolios

User requested preserving Scott Connor's supplied article as a project update and explicitly authorized the next modeled-portfolio step. Full supplied text is archived at docs/references/scott_connor_war_has_changed_2026-09-19.md. WORP_UPDATE_SCOTT_CONNOR_2026-09-20.md records source attribution, accepted distinctions, preserved engine/Core/Lineup Economics decisions, and future hypotheses.

Implemented worp_positional_portfolio_simulation.py; four tests pass. Completed a 2025 12T Superflex case at capacities 15 and 22 (5 versus 12 bench places), with 64 and 256 sampled rosters per composition, three disjoint windows, and exact starting-slot eligibility. A separate 2024 12T case has 11 starters rather than 10, so its 5/12-bench capacities are 16/23; it is not a controlled year-over-year replication. All scenario surfaces and assumptions are saved under research/positional_portfolio_simulation/.

Profiles come from preceding-week league-wide ownership and preceding three-week positional WoRP rank blocks. Simulated holdings stay fixed across compared compositions and each future window. Full capacity is filled exactly; legal lineup competition is optimized jointly. Reported maxima vary by window and sometimes draw count. These are hindsight opportunity ceilings under an explicit selection model, not active-roster observations, expected-win forecasts, market-budget-equivalent portfolios, or validated quotas.

The initial model step is complete. It does not complete the product allocator: selection-policy sensitivity and prospective/manual capture remain unresolved. No new thresholds, redefined Scoring Core, or arbitrary roster defaults were deployed. Engine and app unchanged.
