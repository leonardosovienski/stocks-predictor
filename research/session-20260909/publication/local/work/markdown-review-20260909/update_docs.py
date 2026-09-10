from pathlib import Path
import json, hashlib
ROOT=Path(r"C:\STOCKS")
REPO=ROOT/"stocks-predictor"
WORK=ROOT/"work/markdown-review-20260909"
changed=[]
def read(rel):
    return (REPO/rel).read_text(encoding="utf-8")
def write(path, text):
    path=Path(path)
    if path.exists():
        raw=path.read_bytes()
        target=WORK/"originals"/(hashlib.sha256(raw).hexdigest()+".snapshot")
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists(): target.write_bytes(raw)
    path.write_text(text.rstrip()+"\n",encoding="utf-8",newline="\n")
    changed.append(str(path))
def prepend(rel, text):
    write(REPO/rel,text.rstrip()+"\n\n---\n\n"+read(rel))
def replace(text,old,new):
    if text.count(old)!=1: raise ValueError(f"Expected one match: {old[:80]}, got {text.count(old)}")
    return text.replace(old,new,1)

write(REPO/"AGENTS.md",r"""# Stocks — instruções vigentes para implementação

Atualizado em 09/09/2026 após a rodada H21 e a centralização local.

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

H21 é inconclusiva para lucro líquido executável e candidata a validação adicional.
O próximo passo é inventário de eventos do ETF e despesas/execução. O plano futuro
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
""")

write(REPO/"CLAUDE.md",r"""# Stocks — instruções compartilhadas

As instruções vigentes estão em [AGENTS.md](AGENTS.md). Leia esse arquivo antes
de trabalhar; este ponto de entrada usa a mesma fonte para evitar divergências.

A raiz local é `C:\STOCKS`, com código em `C:\STOCKS\stocks-predictor`.
Consulte [estado atual](STOCKS_CURRENT_STATE.md) e início do [HANDOFF](HANDOFF.md).

A antiga descrição de Python 3.14/3.13 no outro computador e seus comandos
de instalação não se aplicam a este Windows. Não criar venv nem instalar Core.
Python do Codex é auxiliar; a suíte canônica é executada na CI Linux.
H17–H19 já tiveram observações históricas; não são amostras intactas.
""")

write(ROOT/"COMECE_AQUI.md",r"""# Stocks — localização e continuidade atuais

Atualizado em 09/09/2026. A raiz local única é **C:\STOCKS**.

| Conteúdo | Local |
|---|---|
| Código, main e histórico Git | `C:\STOCKS\stocks-predictor` |
| Pesquisa, fontes novas, logs e temporários | `C:\STOCKS\work` |
| Relatórios e recibos | `C:\STOCKS\outputs` |
| Prompt original | `C:\STOCKS\instructions\STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md` |
| Mapa local e movimentações verificadas | `C:\STOCKS\LOCALIZACAO_PROJETO.json` |
| Arquivos originais e bundle offline | Esta raiz e `FONTES_WEB_ORIGINAIS` |

Comece por [AGENTS](AGENTS.md), [README](stocks-predictor/README.md),
[estado atual](stocks-predictor/STOCKS_CURRENT_STATE.md) e
[índice documental](stocks-predictor/docs/DOCUMENTATION_INDEX.md).

O ZIP de dados já foi reunido e verificado. Nove COTAHIST foram recuperados
seletivamente; os bancos continuam preservados no arquivo de migração.
Não juntar novamente, clonar outro checkout ou restaurar tudo por padrão.

A referência integrada da H21 é `4a85d4317657ac5ddaffcacf889b6341cf9c4b0a`,
PR69. Revisões documentais posteriores podem avançar o SHA; conferir HEAD.
O [relatório entregue](outputs/RELATORIO_STOCKS_H21.md) e seus hashes permanecem
intactos. Complementos posteriores estão no estado atual do repositório.
Lucro executável integral e lucro futuro não foram validados.

Guias em `FONTES_WEB_ORIGINAIS` descrevem a exportação do outro computador.
Seus caminhos em Superleo13, E: e `C:\Stocks\codigo` são proveniência histórica.
As sete movimentações verificadas por SHA-256 estão em
`work\centralizacao-20260909\movimentacoes.json`.

Este Windows não recebeu instalações Python/Core. Usar os auxiliares stdlib
disponíveis e a CI Linux conforme [AGENTS do código](stocks-predictor/AGENTS.md).
Nenhum monitor, paper recorrente ou operação real está ativo.
""")

