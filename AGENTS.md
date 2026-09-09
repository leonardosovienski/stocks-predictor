# Stocks — instruções vigentes para implementação

Atualizado em 09/09/2026 após H21, centralização local e complemento de dados R2.

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
R$5 mil e R$10 mil são cenários, não patrimônio confirmado.

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
O próximo passo é fechar a cobertura restante de eventos e despesas/execução. O plano futuro
já está registrado; não está rodando. H20 está estacionada para reconstrução ampla.
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
