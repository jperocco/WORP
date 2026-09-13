# WoRP Lab UI V0.3

Presentation/integration release over UI V0.2.1. Frozen Engine V0.2.1 is unchanged.

Changes:
- WoRP now uses a distinct Ⓦ browser/app icon instead of the football used by JJ Stats.
- Preserves the case-insensitive Sleeper league search.
- Adds a Scott Connor-style 3-Year WoRP Avg reference curve from the local frozen historical WoRP results (2023–2025, positional ranks 1–50).
- Tooltip exposes position, positional rank, player, and 3-year WoRP average.
- Explicitly labels the curve as a reference shape, not as Scott Connor WAR and not as league-specific WoRP.
- Selected Sleeper league roster WoRP remains gated until league-specific scoring/player mapping is validated.

Run from the folder containing your historical CSV:

    python3.12 -m streamlit run app_v0_3.py

Expected historical input (first found):
- worp_2016_2025_normalized.csv
- worp_2016_2025_rankings.csv
