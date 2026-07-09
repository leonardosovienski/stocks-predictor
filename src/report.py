"""M5/M6 — Relatório do veredito da H1 vs. benchmark + telemetria estruturada.

Consome as séries diárias pareadas (estratégia, benchmark) e o veredito do pedágio
(`backtest.judge`) e produz DOIS artefatos:

1. um relatório Markdown legível em `reports/` (equity, Sharpe/Sortino/MaxDD, o IC do
   pedágio, o veredito) — auditável e datado por `run_id`;
2. UM evento estruturado na telemetria JSONL (`obs.emit_event`) — o envelope rígido de
   7 chaves que reconstrói a saúde da plataforma sem dashboard.

Não decide nada: só descreve o que o pedágio já julgou. Não escreve no banco.
"""
import math
import os
import pathlib

from db import get_code_version
from predictor_core import obs
from predictor_core.stats import max_drawdown, sharpe, sortino

ROOT = pathlib.Path(__file__).parent.parent
DOMAIN = "predictor-stocks"
# override p/ isolar testes do reports/ real (mesmo padrão do obs.EVENTS_ENV)
REPORTS_ENV = "PREDICTOR_REPORTS_DIR"


def _num(x):
    """Sanitiza um valor numérico: NaN/inf/não-número -> None."""
    return x if isinstance(x, (int, float)) and math.isfinite(x) else None


def _equity_curve(returns):
    """Retornos diários -> curva de capital (base 1.0)."""
    eq, v = [], 1.0
    for r in returns:
        v *= (1.0 + r)
        eq.append(v)
    return eq


def summarize_series(returns, periods_per_year=252):
    """Métricas descritivas de uma série de retornos diários."""
    if not returns:
        return {"n": 0, "sharpe": None, "sortino": None,
                "total_return": None, "max_drawdown": None}
    eq = _equity_curve(returns)
    return {
        "n": len(returns),
        "sharpe": _num(sharpe(returns, periods_per_year)),
        "sortino": _num(sortino(returns, periods_per_year)),
        "total_return": eq[-1] - 1.0,
        "max_drawdown": max_drawdown(eq),
    }


def _fmt(x, pct=False):
    if x is None:
        return "n/d"
    return f"{x * 100:.2f}%" if pct else f"{x:.4f}"


def build_markdown(verdict, strat, bench, cfg, run_id=None):
    """Monta o corpo Markdown do relatório."""
    s, b = summarize_series(strat), summarize_series(bench)
    lo, hi = verdict.get("sharpe_diff_ci", (None, None))
    boot = cfg.get("bootstrap", {})
    lines = [
        "# predictor-stocks — Relatório do veredito da H1",
        "",
        f"- **run_id:** `{run_id or 'n/d'}`",
        f"- **pregões pareados:** {verdict.get('n', 0)}",
        f"- **veredito H1:** **{verdict.get('veredito', 'n/d')}**",
        "",
        "## Pedágio de 2 lentes",
        "",
        f"- **Lente 1 (PSR):** {_fmt(_num(verdict.get('psr')))}  "
        f"— P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade",
        f"- **Lente 2 (IC {int(boot.get('confidence', 0.95) * 100)}% da diferença de "
        f"Sharpe, block bootstrap pareado, bloco {boot.get('block_length', 21)}):** "
        f"[{_fmt(lo)}, {_fmt(hi)}]",
        f"  - H1 comprovada só se o IC não cruzar zero → "
        f"{'ACIMA de zero' if lo is not None and lo > 0 else 'CRUZA zero / negativo'}",
        "",
        "## Estratégia vs. benchmark (equiponderado do universo)",
        "",
        "| métrica | estratégia | benchmark |",
        "|---|---|---|",
        f"| Sharpe (anual.) | {_fmt(s['sharpe'])} | {_fmt(b['sharpe'])} |",
        f"| Sortino (anual.) | {_fmt(s['sortino'])} | {_fmt(b['sortino'])} |",
        f"| retorno total | {_fmt(s['total_return'], pct=True)} | {_fmt(b['total_return'], pct=True)} |",
        f"| max drawdown | {_fmt(s['max_drawdown'], pct=True)} | {_fmt(b['max_drawdown'], pct=True)} |",
        "",
        "## Ressalvas registradas (não-negociáveis)",
        "",
        "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; o viés FAVORECE a "
        "estratégia de momentum contra o benchmark (declarado no pré-registro).",
        "- Custo roundtrip aplicado no rebalance; execução na abertura de D+1.",
        "- Veredito real da H1 exige COTAHIST **real** da B3 — sintético só valida a máquina.",
        "",
    ]
    return "\n".join(lines), s, b


def write_report(verdict, strat, bench, cfg, run_id=None, reports_dir=None):
    """Grava o relatório Markdown e emite o evento de telemetria. Retorna o Path do MD."""
    body, s, b = build_markdown(verdict, strat, bench, cfg, run_id)

    rel = reports_dir or os.getenv(REPORTS_ENV) or cfg.get("data", {}).get("reports_dir", "reports")
    out_dir = pathlib.Path(rel)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"h1_verdict_{run_id or 'adhoc'}.md"
    out_path = out_dir / fname
    out_path.write_text(body, encoding="utf-8")

    # telemetria: metrics é SÓ numérico E finito (NaN viraria JSON inválido no
    # events.jsonl — json.dumps emite 'NaN', que nenhum parser estrito aceita).
    lo, hi = verdict.get("sharpe_diff_ci", (None, None))
    metrics = {"n_pregoes": verdict.get("n", 0), "psr": verdict.get("psr"),
               "ic_lower": lo, "ic_upper": hi,
               "sharpe_strat": s["sharpe"], "sharpe_bench": b["sharpe"],
               "maxdd_strat": s["max_drawdown"], "maxdd_bench": b["max_drawdown"]}
    metrics = {k: v for k, v in metrics.items() if _num(v) is not None}
    obs.emit_event(
        DOMAIN, "h1_verdict", run_id=run_id, code_version=get_code_version(),
        metrics=metrics,
        metadata={"veredito": verdict.get("veredito", "n/d"),
                  "report_path": str(out_path.name)})
    return out_path
