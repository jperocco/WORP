# WoRP Lab — Roster Construction V0.13 Gate

## Status
V0.13 translation: PASS as a structural constraint map; NOT empirical proof of roster-count optima.

## What V0.13 established
The construction layer can and must treat these league dimensions independently:
- team count;
- starting-lineup size;
- slot eligibility (including FLEX and SF);
- positional league-native Scoring frontier;
- total roster size.

Start8, Start10 and Start11 are not scaled copies. Roster size caps capacity but does not mechanically create Scoring demand.

## Evidence from the six fixture formats
The positional economic supply responds coherently to format:
- 1QB formats have shallow QB demand/supply relative to SF;
- SF expands QB Scoring supply materially;
- deeper starting lineups expand RB/WR/TE demand and economic supply;
- 2TE + TEP expands TE demand/supply;
- team count changes per-team access to league-wide Scoring supply.

V0.13 also shows many legally/economically feasible whole-roster constructions at the same Scoring surplus. Therefore feasibility alone cannot choose an optimal tuple or surplus.

## Wookiee empirical status — PROVISIONAL
V0.12/V0.12.1 produced a striking descriptive pattern across 2023–2025, with lost-Oracle-WoRP declining as Scoring depth rose. However, the exact-family comparisons can have unequal roster-week support because infeasible family/roster-week combinations were skipped. Total/mean loss comparisons can therefore be biased by denominator/support differences.

Accordingly, the apparent Wookiee +2/+4 resilience region is NOT yet an empirical anchor and must not be frozen or generalized.

Required correction: V0.12.2 compares Scoring totals 11..15 on common roster-week support and, within each roster-week x Scoring total, uses the best feasible positional family. This tests Scoring-core SIZE under a hindsight-favorable flexible-family envelope rather than rewarding an exact tuple for skipping difficult weeks.

## Gate conclusion
Do NOT productize raw roster-count envelopes for any format from V0.13 alone.

Evidence sequence:
1. run V0.12.2 fair-support correction for Wookiee;
2. discover user-linked Sleeper league-seasons and their actual settings;
3. for each supported league-season, reconstruct team count, roster positions, starter count, FLEX/SF eligibility, scoring settings and roster size;
4. compute/use league-native WoRP economics;
5. reconstruct roster-weeks and test lost Oracle WoRP as Scoring depth changes on fair support;
6. express results as raw Scoring count and surplus relative to starting-lineup demand;
7. test whether broad elbow/resilience ranges move coherently with league format.

## Required interpretation
- Do not force any Wookiee surplus onto Start8/Start10/other Start11 leagues.
- Do not infer optimal Scoring count from economic supply divided by team count.
- Do not infer optimal tuple from number of feasible constructions.
- Do not let total roster size inflate Scoring demand automatically.
- Preserve broad ranges when neighboring counts imply the same roster decision.
- There is no validated universal 4% relevance threshold. Apply materiality/STOP only when residual differences cannot plausibly change roster construction, lineup decisions, or meaningful weekly/season outcomes.
- FREE/waiver remains Non-Scoring replenishment and need not directly generate WoRP.
- .25/.50/.75 remain sensitivity probes, not universal semantic thresholds.

## Sleeper readonly implementation
User-linked league discovery removes the need to manually supply league IDs. The discovery harness resolves a Sleeper username, inventories NFL league-seasons and settings, and preserves lineage metadata. Sleeper still has no general random/all-leagues endpoint, so the empirical universe is the set of discoverable/user-linked leagues with compatible historical WoRP inputs.

The multi-league validation harness must fail transparently when lineage or WoRP inputs are unavailable rather than filling gaps with Wookiee assumptions.
