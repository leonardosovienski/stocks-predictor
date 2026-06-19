"""Diagnóstico de SENSIBILIDADE ao viés de dividendos (rota-b, só-preço).

NÃO faz parte do pipeline congelado da H1. NÃO altera config.yaml, parâmetros
[H1-FROZEN], nem nenhum resultado histórico. É uma análise SEPARADA, somente-leitura,
que mede a sensibilidade do veredito da H1 a uma hipótese de diferencial de dividend
yield. Roda fora do experimento congelado — não introduz lookahead nem reescreve nada.

CONTEXTO
--------
O pipeline usa a rota-b (só-preço): dividendos/JCP NÃO são reincorporados. Isso
subestima o retorno TOTAL de AMBOS — estratégia (quintil de momentum) e benchmark
(universo equiponderado). O viés líquido sobre a DIFERENÇA de Sharpe depende do
diferencial de yield Δ = yield_estrategia − yield_benchmark.

Não há dado real de dividendos ingerido (a tabela `adjustments` está vazia), então
NÃO é possível MEDIR o viés — só fazer uma análise PARAMÉTRICA: varrer Δ e mostrar
onde (se em algum ponto) o veredito da H1 viraria. Quando o COTAHIST de proventos for
ingerido, troca-se esta varredura pelo Δ medido.

MODELO (1ª ordem)
-----------------
Retorno total ≈ retorno de preço + yield. Como a rota-b omite o yield de AMBOS, o que
move a DIFERENÇA de Sharpe é o EXCESSO de yield da estratégia sobre o benchmark (Δ).
Adiciona Δ/252 ao retorno DIÁRIO da estratégia. Aproximação suave (dividendos são
"lumpy", mas o impacto sobre o Sharpe anualizado é de 2ª ordem para esta sensibilidade).

Hipótese registrada no HANDOFF: a rota-b foi declarada FAVORÁVEL à estratégia — o que
implica a crença de que vencedores de momentum rendem MENOS dividendo que o universo
(Δ < 0): omitir dividendo machuca mais o benchmark, inflando a vantagem aparente. Esta
varredura quantifica em que magnitude de Δ essa crença muda o veredito.

n_boot reduzido (2000) por velocidade — isto é um diagnóstico, não o lacre da H1
(que usa n_boot=10000). A FORMA da curva de sensibilidade é o que importa.

Uso:
    python dividend_sensitivity.py
"""
import copy
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor")]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import backtest
import db
from config import load_config

# Varredura do diferencial anual de yield (estratégia − benchmark), em pontos percentuais.
GRID_ANUAL_PCT = [-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0]
N_BOOT_DIAG = 2000  # diagnóstico — não é o lacre (frozen usa 10000)


def _aplica_yield(strat, delta_anual_pct):
    """Adiciona o excesso de yield diário (Δ/252) a cada retorno da estratégia."""
    incremento = (delta_anual_pct / 100.0) / 252.0
    return [s + incremento for s in strat]


def run():
    cfg = load_config()
    conn = db.get_connection(ROOT / cfg["data"]["db_path"])

    print("=" * 70)
    print("SENSIBILIDADE AO VIÉS DE DIVIDENDOS (rota-b, só-preço) — DIAGNÓSTICO")
    print("=" * 70)
    print("Diagnóstico separado; NÃO altera a H1 congelada. Somente leitura.\n")

    strat, bench = backtest.walk_forward(conn, cfg)
    conn.close()
    n = len(strat)
    if n < 2 * cfg["bootstrap"]["block_length"]:
        print(f"Amostra curta demais (n={n}) — sem veredito. Ingerir mais histórico.")
        return

    # cfg do diagnóstico: n_boot reduzido, resto idêntico (não toca o config real)
    cfg_diag = copy.deepcopy(cfg)
    cfg_diag["bootstrap"]["n_boot"] = N_BOOT_DIAG

    print(f"walk-forward real: n={n} pregões pareados | n_boot diag={N_BOOT_DIAG}\n")
    print(f"{'Δ yield a.a.':>12} | {'PSR':>6} | {'IC95% ΔSharpe (lo, hi)':>26} | veredito")
    print("-" * 70)

    flip = None
    base_verdict = None
    for delta in GRID_ANUAL_PCT:
        strat_adj = _aplica_yield(strat, delta)
        v = backtest.judge(strat_adj, bench, cfg_diag)
        lo, hi = v["sharpe_diff_ci"]
        psr = v["psr"]
        comprovada = lo is not None and lo > 0
        marca = "  ← rota-b (Δ=0)" if delta == 0.0 else ""
        if delta == 0.0:
            base_verdict = comprovada
        lo_s = f"{lo:+.3f}" if lo is not None else "  None"
        hi_s = f"{hi:+.3f}" if hi is not None else "  None"
        psr_s = f"{psr:.3f}" if psr is not None else " None"
        print(f"{delta:>+10.1f}%  | {psr_s:>6} | ({lo_s:>9}, {hi_s:>9})       | "
              f"{'COMPROVADA' if comprovada else 'não comprovada'}{marca}")
        # detecta a fronteira onde o veredito vira em relação à base (Δ=0)
        if base_verdict is not None and comprovada != base_verdict and flip is None and delta != 0.0:
            flip = delta

    print("-" * 70)
    print("\nLEITURA:")
    print("  • Δ < 0  = estratégia rende MENOS dividendo que o benchmark → a rota-b")
    print("            (que omite dividendo de ambos) INFLA a vantagem aparente → favorável.")
    print("  • Δ > 0  = estratégia rende MAIS → a rota-b SUBESTIMA a estratégia → conservador.")
    if flip is not None:
        print(f"  • FRONTEIRA: o veredito vira por volta de Δ ≈ {flip:+.1f}% a.a. — o resultado")
        print(f"            NÃO é robusto a uma hipótese de dividendo dessa magnitude.")
    else:
        print("  • Em toda a faixa varrida [-4%, +4%] o veredito NÃO mudou — robusto ao")
        print("            viés de dividendos nessa magnitude (dado o IC atual).")
    print("\n  Yields típicos de dividendo na B3: ~2-6% a.a.; o diferencial entre um quintil")
    print("  de momentum e o universo raramente excede ±2-3% a.a. — use isso para julgar")
    print("  se a fronteira (se houver) está dentro de uma faixa plausível.")
    print("\n  NOTA: paramétrico (sem dado real de dividendos). Quando `adjustments` tiver")
    print("  proventos ingeridos, substituir a varredura pelo Δ medido por carteira.")


if __name__ == "__main__":
    run()
