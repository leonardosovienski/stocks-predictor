"""Régua nova sobre artefatos históricos, sem reexecutar nada (Prompt 4).

Para hipóteses encerradas, a regra é aplicar a régua nova ao artefato histórico e dizer se o status se mantém ou
fica mais conservador. Nada de nova busca, variante ou reexecução: a ``reopen_policy`` do ``RESEARCH_FREEZE.md``
exige 6 campos revisados por um humano para reabrir.

Artefato: o relatório de veredito versionado (``reports/h*_verdict*.md``) e a linha do ``trials.json``.

DSR na grade de N sem as séries de retorno (que estão no PC 1). O DSR histórico é
``Φ[(SR − SR0_h)·√(T − 1) / D]``, com ``D = √(1 − γ3·SR + (γ4 − 1)/4·SR²)``. Conhecidos o DSR histórico, SR,
SR0_h e T, isola-se ``D = (SR − SR0_h)·√(T − 1) / Φ⁻¹(DSR)``. É a mesma correção de assimetria e curtose que o
veredito usou. O DSR novo é ``Φ[(SR − SR0(N))·√(T − 1) / D]``, com ``SR0(N) = E[max SR]`` do core e V[SR] dos
Sharpes por pregão das tentativas históricas. Quando ``|Φ⁻¹(DSR)| < 0,05`` ou não há DSR histórico, ``D = 1``
(momentos normais), e a linha é marcada como aproximada.
"""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from statistics import NormalDist, variance

from predictor_core.measurement.trials import expected_max_sharpe

_NUM = r"(-?\d+(?:\.\d+)?)"
PATTERNS = {
    "sessions": rf"pregões pareados:\*\*\s*{_NUM}",
    "psr": rf"Lente 1 \(PSR\):\*\*\s*{_NUM}",
    "ic_low": rf"bloco 21\):\*\*\s*\[{_NUM},",
    "ic_high": rf"bloco 21\):\*\*\s*\[{_NUM},\s*{_NUM}\]",
    "dsr": rf"DSR \(Deflated Sharpe Ratio\):\*\*\s*{_NUM}",
    "n_hist": r"E\[max SR \| N=(\d+)\]",
    "sr0_hist": rf"E\[max SR \| N=\d+\] = {_NUM} por-período",
    "sharpe_ann": rf"\| Sharpe \(anual\.\) \| {_NUM} \| {_NUM} \|",
    "total_return": rf"\| retorno total \| {_NUM}% \| {_NUM}% \|",
    "max_drawdown": rf"\| max drawdown \| {_NUM}% \| {_NUM}% \|",
}


def parse_verdict_report(text: str) -> dict:
    """Números do relatório de veredito; ausência vira ``None`` (nunca inventada)."""
    out: dict = {}
    for key, pattern in PATTERNS.items():
        match = re.search(pattern, text)
        if match is None:
            out[key] = None
            continue
        groups = match.groups()
        if key == "ic_high":
            out[key] = float(groups[1])
        elif key in ("sharpe_ann", "total_return", "max_drawdown"):
            out[key] = {"strategy": float(groups[0]), "benchmark": float(groups[1])}
        elif key in ("sessions", "n_hist"):
            out[key] = int(groups[0])
        else:
            out[key] = float(groups[0])
    verdict = re.search(r"\*\*veredito [^:]+:\*\*\s*\*\*([^*]+)\*\*", text)
    out["verdict"] = verdict.group(1).strip() if verdict else None
    out["execution_declared"] = "abertura de D+1" if "abertura de D+1" in text else None
    return out


def implied_denominator(dsr: float, sr: float, sr0: float, sessions: int) -> float | None:
    """D implícito do DSR histórico; ``None`` quando Φ⁻¹(DSR) está perto de zero (instável)."""
    z = NormalDist().inv_cdf(dsr)
    if abs(z) < 0.05:
        return None
    d = (sr - sr0) * math.sqrt(sessions - 1) / z
    return d if d > 0 else None


