# WoRP Lab V0.9.4.7 — user-authored roster scenarios

The user approved closing the exact-quota research sequence and building complete positional scenarios instead of publishing unsupported recommended counts.

## Product behavior

- Current launcher target: `app_v0_9_4_7.py`. It is a ready app, not a builder. The existing `Abrir_WoRP_Lab.command` pulls GitHub and chooses the highest numbered app.
- Roster Construction retains the existing Scoring Core total and positional references. Derived references are identified as model estimates. These references are not recalculated by the scenario editor.
- Users enter Scoring and Extra places for QB/RB/WR/TE. Inputs start at zero: no simulated optimum is prefilled.
- The editor displays per-position totals, chosen Core size, extra-place budget and places remaining. It compares chosen Scoring counts with the individual reference intervals.
- A named scenario can be saved only when the total equals the selected league's active capacity and the complete roster can fill all fixed/FLEX/SF starting vacancies. Unknown slot types are reported instead of silently treated as supported.
- Being outside a Core reference is a visible comparison, not an automatic ban on a user's scenario. Being inside all individual intervals is not joint empirical validation. Counts do not identify actual Scoring players.
- Saved scenarios can be compared side by side in a table and exported as CSV. Saving an existing name replaces that scenario. They remain in the app session, isolated by league, settings, capacity and reference. They are not stored permanently across app restarts.
- If the reference Core exceeds active capacity, show the capacity conflict without clipping the research interval or hiding the editor.
- Replaces the former directional priority sentence in this Roster Construction block. No named-player membership, draft advice, trade values, new thresholds or automatic exact quotas.

## Validation

Ten tests pass: eight accounting/eligibility/context tests and two Streamlit AppTest flows covering edits, disabled invalid saves, saving/comparison and league isolation. The ready app compiles. The full network-dependent app was not run against the user's live league; local screenshot confirmation remains a visual follow-up, not a missing code build.

Engine V0.2.1, frozen Core research and Lineup Economics are unchanged. Known limitations of the derived Core path remain as recorded in the status document; this UI does not upgrade their validation.

## Files

- `app_v0_9_4_7.py`: new launcher-compatible app, derived from the current GitHub V0.9.4.6 with only Roster Construction rendering and version labels changed.
- `worp_roster_scenarios.py`: isolated accounting, eligibility and editor.
- `test_roster_scenarios.py`, `test_roster_scenarios_ui.py`: focused checks.

Run tests with `python3 -m unittest test_roster_scenarios test_roster_scenarios_ui`.
