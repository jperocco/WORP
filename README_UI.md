# WoRP Lab UI V0.1

Read-only first UI over the frozen WoRP Lab V0.2.1 historical engine outputs.

## Run

Keep `app.py` in the same folder as `worp_2016_2025_normalized.csv`.

Inside the existing `.venv`:

```bash
pip install streamlit
streamlit run app.py
```

This UI does not modify or reimplement `worp_engine.py`.
