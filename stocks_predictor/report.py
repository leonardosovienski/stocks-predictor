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
from predictor_core.measurement.stats import max_drawdown, sharpe, sortino

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


_BIAS_NOTE = {
    "H1": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; o viés FAVORECE a "
          "estratégia de momentum contra o benchmark (declarado no pré-registro).",
    "H2": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; papéis de baixa "
          "volatilidade tendem a MAIOR yield, logo o viés PENALIZA a estratégia contra "
          "o benchmark — conservador (declarado no pré-registro da H2).",
    "H4": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; a ponderação "
          "1/vol sobrepesa papéis de baixa volatilidade (maior yield), logo o viés "
          "PENALIZA a estratégia contra o benchmark — conservador (declarado no "
          "pré-registro da H4).",
    "H5": "- Retorno **só-preço** (rota (b)): quedas ex-dividendo classificam papéis "
          "de maior yield como 'perdedores' e o provento omitido subestima o retorno "
          "da carteira → o viés tende a PENALIZAR a estratégia — conservador "
          "(declarado no pré-registro da H5).",
    "H6": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; papéis de "
          "momentum tendem a MENOR yield, logo o viés FAVORECE a estratégia de "
          "momentum 6-1 contra o benchmark — mesma direção e racional da H1 (não "
          "fixado explicitamente no pré-registro original da H6; nota técnica "
          "adicionada na revisão de código de 2026-08-28).",
    "H8": "- Retorno **só-preço** (rota (b)): direção MISTA — a perna momentum tende "
          "a FAVORECER a estratégia (menor yield, como H1/H6) e a perna baixa-vol "
          "tende a PENALIZAR (maior yield, como H2/H4); como a H8 é a INTERSEÇÃO das "
          "duas, o viés líquido não tem sinal a priori (não fixado explicitamente no "
          "pré-registro original da H8; nota técnica adicionada na revisão de código "
          "de 2026-08-28).",
    "H7": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; SEM direção "
          "declarada a priori — ao contrário de H1/H2/H4/H5/H6/H8 (fatores de "
          "preço/vol, onde a relação com yield é conhecida da literatura), a relação "
          "entre ROE alto e política de dividendos de empresas B3 não foi "
          "estabelecida nesta rodada (poderia ir em qualquer direção: empresa lucrativa "
          "paga mais OU reinveste mais). Viés não quantificado, registrado como "
          "limitação honesta (declarado no pré-registro da H7, 2026-09-03) — não "
          "inferir sinal. Adicionalmente: o dado de ROE tem embargo de divulgação de "
          "90 dias sobre `ref_date` (`h7_factor.disclosure_embargo_days`), mas não "
          "cobre a data REAL de entrega da DFP à CVM (ver `ingest_cvm.py`) — um "
          "embargo curto demais vazaria informação contábil antes da publicação real.",
    "H9": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; SEM direção "
          "declarada a priori — mesma limitação da H7 (a relação entre baixa "
          "alavancagem e política de dividendos de empresas B3 não foi estabelecida "
          "nesta rodada; empresa pouco endividada poderia distribuir mais OU menos, "
          "sem prior claro). Viés não quantificado, registrado como limitação honesta "
          "(declarado no pré-registro da H9, 2026-09-04) — não inferir sinal. Mesmo "
          "embargo de divulgação de 90 dias sobre `ref_date` da H7 "
          "(`h9_factor.disclosure_embargo_days`, mesma fonte DFP/CVM), mesma limitação "
          "de não cobrir a data REAL de entrega à CVM.",
}


