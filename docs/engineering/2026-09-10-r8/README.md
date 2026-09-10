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
[CI224 aprovada](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34522721727)
no código `c7f61ed5befda706da4c9a9cd53ff12b61a1d89b`: 891 testes ativos,
17 arquivados e 63 subtests em cada Python. Cobertura geral: 80% no 3.13 e 79%
no 3.14; armazenamento operacional 92%, CLI 89%. Não representa cobertura total.
Lint/tipos, scanner, integridade histórica, builds idênticos e ciclo do wheel
instalado passaram nas duas versões. Recibo: [ci224.json](evidence/ci224.json).
O [PR79](https://github.com/leonardosovienski/stocks-predictor/pull/79) registra
o SHA final, seu check e a integração; alterações documentais posteriores são
novamente verificadas por CI antes da integração.

Na conferência de main/CI226, a action de segredos informou zero commits examinados
após o merge: seu filtro `--no-merges --first-parent` não constitui uma varredura
independente da árvore integrada. O PR havia sido examinado. O complemento
[PR80](https://github.com/leonardosovienski/stocks-predictor/pull/80) mantém essa
checagem histórica e adiciona `git archive HEAD` + Gitleaks sobre todos os arquivos
versionados, com população não vazia e SARIF retido. O PR80 registra os checks e
SHA da integração final desta correção. A versão existente do scanner é fixada em
8.24.3 e comentários automáticos são desativados. Referência da action:
[código/documentação fixados](https://github.com/gitleaks/gitleaks-action/tree/e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e).

| Validação | Carga | Replay | Backup | Restauração | Pico RSS da carga |
|---|---:|---:|---:|---:|---:|
| Windows auxiliar, 250.000 sintéticos | 9,31 s | 8,75 s | 9,30 s | 4,28 s | 29,76 MiB |
| Windows auxiliar, 55.986 reais | 43,20 s | 29,83 s | 1,00 s | 0,88 s | 29,67 MiB |
| Linux CI/Python 3.14, 250.000 sintéticos | 3,56 s | 3,95 s | 2,33 s | 2,27 s | 30,64 MiB |

São medições pontuais de processos novos, não promessa de SLA. As duas cargas
locais foram executadas simultaneamente e disputaram recursos do host. ZIP
sintético usa compressão da plataforma: conteúdo lógico determinístico, bytes
comprimidos potencialmente distintos entre versões de zlib. Cada recibo guarda
o hash dos bytes realmente usados. Os 12 bancos históricos mantiveram seus hashes.

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
