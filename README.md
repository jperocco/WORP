# WoRP Lab

**Wins over Replacement Player** para ligas de fantasy football com formato personalizado (Sleeper).

O app conecta um usuário do Sleeper, recalcula 2023–2025 com a pontuação exata da liga escolhida e mostra:

- **Lineup Economics**: quanto cada slot do lineup representa da pontuação esperada;
- **Roster Construction**: faixas por posição derivadas da economia da própria liga;
- **Roster Scenarios**: editor de elencos completos para comparação.

`WoRP semanal = P(vitória com o jogador) − P(vitória com o substituto)`, via simulação Monte Carlo empírica.

## Versões

| Componente | Versão | Situação |
|---|---|---|
| App (WoRP Lab) | **V0.9.4.7** — `app_v0_9_4_7.py` | atual |
| Motor (`worp_engine.py`) | V0.2.1 | congelado |
| Pesquisa Roster Construction | V0.32 | encerrada |

Decisões de produto e próximos passos: [`docs/WORP_PRODUCT_STATUS_2026-09-15.md`](docs/WORP_PRODUCT_STATUS_2026-09-15.md).

## Estrutura

```
app_v0_9_4_7.py                     app atual (o atalho Abrir_WoRP_Lab.command abre o app_v0_*.py de versão mais alta na raiz)
worp_engine.py                      motor WoRP V0.2.1
sleeper_native_loader.py            leitura de ligas e pontuação do Sleeper
worp_league_reading_v0_9_5.py       leitura estrutural da liga
worp_lineup_economics_v0_9_4.py     painel Lineup Economics
worp_roster_construction_product_v0_9_4.py   painel Roster Construction
worp_roster_scenarios.py            editor de cenários
worp_optionality_* / worp_portfolio_* / worp_positional_portfolio_simulation.py /
worp_manual_* / worp_active_roster_bounds.py   módulos de pesquisa ainda cobertos por testes
*.csv (4 na raiz)                   histórico lido pelo app e pelos módulos acima
data/                               dados empacotados com o produto
tests/                              testes automatizados
scripts/                            publicação segura (publish_main.sh, verify_release.py)
docs/                               status, handoffs e notas de pesquisa
research/                           saídas de estudos (cada pasta com README)
research/legacy/                    scripts e CSVs das rodadas de pesquisa encerradas
archive/apps/                       versões antigas do app, builders e READMEs de UI antigos
```

## Instalar e rodar

Python 3.12 recomendado.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3.12 -m streamlit run app_v0_9_4_7.py
```

O primeiro cálculo de cada formato/pontuação pode demorar (3 temporadas × simulações Monte Carlo). Os resultados ficam em cache em `~/.worp_lab/`.

## Testes

```bash
python -m unittest discover -p "test_*.py"
```

## Publicação segura

```bash
bash scripts/publish_main.sh
```

Interrompe a publicação se houver arquivos soltos, se a cópia local estiver atrás do GitHub ou se algum teste falhar. Não troca de versão, não força publicação e não mexe no atalho do app.

## Notas técnicas

A descrição do modelo empírico de vitória (V0.2) e do patch de transparência do replacement (V0.2.1) está em [`docs/ENGINE_V0_2_NOTES.md`](docs/ENGINE_V0_2_NOTES.md).