def build_markdown(verdict, strat, bench, cfg, run_id=None, hypothesis="H1"):
    """Monta o corpo Markdown do relatório. `hypothesis` rotula H1/H2 — a
    maquinaria (pedágio, métricas) é a mesma; a H2 acrescenta a linha do DSR."""
    s, b = summarize_series(strat), summarize_series(bench)
    lo, hi = verdict.get("sharpe_diff_ci", (None, None))
    boot = cfg.get("bootstrap", {})
    lines = [
        f"# predictor-stocks — Relatório do veredito da {hypothesis}",
        "",
        f"- **run_id:** `{run_id or 'n/d'}`",
        f"- **pregões pareados:** {verdict.get('n', 0)}",
        f"- **veredito {hypothesis}:** **{verdict.get('veredito', 'n/d')}**",
        "",
        "## Pedágio de 2 lentes",
        "",
        f"- **Lente 1 (PSR):** {_fmt(_num(verdict.get('psr')))}  "
        f"— P(Sharpe estratégia > Sharpe benchmark), corrige não-normalidade",
        f"- **Lente 2 (IC {int(boot.get('confidence', 0.95) * 100)}% da diferença de "
        f"Sharpe, block bootstrap pareado, bloco {boot.get('block_length', 21)}):** "
        f"[{_fmt(lo)}, {_fmt(hi)}]",
        f"  - {hypothesis} comprovada só se o IC não cruzar zero → "
        f"{'ACIMA de zero' if lo is not None and lo > 0 else 'CRUZA zero / negativo'}",
    ]
    if "dsr" in verdict:
        # mesmo fallback de trials_gate.apply_dsr (que realmente decide o veredito):
        # seção `{h}_criteria` ausente -> {} -> dsr_min default 0.95. Divergir daqui
        # (ex.: cair para h2_criteria) exibiria um limiar que não foi o usado pra
        # julgar (achado de revisão de código 2026-08-28).
        crit = cfg.get(f"{hypothesis.lower()}_criteria", {})
        lines += [
            f"- **Critério (ii) — DSR (Deflated Sharpe Ratio):** "
            f"{_fmt(_num(verdict.get('dsr')))} contra E[max SR | N="
            f"{verdict.get('n_trials')}] = {_fmt(_num(verdict.get('sr0')))} por-período "
            f"(mínimo pré-registrado: {crit.get('dsr_min', 0.95)})",
        ]
    if verdict.get("maxdd_strat") is not None:
        dd_s, dd_b = verdict["maxdd_strat"], verdict["maxdd_bench"]
        lines += [
            f"- **Critério (iii) — drawdown (\"Sharpe E drawdown\", design §10):** "
            f"maxDD estratégia {_fmt(dd_s, pct=True)} vs benchmark {_fmt(dd_b, pct=True)} "
            f"→ {'OK (não pior)' if dd_s <= dd_b else 'REPROVADO (pior que o benchmark)'}",
        ]
    lines += [
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
        _BIAS_NOTE.get(hypothesis, "- Retorno **só-preço** (rota (b)): dividendos/JCP "
                                   f"omitidos; direção do viés NÃO documentada para "
                                   f"{hypothesis} em `report._BIAS_NOTE` — adicionar "
                                   "antes de interpretar o veredito (não herdar a nota "
                                   "de outra hipótese)."),
        "- Custo proporcional ao turnover real; execução na abertura de D+1.",
        f"- Veredito real da {hypothesis} exige COTAHIST **real** da B3 — sintético só "
        "valida a máquina.",
        "",
    ]
    return "\n".join(lines), s, b


def write_report(verdict, strat, bench, cfg, run_id=None, reports_dir=None,
                 hypothesis="H1"):
    """Grava o relatório Markdown e emite o evento de telemetria. Retorna o Path do MD."""
    body, s, b = build_markdown(verdict, strat, bench, cfg, run_id, hypothesis)

    rel = reports_dir or os.getenv(REPORTS_ENV) or cfg.get("data", {}).get("reports_dir", "reports")
    out_dir = pathlib.Path(rel)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = hypothesis.lower()
    fname = f"{tag}_verdict_{run_id or 'adhoc'}.md"
    out_path = out_dir / fname
    out_path.write_text(body, encoding="utf-8")

    # telemetria: metrics é SÓ numérico E finito (NaN viraria JSON inválido no
    # events.jsonl — json.dumps emite 'NaN', que nenhum parser estrito aceita).
    lo, hi = verdict.get("sharpe_diff_ci", (None, None))
    metrics = {"n_pregoes": verdict.get("n", 0), "psr": verdict.get("psr"),
               "ic_lower": lo, "ic_upper": hi,
               "dsr": verdict.get("dsr"), "sr0": verdict.get("sr0"),
               "sharpe_strat": s["sharpe"], "sharpe_bench": b["sharpe"],
               "maxdd_strat": s["max_drawdown"], "maxdd_bench": b["max_drawdown"]}
    metrics = {k: v for k, v in metrics.items() if _num(v) is not None}
    obs.emit_event(
        DOMAIN, f"{tag}_verdict", run_id=run_id, code_version=get_code_version(),
        metrics=metrics,
        metadata={"veredito": verdict.get("veredito", "n/d"),
                  "report_path": str(out_path.name)})
    return out_path
