# predictor-stocks — instruções para o implementador

## Mandato vigente de 09/09/2026

O usuário autorizou novas pesquisas e mudanças técnicas pelo mandato
`STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md`, executado em `C:\STOCKS`.
Priorizar validade da medição e decisão econômica; registrar hipóteses novas
antes de observar desempenho. As restrições antigas de arquitetura, ordem de
marcos e escopo não impedem esse trabalho. Não alterar protocolos/vereditos
congelados, assinar revisão humana, operar capital ou ativar automações.
Preservar originais e alterações do usuário; trabalhar sem outros agentes.

No Windows, não criar venv nem instalar Core via pip. Verificar o runtime real:
este computador dispõe inicialmente apenas do Python 3.12.14 empacotado no
Codex, fora do PATH. Ele pode executar ferramentas auxiliares stdlib compatíveis;
isso não valida o contrato do pacote (`>=3.13,<3.15`) nem a suíte canônica.
Não instalar/alterar runtime global ou contornar EDR para satisfazer checks.
Linux CI continua permitido conforme `.github/workflows/ci.yml`.

As regras abaixo preservam contexto histórico e valem onde não conflitarem
com esse mandato. Fonte de verdade do Core atual: wheel oficial 3.2.0,
`pyproject.toml`/`uv.lock`; `vendor/` é histórico e não runtime normal.

**Antes de escrever qualquer linha: ler [docs/DESIGN.md](docs/DESIGN.md) INTEIRO e
[HANDOFF.md](HANDOFF.md) (estado atual, decisões, próximos passos).**

## Regras invioláveis (resumo do design §11 — o design manda em caso de conflito)

- PROIBIDO: ML/IA gerando sinal antes do M6 julgado (exceção: analista somente-leitura do §9b);
  IA escrevendo no banco ou resolvendo quarentena; lookahead de qualquer espécie;
  sobrescrever `prices_raw` ou linhas do ledger; instalar o core via pip; importar código
  de outro domínio; dependência de runtime sem justificativa no HANDOFF; ajustar parâmetros
  da H1 após qualquer rodada; "consertar" dados sem trilha em `adjustments`/`quarantine`.
- OBRIGATÓRIO: testes verdes antes de avançar de marco; golden tests com dados reais no parse;
  teste anti-lookahead automatizado (M4+); HANDOFF atualizado ao fim de cada marco;
  separação download/processamento; reproduzível por `run_id`+`config_hash`.
- Em dúvida de design não coberta: PARAR e perguntar. Não decidir em silêncio.

## Ambiente

- Windows, Python 3.13 **global** — NUNCA criar venv (EDR corporativo quarentena venvs).
- stdlib-first. `numpy` pré-aprovado (ainda não usado — só adicionar quando precisar).
  `pytest` é dev. Qualquer outra dependência: justificar no HANDOFF e o humano decide.
- Downloads bulk rodam em rede limpa (cron) — código separa "baixar" de "processar".

## Convenções do projeto

- TODO I/O de texto declara `encoding="utf-8"` (default do Windows é cp1252 — já mordeu).
- `vendor/predictor_core/` NÃO se edita à toa — a fonte da verdade é o repo irmão
  `C:\Claude-projetos\Claude\predictor_core\` e o sync é UNIDIRECIONAL via o
  `sync_core.py` de lá (`--check`/`--write`). Evolução por demanda vai PRO upstream
  primeiro e desce pelo sync; código customizado no vendor é DELETADO pelo prune.
- Migrações em `stocks_predictor/db.py` são append-only: nunca alterar uma existente, sempre adicionar.
- Config: `stocks_predictor/config.py` (mini-parser stdlib do subconjunto plano de YAML). Parâmetros
  `[H1-FROZEN]` no config.yaml não se tocam após qualquer rodada de resultado.

## Comandos

```powershell
python -m pytest tests/ -v        # suíte completa (deve estar SEMPRE verde no main)
```