current=r"""## Estado vigente após a centralização — 09/09/2026

Raiz única: `C:\STOCKS`; checkout: `C:\STOCKS\stocks-predictor`, main.
Entregas: `C:\STOCKS\outputs`; pesquisa/logs: `C:\STOCKS\work`; prompt original:
`C:\STOCKS\instructions\STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md`.
Seis entregas e o prompt foram movidos com SHA-256 conferido; a pasta anterior
da tarefa ficou sem arquivos do projeto. Mapas: `C:\STOCKS\LOCALIZACAO_PROJETO.json`
e [LOCAL_PATHS_20260909.json](docs/continuation/LOCAL_PATHS_20260909.json).

A rodada H21 foi integrada pelo [PR69](https://github.com/leonardosovienski/stocks-predictor/pull/69),
commit `4a85d4317657ac5ddaffcacf889b6341cf9c4b0a`.
A [CI184 desse SHA](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34386092297)
passou 782 testes regulares, Ruff, Pyright, build, gitleaks e wheel fora do checkout;
Linux, Python 3.13.15/Core 3.2.0, cobertura 78%. Os 17 testes arquivados não foram
executados. Revisões documentais posteriores não são nova medição econômica.

Somente nove COTAHIST foram recuperados da migração; bancos não foram abertos
ou integralmente restaurados. Python auxiliar local: 3.12.14; produção
3.13/Core/pytest indisponível localmente. Nenhuma instalação Windows foi feita.

H21: uma história exploratória BOVA11 de 2018-01-02 a 2026-04-01,
quatro especificações e oito valorizações de capital, com 2.050 cotações.
Ganho condicional R$5.515,48–5.618,39 no cenário R$5 mil e
R$11.950,19–12.173,17 no cenário R$10 mil; drawdown máximo 43,46–46,31%.
Custos/imposto modelados não resolvem despesas reais e inventário de eventos
do ETF. Lucro executável integral e previsão permanecem desconhecidos (`null`).
H21 é candidata a validação adicional; reconstrução ampla H20 estacionada.
Não há comparação líquida H21–H20 nem holdout intacto demonstrados.
57/59 são mínimos administrativos, não provas independentes.

O [plano prospectivo](docs/research/2026-09-09-h21-forward-plan.json) já está
registrado, para o primeiro pregão a partir de 10/09/2026 até o primeiro a partir
de 10/09/2027. Zero observações futuras e nenhum processo ativo.
Próximo trabalho: inventariar eventos do ETF e direitos após a venda, apurar
despesas/execução, reconciliar sem tuning e seguir o plano quando houver dados.
O pré-registro do plano não está pendente.

O experimento terminou às 16:50:16 UTC. A finalização excedeu o prazo registrado
de 17:38 UTC e foi conferida após 18:02 UTC; atraso declarado, sem novas variantes.
Recibo: `C:\STOCKS\outputs\ENTREGA_STOCKS_H21.json`.

Os blocos abaixo são registros datados. “Atual”, “nunca rodou”, contagens e
caminhos externos neles se referem à respectiva versão.
[Índice documental](docs/DOCUMENTATION_INDEX.md): orientação vigente e acervo."""
prepend("STOCKS_CURRENT_STATE.md",current)

