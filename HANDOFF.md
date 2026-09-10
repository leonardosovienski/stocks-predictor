# Continuidade do Stocks Predictor

Leia [AGENTS](AGENTS.md), [estado atual](STOCKS_CURRENT_STATE.md),
[mandato integral](docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md) e
[índice documental](docs/DOCUMENTATION_INDEX.md). Antes de agir, confira HEAD,
remoto, branch, alterações e worktrees. O checkout canônico é
`C:\STOCKS\stocks-predictor`; não usar um SHA histórico para fazer reset.

## Estado para retomada

O [encerramento revisado](docs/continuation/2026-09-10-closure/README.md) foi
integrado pelo [PR81](https://github.com/leonardosovienski/stocks-predictor/pull/81),
merge `bf7b3bc9f888dc94fd186646424159f31682b747`, com CI232 aprovada.
A [revisão dos arquivos](docs/maintenance/2026-09-10-files/README.md) acrescenta
limpeza de caches, configuração única e navegação documental verificável.

A infraestrutura R8 está pronta para pesquisa em lote no escopo do
[runbook](docs/engineering/2026-09-10-r8/RUNBOOK.md). Fontes, custos e tempo
prospectivo permanecem incompletos. Não há operação financeira ativa nem lucro validado.
Não criar automações ou reabrir uma busca de estratégias por inércia.

## Condições concretas de continuação

1. Conferir o [registro R7](docs/audit/2026-09-10-r7/current.json) e seu
   [consolidado](docs/audit/2026-09-10-r7/CONSOLIDADO.md), distinguindo os estados
   históricos das implementações acrescentadas pela R8.
2. Selecionar uma dependência material com informação nova: identidade/publicação
   histórica, eventos e líquidos faltantes, tarifas, cenário pessoal ou observação futura.
3. Para hipótese nova, registrar mecanismo, fontes, universo, corte, orçamento e
   critério antes de medir desempenho. Preservar resultados negativos.
4. Validar e integrar as mudanças no SHA exato, conforme a CI e o mandato.

Capital confirmado R$5.000. Prazo, residência fiscal, custos XP/assessor/fixos,
valor do tempo e limite de perda quantificado não foram informados. Não usar zero
por padrão. A janela prospectiva H21 já está fixada até a primeira sessão em/após
10/09/2027; zero observações concluídas. O plano não pode ser antecipado ou
redefinido retrospectivamente para aprovar lucro.

## Reprodução e preservação

- [R3: auditoria de 24 frentes](docs/audit/2026-09-10-integral/README.md).
- [R4: ingestão e diagnóstico](docs/engineering/2026-09-10-r4/README.md).
- [R5: experimento H22](docs/research/2026-09-10-r5/README.md).
- [R6: recuperação de fontes](docs/research/2026-09-10-r6/README.md).
- [R7: inventário e reprodução](docs/audit/2026-09-10-r7/REPRODUCTION.md).
- [R8: operação e recuperação](docs/engineering/2026-09-10-r8/README.md).

Bancos originais não devem receber migrações ou ingestões. Dados locais,
recibos/entregas e protocolos congelados são preservados conforme
[RESEARCH_FREEZE.md](RESEARCH_FREEZE.md) e os mandatos atuais.

## Diário histórico preservado

O [HANDOFF anterior completo, com 4.483 linhas](https://github.com/leonardosovienski/stocks-predictor/blob/bf7b3bc9f888dc94fd186646424159f31682b747/HANDOFF.md)
continua imutável no Git. Contém a gênese da H1, seu critério Sharpe e a janela
2018-01, além das decisões, tentativas e revisões posteriores. Para consulta offline:

```text
git show bf7b3bc9f888dc94fd186646424159f31682b747:HANDOFF.md
```

O antigo `reports/splits_candidates.csv` era um derivado local de revisão de
quarentenas, não uma dependência do runtime nem um resultado certificado.
Não foi recuperado no acervo examinado; não foi inventado ou regenerado como se
fosse o original. As referências históricas estão mapeadas na revisão de arquivos.