def rescaled_dsr(sr: float, sr0: float, sessions: int, denominator: float) -> float:
    return NormalDist().cdf((sr - sr0) * math.sqrt(sessions - 1) / denominator)


def reassess(report: dict, *, sr_per_session: float, trial_sharpes: list[float], n_grid: list[int]) -> dict:
    """DSR na grade de N para um artefato. ``sr_per_session`` vem do ``trials.json`` (Sharpe por pregão)."""
    var = variance(trial_sharpes)
    denominator, approximate = None, True
    if report.get("dsr") is not None and report.get("sr0_hist") is not None and report.get("sessions"):
        denominator = implied_denominator(report["dsr"], sr_per_session, report["sr0_hist"], report["sessions"])
        approximate = denominator is None
    if denominator is None:
        denominator = 1.0
    rows = []
    for n in sorted(set(n_grid)):
        sr0 = expected_max_sharpe(n, var)
        rows.append({"n": n, "sr0": sr0, "dsr": rescaled_dsr(sr_per_session, sr0, report["sessions"], denominator)})
    worst = min(rows, key=lambda row: row["dsr"])
    historical = report.get("dsr")
    return {"denominator": denominator, "denominator_approximate": approximate, "var_trial_sharpe": var,
            "rows": rows, "worst": worst, "historical_dsr": historical, "historical_n": report.get("n_hist"),
            "more_conservative": historical is None or worst["dsr"] <= historical + 1e-12}


def annualized(total_return_pct: float, sessions: int, per_year: int = 252) -> float:
    return (1 + total_return_pct / 100) ** (per_year / sessions) - 1


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# Incompatibilidades entre o protocolo dos vereditos e o v2 (evidência: docs/evidence/2026-09-24-prompt2-auditoria.md).
_JUDGED_LEGACY = {f"H{n}" for n in (1, 2, *range(4, 17))}
BIASES = {
    "execucao_no_fechamento_do_sinal": (_JUDGED_LEGACY, "o relatório declara abertura de D+1, mas o "
                                        "`legacy_walk_forward` executa no fechamento de D (backtest.py:126-181, "
                                        "factor.py:36); favorece a estratégia"),
    "fundamento_com_embargo_estimado": ({"H7", "H9", "H10", "H12", "H13"}, "ref_date + 90 dias em vez da data de "
                                        "divulgação (factor.py:118-145)"),
    "identidade_por_prefixo_do_ticker": (_JUDGED_LEGACY, "universe.py:74-80; quarentena pelo estado de resolução "
                                         "atual"),
    "retorno_so_preco": (_JUDGED_LEGACY - {"H11"}, "proventos omitidos; o pré-registro da H1 declara que isso "
                         "favorece momentum"),
    "benchmark_sem_custo": (_JUDGED_LEGACY, "o EW do legado não paga turnover (backtest.py:181); desfavorece a "
                            "estratégia"),
    "sharpe_com_rf_zero": (_JUDGED_LEGACY, "sem excesso de CDI; como o CDI é positivo em todo pregão, o Sharpe em "
                           "excesso seria menor"),
}


def biases_for(hypothesis: str) -> list[dict]:
    return [{"bias": name, "evidence": text} for name, (members, text) in BIASES.items() if hypothesis in members]


def hypothesis_number(path: Path) -> int:
    match = re.search(r"h(\d+)_", path.name)
    if match is None:
        raise ValueError(f"nome de relatório fora do padrão: {path.name}")
    return int(match.group(1))


def _cdi_annualized(rf, start: str, end: str) -> dict | None:
    sessions = [s for s in rf.sessions() if start <= s <= end]
    if not sessions:
        return None
    return {"from": sessions[0], "to": sessions[-1], "sessions": len(sessions),
            "annualized": (1 + rf.compounded(sessions)) ** (252 / len(sessions)) - 1}


