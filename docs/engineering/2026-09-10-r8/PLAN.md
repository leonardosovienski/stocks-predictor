# Plano operacional R8 — registrado antes da validação

Alvo: pesquisa local em lote, um host, SQLite em disco local, Python 3.13/3.14
no Linux de CI. Windows/Python 3.12 é apenas auxiliar stdlib. Não é um serviço
de negociação nem um banco distribuído. Capital habilitado: não.

Critérios de aceitação:

1. Entrada instalada `python -m stocks_predictor` integra fontes versionadas,
   hash obrigatório, inspeção, backup, restauração e avaliação de entradas datadas.
2. Banco novo identificado e separado dos bancos históricos. Leitores legados
   e migrações recusam esse banco antes de mutações. Versões não são agregadas
   implicitamente em séries financeiras; inspeção apresenta cada fonte.
3. Transações atômicas, append-only, replay idempotente, divergência rejeitada;
   timeout de escritor explícito. Dados observados não recebem certificação PIT.
4. Backup SQLite com WAL ativo, hash, integridade e restauração em destino novo.
   Falhas preservam um marcador de incompletude, sem sobrescrever dados existentes.
5. Regressões: processos concorrentes, leitores durante escrita, interrupção
   abrupta de transação, destino ocupado, backup corrompido e erro de armazenamento
   simulado. Não extrapolar esses testes para falha física de energia/disco.
6. Carga sintética determinística de 250 mil registros; medir tempo e RSS,
   sem escolher critérios de lucro nem ajustar estratégias. Carga real COTAHIST
   2026, replay e restauração devem reconciliar com os 55.986 registros R7.
7. CI nas duas versões: suíte integral, arquivos históricos, lint/tipos do pacote,
   cobertura sem reduzir piso 77%, builds idênticos e CLI de wheel fora do checkout.
8. Evidência R7 permanece ancorada no commit original; documentos/recibos históricos
   continuam verificados no disco. Evidência R8 vincula os novos arquivos por hash.
9. Publicar runbook, resultados, limites operacionais, SHA/CI e entrega reproduzível.

Não são critérios de infraestrutura: preencher eventos sem fonte, presumir custos
XP, validar lucro com testes de software ou observar antecipadamente 2027. Os
75 achados, 50 líquidos, 22 datas e 28 eventos societários R7 permanecem rastreados.

Referências técnicas: [SQLite Online Backup](https://www.sqlite.org/backup.html),
[WAL](https://www.sqlite.org/wal.html),
[API Python 3.13](https://docs.python.org/3.13/library/sqlite3.html#sqlite3.Connection.backup).
