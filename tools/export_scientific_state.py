"""Estado científico do stocks legível por máquina, para consumidores somente leitura (CAIN).

    python tools/export_scientific_state.py --write    # regrava research/scientific_state.json
    python tools/export_scientific_state.py --check    # falha se o arquivo versionado divergir das fontes

Tudo sai de arquivos versionados deste repositório; nada é inventado nem interpretado:

- estado de cada hipótese: ``stocks_predictor.research_admission.closed_hypotheses()``, literal;
- tentativas: ``trials_v2.json`` (``hypothesis_id`` → ``trial_id``);
- famílias encerradas: as famílias que o repositório registra para hipóteses encerradas, no manifesto
  ``ST_RESEARCH_FREEZE`` do ``RESEARCH_FREEZE.md`` e em ``trials_v2.json``. Quando os dois dão nomes diferentes
  para a mesma hipótese, os dois entram (o lado conservador: bloquear reteste pelos dois nomes);
- ``reopen_policy``: o texto literal do manifesto;
- reavaliação do Prompt 4 (``evidence/prompt4/reassessment.json``), com o relatório de veredito conferido pelo
  sha256 e citado pelo caminho no repositório;
- referência ao índice do ledger de domínio e identidade da política de decisão.

O consumidor lê o arquivo num commit fixado (``git show``) e confere as fontes pelos sha256 (bytes com CRLF
normalizado para LF). O arquivo não tem relógio: a mesma árvore gera os mesmos bytes, e ``--check`` prova que
o arquivo versionado acompanha as fontes. Os campos ``hypotheses``, ``hypothesis_trials`` e ``frozen_families``
seguem o formato de estado científico que a CAIN já lê do Cripto; ``domain`` impede ingestão em outro domínio.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = "research/scientific_state.json"
SCHEMA = "stocks-scientific-state/1"
FREEZE = "RESEARCH_FREEZE.md"
ADMISSION = "stocks_predictor/research_admission.py"
TRIALS = "trials_v2.json"
PROTOCOL = "docs/engineering/2026-09-24-protocol-v2"
REASSESSMENT = f"{PROTOCOL}/evidence/prompt4/reassessment.json"
LEDGER_INDEX = f"{PROTOCOL}/evidence/ledger/stocks-domain-ledger-index.json"
POLICY = "policy/stocks-evaluation-policy-v1.json"

# O que cada estado significa, na linguagem do próprio repositório. ``closed``: encerrada cientificamente.
# Nenhum estado abre trial novo no circuito (research_admission recusa todo stocks:H<n>, fail closed).
VOCABULARY = {
    "CLOSED_JUDGED": {"closed": True, "meaning": "julgada em rodada única; NOT_SUPPORTED no manifesto de congelamento"},
    "CLOSED_EMBARGO_ORIGINAL": {"closed": True,
                                "meaning": "julgada; conserva o embargo estimado original dos fundamentos"},
    "CLOSED_HISTORICAL": {"closed": True, "meaning": "encerrada; registro histórico"},
    "CLOSED_HISTORICAL_CONDITIONAL": {"closed": True,
                                      "meaning": "encerrada; resultado histórico condicional, nunca aprovação"},
    "CLOSED_REJECTED": {"closed": True, "meaning": "rejeitada"},
    "PAUSED": {"closed": False, "meaning": "pausada; não observada; bloqueada até dataset e metodologia validados"},
    "PAUSED_INCONCLUSIVE_DATA_QUALITY": {"closed": False,
                                         "meaning": "pausada; resultado observado INCONCLUSIVE_DATA_QUALITY"},
}


def lf_sha256(path: Path) -> str:
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _freeze_manifest(root: Path) -> dict:
    text = (root / FREEZE).read_text(encoding="utf-8")
    found = re.search(r"```yaml\n(ST_RESEARCH_FREEZE:.*?)```", text, re.S)
    if found is None:
        raise ValueError(f"{FREEZE}: manifesto ST_RESEARCH_FREEZE não encontrado")
    return yaml.safe_load(found.group(1))["ST_RESEARCH_FREEZE"]


def _hypothesis_number(value: str) -> int:
    return int(re.fullmatch(r"H(\d+)", value).group(1))


def build(root: Path = ROOT) -> dict:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from stocks_predictor.research_admission import closed_hypotheses
    from stocks_predictor.v2.policy import load_policy

    states = {key.split(":", 1)[1]: value for key, value in closed_hypotheses().items()}
    unknown = sorted(set(states.values()) - set(VOCABULARY))
    if unknown:
        raise ValueError(f"estado sem significado declarado em VOCABULARY: {unknown}")

    trials = json.loads((root / TRIALS).read_text(encoding="utf-8"))
    hypothesis_trials, families = {}, {}
    for row in trials:
        hypothesis = row["hypothesis_id"]
        if hypothesis not in states:
            raise ValueError(f"{TRIALS}: {row['trial_id']} aponta para hipótese desconhecida {hypothesis}")
        if hypothesis in hypothesis_trials:
            raise ValueError(f"{TRIALS}: mais de uma tentativa para {hypothesis}")
        hypothesis_trials[hypothesis] = row["trial_id"]
        if row.get("hypothesis_family") not in (None, "UNKNOWN"):
            families.setdefault(hypothesis, set()).add(row["hypothesis_family"])
    manifest = _freeze_manifest(root)
    for stopped in manifest["stopped_hypotheses"]:
        families.setdefault(stopped["id"], set()).add(stopped["family"])
    frozen = sorted({family for hypothesis, names in families.items()
                     if VOCABULARY[states[hypothesis]]["closed"] for family in names})

    reassessment = {}
    raw = json.loads((root / REASSESSMENT).read_text(encoding="utf-8"))
    for row in raw["rows"]:
        report = f"reports/{Path(row['artifact']).name}"
        if lf_sha256(root / report) != row["artifact_sha256"]:
            raise ValueError(f"{REASSESSMENT}: {report} não confere com o sha256 registrado")
        reassessment[row["hypothesis"]] = {"status_before": row["status_before"], "status_after": row["status_after"],
                                           "report": report, "report_sha256": row["artifact_sha256"],
                                           "ledger_hash": row["ledger_hash"]}

    index = json.loads((root / LEDGER_INDEX).read_text(encoding="utf-8"))
    policy = load_policy(root / POLICY)
    sources = [ADMISSION, FREEZE, TRIALS, REASSESSMENT, LEDGER_INDEX, POLICY]
    by_number = sorted(states, key=_hypothesis_number)
    return {
        "schema": SCHEMA,
        "domain": "stocks",
        "hypotheses": {h: states[h] for h in by_number},
        "hypothesis_trials": {h: hypothesis_trials[h] for h in by_number if h in hypothesis_trials},
        "frozen_families": frozen,
        "vocabulary": VOCABULARY,
        "reopen_policy": {"source": f"{FREEZE}#ST_RESEARCH_FREEZE.reopen_policy",
                          "text": manifest["reopen_policy"]},
        "reassessment": {h: reassessment[h] for h in sorted(reassessment, key=_hypothesis_number)},
        "n_trials": raw["n_trials"],
        "ledger_index": {"path": LEDGER_INDEX, "schema": index["schema"], "records": index["records"],
                         "head": index["head"], "counts": index["counts"]},
        "decision_policy": {"path": POLICY, "version": policy.version, "status": policy.status,
                            "sha256": policy.sha256},
        "sources": [{"path": path, "sha256_lf": lf_sha256(root / path)} for path in sources],
        "notes": ("Estados literais do repositório; nenhum GO, nenhum edge econômico demonstrado. "
                  "Preços não fazem parte deste arquivo (licença de redistribuição não verificada)."),
    }


def render(state: dict) -> str:
    return json.dumps(state, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python tools/export_scientific_state.py", description=__doc__.split("\n")[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / OUTPUT)
    args = parser.parse_args(argv)
    text = render(build())
    if args.write:
        args.output.write_text(text, encoding="utf-8", newline="\n")
        print(json.dumps({"written": str(args.output.relative_to(ROOT) if args.output.is_relative_to(ROOT)
                                         else args.output), "sha256": sha256(text.encode()).hexdigest()}))
        return 0
    current = args.output.read_text(encoding="utf-8") if args.output.exists() else None
    if current != text:
        print(f"{args.output.name} diverge das fontes: rode --write e revise o diff", file=sys.stderr)
        return 1
    print(json.dumps({"status": "OK", "sha256": sha256(text.encode()).hexdigest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
