"""Previsões zero-shot do Chronos-Bolt para as tarefas exportadas pelo protocolo v2 (ambiente ISOLADO).

Roda no venv próprio do Chronos (torch + chronos-forecasting), nunca no do stocks-predictor, e não importa o
pacote. Entrada: ``stocks-forecast-tasks/1`` (``forecast_eval --export-tasks``). Saída: ``stocks-forecasts/1``,
com a proveniência exigida por ``stocks_predictor.v2.forecasting.load_forecasts``.

- Offline: ``HF_HUB_OFFLINE=1``; os pesos vêm de um diretório local, e o sha256 deles é conferido antes do uso.
- Alvo: o contexto são os fechamentos; o quantil do nível τ no passo h vira log(q_τ/fechamento(D)). A transformação
  é monótona, então preserva quantis. Quantil de preço não positivo interrompe a execução (falha fechada).
- Quantis cruzados: rearranjo monótono (ordenação), com a contagem registrada.
- O Chronos-Bolt prevê quantis diretamente, sem amostragem; a semente e as threads ficam fixas assim mesmo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--tasks", required=True, type=Path)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--provenance", required=True, type=Path, help="JSON com os campos de proveniência do modelo")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error(f"{args.output} já existe: nada é sobrescrito")
    os.environ["HF_HUB_OFFLINE"] = "1"
    provenance = json.loads(args.provenance.read_text(encoding="utf-8"))
    weights = hashlib.sha256((args.model_dir / "model.safetensors").read_bytes()).hexdigest()
    if weights != provenance["weights_sha256"]:
        raise SystemExit(f"pesos diferentes do declarado: {weights}")
    payload = json.loads(args.tasks.read_bytes())
    if payload.get("schema") != "stocks-forecast-tasks/1":
        raise SystemExit("arquivo de tarefas inválido")
    body = [{"security_id": t["security_id"], "origin_session": t["origin_session"], "context": t["context"]}
            for t in payload["tasks"]]
    if hashlib.sha256(canonical(body)).hexdigest() != payload["tasks_sha256"]:
        raise SystemExit("tasks_sha256 não confere com o conteúdo")

    import chronos
    import torch
    from chronos import BaseChronosPipeline

    torch.manual_seed(0)
    torch.set_num_threads(args.threads)
    pipeline = BaseChronosPipeline.from_pretrained(str(args.model_dir), device_map="cpu", torch_dtype=torch.float32)
    horizon, levels = payload["horizon"], payload["levels"]
    entries, rearranged = [], 0
    for start in range(0, len(body), args.batch_size):
        batch = body[start:start + args.batch_size]
        contexts = [torch.tensor(t["context"], dtype=torch.float32) for t in batch]
        quantiles, _mean = pipeline.predict_quantiles(contexts, prediction_length=horizon, quantile_levels=levels)
        for task, row in zip(batch, quantiles[:, horizon - 1, :].tolist()):
            if any(q <= 0 for q in row):
                raise SystemExit(f"quantil de preço não positivo em {task['security_id']} {task['origin_session']}")
            logs = [math.log(q / task["context"][-1]) for q in row]
            if logs != sorted(logs):
                rearranged += 1
                logs.sort()
            entries.append({"security_id": task["security_id"], "origin_session": task["origin_session"],
                            "quantiles": logs})
    out = {"schema": "stocks-forecasts/1", "model": provenance, "horizon": horizon, "levels": levels,
           "tasks_sha256": payload["tasks_sha256"], "dataset_hash": payload["dataset_hash"],
           "spec_sha256": payload["spec_sha256"],
           "runtime": {"torch": torch.__version__, "chronos_forecasting": getattr(chronos, "__version__", "unknown"),
                       "python": sys.version.split()[0], "threads": args.threads, "rearranged_rows": rearranged},
           "entries": entries}
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, allow_nan=False)
    print(json.dumps({"entries": len(entries), "rearranged_rows": rearranged, "weights_sha256": weights}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
