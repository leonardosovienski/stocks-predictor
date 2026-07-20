# predictor-stocks — instruções para o implementador

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
  `C:\Codex-projetos\Codex\predictor_core\` e o sync é UNIDIRECIONAL via o
  `sync_core.py` de lá (`--check`/`--write`). Evolução por demanda vai PRO upstream
  primeiro e desce pelo sync; código customizado no vendor é DELETADO pelo prune.
- Migrações em `src/db.py` são append-only: nunca alterar uma existente, sempre adicionar.
- Config: `src/config.py` (mini-parser stdlib do subconjunto plano de YAML). Parâmetros
  `[H1-FROZEN]` no config.yaml não se tocam após qualquer rodada de resultado.

## Comandos

```powershell
python -m pytest tests/ -v        # suíte completa (deve estar SEMPRE verde no main)
```
