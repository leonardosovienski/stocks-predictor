# Infraestrutura operacional R8 — 10/09/2026

Implementação do [plano registrado antes dos testes](PLAN.md), com
[runbook operacional](RUNBOOK.md) e [evidências atuais](evidence.json).

A entrada `python -m stocks_predictor` integra inicialização, fontes versionadas
com hash obrigatório, inspeção por fonte, snapshot SQLite, restauração em destino
novo, perfil pessoal e evidência datada. `python main.py ops` usa a mesma entrada.
O armazenamento gerido não substitui bancos históricos nem mistura versões em
backtests. O escopo é pesquisa em lote em disco local, um host, um escritor SQLite.

Testes de processo verificam concorrência, replay simultâneo, leitores durante
transação, morte abrupta de escritor e recuperação. Backup é confrontado com WAL
ativo e dados não confirmados; corrupção, timeout, destino ocupado e erro simulado
de gravação não publicam artefato pronto. A suíte também verifica a cadeia real
de 15 migrações Core em banco isolado e a recusa de acesso legado ao novo banco.

Os recibos de carga contêm os hashes de todos os módulos realmente usados. A carga
real reconcilia com os 55.986 preços, 408 tickers e hash de linhas da R7. O teste
de capacidade usa 250 mil registros sintéticos. São validações de software e
de volume finito; resultados de tempo/RSS dependem da máquina e concorrência.

O verificador R7 agora lê evidências de código no commit original
`c259ff64771a6c560ddb4aadac6bf81301c3066a`, mantendo documentos e recibos históricos
verificados no disco. O verificador R8 confere separadamente todo o código atual
do pacote, testes e ferramentas, workflow, lock, identidade real e ciclo de recuperação.
Isso permite evolução sem atribuir testes antigos ao código novo.

Falhas encontradas durante esta rodada ficam em `evidence/failures.json`.
A aprovação de CI e a entrega são registradas depois dos checks do commit final.
Estado nesta edição: implementação e validações locais executadas; CI em andamento.

Permanecem fora de uma conclusão de infraestrutura universal: infraestrutura
distribuída, negociação ao vivo, hardware/energia e recuperação de perda completa
do host sem cópia externa provisionada. Nenhum desses ambientes está implantado
neste projeto. O runbook declara RPO/RTO e condições de retomada.

O [inventário R7 de 75 itens](../../audit/2026-09-10-r7/CONSOLIDADO.md) permanece
preservado. A R8 resolve a entrada operacional, os testes de falha/concorrência,
backup/restauração e a separação temporal de atestados de código. Não fecha I10–I14
ou I16: seguem 50 líquidos, 22 datas, 28 eventos societários, custos/prazo pessoais
desconhecidos e ausência de observação prospectiva concluída. Capital confirmado
R$5.000; capital habilitado não; lucro integral/futuro não certificado.
