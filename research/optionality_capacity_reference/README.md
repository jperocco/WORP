# Optionality capacity: reference audit, 2026-09-16

## Decision

Exact whole-roster QB/RB/WR/TE quotas are **not established** by this audit.
The previously suggested 5 QB / 10 RB / 6 WR / 3 TE allocation was an
illustration without empirical support and must not become a product default.
Scoring Core and the V0.24/V0.32 research remain frozen. The app is unchanged.

## Work completed

Retrieved Wookiee's 2023, 2024 and 2025 league settings and all 18 weekly
matchup snapshots per season from Sleeper. Evaluated weeks 3–15: 12 rosters ×
13 weeks × 3 seasons = 468 roster-week cohorts. Joined the repository's
league-native weekly WoRP outcomes. Produced 4,749 positional slot observations.

Low-use eligibility requires ownership in the previous two snapshots and no
actual or positive-WoRP optimal-lineup selection in the previous up-to-five
calendar weeks. Future outcomes do not select the candidate pool. Ownership is
from matchup snapshots; transaction timestamps are not audited, so this is not
a fully validated pregame acquisition policy.

For each positional pool, evaluate 32 random nested orderings (seed 7), adding
one candidate at a time to the same baseline roster. Score the following four
weeks including the evaluation week using the best legal positive-WoRP lineup.
This is a hindsight ceiling on sporting opportunity, not actual captured WoRP.
Zero padding represents zero positive contribution, not an available waiver.
Missing production rows also contribute zero positive WoRP, not observed zero
fantasy points. No new materiality cutoff was selected.

## Capacity support for the user's eight/nine-slot question

| Optionality allocation or comparison | Eligible roster-weeks | Share of 468 |
|---|---:|---:|
| At least 2 QB + 6 RB candidates | 44 | 9.4% |
| Common pool for 2 QB + 6 RB versus 3 QB + 5 RB | 32 | 6.8% |
| Common pool for 2 QB + 7 RB versus 3 QB + 6 RB | 17 | 3.6% |

The eight-slot common pool spans only seven roster-seasons; the nine-slot pool
spans six. Windows overlap, so these are not independent experiments.
These counts describe players already held by those teams. They do not prove
that equivalent options were unavailable elsewhere, or that those quotas are
impossible. They show the current reference sample cannot establish a general
allocation recommendation. Joint portfolio returns were not estimated.

The nine-slot comparison crosses the project's <4% relevance STOP. Do not tune
a numerical quota on those 17 observations. This is not automatic evidence that
the question is unimportant: allocation is the requested product decision.
It means more micro-refinement of this reference sample is not justified.

## First-slot paired diagnostic

Same-cohort average incremental positive WoRP over the four-week horizon:

| Season | First QB option | First RB option | Paired roster-weeks |
|---|---:|---:|---:|
| 2023 | 0.023254 | 0.016939 | 131 |
| 2024 | 0.029213 | 0.030401 | 148 |
| 2025 | 0.026856 | 0.021773 | 116 |

The first-slot ordering changes in 2024. The small mean gaps do not establish
decision-material superiority. These averages are not the V0.7 material-tail
event metric and do not invalidate that earlier directional evidence. They
also do not establish the return on the second, third or later simultaneous
QB/RB options. Raw per-slot summaries use different support at different depths;
never sort those averages into a roster prescription.

## Boundaries and next useful test

- Wookiee's actual settings are in provenance.json. They are not the user's
  screenshot league and cannot be treated as a universal format.
- The baseline is defined by prior lineup use, not by a selected joint V0.32
  construction. Independent positional envelope bounds cannot supply that joint
  construction by themselves.
- Owned low-use pools are not the acquisition pool. IR/taxi membership is not
  reconstructed, so their counts must not be equated to active bench capacities.
- Uniform subset sampling is a declared diagnostic policy, not an empirically
  validated method for choosing which options to hold.
- Individual-position marginal returns omit joint FLEX/SF substitution and
  correlation. A product allocator must evaluate joint portfolios on common
  support with the actual league's scoring and slots.

The next material experiment would compare full QB/RB allocation policies over
multiple league environments using timestamped acquisition eligibility, active
roster capacity, and a fixed scoring baseline. It must establish supply and
joint returns before emitting exact positional totals. This audit does not
authorize replacing that experiment with a fixed ratio, a 3/3-versus-2/3 season
count ratio, a sum of positional curves, or a hand-selected tuple.

## Reproduce

From the repository root:

```sh
python3 worp_optionality_capacity_audit.py --out research/optionality_capacity_reference --draws 32
python3 worp_optionality_support_summary.py research/optionality_capacity_reference
```

The scripts use public Sleeper league and matchup endpoints. Generated details,
aggregate results and settings are committed together so the result does not
depend on unshared local outputs. Regeneration fetches current API snapshots;
the committed detail tables preserve this run's numerical observations.
