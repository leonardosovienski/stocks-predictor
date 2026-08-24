# Stocks Predictor — estado corrente

**Vigência:** 2026-08-24

Este documento é o ponto de entrada técnico corrente. `HANDOFF.md` preserva a
continuidade histórica detalhada e deve ser interpretado pela data quando divergir
deste estado ou do código/Git atual.

## Papel atual

`stocks-predictor` é um dos três predictors econômicos canônicos do PREDICTORS. A
linha científica ativa é `predictor-rj`, descrita em `docs/RJ_DESIGN.md`. O domínio
cross-sectional/fatores anterior permanece histórico.

## Infraestrutura corrente

- Python `>=3.13,<3.15`;
- package `stocks-predictor 0.1.0` via `pyproject.toml`;
- `predictor-core>=2.3,<3` por wheel oficial;
- `predictor-ops>=3.1,<4` por wheel oficial;
- CI em Python 3.13 com Ruff, Pyright RJ, pytest/coverage, build/wheel smoke e gitleaks;
- `vendor/predictor_core` preservado como snapshot histórico/integrity artifact durante
  a transição; não é a dependência arquitetural alvo.

A suíte deve fixar Core/Ops das wheels antes de módulos legados que ainda carreguem
hooks históricos de `sys.path`. Remover esses hooks remanescentes é housekeeping de
runtime e não pode alterar comportamento científico.

## Estado científico

A modernização técnica não promove nenhum estado científico. O RJ continua no estágio
registrado em `docs/RJ_DESIGN.md`/histórico de 2026-08-23: protocolo criado, testes
sintéticos/power gate existentes e coleta/validação real ainda separadas dessa prova de
mecânica.

Nenhum parâmetro RJ foi alterado por esta modernização.

## Estado econômico

Não existe evidência suficiente neste estado técnico para alegar edge econômico ou
lucro prospectivo. Detectar um padrão que anteceda rally é etapa anterior à definição
de entrada/saída, preço executável, custos, liquidez e P&L.

`capital_permission = FORBIDDEN` nesta migração.

## Fontes

1. `docs/RJ_DESIGN.md` — protocolo científico RJ;
2. `config_rj.yaml` — parâmetros congelados;
3. `pyproject.toml` — runtime/dependências atuais;
4. `.github/workflows/ci.yml` — gates técnicos atuais;
5. Git/CI — evidência mecânica;
6. `HANDOFF.md` — histórico detalhado, válido para suas datas.
