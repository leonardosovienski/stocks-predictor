# Stocks — instruções vigentes

Trabalhar sozinho, sem agentes auxiliares. O usuário autoriza correções, pesquisa
com orçamento finito, commits, push e integração validada. Instruções atuais do
usuário e regras superiores prevalecem; versões antigas não reabrem permissões.

## Leitura e objetivo

Ler [README](README.md), [HANDOFF](HANDOFF.md), [estado atual](STOCKS_CURRENT_STATE.md)
e [índice documental](docs/DOCUMENTATION_INDEX.md). O
[mandato integral](docs/continuation/PROMPT_AUDITORIA_INTEGRAL_20260909.md) e o
[mandato de pesquisa](docs/continuation/MANDATO_20260909.md) estão preservados.
Antes de alterar domínio, ler integralmente [DESIGN](docs/DESIGN.md) e os protocolos
pertinentes. A evolução do runtime não altera o significado dos congelamentos.

O objetivo é investigar lucro líquido executável; ele permanece não atingido.
A infraestrutura R8 está validada para pesquisa em lote, com
[runbook](docs/engineering/2026-09-10-r8/RUNBOOK.md) e
[encerramento](docs/continuation/2026-09-10-closure/README.md).
O [consolidado R7](docs/audit/2026-09-10-r7/CONSOLIDADO.md) guarda os achados;
I15/arquivos e omissão PR75 resolvidos, I10–I14/I16 ainda limitados.
Capital confirmado R$5.000; não inferir custos, prazo, residência fiscal ou perdas.
H22 rejeitada; H21 histórica condicional. Não transformar repetição de backtest
em validação independente nem antecipar a janela prospectiva fixada.

## Raiz e ambiente

- Raiz canônica: `C:\STOCKS`; checkout `C:\STOCKS\stocks-predictor`.
- Pesquisa, fontes novas, logs e temporários: `C:\STOCKS\work`;
  entregas: `C:\STOCKS\outputs`; bancos originais: `C:\STOCKS\data`.
- Não gravar conteúdo do projeto em Documents/Codex. Runtimes/caches internos
  do ambiente não precisam ser movidos. Não criar links para desviar conteúdo.
- Conferir Git, HEAD, remoto, branches, worktrees e alterações. Não impor um SHA
  antigo por reset, recriar branches antigas, fazer force-push ou apagar trabalho concorrente.
- Runtime: Python `>=3.13,<3.15`, PyYAML `>=6,<7`, Core `>=3.2,<4`.
  [pyproject.toml](pyproject.toml) e [uv.lock](uv.lock) são as fontes canônicas;
  o lock usa wheel oficial Core 3.2.0. Vendor é histórico, fora do runtime.
- Neste Windows, não criar venv, instalar Core/dependências, alterar Python global
  ou EDR. Python 3.12.14 fornecido pelo Codex é auxiliar stdlib. Suíte completa,
  dependências e builds são executados no Linux CI autorizado.

## Preservação e limites

Não enviar ordens, autenticar corretoras, movimentar capital, contratar serviços,
criar contas financeiras ou automações recorrentes. Não ativar comandos legados
de ingestão/backtest/paper automaticamente. Revisão por este assistente não é independente.

Preservar fontes originais, os 12 bancos, ledgers, quarentenas, resultados negativos,
recibos e protocolos H1–H20/H21. Migrações/observações são append-only. Não corrigir
caminhos dentro de evidências congeladas nem reemitir lacres para aceitar alteração.
H7/H9/H10/H12/H13 conservam o embargo estimado original; H17/H18/H19 usam a data CVM
observada somente quando `use_known_at` foi habilitado no procedimento original.

A [política de arquivos](docs/maintenance/2026-09-10-files/README.md) separa instruções
atuais, histórico e dados externos. Limpeza alcança apenas caches e configuração
redundante identificados, com registro; arquivo grande, antigo, repetido ou vazio
não é por isso descartável. `LOCALIZACAO_PROJETO.json` e mapas datados preservam a
migração; HEAD e estado atual vêm do Git e dos documentos de entrada.

## Verificação e integração

Usar UTF-8 explicitamente. Validar mudanças proporcionalmente, com regressão para
bugs materiais. Não reduzir gates, lacres, cobertura ou checks para obter aprovação.
Atestados/builds Core exigem checkout limpo; não contornar essa recusa.
Seguir [.github/workflows/ci.yml](.github/workflows/ci.yml): suíte ativa e arquivada,
lint, tipos, hashes, build repetido e wheel instalado realmente fora do checkout.
Conferir o SHA e todos os checks antes e depois do merge; CI verde não prova lucro.

Ao adicionar/remover Markdown, executar `python tools/check_project_files.py --write-index`
e revisar o índice. O checker exige arquivos/links versionados e preserva somente
exceções históricas exatas. Mudanças em código/CI exigem atualizar a evidência atual
R8, mantendo os recibos históricos e repetindo a validação afetada. Mudança no pacote
exige novos recibos de carga real/capacidade ligados ao código efetivamente executado.
