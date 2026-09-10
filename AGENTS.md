## Pausa e encerramento revisado — 10/09/2026 UTC

[Estado final, evidências e retomada](docs/continuation/2026-09-10-closure/README.md).
Infraestrutura de pesquisa em lote validada; CI230 e recibos finais preservados.
O objetivo econômico permanece aberto. Lucro não validado; nenhuma operação financeira ativa.
As seções anteriores abaixo conservam seu contexto e suas datas.

## Operação R8 — 10/09/2026 UTC

[Relatório operacional](docs/engineering/2026-09-10-r8/README.md) e
[runbook](docs/engineering/2026-09-10-r8/RUNBOOK.md).
Entrada instalada: `python -m stocks_predictor`; no checkout: `python main.py ops`.
Banco gerido separado, ingestão por hash, inspeção por versão, backup e restauração.
O escopo é pesquisa local em lote; fontes/custos/observação futura ainda pendentes.
R7 mantém o inventário econômico e os recibos históricos. Os blocos abaixo são datados.

# Stocks — instruções vigentes para implementação

## Execução vigente R7 — 10/09/2026 UTC

Ler [relatório R7](docs/audit/2026-09-10-r7/README.md),
[registro atual](docs/audit/2026-09-10-r7/current.json) e [reprodução](docs/audit/2026-09-10-r7/REPRODUCTION.md).
Capital confirmado: R$5.000; custos, prazo e residência fiscal ainda desconhecidos.
O registro preserva todos os achados e distingue engenharia implementada de
fontes e observações ainda ausentes. I15/arquivos e CHAT-01/PR75 resolvidos.
I10–I14/I16 e lucro integral continuam abertos. Executar o verificador do registro
antes de atualizar estados. Novas APIs de origem/tempo são opt-in, sem migrar os
bancos legados. Os blocos datados abaixo conservam contexto das rodadas anteriores.

## Correções de dados R6 — 10/09/2026 UTC

[R6](docs/research/2026-09-10-r6/README.md) recuperou os cinco objetos ausentes:
verificador original com 1.448/1.448 arquivos aprovados. I15 resolvido quanto aos
arquivos; o comparador numérico estrito conserva uma diferença de float de 2,22e-16.
Fonte BOVA atualizada até 09/09, sem mudar o corte R5. Revisão 15: 22 datas e 50
líquidos pendentes após dois pagamentos B3 reconciliados; disponibilidade histórica
continua sem certificação ampla. Usar o manifesto R6 e preservar revisões 13/14.
As demais pendências I10–I14/I16 e o objetivo econômico continuam abertos.

Atualizado em 10/09/2026 UTC após a auditoria integral AUDIT-R3.

## Pesquisa econômica R5 — 10/09/2026 UTC

