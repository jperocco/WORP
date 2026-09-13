# WORP LAB — RESEARCH TOUCHPOINT V2

**Date:** 2026-09-13  
**Repository:** `jperocco/WORP`  
**Purpose:** canonical research handoff after the latest conceptual evolution around dynamic replacement, capture, league-native lineup reconstruction, and the null-FLEX micro-audit.

---

## 1. Non-negotiable research posture

The research is **not trying to prove that waiver is optimal**.

The initial human hypothesis came from two prior observations:

1. the WR economic curve becomes increasingly compressed / flat in the tail; and
2. WR value is unusually concentrated at the top, with the strongest historical regime around the very top of the position rather than clean fixed 12-player fantasy buckets.

Those observations motivated the candidate construction:

> concentrate resources in stronger top WRs and potentially outsource a marginal lineup slot to the dynamic market.

But this is only a **candidate hypothesis**.

If the evidence says the better structure is to keep rostered depth — conceptually something like `WR3* + WR3* + WR3*` across relevant slots — that is a valid positive research result, **not a failure of the waiver thesis**.

Possible valid outcomes include:

- zero dynamically supplied slots;
- one dynamically supplied slot;
- two or more dynamically supplied slots;
- a result dependent on league format, season, position mix, or market conditions;
- rostered depth dominating dynamic replacement.

The objective is to discover the economic structure, not to force waiver into the answer.

---

## 2. Core distinctions that must remain intact

Never collapse these concepts:

`compression ≠ fungibility ≠ FREE ≠ capturable ≠ identifiable ≠ selectable ≠ startable ≠ economically superior`

Also:

- Flat WR tail does **not** establish a waiver threshold.
- A player being FREE does **not** mean a manager could have captured him before the useful production.
- Capturability does **not** mean the correct player could be selected ex ante.
- Ex-ante signal discrimination does **not** prove an executable waiver policy.
- Positive absolute WoRP is **not** required for a dynamic replacement to be economically useful.
- Negative absolute WoRP does **not** make a replacement useless if the rostered marginal alternative is similarly weak.
- WoRP is descriptive, not predictive.

No rank such as WR60, WR72, WR80, etc. may be promoted into a waiver/fungibility cutoff without separate evidence.

---

## 3. Economic WR structure already established

Fixed 12-player WR buckets do not describe the historical economic regimes particularly well.

Important prior findings:

- strong top concentration;
- first major season-WoRP regime break around WR8/9;
- progressive compression through the middle;
- low marginal-value tail with evidence beginning roughly around WR55/60+;
- the tail is economically compressed, but this does **not** establish fungibility or waiver usability.

Historical season-WoRP breakpoints recovered earlier:

- 9
- 18
- 36
- 55

Approximate interpretive regions only:

- WR1–8: elite / highly concentrated;
- WR9–20-ish: meaningful decline / different regime;
- WR20–40/50: middle compression;
- WR55/60+: low marginal-value tail.

These are descriptive regions, not roster rules.

---

## 4. STARTED / BENCHED / FREE foundation

Historical Sleeper snapshots reconstruct player state as:

- **STARTED** = observed in the lineup that week;
- **BENCHED** = rostered but not started;
- **FREE** = not rostered in the league snapshot.

This establishes where realized WoRP occurred. It does not by itself establish capture or manager decision quality.

Prior positive realized WoRP shares included:

- QB FREE: ~0.86%
- RB FREE: ~1.00%
- WR FREE: ~3.72%
- TE FREE: ~7.39%

The relatively meaningful TE FREE share was one reason interpositional analysis became important.

---

## 5. Capture — canonical concept

**Capture is central to the research.**

A hindsight FREE winner is not enough.

The useful decomposition is:

### 5.1 Availability / temporal capturability

Was the player genuinely available to be acquired **before** the production being evaluated?

The validated temporal capturability audit V0.2 found:

- 506 positive FREE candidate player-weeks;
- 495 CAPTURABLE;
- 11 AMBIGUOUS;
- ambiguity rate 2.17%;
- 97.75% of observed positive FREE WoRP temporally compatible with availability before production under that audit definition.

This establishes temporal compatibility, not manager capture.

### 5.2 Ex-ante identifiability

Could the player have been distinguished using information that existed before the target week?

Prior usage signal was tested without target-week information.

The denominator/control audit showed real discrimination:

- MID+HIGH prior-signal FREE player-weeks hit positive WoRP at ~21.17%;
- ZERO+LOW hit at ~2.45%;
- hit-rate lift ~8.65×;
- WoRP-rate lift ~10.38×.

For WR specifically, future positive-WoRP hit rate rose materially with prior signal.

The continuous WR signal curve suggested a candidate bend around roughly 2–4 prior targets under the specific signal definition, but this is **not a waiver threshold**.

### 5.3 Executable selection

Even if signal discriminates, an actual policy must choose the correct candidate from the available pool before the week.

The first naive policy — highest prior signal and immediate start — failed in absolute WoRP.

That failure does not invalidate dynamic replacement. It invalidates that specific policy and helped expose that absolute waiver WoRP was the wrong central economic question.

