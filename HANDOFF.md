# Continuidade do Stocks Predictor

## Candidato local ResearchBundleV1

Leia [o exportador aditivo](docs/RESEARCH_BUNDLE_V1.md): recibo real de catálogo,
versão exata e lineage, com recursos reference_only/licença UNKNOWN. O modo opcional
executa DatasetSelection para esta exportação sobre cópia verificada; não prova input
de experimento histórico e não roda simulação. São nove testes do exportador e cinco
do seletor, além do Snapshot legado. A remediação de 12/09 usa perfil 2 e proveniência
dos bytes efetivos do helper/contratos. Recibos científicos preservados; sem push ou
instalação operacional. O documento do exportador aponta a evidência da rodada atual.

## Entrega arquitetural publicada — 11/09/2026

Versão **0.2.0** publicada: [release e artefatos](https://github.com/leonardosovienski/stocks-predictor/releases/tag/v0.2.0). [CI de engenharia aprovada](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34629227472) para a fonte `56c1a7b8db33f15404342fc61cceaa64452517d5`. Consulte [ARCHITECTURE_IMPLEMENTATION.md](ARCHITECTURE_IMPLEMENTATION.md) para comportamento, migração e limites. Este registro atualiza a entrega de software; estados científicos e registros datados abaixo conservam sua autoridade e contexto histórico.

## Exportação local de relatos para Cain — 11/09/2026

[tools/export_cain_status.py](tools/export_cain_status.py) é um exportador stdlib
independente do runtime científico. Lê somente `STOCKS_CURRENT_STATE.md`, com SHA-256
previamente conferido e fonte commitada. Preserva estados literais, offsets, hashes,
cobertura parcial e tempos desconhecidos. Não abre bancos, usa LLM ou executa pipeline.
Publicações desta instalação ficam em `C:\STOCKS\work\cain-l0\publications`.
Cain recebe cópias autorizadas; este produtor continua independente do consumidor.

```text
python tools/export_cain_status.py --root CAMINHO_DO_CHECKOUT --expected-sha SHA256_CONFERIDO --output DESTINO_NOVO_FORA_DO_CHECKOUT.json
python tools/test_export_cain_status.py
```

O destino deve permanecer na raiz local autorizada do projeto. Não reutilizar um hash
antigo depois de mudar a fonte. A publicação é ResearchSnapshotV1; o consumidor usa o
validador canônico do contrato. O exportador não impõe instalações ao ambiente científico.
No Windows, os checks usam Python auxiliar stdlib; temporários ficam na raiz do projeto.

Integração real Stocks → Cain exercitada nesta rodada: exportação, validação
canônica, importação/reimportação, consulta na interface, referências e recuperação
sem acesso ao produtor. É integração de relatos públicos selecionados, sem nova
validação científica/econômica. O estado do runtime e os protocolos anteriores permanecem.
Mudança restrita a ferramentas de intercâmbio; não altera pacote ou recibos R8/operacionais.
Branch de continuidade deste incremento: `integration/cain-status-20260911`.


Leia [AGENTS](AGENTS.md), [estado atual](STOCKS_CURRENT_STATE.md),
[mandato integral](docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md) e
[índice documental](docs/DOCUMENTATION_INDEX.md). Antes de agir, confira HEAD,
remoto, branch, alterações e worktrees. O checkout canônico é
`C:\STOCKS\stocks-predictor`; não usar um SHA histórico para fazer reset.

## Estado para retomada

Atualização de 11/09/2026: a iniciativa `OSS-20260911-01` foi encerrada no
[relatório final OSS](docs/open_source_research/OSS-20260911-01/closure/REPORT.md).
O commit `860996d` preserva pesquisa, continuidades, recibos e cinco capacidades
experimentais no [kit executável](research/oss/OSS-20260911-01/README.md).
São 33 checks principais e 40 comparações de custos já registrados; não são
testes econômicos B3 nem certificação de produção. Quatro capacidades são
candidatas à integração; o alocador com limite de giro continua experimental.

Para retomar sem este chat, ler o relatório final e seu roadmap. Não reiniciar
discovery, baseline, UNC02/X03 ou reconstrução TOTS3 sem evidência material.
X05 depende de um painel B3 congelado com inputs disponíveis na decisão e labels
econômicos completos no mesmo universo/período. Aplicar esse bloqueio somente
aos experimentos dependentes. O runtime R8 e os estados históricos permanecem.

Pasta de entrega local: `C:\STOCKS\outputs\OSS-20260911-01-ENCERRAMENTO`.
O pacote `OSS-closure-kit-final.zip` e `manifest-final.json` preservam a entrega;
não sobrescrever recibos. Fontes e bancos externos ao Git continuam na raiz
`C:\STOCKS`; apagar o chat não é autorização para removê-los.

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


## Implementação arquitetural local — 2026-09-11

As alterações candidatas, seus limites, verificações e rollback estão em [ARCHITECTURE_IMPLEMENTATION.md](ARCHITECTURE_IMPLEMENTATION.md). Esta implementação local não publica releases, não atualiza automaticamente os consumidores e não altera os vereditos científicos históricos.
