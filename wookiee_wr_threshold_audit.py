#!/usr/bin/env python3
"""
Wookiee WR Threshold Audit
PROVOCAÇÃO / NÃO ALTERA O ENGINE

Pergunta ÚNICA:
    Quantos WRs o formato da Wookiee demanda como starters por semana?

Fixture oficial:
    12 teams
    11 starters
    roster_positions esperado no Sleeper:
      QB, RB, RB, WR, WR, TE, FLEX x4, SUPER_FLEX
    (bench/IR/taxi não entram neste audit)

Método:
- Usa a MESMA função select_aggregate_starters do worp_engine.py congelado.
- Usa fantasy_points semanais já calculados no histórico WoRP.
- Filtra REG.
- Para cada season/week, seleciona o starter pool agregado.
- Conta quantos WRs foram selecionados.
- Reporta min, P25, mediana, média, P75, max e distribuição.
- O rank estrutural do último WR demandado = número de WR starters naquela semana.

NÃO:
- define waiver
- modela Captura
- compara WR com RB backup
- altera o engine
"""

from pathlib import Path
import inspect
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    import worp_engine as we
except Exception as e:
    raise SystemExit(f"ERRO: não consegui importar worp_engine.py: {e}")

if not hasattr(we, "select_aggregate_starters"):
    raise SystemExit("ERRO: worp_engine.py não expõe select_aggregate_starters.")

# Wookiee: 12T, 1QB, 2RB, 2WR, 1TE, 4 FLEX, 1 SF.
# Bench/IR/Taxi deliberadamente não participam da demanda de STARTERS.
FORMAT = {
    "teams": 12,
    "qb": 1,
    "rb": 2,
    "wr": 2,
    "te": 1,
    "flex": 4,
    "superflex": 1,
}

EXPECTED_TOTAL_STARTERS = FORMAT["teams"] * (
    FORMAT["qb"] + FORMAT["rb"] + FORMAT["wr"] + FORMAT["te"]
    + FORMAT["flex"] + FORMAT["superflex"]
)

CANDIDATES = [
    "worp_2016_2025_weekly.csv",
    "worp_2025_weekly.csv",
    "weekly_worp.csv",
]

def find_weekly_csv():
    for name in CANDIDATES:
        p = ROOT / name
        if p.exists():
            return p

    # fallback conservador
    hits = [
        p for p in ROOT.glob("*.csv")
        if "weekly" in p.name.lower() and "worp" in p.name.lower()
    ]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        raise SystemExit(
            "ERRO: encontrei múltiplos CSVs weekly WoRP. "
            "Renomeie/use worp_2016_2025_weekly.csv.\n"
            + "\n".join(f"  - {p.name}" for p in hits)
        )
    raise SystemExit(
        "ERRO: não achei o histórico weekly WoRP na pasta.\n"
        "Esperado: worp_2016_2025_weekly.csv"
    )

