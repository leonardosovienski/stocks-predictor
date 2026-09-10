# Dados recuperados de Stocks

Comece por [CATALOG.json](CATALOG.json) e pelo
[relatório R2](../stocks-predictor/docs/research/2026-09-09-data-completion-r2.md).
O catálogo declara explicitamente quais dados estão disponíveis e quais condições
econômicas ainda não foram certificadas. `all_data_ready` permanece `false`.

- `recovery-r2/catalog.json`: nomes originais, hashes e integridade dos 12 bancos.
- `recovery-r2/objects`: bytes originais recuperados, identificados pelo SHA-256.
- `recovery-r2/bundles/source13`: fonte canônica 13, preservada.
- `recovery-r2/bundles/source14`: complemento original 14, preservado.
- `recovery-r2/source14-inputs`: composição separada da revisão 14, auditada.

Os objetos de banco não precisam de extensão `.db` para leitura SQLite. Abrir
somente em modo de leitura e não ativar ingestões/migrações sobre eles. O catálogo
separa o banco original do projeto, versões de pesquisa, reparos e fixtures.
Fonte íntegra não significa retorno total completo ou lucro executável aprovado.

Código e comandos de reprodução:
[README da recuperação](../stocks-predictor/research/session-20260909/data_completion/README.md).
Fontes públicas novas ficam em `C:\STOCKS\work\data-completion-r2-20260909`.