prepend("HANDOFF.md",r"""## Revisão dos Markdown e raiz única — 09/09/2026

Inventário inicial: 94 Markdown, incluindo documentos locais fora do Git.
Corrigidas divergências de AGENTS/CLAUDE, README, continuidade e migração.
Relatórios, fontes originais e documentos congelados permanecem preservados.
Classificação: [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md).

Base H21 integrada: `4a85d4317657ac5ddaffcacf889b6341cf9c4b0a`, PR69, CI184:
782 testes regulares, Linux/Python 3.13.15/Core 3.2.0, 78% cobertura,
Ruff/Pyright/build/gitleaks e wheel externa aprovados. Esta revisão é documental;
não altera código, parâmetros, fontes, bancos, trials ou resultados.
Recibo e SHA posteriores: `C:\STOCKS\work\markdown-review-20260909`.

Código: `C:\STOCKS\stocks-predictor`; relatórios: `C:\STOCKS\outputs`;
pesquisa/logs: `C:\STOCKS\work`; prompt original em `instructions` da raiz.
A centralização conferiu sete arquivos por hash e removeu as origens externas.
Mapa atual: `C:\STOCKS\LOCALIZACAO_PROJETO.json`; `PATHS.json` é histórico.

H21 continua inconclusiva para lucro executável; H20 estacionada para
reconstrução ampla. O plano prospectivo já existe, sem execução. Próximo passo:
eventos do ETF, custos reais e reconciliação. A finalização H21 excedeu
17:38 UTC; o recibo registra o atraso, sem novas variantes.
As entradas seguintes preservam o histórico de cada data.""")

write(REPO/"docs/continuation/PROMPT_NOVO_CHAT.md",r"""# Prompt vigente de continuidade — 09/09/2026

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

Próximo trabalho: completar eventos BOVA11 e direitos/obrigações após a venda,
apurar despesas/execução e reconciliar mantendo parâmetros.
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
""")

prepend("docs/continuation/SESSION_CONTEXT.md",r"""# Contexto vigente e histórico — 09/09/2026

Use [PROMPT_NOVO_CHAT](PROMPT_NOVO_CHAT.md), [mandato](MANDATO_20260909.md)
e [estado atual](../../STOCKS_CURRENT_STATE.md).
Raiz `C:\STOCKS`; código em `C:\STOCKS\stocks-predictor`, main;
entregas em `C:\STOCKS\outputs`. [Mapa local](LOCAL_PATHS_20260909.json).

O texto de 07–08/09 abaixo é histórico. Capital informado, branch fix ativa,
raízes em Superleo13, dependências locais e ausência de push ali descritos
não são fatos deste computador. R$5/10 mil são cenários. Base H21 integrada:
`4a85d43`, 782 testes regulares na CI184. Somente nove COTAHIST recuperados;
bancos não restaurados integralmente. H21 inconclusiva para lucro executável,
com plano prospectivo já registrado, sem execução.""")

prepend("docs/continuation/MIGRACAO_MAIN.md",r"""# Migração neste computador — 09/09/2026

Raiz `C:\STOCKS`; código em `C:\STOCKS\stocks-predictor`, main.
ZIP já reunido e hashes conferidos; nove COTAHIST recuperados seletivamente.
Bancos permanecem no arquivo preservado. Não houve restauração integral ou
instalação de bibliotecas de produção aqui. Use
[mapa local](LOCAL_PATHS_20260909.json) e [estado](../../STOCKS_CURRENT_STATE.md).

O guia abaixo é o registro da exportação de 08/09/2026. Os 777 testes, 25 bancos,
`E:\...`, `C:\Stocks\codigo`, `DEPENDENCIAS` e instalações pertencem ao computador
anterior. Não reaplicar como roteiro atual, recriar checkout ou trocar caminhos
em fontes/recibos originais. A cópia do guia em FONTES_WEB_ORIGINAIS é imutável.""")

prepend("docs/RUNBOOK_H18.md",r"""# Runbook histórico H18/H19 — contexto em 09/09/2026

O roteiro abaixo descreve ambiente e medições de 04–06/09/2026.
H17–H19 tiveram observações posteriores; “nunca rodaram” ou “sem execução”
são afirmações daquela data. Caminhos, instalações e ordem de rodadas abaixo
não são instruções atuais.

Retome por [AGENTS](../AGENTS.md), [estado atual](../STOCKS_CURRENT_STATE.md)
e [H21](../research/session-20260909/h21/README.md).
Raiz `C:\STOCKS`; não criar venv ou instalar Core neste Windows.
Este runbook não autoriza reabrir H18/H19 ou escrever nos bancos.""")

