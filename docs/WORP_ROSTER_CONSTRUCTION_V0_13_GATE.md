# WoRP Lab — Roster Construction Empirical Gate (V0.13 → V0.19)

## Status
**SCORING-CORE EMPIRICAL RANGE: PASS / FREEZE for the studied multi-league universe.**

V0.13 remains a PASS as structural translation, not as empirical proof by itself. The subsequent sequence V0.12.2 + V0.14–V0.19 now supplies the empirical layer that V0.13 lacked.

This document does **not** claim a universal exact Scoring count. The supported conclusion is a broad league-native construction principle and observed range behavior.

## Structural foundation — V0.13
Roster Construction must treat independently:
- team count;
- offensive starting-lineup size;
- slot eligibility, including FLEX and SF;
- positional league-native WoRP economics;
- total roster size;
- scoring settings, including economically material TE treatment.

Start8, Start10, Start11, etc. are not scaled copies. Roster size caps capacity but does not mechanically create Scoring demand. Slot eligibility, not traditional slot naming, is the governing representation.

## Wookiee empirical correction — V0.12.2 PASS
The original V0.12/V0.12.1 family comparisons had an unequal-support risk because infeasible family/roster-week combinations could be skipped. V0.12.2 corrected this with common roster-week support and flexible best-feasible positional families within each Scoring total.

On 531 common-support Wookiee roster-weeks, mean lost Oracle WoRP and >=.50 loss-event rates declined sharply as the Scoring core deepened from 11 to 15. The strongest regime change was 12 → 13; 14–15 bought additional resilience with diminishing returns.

**Wookiee-only frozen reading:** with 11 offensive starters, the efficient Scoring core appears broadly ~13–15. This is a benchmark, not a universal +2/+4 rule.

## Multi-league universe — V0.14/V0.15
Sleeper readonly discovery for user `jperocco` produced:
- 326 league-season observations;
- 53 structural formats;
- 174 lineages;
- 97 multi-season lineage candidates.

The IDP starter-count bug found in smoke testing was corrected: Scoring-core StartN refers to **offensive** QB/RB/WR/TE/FLEX/SF demand, while IDP is tracked separately.

The empirical V0.16 supported-format run completed:
- 305/305 league-seasons PASS;
- 29 empirical structural formats;
- zero failures.

Each league-season recomputed Sleeper-native fantasy scoring and league-native weekly WoRP from its own settings, reconstructed real roster-week ownership, and compared Scoring-core sizes on common support within league-season.

## V0.16 empirical result
Across the studied formats, additional Scoring depth protects Oracle WoRP rapidly at first and then enters diminishing returns. The location of the curve is league-native rather than a universal absolute roster count.

The evidence supports the construction concept:

> **Scoring Core = enough league-native Scoring depth to preserve the material WoRP available to the roster; once additional Scoring spots buy only decision-immaterial protection, remaining roster capacity belongs to Non-Scoring optionality.**

This does NOT mean FREE/waiver must itself generate WoRP. Existing Scoring bench depth can feed the lineup while FREE replenishes Non-Scoring capacity.

## V0.17 structural contrasts
V0.17 condensed 29 exact-format surfaces and searched for matched one-dimension contrasts.

Observed matched-pair evidence:
- team count: 6 matched pairs, median maximum curve separation ~0.0995 WoRP, maximum ~0.1861;
- TEP: 1 exact matched pair, maximum separation ~0.0086, decision-immaterial in that isolated comparison.

Interpretation constraint: this does **not** prove that StartN, SF, FLEX structure or TEP never matter. Exact matched pairs were sparse. Lack of isolated contrast is not evidence of no effect; league-native computation remains mandatory.

## V0.18 range candidates
A transparent decision-stability mapper, using each format's own curve rather than a universal absolute loss threshold, resolved all 29 observed formats.

Observed broad behavior:
- most formats mapped to approximately **StartN +3 to +5** Scoring players;
- high-support 12T SF Start10, Start11 and Start12 families mapped to **+4 to +5**;
- some larger-team / 1QB structures mapped to **+3 to +4**;
- exact neighboring boundaries are not treated as different decisions when roster construction is unchanged.

Because 29/29 resolution and strong +3..+5 convergence could have been an artifact of V0.18's guards, this result was NOT accepted without falsification.

