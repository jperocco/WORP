# Pesquisa encerrada (legado)

Scripts e CSVs das rodadas de pesquisa do WoRP (auditorias Wookiee, Scoring Core, Roster Construction até V0.32, multiliga etc.), movidos da raiz do repositório sem alterações de conteúdo.

A pesquisa de Roster Construction foi encerrada na V0.32 (ver `docs/WORP_PRODUCT_STATUS_2026-09-15.md`). Nenhum destes arquivos é usado pelo app atual nem pelos testes.

## Para rodar um script antigo

Os scripts foram escritos para a raiz do repositório: leem e gravam CSVs pelo nome, a partir da pasta atual, e importam `worp_engine` e outros módulos da raiz. Rode de dentro desta pasta com a raiz no caminho de importação:

```bash
cd research/legacy
PYTHONPATH=../.. python nome_do_script.py
```

Alguns scripts também leem `worp_2016_2025_rankings.csv` ou `worp_2016_2025_normalized.csv`, que continuam na raiz porque o app usa esses arquivos. Para reproduzir uma rodada exatamente como foi feita, use o layout original do repositório: commit `93c7154`.
