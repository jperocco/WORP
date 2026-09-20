# Historical active-roster accounting: conditional bounds

## Finding

The previous `owned_count <= active_capacity` screen discarded valid possibilities: ownership can include IR/taxi. Conversely, a small ownership count does not establish that all owned players were active. The old 97/2,544 screen is a selected sensitivity sample, not validated active-roster recovery.

The 4% rule was also misapplied: 3.8% surviving coverage means 96.2% missing coverage, a central data problem rather than a residual exception. The user authorized proceeding. This correction supersedes the previous coverage STOP.

## Evidence checked

All 324 cached weekly matchup payloads from the 18 selected league-seasons expose players/starters but not reserve/taxi assignments. The [official Sleeper documentation](https://docs.sleeper.com/) describes weekly matchups separately from the league roster endpoint. The latter has no documented week parameter; its reserve lists cannot be silently backdated.

A live probe of league 1180084795436826624 returned 12 roster objects with separate reserve and taxi fields, without a weekly assignment timeline. Transaction probes for weeks 3 and 4 returned seven and two waiver transactions respectively, with no reserve/taxi transition history. These probes do not establish that no other historical source exists. The documented transaction endpoint covers waivers, free agents and trades; the checked data are insufficient to reconstruct weekly active identities.

## Calculation and result

For ownership count N, observed starter count S, supplied active capacity C, and combined IR/taxi capacity R:

- active minimum = max(S, N − R)
- active maximum = min(C, N)
- positional minimum = max(observed starters at that position, owned at that position − R)
- positional maximum = min(owned at that position, C − observed starters at other positions)

These are separate bounds, not additive endpoint recommendations. They deliberately relax reserve eligibility and historical membership. They are conditional on the supplied season settings having applied at that time and on position mapping. They must not be presented as reconstructed facts.

Of 2,544 roster-week observations, 2,538 (99.76%) admit bounds and six conflict with supplied capacity. Of the compatible observations, 360 have an exact conditional active total; none have all four positional counts determined. The six inconsistencies remain flagged and are not silently clipped or further investigated as a priority.

## Decision

Preserve all compatible observations as bounds instead of discarding rosters above active capacity. Do not reuse the prior marginal portfolio outputs as active-roster evidence, and do not rerun them by pretending the bounds identify active players. We have recovered count constraints, not historical player eligibility, acquisition feasibility, or validated positional quotas.

The endpoint investigation is complete for the checked sources. Further exact historical reconstruction needs a source with dated reserve/taxi assignments. A numerical allocator using simulated positional portfolios is a different modeling choice and cannot be relabeled observed validation. Engine and app remain unchanged.

## Reproduction

Use the same manifest and cached inputs documented in `research/optionality_multileague/`:

```bash
python3 -m unittest test_active_roster_bounds
python3 worp_active_roster_bounds.py
```

`weekly_bounds.csv` preserves every cohort, positional intervals, and conflict reasons without player identifiers. Four focused tests verify the count logic. Raw endpoint probes remain local; `probe_summary.json` preserves schemas and hashes.
