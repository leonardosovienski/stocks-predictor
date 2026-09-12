# Estado atual do Stocks Predictor

<!-- DOC-SYNC-20260912 -->
> **Estado de publicação em 12/09/2026:** leia [a continuidade atual](PUBLICATION_STATUS_20260912.md). Branch `validation/retest-six-20260911`. O código deste projeto foi publicado na branch indicada. O candidato CAIN Supply permanece sem aprovação de estabilização. Afirmações anteriores de “sem push” descrevem a etapa histórica anterior à autorização.
<!-- /DOC-SYNC-20260912 -->


## Entrega arquitetural publicada — 11/09/2026

Versão **0.2.0** publicada: [release e artefatos](https://github.com/leonardosovienski/stocks-predictor/releases/tag/v0.2.0). [CI de engenharia aprovada](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34629227472) para a fonte `56c1a7b8db33f15404342fc61cceaa64452517d5`. Consulte [ARCHITECTURE_IMPLEMENTATION.md](ARCHITECTURE_IMPLEMENTATION.md) para comportamento, migração e limites. Este registro atualiza a entrega de software; estados científicos e registros datados abaixo conservam sua autoridade e contexto histórico.

Estado atualizado em 11/09/2026. A infraestrutura está validada para pesquisa
em lote em um host/disco local. **O pedido econômico integral permanece aberto;
lucro líquido pessoal executável ou futuro não foi demonstrado.**

[Mandato integral](docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md),
[encerramento R8](docs/continuation/2026-09-10-closure/README.md),
[revisão de arquivos](docs/maintenance/2026-09-10-files/README.md) e
[índice completo](docs/DOCUMENTATION_INDEX.md).

## Prontidão por uso

A iniciativa [OSS-20260911-01](docs/open_source_research/OSS-20260911-01/closure/REPORT.md)
terminou com cinco protótipos stdlib executados: fit temporal, ranking por data,
neutralização por grupo, participação ordem/volume e alocação com limite de giro.
Quatro são candidatos de engenharia; o último permanece experimental após
contraexemplo de reversão. Os recibos registram 33 checks e 40 comparações de
custos; nenhum benchmark econômico B3 novo. Código e evidências foram salvos
no commit `860996d`, sem integração no runtime. X05 continua bloqueado pelo
painel comum de inputs PIT e labels econômicos completos. UNC02 e TOTS3 mantêm
seus resultados e UNKNOWNs originais. Ver a [retomada](HANDOFF.md).

| Uso | Estado e limite |
|---|---|
| Diagnóstico e pesquisa histórica | Funcionais no runtime suportado, com gates de dados e evidência |
| Banco gerido e fontes versionadas | Ingestão por hash, replay, inspeção, backup e restauração testados; não mistura versões nem substitui bancos legados |
| Capacidade e recuperação | 250 mil linhas sintéticas e 55.986 preços reais; concorrência, WAL, morte de processo e falhas testados; sem certificação de falha física do host |
| Reprodução H21/H20 | Histórica, com escopo e entradas preservados; não é nova evidência independente |
| Retorno líquido pessoal e operação real | Não aptos: custos, eventos, cenário pessoal e observações insuficientes |
| Backup externo e produção distribuída | Não implantados; RPO limitado ao último snapshot local concluído |

## Dados e hipóteses

- Capital confirmado: R$5.000. Demais premissas pessoais continuam desconhecidas.
- R6 recuperou os cinco objetos antes ausentes; 1.448 arquivos do pacote original
  conferidos. O erro estrito de float de 2,22e-16 permanece documentado.
- 12 bancos originais preservados, com funções e hashes distintos. Integridade
  física não certifica cobertura econômica. Fonte15 é separada das revisões 13/14.
- Persistem 50 valores líquidos, 22 datas de pagamento e 28 registros societários
  incompletos. As contagens se sobrepõem; não significam ausência de todos os preços.
- H22: 24 avaliações, 22 calculadas e duas inviáveis; rejeição nos 11 pares calculáveis.
- H21: lucro histórico condicional, não lucro pessoal executável/futuro certificado.
  [Plano prospectivo](docs/research/2026-09-09-h21-forward-plan.json) fixado até
  primeira sessão em/após 10/09/2027, sem observações concluídas nem ordens.
- [R7](docs/audit/2026-09-10-r7/CONSOLIDADO.md) preserva 75 itens e 1.590 ocorrências
  sobrepostas. I15/arquivos e omissão PR75 resolvidos; I10–I14/I16 permanecem limitados.
- Licenças de 792 documentos individuais e disponibilidade histórica ampla não
  foram certificadas. A licença de uma base não se transfere automaticamente a seus PDFs.

## Evidência técnica

Runtime Linux/Python 3.13/3.14, Core 3.2.0 travado; tipagem/lint, piso de cobertura
77%, build reproduzível e teste do wheel fora do checkout. CI232 do merge
`bf7b3bc` aprovou 891 testes ativos + 17 históricos + 63 subtests por runtime;
cobertura exibida 80%/79%, sem somar versões ou tratar subtests como provas independentes.
Para qualquer commit posterior, consultar a CI correspondente.

O scanner verifica a árvore completa, inclusive merges, e um controle sintético.
A entrada operacional é `python -m stocks_predictor`; ver [runbook](docs/engineering/2026-09-10-r8/RUNBOOK.md).
Neste Windows, não instalar o runtime de produção nem criar venv.

O [estado anterior completo](https://github.com/leonardosovienski/stocks-predictor/blob/bf7b3bc9f888dc94fd186646424159f31682b747/STOCKS_CURRENT_STATE.md)
permanece no Git com suas datas. A [continuidade](HANDOFF.md) define a retomada.
