# Implementação arquitetural — 2026-09-11

`DatasetSelection` liga o catálogo versionado ao simulador causal existente. Exige IDs de fonte, corte de observação e período. Abre um snapshot SQLite somente leitura, recusa fontes ausentes/futuras e preços conflitantes, normaliza barras e produz recibo por conteúdo. Não escolhe silenciosamente a versão mais recente.

`python -m stocks_predictor simulate-selected --db PATH --input JSON` recebe exatamente `selection`, `targets`, `corporate_actions`, `cost_per_side` e `price_mode`. A seleção contém `source_ids`, `observed_before`, `start` e `end`. Ações corporativas exigem `reference`, `splits`, `cash_events` e `stock_events`, mesmo que vazios. A integridade/completude dessas declarações não é certificada pelo comando. O corte do catálogo não significa disponibilidade pública histórica.

O caminho ativo usa imports relativos; a entrada legada continua compatível e `legacy_walk_forward` não foi reescrita. Não há nova hipótese, promoção econômica, dependência de Ops ou alteração de ledger.

Quatro testes stdlib passaram em Python 3.12 auxiliar: seleção exata, versão futura/ausente, conflito e ligação ao simulador. Ruff e Pyright do módulo novo aprovados. As cargas R8 devem ter recibos novos vinculados aos hashes atuais; recibos históricos não são atualizados retroativamente. CI Linux, build e wheel instalado mantêm seus gates existentes.

Rollback remove somente o uso da nova entrada e reinstala o pacote anterior. Nenhuma migração de dados é necessária. H1–H22, protocolos e evidências preservados.

As duas cargas finais passaram: 55.986 linhas da população pública preservada e 250.000 linhas sintéticas. Os recibos novos estão em `docs/engineering/2026-09-11-architecture/evidence/`. O registry R8 verifica 190 arquivos atuais e preserva todos os hashes históricos. Estado atual: `LOCAL_VALIDATED_CI_PENDING`; recibos anteriores de CI não certificam este candidato.
