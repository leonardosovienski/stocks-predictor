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
- stdlib-first, mas o runtime NÃO é stdlib puro: `PyYAML>=6.0,<7` é dependência
  declarada (`pyproject.toml`, `requirements.txt`) e usada de verdade em
  `rj_power.py` e `rj_pipeline.py` — a linha RJ lê YAML completo, o mini-parser de
  `config.py` cobre só o subconjunto plano. `predictor-core` vem por wheel (abaixo).
  `numpy` está pré-aprovado e continua NÃO usado. `pytest` é dev. Qualquer outra
  dependência: justificar no HANDOFF e o humano decide.
- Downloads bulk rodam em rede limpa (cron) — código separa "baixar" de "processar".

## Convenções do projeto

- TODO I/O de texto declara `encoding="utf-8"` (default do Windows é cp1252 — já mordeu).
- O core vem por WHEEL do repo irmão `leonardosovienski/core-predictor`, NÃO do
  `vendor/`. `tests/conftest.py` asserta isso (`assert "vendor" not in
  predictor_core.__file__`) — a suíte se recusa a rodar contra o vendor. Instalar:
  `py -3.13 -m pip install --upgrade "https://github.com/leonardosovienski/core-predictor/releases/download/v3.1.0/predictor_core-3.1.0-py3-none-any.whl"`.
  (Correção de 2026-09-06: este arquivo dizia que a fonte da verdade era o
  `vendor/`, contradizendo o `conftest.py` desde a migração para wheels.
  `vendor/` permanece no repo como fallback histórico, fora do runtime.)
- Migrações em `stocks_predictor/db.py` são append-only: nunca alterar uma existente, sempre adicionar.
- Config: `stocks_predictor/config.py` (mini-parser stdlib do subconjunto plano de YAML). Parâmetros
  `[H1-FROZEN]` no config.yaml não se tocam após qualquer rodada de resultado.

## Onde ler antes de tocar em H17/H18/H19

- **`HANDOFF.md`, entrada `VEREDITO` no topo** — estado corrente: os 5 critérios
  de aceite da H18 fecharam em 2026-09-06; falta FIXAR A ORDEM das rodadas
  (o N do DSR cresce a cada tentativa, então quem roda por último enfrenta a
  barra mais alta — escolher depois de ver resultado é p-hacking).
- **`docs/RUNBOOK_H18.md`** — do zero até a medição, com o caminho real do repo
  nesta máquina, os quatro checkouts existentes e a tabela de erros comuns.
- **`docs/auditoria_2026-09-04.md`** — o parecer independente que originou tudo,
  com errata no topo apontando o que medições posteriores corrigiram.

## Política de `known_at` — não herde por acidente

`fundamentals.known_at` é a data OBSERVADA de recebimento pela CVM (`DT_RECEB`).
`factor._fundamental_signals` só a usa quando o chamador passa `use_known_at=True`.

- **H7, H9, H10, H12, H13 (JULGADAS)** passam `False`: ficam no embargo estimado
  com que foram efetivamente rodadas. Não mude isso — o veredito delas é registro
  histórico e um re-run silenciosamente diferente quebraria a reprodutibilidade.
- **H17, H18, H19 (nunca rodaram)** usam a data observada, declarado em
  `known_at_policy: observed` no config e selado no hash congelado.

## Comandos

```powershell
py -3.13 -m pytest tests\ -q      # suíte completa (deve estar SEMPRE verde no main)
py -3.13 main.py                  # status: contagem por tabela, hashes, trials
```

**Use `py -3.13`, não `python`** — nesta máquina `python` resolve para 3.14.