O usuário reabriu a pesquisa em busca de lucro validado, com liberdade sobre hipóteses
e arquitetura. [R5/H22](docs/research/2026-09-10-r5/README.md) executou uma regra mensal
de dez meses, registrada antes de medir, e uma alternativa de comprar e manter.
24 avaliações: 22 calculadas/reconciliadas e duas inviáveis; H22 rejeitada, sem
incremento positivo nos 11 pares calculáveis. Ganho nominal da alternativa simples
permanece condicional a eventos/custos. Lucro integral ou futuro não demonstrado.
Demonstrações2024 e AGO2025 recuperadas; fontes/livros anteriores preservados.
[PR76](https://github.com/leonardosovienski/stocks-predictor/pull/76) contém a integração
com testes e checks por SHA. O objetivo econômico permanece não atingido; as
restrições antigas de fila/coleta não substituem a nova autorização do usuário.
Não transformar busca repetida na mesma história em validação futura.

---

## Engenharia R4 posterior à auditoria

O pedido seguinte foi corrigir erros e melhorar infraestrutura/desempenho.
Ler o [relatório R4](docs/engineering/2026-09-10-r4/README.md) e
[PR75](https://github.com/leonardosovienski/stocks-predictor/pull/75) para os checks
e integração desta rodada. A auditoria R3 permanece um registro datado.
Ingestão agora informa inserções efetivas, rejeita conteúdo divergente sob a mesma
identidade e preserva transações do chamador. Não adaptar fontes para contornar isso.
`python main.py doctor` funciona sem Core e sem abrir banco por padrão;
`--check` retorna 1 quando o ambiente não atende ao contrato de metadados.
A CI verifica Python 3.13/3.14, lock e cobertura mínima de 77%; não remover esses
controles para acomodar falhas. Diagnóstico de ambiente não certifica operação.

## Continuidade após auditoria integral

O usuário preparou e revisou o
[mandato completo de auditoria](docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md).
Foi executado com revisão das 24 frentes, correções e validação.
Ler o [relatório canônico](docs/audit/2026-09-10-integral/README.md),
[registro único](docs/audit/2026-09-10-integral/registry.json) e
[reprodução](research/session-20260910/integral/README.md).
H21 continua justificável como validação simples e finita; lucro executável/futuro
não foi demonstrado. H20 amplo continua estacionado; na R3 cinco arquivos impediam seu
certificado integral; foram recuperados na R6. A falta de caixa integral permanece.
Não reabrir busca de estratégias ou coleta ilimitada por inércia. Usar I10–I16 para
condições concretas de retomada; I01–I09 foram resolvidos no escopo declarado.
CI197 aprovou 815 testes no domínio consolidado; PR74 registra integração e último check.
Protocolos e resultados históricos mantêm seus bytes; funções legacy existem apenas
para reproduzir sua semântica, sem certificado PIT geral ou forward real.

## Mandato e leitura

O [mandato de 09/09/2026](docs/continuation/MANDATO_20260909.md) autoriza pesquisa,
implementação, commits, push e integração, com orçamento finito e evidência preservada.
Instruções atuais do usuário e regras superiores do ambiente prevalecem.
Documentos antigos não impõem novamente arquitetura ou fila de trabalho superadas.
O significado dos protocolos congelados permanece intacto.

Ler este arquivo, [README](README.md), início do [HANDOFF](HANDOFF.md),
[estado atual](STOCKS_CURRENT_STATE.md) e [índice documental](docs/DOCUMENTATION_INDEX.md).
Antes de alterar código do domínio, ler integralmente [DESIGN](docs/DESIGN.md)
e os protocolos pertinentes; suas descrições antigas de runtime/caminhos são históricas.

## Raiz e ambiente

- Todos os arquivos locais do projeto ficam em `C:\STOCKS`.
- Checkout: `C:\STOCKS\stocks-predictor`, branch `main`. Conferir HEAD, remoto,
  worktrees e alterações antes de agir; nunca impor um SHA antigo por reset.
- Pesquisa, fontes novas, logs e temporários: `C:\STOCKS\work`;
  entregas: `C:\STOCKS\outputs`. Não usar a pasta gerada de Documents/Codex.
- Mapa: `C:\STOCKS\LOCALIZACAO_PROJETO.json` e
  [LOCAL_PATHS_20260909.json](docs/continuation/LOCAL_PATHS_20260909.json).
  `PATHS.json` e recibos antigos preservam proveniência, não destinos atuais.
- Produção: Python `>=3.13,<3.15`, PyYAML `>=6,<7`, predictor-core `>=3.2,<4`.
  Lock/CI usam wheel oficial Core 3.2.0. `vendor/` é histórico, fora do runtime.
- No Windows atual, não criar venv, instalar Core/dependências ou alterar runtime
  global/EDR. Python 3.12.14 fornecido pelo Codex serve a auxiliares stdlib compatíveis.
  Python 3.13/Core/pytest de produção não foram disponibilizados localmente.
- A CI Linux permite instalar dependências declaradas e executar os checks.
  Seguir `.github/workflows/ci.yml`; suas instalações não se aplicam a este Windows.

## Integridade e pesquisa

Trabalhar sozinho, sem agentes auxiliares. Não enviar ordens, autenticar corretoras,
movimentar capital, contratar serviços ou criar automações recorrentes.
R$5 mil é capital confirmado nesta conversa; R$10 mil permanece cenário histórico.

Preservar fontes originais, bancos, ledgers, quarentenas, trabalho do usuário e
protocolos H1–H20/H21. Não editar bytes históricos para corrigir caminhos.
Migrações de banco e registros de observação são append-only. Nova hipótese,
reabertura ou variante exige procedimento próprio antes de observar desempenho.
Não descartar tentativas negativas nem contar reprodução idêntica como evidência nova.

Preservar a política histórica de informação conhecida: H7/H9/H10/H12/H13 usam
o embargo estimado com que foram julgadas; H17/H18/H19 usam a data CVM observada
quando o chamador habilita `use_known_at`. Não migrar silenciosamente hipóteses
antigas para outra política de `known_at`, nem reemitir lacres por conveniência.

H21 é inconclusiva para lucro líquido executável e candidata a validação adicional.
O [complemento R2](docs/research/2026-09-09-data-completion-r2.md) recuperou os
12 bancos e fontes 13/14; sua integridade não é completude econômica. Usar
`C:\STOCKS\data\CATALOG.json` e a [reprodução](research/session-20260909/data_completion/README.md).
R1 atualizou preços BOVA11 até 08/09; R2 ampliou demonstrações e tarifas históricas.
Rodadas de coleta encerradas; consultar os inventários antes de novo orçamento.
Preferência: XP;
não inferir elegibilidade, capital, horizonte ou limite de perda. Consultar
as entradas operacionais e o inventário antes de repetir aquisições.
A auditoria indicada acima já foi executada; as condições de retomada estão em
I10–I16. O plano prospectivo H21 está registrado, sem execução. H20 amplo
permanece estacionado. A rodada R4 trata da engenharia posterior à auditoria.
Não ativar comandos legados de ingestão, backtest ou paper automaticamente.

## Engenharia e validação

Usar UTF-8 explicitamente no I/O de texto. Justificar dependências novas por
necessidade, licença e compatibilidade; respeitar as autorizações vigentes.
Não relaxar checks, lacres ou limites de integridade para obter aprovação.

Validar proporcionalmente à mudança; bugs materiais exigem regressão que detecte
o comportamento anterior. A suíte canônica usa `tests/`; testes de sessões
arquivadas são separados. Atestados do Core exigem árvore Git limpa:
não contornar a recusa com flags ou alterações de teste.

Para H21 local, seguir [a reprodução stdlib](research/session-20260909/h21/README.md).
Para a suíte completa, usar Linux CI. O smoke de wheel deve ocorrer realmente
fora do checkout, verificando a origem dos imports. Registrar SHA, ambiente e
checks executados; CI verde não prova lucro.