def main(argv: list[str] | None = None) -> int:
    """Reavaliação dos artefatos das hipóteses encerradas, gravada no ledger (``REASSESSMENT``)."""
    import argparse
    import json

    from ..research_admission import closed_hypotheses
    from .forecast_eval import load_riskfree
    from .manifest import TrialLedger, utc_now
    from .metrics import n_trials_grid
    from .policy import load_policy

    parser = argparse.ArgumentParser(prog="python -m stocks_predictor.v2.reassessment")
    parser.add_argument("--reports", required=True, type=Path)
    parser.add_argument("--trials", required=True, type=Path)
    parser.add_argument("--riskfree", required=True)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error(f"{args.output} já existe: nada é sobrescrito")
    policy, ledger, rf = load_policy(args.policy), TrialLedger(args.ledger), load_riskfree(args.riskfree)
    trials = {t["name"].split("-")[0].upper(): t for t in json.loads(args.trials.read_text(encoding="utf-8"))}
    sharpes = [t["sharpe"] for t in trials.values()]
    status = closed_hypotheses()
    reports = sorted(args.reports.glob("h*_verdict*.md"), key=hypothesis_number)
    dsr_rules = policy.section("dsr")
    started = len(ledger.started())
    n_known = dsr_rules["n_prior_lower_bound"] + started + len(reports)
    grid = n_trials_grid(n_known, dsr_rules["n_multipliers"], max(dsr_rules["n_upper"], n_known))
    min_rate = rf.min_daily_rate()
    rows = []
    for path in reports:
        hypothesis = f"H{hypothesis_number(path)}"
        text = path.read_text(encoding="utf-8")
        report = parse_verdict_report(text)
        trial = trials[hypothesis]
        result = reassess(report, sr_per_session=trial["sharpe"], trial_sharpes=sharpes, n_grid=grid)
        start = trial["test_period"][0][:10]
        end = "2022-12-31" if "2018-2022" in text else trial["test_period"][1][:10]
        strategy_ann = annualized(report["total_return"]["strategy"], report["sessions"])
        benchmark_ann = annualized(report["total_return"]["benchmark"], report["sessions"])
        keep = (report["verdict"] or "").startswith("não comprovada") and result["worst"]["dsr"] < dsr_rules["min_probability"]
        row = {
            "hypothesis": hypothesis, "status_before": status.get(f"stocks:{hypothesis}"),
            "verdict_before": report["verdict"], "artifact": path.as_posix(), "artifact_sha256": file_sha256(path),
            "sessions": report["sessions"], "window_declared": [start, end],
            "sharpe_ann": report["sharpe_ann"], "sr_per_session": trial["sharpe"], "psr_hist": report["psr"],
            "ic95_diff_sharpe": [report["ic_low"], report["ic_high"]],
            "execution_declared": report["execution_declared"], "reassessment": result,
            "annual_return": {"strategy": strategy_ann, "benchmark": benchmark_ann,
                              "cdi_same_window": _cdi_annualized(rf, start, end)},
            "biases": biases_for(hypothesis),
            "status_after": ("NOT_SUPPORTED mantido — régua nova mais conservadora" if keep and result["more_conservative"]
                             else "REVISAR (a régua nova não foi mais conservadora)"),
        }
        record = ledger.append_record("REASSESSMENT", f"reassessment:{hypothesis}",
                                      {"row": row, "policy": policy.identity(), "risk_free": rf.to_dict(),
                                       "recorded_at": utc_now()})
        row["ledger_hash"] = record["hash"]
        rows.append(row)
    out = {"policy": policy.identity(), "risk_free": rf.to_dict(), "cdi_min_daily_rate": min_rate,
           "n_trials": {"prior_lower_bound": dsr_rules["n_prior_lower_bound"], "ledger_started": started,
                        "reassessed_artifacts": len(reports), "n_known": n_known, "grid": grid},
           "var_trial_sharpe": variance(sharpes), "rows": rows,
           "ledger": {"records": len(ledger.records), "head": ledger.records[-1]["hash"]}}
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"rows": len(rows), "n_known": n_known, "grid": grid}))
    return 0


__all__ = ["BIASES", "PATTERNS", "annualized", "biases_for", "file_sha256", "implied_denominator", "main",
           "parse_verdict_report", "reassess", "rescaled_dsr"]


if __name__ == "__main__":
    raise SystemExit(main())
