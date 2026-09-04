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
    "H10": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; SEM direção "
           "declarada a priori — mesma limitação de H7/H9 (a interseção de ROE alto "
           "e baixa alavancagem não tem relação estabelecida com política de "
           "dividendos nesta rodada). Viés não quantificado, registrado como "
           "limitação honesta (declarado no pré-registro da H10, 2026-09-04) — não "
           "inferir sinal. Mesmo embargo de divulgação de 90 dias por variável "
           "(`h10_factor.roe_disclosure_embargo_days`/`leverage_disclosure_embargo_days`), "
           "mesma fonte DFP/CVM de H7/H9.",
    "H17": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; direção do "
           "viés NÃO estabelecida — empresa com lucro lastreado em caixa tem mais "
           "folga para distribuir provento (o que PENALIZARIA a estratégia numa "
           "medida só-preço), mas a relação não foi verificada nesta amostra; "
           "registrada como limitação honesta, não como sinal. Mesmo embargo de "
           "divulgação de 90 dias sobre `ref_date` de H7/H9/H12/H13 "
           "(`h17_factor.disclosure_embargo_days`, mesma fonte DFP/CVM), mesma "
           "limitação de não cobrir a data REAL de entrega à CVM.\n"
           "- **Cobertura da DFC-MI não é universal**: companhia que publica a DFC "
           "pelo método DIRETO (DFC-MD), e ano cujo zip não traga o arquivo, ficam "
           "com `accruals` NULL e simplesmente FORA do sinal "
           "(`ingest_cvm.ingest_dfp_year` avisa e segue). O universo efetivo da H17 "
           "pode portanto ser MENOR que o de H7/H9/H12/H13 — comparar contagem de "
           "papéis por rebalance antes de interpretar o veredito.",
    "H18": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; aqui a "
           "direção do viés É conhecida e PENALIZA a estratégia: ações de valor "
           "(E/P alto) têm sistematicamente MAIOR dividend yield, e a rota (b) "
           "descarta justamente esse componente do retorno. O teste é portanto "
           "CONSERVADOR — um veredito NOT_SUPPORTED aqui não separa 'o fator não "
           "funciona' de 'o retorno do fator está no provento que esta rota não "
           "mede'. Declarado no pré-registro (2026-09-04), não descoberto depois.\n"
           "- **Duas fontes com datas próprias**: lucro vem da DFP, quantidade de "
           "ações vem do FRE — formulários distintos, cada um com sua `ref_date` e "
           "seu embargo, deliberadamente NÃO casados à força "
           "(`ingest_cvm.ingest_fre_shares_year`). A capitalização de mercado usa a "
           "contagem de ações mais recente JÁ DIVULGADA em `asof`, que pode estar "
           "defasada de uma emissão/recompra recente — limitação real da "
           "granularidade anual do FRE, registrada, não corrigida por estimativa.\n"
           "- **Preço CRU, não ajustado**, no denominador do múltiplo (ver "
           "`factor._price_at`): multiplicar a série retro-ajustada pela contagem de "
           "ações vigente daria uma capitalização que nunca existiu.",
    "H19": "- Retorno **só-preço** (rota (b)): mesma direção de viés da H18 e pela "
           "mesma razão (B/M alto e E/P alto selecionam carteiras muito "
           "sobrepostas, ambas com yield acima da média) — teste CONSERVADOR, "
           "declarado no pré-registro.\n"
           "- Mesmas duas limitações de fonte da H18 (DFP e FRE com datas próprias "
           "não casadas à força; preço CRU no múltiplo).\n"
           "- **Patrimônio líquido contábil não é valor de reposição**: empresas "
           "com muito intangível não capitalizado (serviços, tecnologia) aparecem "
           "com B/M estruturalmente baixo sem estarem 'caras'. É a crítica clássica "
           "ao B/M e vale aqui igual; o veredito mede o fator COMO DEFINIDO, não "
           "'valor' em abstrato.",
    "H11": "- Retorno **TOTAL** (rota (a), 2026-09-04): proventos "
           "REINVESTIDOS via `adjust.total_return_series`, ao contrário de "
           "H1-H10 (só-preço). **Cobertura de proventos parcial**: a fonte "
           "(CVM/FRE, `dividends`) só é confiável 2018-2022 (achado "
           "registrado no HANDOFF 2026-09-04 — 2023-2026 têm quase zero "
           "cobertura) — por isso a janela da H11 é restrita a 2018-2022 "
           "(`h11_backtest.test_start/test_end`), não os anos completos de "
           "H1-H10. Duas aproximações do dado de provento em si (não "
           "escondidas): valor por ação médio ON+PN (não por classe "
           "específica) e data de PAGAMENTO como proxy de data-ex (a CVM "
           "não expõe a data-ex real neste dataset).",
    "H12": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; SEM direção "
           "declarada a priori — a relação entre margem líquida e política de "
           "dividendos de empresas B3 não foi estabelecida nesta rodada. Viés "
           "não quantificado, registrado como limitação honesta (declarado no "
           "pré-registro da H12, 2026-09-04) — não inferir sinal. Mesmo embargo "
           "de divulgação de 90 dias sobre `ref_date` de H7/H9/H10 "
           "(`h12_factor.disclosure_embargo_days`, mesma fonte DFP/CVM).",
    "H13": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; SEM direção "
           "declarada a priori — a relação entre crescimento de receita e "
           "política de dividendos de empresas B3 não foi estabelecida nesta "
           "rodada. Viés não quantificado, registrado como limitação honesta "
           "(declarado no pré-registro da H13, 2026-09-04) — não inferir sinal. "
           "Mesmo embargo de divulgação de 90 dias de H7/H9/H10/H12 "
           "(`h13_factor.disclosure_embargo_days`, mesma fonte DFP/CVM). "
           "Adicionalmente: granularidade ANUAL da DFP (não ITR trimestral) — "
           "as duas linhas mais recentes elegíveis usadas no cálculo de "
           "crescimento nem sempre estão exatamente 12 meses de distância "
           "se houver ano com dado faltante (ver `factor.revenue_growth_signals`).",
    "H14": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; papel "
           "próximo da máxima de 52 semanas tende a ter yield mais BAIXO "
           "(preço subiu recentemente), na mesma direção do viés já declarado "
           "no pré-registro da H1 pra momentum — mecanismo semelhante, não "
           "quantificado aqui separadamente.",
    "H15": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos; SEM "
           "direção declarada a priori — a relação entre surto de volume e "
           "política de dividendos de empresas B3 não foi estabelecida nesta "
           "rodada. Viés não quantificado, registrado como limitação honesta "
           "(declarado no pré-registro da H15, 2026-09-04) — não inferir sinal.",
    "H16": "- Retorno **só-preço** (rota (b)): dividendos/JCP omitidos — "
           "irrelevante pro mecanismo desta hipótese (TIMING, não seleção "
           "de papel; estratégia e benchmark usam o MESMO universo, "
           "diferem só em quais dias contam o retorno). Custo simplificado: "
           "cobra 1 perna (`one_way`) em cada transição cash/posicionado, "
           "ignora turnover de composição do universo entre rebalances "
           "mensais (ver `backtest.run_h16`) — aproximação declarada, não "
           "escondida.",
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