prepend("docs/AGENT_CHARTER.md",r"""# Charter histórico — orientação vigente em 09/09/2026

O mandato operacional é [MANDATO_20260909](continuation/MANDATO_20260909.md),
com [AGENTS](../AGENTS.md) e [estado atual](../STOCKS_CURRENT_STATE.md).
O charter abaixo é registro histórico, não prompt ativo.

Estão superadas suas prioridades de ligar paper, impedir novas hipóteses,
exigir capital declarado antes de cenários, usar caminhos do outro computador
e tratar H17/H18/H19 como nunca observadas. Pesquisa nova é autorizada com
protocolo próprio, orçamento finito e fontes preservadas. O padrão é uma hipótese
principal e no máximo uma alternativa ativa, conforme o mandato atual.

R$5/10 mil são cenários; H21 é inconclusiva para lucro executável e H20 fica
estacionada para reconstrução ampla. Plano futuro H21 registrado, não ativo.
Anualização histórica usa campo próprio; `expected_annual_profit_brl` é `null`.
Nada autoriza operação financeira, cobranças, agentes ou automações recorrentes.
Contagens e conclusões abaixo pertencem à respectiva versão histórica.""")

text=read("README.md")
text=text.split("\n",1)[1]
start=text.index("Projeto de pesquisa econômica")
end=text.index("As linhas H1")
text=text[:start]+"""Projeto de pesquisa econômica de ações da B3. A linha ativa de validação é
**H21 — exposição simples via BOVA11**, medida em uma história exploratória
com resultado condicional. Eventos do ETF e despesas reais ainda impedem
concluir lucro líquido executável ou prever lucro futuro.
[Resultados](docs/research/2026-09-09-h21-results.md) e
[reprodução H21](research/session-20260909/h21/README.md).

H20 tem implementação de retenção, bandas, proventos e reserva de impostos;
sua reconstrução ampla está estacionada, com incremento inconclusivo.
H19 e avaliações anteriores preservam seus protocolos e limites.
Não há autorização para operar capital ou ativar o paper legado.

"""+text[end:]
text=replace(text,"## Estado técnico",r"""## Localização e documentação

Raiz local única: `C:\STOCKS`; código em `stocks-predictor`,
pesquisa/logs em `work`, entregas em `outputs`, prompt original em `instructions`.
ZIP de migração reunido; só nove COTAHIST recuperados, sem restauração integral
dos bancos. [Mapa](docs/continuation/LOCAL_PATHS_20260909.json) e
[índice completo dos Markdown](docs/DOCUMENTATION_INDEX.md).

H21 integrada pelo [PR69](https://github.com/leonardosovienski/stocks-predictor/pull/69),
SHA `4a85d4317657ac5ddaffcacf889b6341cf9c4b0a`.
A [CI184 desse SHA](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34386092297)
passou 782 testes regulares, cobertura 78%; 17 testes arquivados não executados.
Revisões documentais posteriores não são novos experimentos.
Relatórios e caminhos antigos preservam proveniência datada.

## Estado técnico""")
text=replace(text,"CI: Python 3.13, Ruff, Pyright nos módulos RJ/H19 declarados, pytest+coverage, build/wheel smoke e","CI: Python 3.13, Ruff, Pyright no escopo de `pyproject.toml` (inclui H20, fontes, H21 e economics), pytest+coverage, build/wheel smoke e")
text=replace(text,"```powershell\nuv sync --all-extras --python 3.13",r"""Os comandos `uv` desta seção são para Linux CI ou outro ambiente autorizado
com produção disponível. **Não executar instalações/venv no Windows atual.**
Aqui, Python 3.12.14 do Codex atende somente aos
[auxiliares stdlib H21](research/session-20260909/h21/README.md).
Python 3.13/Core/pytest não estão disponíveis localmente. Comandos RJ abaixo são
referência histórica; não iniciar automaticamente pesquisa ou ingestão.

```bash
uv sync --all-extras --python 3.13""")
text=text.replace("```powershell\nuv run","```bash\nuv run")
text=text.replace("não reproduzível contra o Core 3.0.0 atual","não reproduzível contra o Core 3.0.0 da época do fechamento")
for pr in (18,19,20,21,22):
    text=text.replace(f"(../../pull/{pr})",f"(https://github.com/leonardosovienski/stocks-predictor/pull/{pr})")
