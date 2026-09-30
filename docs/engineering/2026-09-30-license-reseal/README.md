# Relacrar a evidência R8 depois do commit de licença (2026-09-30)

## O que aconteceu

O commit `97979d5` ("chore(license): mark package metadata as proprietary") mudou `pyproject.toml`, que é um dos
caminhos lacrados por [`tools/verify_operational_evidence.py`](../../../tools/verify_operational_evidence.py). O CI do
`main` ficou vermelho no passo "Current R8 operational evidence identities":
[run 36647068421](https://github.com/leonardosovienski/stocks-predictor/actions/runs/36647068421)
(`ValueError: current operational code changed: pyproject.toml`). O commit anterior, `65fa465` (só o arquivo
`LICENSE`), passou ([run 36647065681](https://github.com/leonardosovienski/stocks-predictor/actions/runs/36647065681)).

Não é regressão de código: nenhum arquivo `.py` mudou desde o lacre de 2026-09-28. É o lacre cumprindo o papel dele.

## Por que este relacre só o dono consegue fazer

[AGENTS.md](../../../AGENTS.md): "Mudança no pacote exige novos recibos de carga real/capacidade ligados ao código
efetivamente executado." O recibo real exige a população preservada de **55.986 linhas** do `COTAHIST_A2026`
observado em 2026-09-10 (sha256 `34b77468…`), que está em `C:\STOCKS\data` / PC 2 e não é redistribuível; o arquivo
público da B3 de hoje tem outra contagem e outro hash, e
[`materialize_current_operational_evidence.py`](../../../tools/materialize_current_operational_evidence.py) recusa
qualquer recibo real que não tenha exatamente 55.986 linhas em `PASS`. Reaproveitar os recibos de 2026-09-28 para
relacrar sem executar nada seria mascarar a falha (não fazer).

## Procedimento (Linux do dono, PC 2 / WSL2, checkout limpo do `main`)

```bash
uv sync --locked --all-extras --python 3.13
OUT=docs/engineering/2026-09-30-license-reseal/evidence
# 1. recibo real: o mesmo arquivo preservado e o mesmo recibo de download usados em 2026-09-28
uv run --no-sync python tools/operational_validation.py --output "$OUT/real" --rows 55986 \
  --archive <caminho do COTAHIST_A2026 preservado (sha256 34b774681cbd…)> --receipt <recibo de download desse arquivo>
cp "$OUT/real/validation.json" "$OUT/operational-real.json"
# 2. recibo de capacidade (sintético, 250.000 linhas)
uv run --no-sync python tools/operational_validation.py --output "$OUT/capacity" --rows 250000
cp "$OUT/capacity/validation.json" "$OUT/operational-capacity.json"
rm -rf "$OUT/real" "$OUT/capacity"     # bancos, zip e snapshots não são versionados
# 3. lacre novo (hashes do código atual + os dois recibos)
uv run --no-sync python tools/materialize_current_operational_evidence.py \
  --real "$OUT/operational-real.json" --capacity "$OUT/operational-capacity.json" \
  --output docs/engineering/current-operational-evidence.json
uv run --no-sync python tools/verify_operational_evidence.py
python tools/check_project_files.py --write-index
```

Depois: branch + PR, CI verde, merge. O lacre de 2026-09-28 e os recibos dele ficam onde estão (histórico append-only).

## O que já foi feito sem tocar nos caminhos lacrados

- Workflows `release.yml` (release reprodutível a partir da tag, mesmo desenho do cripto e do brasileirão) e
  `delete-branches.yml`; nenhum deles entra no lacre (só `ci.yml` entra).
- [Estado de 2026-09-30](../../ESTADO_2026-09-30.md).
