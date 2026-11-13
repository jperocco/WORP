# WoRP cloud readiness check — 2026-09-22

User asked to test whether the existing WoRP app can be hosted for a friend. Tested a fresh clone of jperocco/WORP at f06ad033e21c495d2678549810ae43cf0953f38c, targeting app_v0_9_4_7.py, in a new Python 3.12 virtual environment without a pre-existing engine cache. This is a local Linux readiness check, not a Streamlit Community Cloud deployment.

## Results

- Installed requirements.txt and requirements_ui.txt successfully. pip check reports no broken dependencies. Installed versions include Streamlit 1.64.0, pandas 3.0.6, numpy 2.5.3, Altair 6.3.0.
- AppTest initial app opening: no exceptions or UI errors.
- Actual public Sleeper username connection: first attempt hit the app's 12-second timeout; second attempt succeeded and listed 137 leagues for 2025.
- Real league 1180084795436826624 (2025 PREMIER LEAGUE): league/rosters/users screen loaded without exceptions. For the separate calculation test, this real league was injected into session state to isolate calculation from username discovery; historical data and engine calls were not mocked.
- Headless Streamlit server: HTTP 200 for both / and /_stcore/health. Server stopped after testing.
- Existing roster scenario unit/UI suite: 10 tests passed. This tests the existing editor, not renewed user approval of its product direction.
- Full 2023–2025 calculation at the default 4,000 simulations was started without prior season caches. It did not return during several minutes of observation and was manually interrupted. No season-cache files appeared during that observation. This is INCONCLUSIVE, not a completed calculation, automatic timeout, or proven engine error. End-to-end chart/Lineup Economics/Roster Construction rendering after calculation remains unverified in this clean environment.
- Focused real historical request for 2023 week 1 subsequently succeeded: 2,273 player stat records in 11.7 seconds. The current loader fetches the 54 historical week payloads sequentially; this supports investigating cold-start data-loading time but does not establish the total calculation duration or Community Cloud performance.

## Fix published

requirements.txt now includes -r requirements_ui.txt, ensuring the default dependency installation includes the UI dependencies. Commit 973cb48d1912620bbfe33b7d36e9f9e9cbd79902. No engine, research, or app UI changes were made.

## Remaining before sharing

Complete a cold calculation and subsequent cached rerun, then validate the real hosted environment and its resource limits. No public app was deployed, no link was created, and the user's computer is not part of these tests. Do not describe this check as cloud-ready approval. The user's rejection of the scenario editor as the central product answer remains unresolved; hosting preparation does not reverse that feedback.
