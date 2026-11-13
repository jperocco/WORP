# WoRP Lab UI V0.4

Fixes the V0.3 failure where every league showed the same graph.

V0.4:
- uses the selected Sleeper lineup;
- re-scores 2023–2025 weekly data with the selected league's core scoring;
- supports 4 vs 6 passing TD, PPR and TE premium;
- runs the frozen WoRP V0.2.1 math on the re-scored input;
- averages WoRP by positional rank across 2023–2025;
- blocks unsupported offensive bonus scoring rather than silently ignoring it.

Copy into the existing worp_lab_v0_2_1 folder:
- app_v0_4.py
- league_rescorer.py

Run:
    python3.12 -m streamlit run app_v0_4.py

The first calculation for each unique league format/scoring may take time:
3 seasons × 8,000 Monte Carlo simulations. Results are cached.

Important: worp_engine.py is not modified by this package.