---

## 6. New central economic question: Replacement Gap / Replacement Capacity

The research question evolved from:

> “How much WoRP does waiver produce?”

into:

> **How much value is sacrificed when a marginal lineup slot is supplied dynamically rather than by the relevant rostered alternative?**

Conceptually:

`Replacement Gap(k) = dynamic-market option for kth outsourced slot − equivalent marginal rostered/lineup alternative`

The relevant benchmark is not zero.

Potential comparisons include:

- FREE vs BENCHED;
- FREE vs last starter / last FLEX;
- dynamic replacement vs the marginal rostered depth asset that would otherwise occupy the slot.

A dynamic player may have negative absolute WoRP and still be economically useful if the rostered alternative is only slightly better.

This is the bridge behind the original human intuition of something like:

`WR1* + WR1* + dynamic replacement`

versus a deeper fully rostered WR construction.

But **neither construction is assumed to win**.

---

## 7. Critical new requirement: persistence / week-to-week reliability

A strong rostered player (for example, a top-20 caliber asset) is generally available to be started repeatedly across the season.

Therefore the final comparison cannot merely count isolated waiver hits.

It must account for the fact that a rostered high-quality player supplies repeated weekly start opportunities and may beat his weekly expectation with some frequency, while a dynamic strategy requires repeated successful capture / selection decisions.

Future comparison must therefore consider at least:

- weekly availability of the rostered benchmark;
- frequency with which the rostered player produces above the relevant weekly expectation / replacement baseline;
- week-to-week stability / persistence of rostered value;
- frequency with which the dynamic market produces an eligible alternative;
- frequency with which that alternative is temporally capturable;
- frequency with which it is identifiable/selectable ex ante;
- realized lineup result after those constraints.

The correct comparison is a **seasonal sequence of decisions**, not a cherry-picked set of successful FREE player-weeks.

This is especially important because a rostered top asset can simply remain in the lineup every week, while dynamic replacement incurs a repeated capture problem.

---

## 8. Interpositional correction

FLEX is not inherently a WR slot.

Once the unit of analysis becomes the marginal lineup slot, RB/WR/TE must compete according to actual eligibility.

Therefore:

> `WR1* + WR1* + waiver` is shorthand for concentration + dynamic marginal replacement, not necessarily a WR waiver.

For a normal FLEX, the replacement market is interpositional:

- RB
- WR
- TE

The correct marginal solution may come from any eligible position.

This is the beginning of roster-construction analysis, but current scope remains the **sporting/WoRP cost of outsourcing marginal slots**, not asset-price valuation.

---

## 9. Boundary with roster valuation

Current WoRP layer asks:

> How much sporting value is lost or gained by dynamically supplying a marginal lineup slot?

It does **not yet** ask:

> What can the saved dynasty/startup/trade capital buy elsewhere?

Future picks, startup ADP, auction dollars, trade values, etc. belong to a later valuation layer.

Do not claim that concentration at the top wins simply because dynamic replacement has a small WoRP gap. The cost of obtaining the stronger top assets has not yet been modeled.

Current scope:

**WoRP Lab → Replacement Capacity / sporting cost**

Possible later extension:

**Roster Construction / Valuation → price of reallocating capital**

---

## 10. Failed aggregate interpositional audit V0.1

The first interpositional capacity script attempted to infer league-wide FLEX occupants by taking positional starter counts beyond aggregate mandatory cores.

It failed validation:

- 51/54 weeks did not reconstruct the expected FLEX count.

Therefore its attractive exploratory capacity numbers were **not accepted as findings**.

Reason:

aggregate positional rank cannot reliably reconstruct actual team/slot lineup history.

This established a hard methodological rule:

> replacement capacity must be **league-native, roster-native, week-native, and slot-aware**.

---

## 11. League-native V0.2 — latest capacity audit state

The next audit was rebuilt using the actual Sleeper league structure.

For each league/year it reads:

- real `roster_positions`;
- real matchup `starters` arrays;
- actual roster/team/week lineup slots;
- FREE market from that same league/week.

Actual 2023–2025 fixture starter structure recovered:

`QB, RB, RB, WR, WR, TE, FLEX, FLEX, FLEX, FLEX, SUPER_FLEX`

Thus there are **4 non-QB FLEX slots per team** in this specific league fixture.

The V0.2 correctly excluded SUPER_FLEX from the current RB/WR/TE marginal-market question.

Validation result:

- 54 league-weeks total;
- 46 league-weeks reconstructed perfectly;
- 8 league-weeks had null FLEX starters;
- invalid-week rate 14.81%;
- 4% guardrail triggered;
- **STOP**;
- capacity results were intentionally not interpreted.

Important: this STOP did not indicate positional mapping failure.

Across the failures there were:

- zero starter-array length mismatches;
- zero unknown positions;
- zero position-ineligible FLEX occupants.

The only issue was literal null FLEX starters.

---

## 12. Null FLEX micro-audit V0.1 — latest executed result