## V0.19 threshold-free falsification — PASS
V0.19 returned to the raw V0.16 curves and removed V0.18's range-finding guards. It measured directly how much Oracle-WoRP protection each successive Scoring spot purchased and looked for material late resurgence after the proposed V0.18 range.

Result:
- 29 formats tested;
- **0 late-reversal reviews**;
- high-support formats: 5 formats / 207 league-seasons;
- median share of observed +0..+6 protection already purchased at V0.18 lower bound: **~90.48%**;
- median share purchased at upper bound: **~96.41%**;
- median protection remaining after upper bound: **~3.59%**;
- maximum post-range marginal purchase relative to the strongest prior/inside-range purchase: **~8.98%** in high-support formats.

Medium- and low-support groups showed essentially the same geometry: ~96.5%/~96.4% of observed protection purchased by the upper bound and no late reversals.

### Falsification conclusion
The broad +3..+5 convergence is **unlikely to be merely an artifact of the V0.18 mapping guards**. The raw empirical curves independently show that most of the observed Scoring-depth protection has already been purchased by this broad region, with no material late resurgence in the studied formats.

This is enough to STOP refining +3 versus +4 versus +5 as if there were an exact mathematical optimum. Nearby boundaries that produce the same roster decision are one economic envelope.

## Frozen Scoring-Core conclusion
For the studied Sleeper multi-league universe:

> **The Scoring core is anchored to offensive starting-lineup demand, not total roster size. A relatively small Scoring buffer beyond the starting lineup preserves the large majority of observed Oracle-WoRP protection; empirically this buffer most often lies around StartN +3..+5, with league-native variation. Additional roster capacity beyond the decision-stable Scoring range should not automatically be filled with more Scoring depth.**

Important limits:
- This is an observed multi-league empirical envelope, not a universal law for every possible fantasy format.
- Exact observed formats can use their empirical surface directly.
- Unsupported formats must preserve uncertainty and derive from league-native economics / structurally matched evidence rather than blindly applying +3..+5.
- Team count has demonstrated material matched-pair movement and must remain an active input.
- Starting lineup size and slot eligibility remain first-class inputs by construction even where exact causal matched pairs are sparse.
- Total roster size remains capacity, not automatic Scoring demand.
- No universal 4% loss threshold is validated or required.
- .25/.50/.75 remain sensitivity probes, not semantic thresholds.
- Oracle WoRP is a hindsight-perfect legal-lineup ceiling; this experiment is intentionally favorable to lean Scoring cores because retention uses realized season positional rank.

## Product translation contract
The product should NOT say `always roster starters +4`.

Correct architecture:

**league settings → league-native WoRP economics → observed/matched Scoring-core envelope → Scoring capacity range → remaining capacity as Non-Scoring → Roster Diagnostic**

For a directly observed/high-support format, the empirical range can be surfaced with appropriate confidence. For a sparse/unseen format, widen uncertainty and use league-native structural translation rather than false precision.

## STOP / next research boundary
**STOP Scoring-Core range micro-refinement.** V0.19 closes the question sufficiently for roster-construction decisions in the studied universe.

Do not spend cycles deciding whether +3, +4 or +5 is the single optimum unless new evidence shows a decision-material difference.

The next Roster Construction problem is no longer "how many total Scoring players?". It is:

> **Given a league-native Scoring-core capacity range, how should that Scoring capacity be distributed across QB/RB/WR/TE under slot eligibility and positional WoRP economics, without forcing exact positional quotas?**

This should remain range-based and interpositional. FLEX/SF means positional upper bounds cannot simply be summed. The goal is robust construction families, not a single exact tuple.

## Required interpretation preserved
- WoRP is positional economics; do not use `WoRP per player`.
- Economic zero is decision-immaterial marginal impact, not necessarily numeric 0.000.
- Compression alone is not fungibility or economic relevance.
- Non-Scoring ≠ FREE. FREE is an availability state within the Non-Scoring ecosystem.
- FREE/waiver need not directly generate WoRP to justify Non-Scoring capacity.
- Asset Value remains out of scope.
- Do not infer waiver thresholds from raw positional ranks.
- Preserve broad ranges whenever neighboring counts imply the same roster decision.
- Wookiee is a reference/test league, never the definition of WoRP.
- League adaptability remains priority zero.
