# Estado científico legível por máquina para a CAIN — 2026-09-26

A CAIN passa a conhecer o estado da pesquisa do stocks pelos achados (`cain findings`): lê arquivos versionados
deste repositório num commit fixado (`git show`), somente leitura. A CAIN não abre bancos do stocks, não executa
código do stocks e não recebe preços. É o caminho B do estudo de 25/09. A orquestração em que a CAIN propõe
pesquisas (Etapa B, `integration-stocks`) continua dependendo das pré-condições do `predictor-qualification`.

## O que a CAIN lê

| Arquivo | Conteúdo | Comando da CAIN |
|---|---|---|
| [`research/scientific_state.json`](../../../research/scientific_state.json) | `stocks-scientific-state/1`. Estado literal de H1–H22, tentativa de cada hipótese, famílias encerradas, `reopen_policy` literal, reavaliação do Prompt 4, referência ao índice do ledger, identidade da política e sha256 de cada fonte | `cain findings ingest-state --domain stocks --path research/scientific_state.json` |
| [`trials_v2.json`](../../../trials_v2.json) | Registro canônico das 15 tentativas históricas, com `trial_id` e `hypothesis_id` | `cain findings ingest-registry --domain stocks --path trials_v2.json` |
| [Índice do ledger de domínio](../2026-09-24-protocol-v2/evidence/ledger/stocks-domain-ledger-index.json) | `stocks-trial-ledger-index/1`. Execuções v2 e desfechos, decisões, reavaliações, pré-registros e holdouts, com a cadeia de hashes | `cain findings ingest-ledger-index --domain stocks --path …/stocks-domain-ledger-index.json` |

Os três comandos recebem `--repo` (checkout local do stocks) e `--commit` (o commit fixado).

## Como o arquivo é gerado

```bash
python tools/export_scientific_state.py --write   # regrava a partir das fontes
python tools/export_scientific_state.py --check   # recusa divergência
```

- **Estados:** `stocks_predictor.research_admission.closed_hypotheses()`, sem tradução. O que cada estado
  significa e se ele encerra a hipótese está declarado no próprio arquivo (`vocabulary`).
- **Famílias encerradas:** as famílias que o repositório registra para as hipóteses encerradas, no manifesto
  `ST_RESEARCH_FREEZE` e em `trials_v2.json`. A H10 aparece com dois nomes: `quality_roe_leverage_double_filter`
  no manifesto e `quality_roe_leverage_intersection` no registro. Os dois entram, porque bloquear o reteste pelos
  dois nomes é o lado conservador. Os arquivos históricos não foram alterados.
- **Reavaliação:** cada relatório de veredito é citado pelo caminho no repositório e conferido pelo sha256
  registrado no Prompt 4.
- **Formato:** o arquivo não tem relógio. A mesma árvore gera os mesmos bytes. O
  [teste](../../../tests/test_scientific_state.py) falha se o arquivo versionado divergir das fontes, então mudar
  estado, tentativa, congelamento, reavaliação, índice do ledger ou política exige regravar o arquivo no mesmo commit.

## Como a CAIN interpreta

A leitura de cada estado é política versionada da CAIN (`findings/data/state-vocabulary.json`, aprovada pelo merge
do dono):

- Todo `CLOSED_*` é achado negativo. Bloqueia reteste da hipótese pela identidade (`hypothesis_id`) e pela família
  encerrada, mesmo em quarentena.
- `PAUSED` e `PAUSED_INCONCLUSIVE_DATA_QUALITY` são informativos. Não são resultado negativo, mas o circuito do
  stocks continua recusando trial novo para qualquer H histórica.

A CAIN recusa, antes de gravar qualquer coisa:
- estado que o vocabulário não lista;
- arquivo que declara outro domínio;
- schema desconhecido;
- índice com a cadeia quebrada.

Tudo entra como `DECLARED` (quarentena). Para virar `PROVEN`, a CAIN exige relatório de avaliação e transição de
governança com hash; isso fica para uma etapa futura.

## O que não vai para a CAIN

- **Preços** (COTAHIST, painel): a licença de redistribuição não foi verificada. O ADR 0020 da CAIN proíbe a
  transferência.
- **O ledger de domínio inteiro:** os registros anteriores a 25/09 guardam o hostname. Só o índice é publicado.
- **Nada do PC 1** nem de `C:\STOCKS\data`.