A dedicated micro-audit isolated every null real FLEX slot.

### 2024

All 12 null rows belong to a single roster:

- roster_id: 3
- team: `Frangalhos`
- weeks: 15, 16, 17, 18
- three FLEX slots left null each week
- starter indices: 7, 8, 9
- rostered player count: 30

Thus:

- 3 persistent null FLEX slots × 4 weeks = 12 rows.

### 2025

All 4 null rows belong to a single roster:

- roster_id: 6
- team: `We coming!!`
- weeks: 15, 16, 17, 18
- one FLEX slot left null each week
- starter index: 6
- rostered player count: 24

Thus:

- 1 persistent null FLEX slot × 4 weeks = 4 rows.

### Total

- 16 null FLEX rows;
- only 2 distinct season-rosters;
- only 4 distinct season-roster-slot combinations;
- every null occurs in weeks 15–18;
- the pattern is persistent within the affected roster/slot rather than random league-wide corruption.

No decision has yet been made to:

- exclude playoffs;
- impute starters;
- treat these as noise;
- resume capacity analysis.

The micro-audit explicitly ended at interpretation STOP.

---

## 13. What the null-FLEX result suggests — but does NOT yet prove

The concentration in exactly two rosters and exactly weeks 15–18 suggests that the failure is qualitatively different from the failed aggregate V0.1 reconstruction.

It may reflect:

- eliminated/inactive managers;
- playoff/consolation behavior;
- deliberate incomplete lineups;
- some league-specific late-season state.

But this must be established before changing the universe.

Do **not** simply drop weeks 15–18 because doing so makes validation pass.

The next methodological decision should determine what those late-season nulls represent and whether competitive regular-season market behavior and postseason/inactive-roster behavior should belong to the same replacement-capacity universe.

---

## 14. Research neutrality requirement for the next stages

Every future batch must be capable of returning **0 waiver/dynamic slots** as the correct answer.

Do not define success as “finding a waiver construction that works.”

The capacity curve should ask, without directional bias:

- 0 dynamic slots: fully rostered marginal depth;
- 1 dynamic slot;
- 2 dynamic slots;
- 3 dynamic slots;
- etc., subject to the actual league format.

Each additional dynamic slot faces a harder market-depth requirement.

If the marginal gap becomes economically unacceptable at slot 1, the waiver hypothesis dies for that format/sample.

If the gap remains small for one slot but not two, that supports one dynamically supplied slot.

If rostered depth consistently dominates after incorporating capture and persistence, that is the research result.

---

## 15. Intended future bridge after structural capacity survives

Structural/hindsight capacity is only the first layer.

A defensible final strategy comparison requires the following chain:

**league structure**
→ **actual marginal lineup slot**
→ **same-league FREE market**
→ **structural replacement capacity**
→ **temporal capturability**
→ **ex-ante identifiability**
→ **executable selection policy**
→ **week-to-week repeated capture**
→ **realized lineup value**
→ **comparison against persistent rostered alternative**

Only after this chain is validated can the research seriously compare concentration + dynamic replacement against fully rostered depth.

---

## 16. Current exact frontier

We are **not yet** at the point of deciding whether `WR1* + WR1* + waiver` beats deeper WR construction.

The immediate unresolved question is:

> **How should the league-native replacement-capacity universe treat the persistent null FLEX slots observed only in weeks 15–18 for two specific rosters?**

This must be resolved without outcome-driven filtering.

After that, the league-native structural capacity audit can be resumed/revised.

If structural capacity survives, the next major stage must incorporate **capture plus repeated week-to-week decision economics**, not merely hindsight FREE supply.

---

## 17. Do-not-assume checklist for any future chat/model

Do not assume:

- waiver is supposed to win;
- concentration is optimal;
- fully rostered depth is inferior;
- a flat WR tail is fungible;
- WR55/60+ is a waiver threshold;
- FREE production was capturable;
- capturable production was identifiable;
- identifiable candidates were executable selections;
- isolated waiver hits equal a sustainable seasonal strategy;
- absolute positive waiver WoRP is the correct benchmark;
- FLEX must be filled by WR;
- the failed V0.1 aggregate FLEX numbers are valid;
- the V0.2 capacity result has passed validation;
- weeks 15–18 should automatically be removed;
- future picks/trade values belong in the current WoRP layer.

Do preserve:

- league-native format;
- roster/week/slot reconstruction;
- interpositional FLEX eligibility;
- 4% methodological guardrail;
- capture distinction;
- ex-ante discipline;
- persistence / repeated weekly opportunity of rostered players;
- research neutrality between dynamic replacement and rostered depth.

---

## 18. Status label

**CURRENT STATUS: LEAGUE-NATIVE STRUCTURAL CAPACITY — VALIDATION STOP PENDING LATE-SEASON NULL-FLEX INTERPRETATION.**

The research has evolved materially beyond a simple “waiver value” question. The target is now an unbiased, league-specific comparison between persistent rostered marginal value and dynamically supplied marginal value, with capture and repeated weekly decision costs explicitly required before any roster-construction conclusion.