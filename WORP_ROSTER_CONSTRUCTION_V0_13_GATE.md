# WoRP Lab — Roster Construction V0.13 Gate

## Status
V0.13 translation: PASS as a structural constraint map; NOT empirical proof of non-Wookiee roster-count optima.

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

## Wookiee empirical anchor
Wookiee starts 11. V0.12/V0.12.1 replicated across 2023–2025 that exact-starter Scoring coverage is too shallow. The decision-relevant resilience region is approximately 13–15 Scoring (+2 to +4 above starters), with >=.50 lost-Oracle-WoRP rates falling to roughly 4% around 14 Scoring and roughly 1–3% around 15.

This is a Wookiee empirical anchor, not a universal +2/+4 rule.

## Gate conclusion
Do NOT productize raw roster-count envelopes for non-Wookiee formats from V0.13 alone.

The next evidence requirement is empirical multi-league / multi-format validation. For each observed league-season:
1. read actual league settings from Sleeper readonly;
2. reconstruct team count, roster positions, starter count, FLEX/SF eligibility, scoring settings and roster size;
3. compute/use league-native WoRP economics;
4. reconstruct roster-weeks and test lost Oracle WoRP as Scoring depth changes;
5. express the result both as raw Scoring count and surplus relative to that league's starting-lineup demand;
6. compare whether the elbow/resilience zone moves coherently with format.

## Required interpretation
- Do not force Wookiee +2/+4 onto Start8/Start10/other Start11 leagues.
- Do not infer optimal Scoring count from economic supply divided by team count.
- Do not infer optimal tuple from number of feasible constructions.
- Do not let total roster size inflate Scoring demand automatically.
- Preserve broad ranges when neighboring counts imply the same decision.
- Apply the <4% relevance STOP when residual differences cease to alter roster construction.
- FREE/waiver remains Non-Scoring replenishment and need not directly generate WoRP.

## Data blocker / next implementation
Sleeper readonly can validate many league formats only if league IDs are discoverable/available. There is no general random/all-leagues endpoint. Wookiee alone cannot empirically validate the six fixture formats.

Next implementation should be a reusable multi-league validation harness that accepts a list of Sleeper league IDs (or user-linked league discovery), reads settings automatically, classifies slot eligibility from `roster_positions`, and runs the V0.12 depth-capture test league by league. The harness must fail transparently when a league's historical lineage or WoRP inputs are unavailable rather than filling gaps with Wookiee assumptions.
