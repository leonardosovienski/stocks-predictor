# Implementação arquitetural — 2026-09-11

`DatasetSelection` liga o catálogo versionado ao simulador causal existente. Exige IDs de fonte, corte de observação e período. Abre um snapshot SQLite somente leitura, recusa fontes ausentes/futuras e preços conflitantes, normaliza barras e produz recibo por conteúdo. Não escolhe silenciosamente a versão mais recente.

`python -m stocks_predictor simulate-selected --db PATH --input JSON` recebe exatamente `selection`, `targets`, `corporate_actions`, `cost_per_side` e `price_mode`. A seleção contém `source_ids`, `observed_before`, `start` e `end`. Ações corporativas exigem `reference`, `splits`, `cash_events` e `stock_events`, mesmo que vazios. A integridade/completude dessas declarações não é certificada pelo comando. O corte do catálogo não significa disponibilidade pública histórica.

O caminho ativo usa imports relativos; a entrada legada continua compatível e `legacy_walk_forward` não foi reescrita. Não há nova hipótese, promoção econômica, dependência de Ops ou alteração de ledger.

Quatro testes stdlib passaram em Python 3.12 auxiliar: seleção exata, versão futura/ausente, conflito e ligação ao simulador. Ruff e Pyright do módulo novo aprovados. As cargas R8 devem ter recibos novos vinculados aos hashes atuais; recibos históricos não são atualizados retroativamente. CI Linux, build e wheel instalado mantêm seus gates existentes.

Rollback remove somente o uso da nova entrada e reinstala o pacote anterior. Nenhuma migração de dados é necessária. H1–H22, protocolos e evidências preservados.

As duas cargas finais passaram: 55.986 linhas da população pública preservada e 250.000 linhas sintéticas. Os recibos novos estão em `docs/engineering/2026-09-11-architecture/evidence/`. O registry R8 verifica 190 arquivos atuais e preserva todos os hashes históricos. Estado atual: `CI_VALIDATED`; a CI Linux 34629227472 passou em Python 3.13/3.14, incluindo builds reproduzíveis, wheel instalado e carga sintética de 250.000 linhas. O merge de teste 19ce2d5 e a fonte 56c1a7b têm a mesma árvore 6aea5beace71de87633daff54a5c0bde89c90014.

## Entrega arquitetural publicada — 11/09/2026

Versão **0.2.0** publicada: [release e artefatos](https://github.com/leonardosovienski/stocks-predictor/releases/tag/v0.2.0). [CI de engenharia aprovada](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34629227472) para a fonte `56c1a7b8db33f15404342fc61cceaa64452517d5`. Consulte [ARCHITECTURE_IMPLEMENTATION.md](ARCHITECTURE_IMPLEMENTATION.md) para comportamento, migração e limites. Este registro atualiza a entrega de software; estados científicos e registros datados abaixo conservam sua autoridade e contexto histórico.
