# Prompt vigente de continuidade — 09/09/2026

Continue stocks-predictor na raiz local única `C:\STOCKS`.
Use `C:\STOCKS\stocks-predictor`, main; confira HEAD, remoto, worktrees e
alterações antes de agir. Preserve commits posteriores à referência H21
`4a85d4317657ac5ddaffcacf889b6341cf9c4b0a`, PR69.
Não fazer reset, reclonar sem necessidade ou recriar branches históricas.

Leia `AGENTS.md`, início do `HANDOFF.md`, `STOCKS_CURRENT_STATE.md`,
`docs/DOCUMENTATION_INDEX.md` e o mandato integral
`docs/continuation/MANDATO_20260909.md`. Para código, ler os designs e protocolos
pertinentes, preservando o significado dos congelamentos.

Todos os arquivos locais novos ficam em `C:\STOCKS`: pesquisa/logs/temporários
em `work`; entregas em `outputs`; prompt original em
`instructions\STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md`.
Use `C:\STOCKS\LOCALIZACAO_PROJETO.json` e
`docs/continuation/LOCAL_PATHS_20260909.json`. Caminhos antigos em recibos e
`PATHS.json` são proveniência; não reescrever bytes para trocar caminhos.

H21 avaliou uma compra/venda BOVA11, 2018-01-02 a 2026-04-01, com quatro
especificações e oito valorizações de R$5/10 mil. São cenários, não patrimônio
informado. Ganhos condicionais positivos e drawdown máximo 43–46% não validam
lucro executável/futuro. Faltam eventos do ETF e despesas reais documentadas.
H20 permanece inconclusiva e estacionada para reconstrução ampla.
Não há comparação líquida H21–H20 ou holdout intacto demonstrados.

A revisão `docs/research/2026-09-09-h21-source-closure.md` já atualizou a fonte
para 2.159 preços até 08/09, com sobreposição conferida e sem recalcular H21.
Consulte seus JSON de entradas operacionais e inventário: XP é a preferência,
Rico alternativa condicional; conta, capital, horizonte e tolerância são desconhecidos.
Regulamentos/demonstrações apoiam inventário parcial; não declarar ausência integral
de eventos nem incorporação executada pela presença do assunto num aviso.
Próximo trabalho: fechar a cobertura histórica restante de eventos/direitos e
custos efetivos. As aquisições desta rodada estão encerradas, com duas revisões;
não repetir coleta ou criar variantes sem novo orçamento/procedimento.
O plano `docs/research/2026-09-09-h21-forward-plan.json` já está registrado,
para os pregões especificados de 10/09/2026–10/09/2027.
Zero observações futuras e nenhum monitor. Nova rodada exige orçamento finito
e critérios antes de observar novos desempenhos.

A CI184 do commit integrado H21 passou 782 testes regulares, Ruff/Pyright,
build/gitleaks e wheel externa; Linux/Python 3.13.15/Core 3.2.0, cobertura 78%.
Os 17 testes arquivados não foram executados. Para outro SHA, verificar sua CI.
A finalização H21 excedeu o prazo de 17:38 UTC; não foi extensão prospectiva
ou nova variante. Recibos entregues estão em `C:\STOCKS\outputs`.

Windows atual: Python 3.12.14 auxiliar do Codex. Não criar venv, instalar
Core/dependências ou alterar runtime/EDR. Suíte canônica em Linux CI.
Só nove COTAHIST foram recuperados; bancos preservados no arquivo de migração.
Não afirmar restauração completa ou importar bancos por padrão.

Trabalhe sozinho. Autonomia cobre pesquisa, correções, commits/push/integração
verificados, conforme mandato; não cobre ordens, corretoras, capital, novas
cobranças, agentes ou automações recorrentes. Preserve fontes, bancos, ledgers,
quarentenas e H1–H20/H21. Não executar scripts históricos automaticamente.
Entregue em português e separe histórico, simulação, observação futura e
execução real. Não converter CI verde ou retorno passado em promessa.