text=text.replace("git log origin/main --oneline -10   # deve mostrar os merges dos PRs #18-#22","git log origin/main --oneline -10   # mostra os commits mais recentes")
text=text.replace("uv run pytest -q                    # suíte completa, incluindo os testes novos do congelamento\n","")
text=replace(text,"""A suíte completa passa 100% sobre o `origin/main`. **A contagem canônica é a da
última execução do CI na `main`, não um número escrito aqui:** eram 252 testes quando
esta linha foi escrita e são 374 em 2026-09-06. Número de teste em README envelhece a
cada PR; o CI não.""","""A validação confirmada da base H21 está vinculada ao SHA e à CI184 acima.
Para qualquer HEAD posterior, conferir a execução correspondente antes de declarar
a suíte aprovada. Contagens de versões antigas são histórico, não checks do HEAD.""")
write(REPO/"README.md",text)

prepend("docs/research/2026-09-09-h21-results.md",r"""## Atualização documental após a entrega — 09/09/2026

H21 integrada na main em `4a85d4317657ac5ddaffcacf889b6341cf9c4b0a`.
[CI184](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34386092297):
782 testes regulares aprovados, 78% cobertura, Ruff/Pyright/build/gitleaks e
wheel fora do checkout. Linux/Python 3.13.15/Core 3.2.0; não são testes completos
deste Windows. Os 17 testes arquivados não foram executados.

Experimento encerrado às 16:50:16 UTC. O prazo de 17:38 UTC foi ultrapassado
na finalização, conferida após 18:02 UTC. Não houve extensão prospectiva ou
novos cenários. Abaixo permanece o prazo planejado; este complemento registra
o ocorrido. O plano `2026-09-09-h21-forward-plan.json` já está registrado,
sem observações futuras ou monitor; seu pré-registro não está pendente.

Entregas centralizadas em `C:\STOCKS\outputs`; pesquisa em `C:\STOCKS\work`.
Relatório entregue e recibo/hash original preservados sem reescrita.
Este complemento não altera resultados, parâmetros ou observações.""")

prepend("research/session-20260909/h21/README.md",r"""# Localização e validação da reprodução — 09/09/2026

Destinos locais sempre em `C:\STOCKS`. Fontes e primeira medição permanecem em
`C:\STOCKS\work\h21`; relatórios/recibos em `C:\STOCKS\outputs`, movidos com
SHA-256 conferido. O runtime Codex abaixo é ferramenta instalada, não conteúdo
a mover. Não gravar saídas na antiga pasta da tarefa.

[Estado atual](../../../STOCKS_CURRENT_STATE.md): CI184 aprovada do commit H21
`4a85d43` e plano prospectivo já registrado, sem execução.
Reprodução idêntica não é evidência nova. Usar destinos novos; preservar lacres.""")

paths=json.loads(read("docs/continuation/LOCAL_PATHS_20260909.json"))
paths.update({"local_project_root":r"C:\STOCKS","deliverables":r"C:\STOCKS\outputs",
"original_mandate_current_path":r"C:\STOCKS\instructions\STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md",
"local_location_registry":r"C:\STOCKS\LOCALIZACAO_PROJETO.json",
"relocation_receipt":r"C:\STOCKS\work\centralizacao-20260909\movimentacoes.json",
"path_policy":"All new local project files remain under C:\\STOCKS. Sealed historical paths remain provenance; installed Codex runtime and GitHub are environment/remote resources."})
write(REPO/"docs/continuation/LOCAL_PATHS_20260909.json",json.dumps(paths,ensure_ascii=False,indent=2))
(WORK/"changed.json").write_text(json.dumps(changed,indent=2),encoding="utf-8")
print(json.dumps({"changed":len(changed),"paths":changed},ensure_ascii=False))

