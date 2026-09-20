# WoRP — referência Scott Connor e próximo passo autorizado

## Fonte preservada

Scott Connor, **WAR Has Changed: A New Way to Measure Wins Above Replacement**, DD Fantasy Football, 19/09/2026 (data exibida no material enviado pelo usuário).

O texto fornecido foi preservado em [docs/references/scott_connor_war_has_changed_2026-09-19.md](docs/references/scott_connor_war_has_changed_2026-09-19.md). É material de terceiro para referência do projeto, não documentação metodológica aprovada do WoRP. O arquivo contém links para imagens externas, não cópias dessas imagens. Não atribuir ao WoRP autoria nem validação dos exemplos do artigo.

## Ideias do artigo

- Distinguir produção positiva disponível de produção efetivamente capturada na escalação.
- Medir oportunidades semanalmente; banco pode oferecer cobertura ou oportunidades futuras mesmo sem pontuar hoje.
- Profundidade pode gerar produção redundante quando faltam vagas para aproveitá-la.
- Diferenciar falta de cobertura de produção que ficou fora da escalação.
- Best ball e escalação manual têm mecanismos diferentes de aproveitamento.
- Formato, elegibilidade e scoring da liga definem a economia; produção não equivale a valor de mercado dynasty.

## Decisão aceita pelo usuário

Preservar o motor V0.2.1. Aplicar a distinção entre oportunidade disponível e contribuição acessível ao Roster Construction/Diagnostic. Avaliar cada vaga adicional junto às demais posições, respeitando vagas fixas, FLEX e SF. Manter apresentação posicional, sem nomes ou membership individual de produto.

Não substituir o WoRP assinado por piso zero. O positivo truncado pode ser usado como teto retrospectivo de oportunidade, explicitamente identificado. Não somar diferenças individuais de probabilidade e apresentá-las como probabilidade conjunta ou vitórias reais. Não usar soma irrestrita de produção do banco como denominador de captura. Uma escalação retrospectivamente inferior não prova erro de decisão antes dos jogos.

Lineup Economics permanece com fantasy points/share/pts-week/composição FLEX-SF. Scoring Core V0.24/V0.32 permanece congelado. O artigo não autoriza thresholds novos, quotas arbitrárias ou mudança do motor.

## Próximo passo autorizado

O usuário aprovou simular composições posicionais dentro da capacidade ativa da liga. Esta é uma estimativa de modelo, não reconstrução de IR/taxi nem observação de rosters reais.

Primeira execução: comparar todos os vetores QB/RB/WR/TE viáveis para duas profundidades de banco no mesmo formato e scoring; usar somente informações anteriores à janela avaliada para ordenar/selecionar os perfis, manter os mesmos perfis nas comparações e otimizar apenas a escalação legal de cada semana. Reportar resultados por janela e sensibilidade; não publicar o máximo amostral como quota ideal.

O ganho retrospectivo acessível continua sendo um teto para ligas com escalação manual. Ordenação por histórico curto, amostra de perfis, disponibilidade de aquisição e incerteza de temporadas precisam ficar explícitas. Resultados iniciais pertencem à pesquisa; integração no app exige evidência suficiente para uma recomendação estável.
