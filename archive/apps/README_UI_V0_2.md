# WoRP Lab UI V0.2 — Sleeper Integration Gate

Purpose: validate the live data path:

USER → LEAGUES → LEAGUE FORMAT → ROSTERS

This build deliberately does **not** calculate or display fake roster WoRP.

## Files
Copy `app_v0_2.py` into the existing `worp_lab_v0_2_1` folder.

## Run
```bash
python3.12 -m streamlit run app_v0_2.py
```

## Validation gate
1. Sleeper username resolves.
2. Correct leagues appear.
3. Selected league has correct team count and roster positions.
4. Scoring settings are detected.
5. Managers/rosters load correctly.

Only after this passes should Sleeper player IDs be mapped to the WoRP universe and league-specific WoRP be computed.