def pick_col(df, names, required=True):
    lower = {str(c).lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    if required:
        raise SystemExit(
            f"ERRO: coluna necessária ausente. Procurei {names}. "
            f"Colunas disponíveis: {list(df.columns)}"
        )
    return None

def call_frozen_selector(group):
    """
    Adapter pequeno para tolerar nomes de argumentos do frozen engine.
    Não reimplementa a matemática.
    """
    fn = we.select_aggregate_starters
    sig = inspect.signature(fn)
    params = sig.parameters

    kwargs = {}
    # dataframe
    for n in ("week_df", "df", "players", "player_week", "weekly_df"):
        if n in params:
            kwargs[n] = group
            break

    mapping = {
        "n_teams": FORMAT["teams"],
        "teams": FORMAT["teams"],
        "num_teams": FORMAT["teams"],
        "qb_slots": FORMAT["qb"],
        "qb": FORMAT["qb"],
        "rb_slots": FORMAT["rb"],
        "rb": FORMAT["rb"],
        "wr_slots": FORMAT["wr"],
        "wr": FORMAT["wr"],
        "te_slots": FORMAT["te"],
        "te": FORMAT["te"],
        "flex_slots": FORMAT["flex"],
        "flex": FORMAT["flex"],
        "sf_slots": FORMAT["superflex"],
        "superflex_slots": FORMAT["superflex"],
        "superflex": FORMAT["superflex"],
    }
    for k, v in mapping.items():
        if k in params:
            kwargs[k] = v

    # Alguns builds recebem um objeto/settings dict.
    for n in ("settings", "league_settings", "format_settings"):
        if n in params:
            kwargs[n] = {
                "teams": FORMAT["teams"],
                "n_teams": FORMAT["teams"],
                "qb_slots": FORMAT["qb"],
                "rb_slots": FORMAT["rb"],
                "wr_slots": FORMAT["wr"],
                "te_slots": FORMAT["te"],
                "flex_slots": FORMAT["flex"],
                "sf_slots": FORMAT["superflex"],
            }

    try:
        if any(n in params for n in ("week_df","df","players","player_week","weekly_df")):
            return fn(**kwargs)
        # fallback: dataframe como primeiro argumento posicional
        non_df_kwargs = {k:v for k,v in kwargs.items() if v is not group}
        return fn(group, **non_df_kwargs)
    except TypeError as e:
        raise SystemExit(
            "ERRO ao chamar select_aggregate_starters do engine congelado.\n"
            f"Assinatura encontrada: {sig}\n"
            f"Detalhe: {e}\n"
            "Não vou reimplementar a função silenciosamente."
        )

def normalize_selected(result, original):
    if isinstance(result, pd.DataFrame):
        return result.copy()

    # tuple: procura DataFrame ou coleção de índices
    if isinstance(result, tuple):
        for x in result:
            if isinstance(x, pd.DataFrame):
                return x.copy()
        for x in result:
            if isinstance(x, (list, tuple, np.ndarray, pd.Index, set)):
                vals = list(x)
                if vals and all(v in original.index for v in vals):
                    return original.loc[vals].copy()

    if isinstance(result, (list, tuple, np.ndarray, pd.Index, set)):
        vals = list(result)
        if not vals:
            return original.iloc[0:0].copy()
        if all(v in original.index for v in vals):
            return original.loc[vals].copy()

    raise SystemExit(
        "ERRO: retorno de select_aggregate_starters não reconhecido: "
        f"{type(result).__name__}. Não vou adivinhar."
    )

csv_path = find_weekly_csv()
df = pd.read_csv(csv_path)

season_col = pick_col(df, ["season"])
week_col = pick_col(df, ["week"])
pos_col = pick_col(df, ["position", "pos"])
fp_col = pick_col(df, ["fantasy_points", "fantasy_points_ppr", "points", "fp"])
season_type_col = pick_col(df, ["season_type"], required=False)

# REG-only gate.
if season_type_col is not None:
    df = df[df[season_type_col].astype(str).str.upper().eq("REG")].copy()

df = df[df[pos_col].astype(str).str.upper().isin(["QB","RB","WR","TE"])].copy()
df[fp_col] = pd.to_numeric(df[fp_col], errors="coerce")
df = df[df[fp_col].notna()].copy()

rows = []
allocation_rows = []

for (season, week), g in df.groupby([season_col, week_col], sort=True):
    g = g.copy()
    # Padroniza nomes somente na cópia enviada ao selector se necessário.
    if "position" not in g.columns:
        g["position"] = g[pos_col]
    if "fantasy_points" not in g.columns:
        g["fantasy_points"] = g[fp_col]

    selected_raw = call_frozen_selector(g)
    selected = normalize_selected(selected_raw, g)

    selected_pos_col = "position" if "position" in selected.columns else pos_col
    counts = (
        selected[selected_pos_col].astype(str).str.upper()
        .value_counts()
        .reindex(["QB","RB","WR","TE"], fill_value=0)
    )

    total = int(counts.sum())
    if total != EXPECTED_TOTAL_STARTERS:
        raise SystemExit(
            f"FAIL season={season} week={week}: selector retornou {total} starters; "
            f"esperado {EXPECTED_TOTAL_STARTERS}. Audit interrompido."
        )

    wr_n = int(counts["WR"])
    rows.append({
        "season": int(season),
        "week": int(week),
        "wr_starters": wr_n,
        "wr_threshold_rank": wr_n,
    })
    allocation_rows.append({
        "season": int(season),
        "week": int(week),
        "QB": int(counts["QB"]),
        "RB": int(counts["RB"]),
        "WR": int(counts["WR"]),
        "TE": int(counts["TE"]),
        "total": total,
    })

weekly = pd.DataFrame(rows)
alloc = pd.DataFrame(allocation_rows)

if weekly.empty:
    raise SystemExit("ERRO: nenhuma semana REG auditável.")

q = weekly["wr_starters"].quantile([0, .25, .5, .75, 1.0])
summary = pd.DataFrame([{
    "weeks": len(weekly),
    "min": q.loc[0.0],
    "p25": q.loc[0.25],
    "median": q.loc[0.5],
    "mean": weekly["wr_starters"].mean(),
    "p75": q.loc[0.75],
    "max": q.loc[1.0],
    "sd": weekly["wr_starters"].std(ddof=1),
}])

by_season = (
    weekly.groupby("season")["wr_starters"]
    .agg(
        weeks="size",
        min="min",
        median="median",
        mean="mean",
        max="max",
    )
    .reset_index()
)
by_season["p25"] = weekly.groupby("season")["wr_starters"].quantile(.25).values
by_season["p75"] = weekly.groupby("season")["wr_starters"].quantile(.75).values
by_season = by_season[
    ["season","weeks","min","p25","median","mean","p75","max"]
]

dist = (
    weekly["wr_starters"]
    .value_counts()
    .sort_index()
    .rename_axis("wr_starters")
    .reset_index(name="weeks")
)
dist["pct_weeks"] = dist["weeks"] / len(weekly) * 100

weekly.to_csv(ROOT / "wookiee_wr_threshold_weekly.csv", index=False)
summary.to_csv(ROOT / "wookiee_wr_threshold_summary.csv", index=False)
by_season.to_csv(ROOT / "wookiee_wr_threshold_by_season.csv", index=False)
dist.to_csv(ROOT / "wookiee_wr_threshold_distribution.csv", index=False)
alloc.to_csv(ROOT / "wookiee_starter_allocation_weekly.csv", index=False)

print("=" * 82)
print("WOOKIEE WR THRESHOLD AUDIT — PROVOCAÇÃO / NÃO ALTERA O ENGINE")
print("=" * 82)
print(f"\nSource: {csv_path.name}")
print("Format: 12T | 1QB 2RB 2WR 1TE 4FLEX 1SF | 11 starters/team")
print(f"Expected aggregate starters/week: {EXPECTED_TOTAL_STARTERS}")
print(f"REG weeks audited: {len(weekly)}")

print("\n1. WR STRUCTURAL DEMAND — ALL WEEKS\n")
print(summary.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

print("\n2. WR STRUCTURAL DEMAND — BY SEASON\n")
print(by_season.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

print("\n3. DISTRIBUTION OF WEEKLY WR THRESHOLD\n")
print(dist.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

print("\n4. SANITY CHECK — STARTER ALLOCATION\n")
print(
    alloc[["QB","RB","WR","TE","total"]]
    .agg(["min","median","mean","max"])
    .to_string(float_format=lambda x: f"{x:.2f}")
)

print("\nSaved:")
for name in [
    "wookiee_wr_threshold_weekly.csv",
    "wookiee_wr_threshold_summary.csv",
    "wookiee_wr_threshold_by_season.csv",
    "wookiee_wr_threshold_distribution.csv",
    "wookiee_starter_allocation_weekly.csv",
]:
    print(f"  {name}")

print("\nGATE:")
print("Este audit mede SOMENTE a demanda estrutural semanal por WR.")
print("Não interpretar waiver, Captura, RB backups ou roster construction ainda.")
print("Se a distribuição for concentrada, Threshold sobrevive ao Ponto 1.")
print("Se for ampla/instável, não forçaremos um número único.")
