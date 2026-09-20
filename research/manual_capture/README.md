# Earlier-data lineup policies versus perfect opportunity capture

Completed on the 69 evaluable cases from chronological portfolio validation. The three previous supply failures remain excluded and documented; this does not repair them. Compositions are frozen from that earlier calculation, never chosen again on the manual-policy test results.

## Procedure fixed before this run

Two policies select each week's legal lineup by the preceding three or five calendar weeks' mean fantasy points under exact league scoring. Selection uses no current-week results. Holdings are recreated with the same 256 draws and three seeds as before. Policy ties use stable ordering. Legal FLEX/SF eligibility and the actual number of players held constrain selection.

Measure separately: positive opportunity captured, negative performance captured, their signed sum, and the positive hindsight lineup ceiling. Negative bench performances do not count; negative performances selected into the lineup do. When a selected player's weekly stat row is absent, this simulation assumes zero fantasy points and applies that week's positional zero-point WoRP from the frozen engine's other zero-point rows. It never treats absence as replacement-level production. This assumption is not recovery of historical injury/availability.

The protocol records that policy-dependent conclusions cannot be deployed automatically; no new acceptable-capture percentage was invented. These are simple baseline policies with no injury/bye filters or outside projections. They do not reproduce actual manager decisions or prove that a more informed policy could not capture more.

## Capture of positive opportunity

Within each league-season/bench/policy, sum captured positive opportunity and the legal positive ceiling across evaluated windows; take their ratio, then average league-season ratios equally. Do not interpret this as net WoRP capture: negative starts are reported separately.

| Group | 5 bench: 3-week policy | 5 bench: 5-week policy | 12 bench: 3-week policy | 12 bench: 5-week policy |
|---|---:|---:|---:|---:|
| 1QB | 83.47% | 83.97% | 74.56% | 74.90% |
| SF/1TE | 83.63% | 84.14% | 74.70% | 74.77% |
| SF/2TE | 86.12% | 86.84% | 78.81% | 79.43% |

The denominator grows with bench depth. A lower capture fraction alone does not mean a worse roster. Neither ratio should be interpreted as a real manager's efficiency.

On matched league/window cases, increasing bench from 5 to 12 yields the following league-weighted four-week differences:

| Group | Extra perfect positive opportunity | Extra signed capture: 3-week policy | Extra signed capture: 5-week policy |
|---|---:|---:|---:|
| 1QB | 0.456612 | 0.017061 | 0.013636 |
| SF/1TE | 0.526450 | 0.042086 | 0.015570 |
| SF/2TE | 0.433432 | 0.021275 | 0.020084 |

Units are sums of individual weekly WoRP measurements, not actual victories or a jointly calibrated team win probability. The deeper and shallower compositions were selected separately by the prior rule; this compares whole-roster scenarios, not a causal isolated seven-player addition.

## Interpretation

For both tested policies, much of the extra hindsight ceiling is not captured. Similar aggregate fractions under two lookbacks do not validate other lineup policies, the composition ranking, or a universal capture discount. Do not multiply all portfolio scores by a constant or conclude that bench optionality is worthless. Coverage during injuries, acquisition, future season value, and manager information remain outside this simplified test.

This closes the specific manual-policy sensitivity test. The perfect-lineup objective alone is insufficient evidence to deploy exact manual-league roster quotas. The frozen Core and QB/RB directional evidence are not overturned. Engine and app remain unchanged; no automatic recommendation was added.

## Validation and files

Three focused tests pass: current-week spikes do not influence selection, selected missing-stat profiles receive the zero-point penalty, and negative bench results do not reduce captured performance. Across every evaluated case, the recalculated positive oracle matches the preceding validation's oracle within 1.8e-15, verifying identical holdings and denominator. Capture fractions stay within [0,1].

`capture_detail.csv` contains seed-level results; `case_results.csv` averages seeds; `summary.csv` records grouped capture; `paired_bench_results.csv` preserves matched depth differences. Results use the same documented manifest and native caches. Run:

```bash
python3 -m unittest test_manual_capture
python3 worp_manual_capture_test.py
```
