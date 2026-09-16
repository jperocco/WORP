# WoRP Lab — Product Status and Handoff

Date: 2026-09-16  
Status: ACTIVE — V0.9.4.3 PRODUCT VALIDATION  
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

- `app_v0_9_4_3.py` is the launcher-compatible current app.
- Lineup Economics is frozen after visual and numerical validation.
- Roster Construction has two product paths: exact historical support and lower-validation league-native derivation.
- A header-only/missing V0.32 product CSV is recovered in memory from the user's populated local V0.24 envelope using the frozen V0.32 aggregation.
- If neither populated V0.32 nor V0.24 research output exists locally, the app remains fail-honest and uses only the clearly labeled derived path.
- Derived-format validation covers 1QB, Superflex, 2TE, active-roster capacity, and non-additive positional bounds.
- No nearest-format, Wookiee fallback, player-name membership, or new research threshold was introduced.

## Immediate next steps

1. Validate one exact-historical league locally so the recovered V0.24 → V0.32 path is observed in the product.
2. Review derived envelopes across materially different real leagues for decision usefulness, especially overly broad positional bounds.
3. If those checks pass, freeze Roster Construction product integration.
4. Move next to the structural, player-free Roster Diagnostic presentation.

## Execution guardrails

- GitHub is the source of truth.
- Do not call an output validated until the required local run passes.
- Do not reopen named-player membership for this layer.
- Do not reopen Roster Construction threshold research without a new decision-material failure.
- Apply the less-than-4% relevance STOP to residual technical disputes that cannot change a product decision.
- Keep WoRP and JJ Stats as separate projects and repositories.
