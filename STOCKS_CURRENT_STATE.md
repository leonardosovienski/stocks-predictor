# Estado atual do Stocks Predictor

Estado consolidado em 10/09/2026. A infraestrutura está validada para pesquisa
em lote em um host/disco local. **O pedido econômico integral permanece aberto;
lucro líquido pessoal executável ou futuro não foi demonstrado.**

[Mandato integral](docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md),
[encerramento R8](docs/continuation/2026-09-10-closure/README.md),
[revisão de arquivos](docs/maintenance/2026-09-10-files/README.md) e
[índice completo](docs/DOCUMENTATION_INDEX.md).

## Prontidão por uso

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
