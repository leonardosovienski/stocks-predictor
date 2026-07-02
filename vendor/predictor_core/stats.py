"""predictor-core.stats — estimadores estatísticos: ci_mean (iid) e block bootstrap."""
import math
import random
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def ci_mean(data: list[float], confidence: float = 0.95,
            n_boot: int = 10_000, seed: int = 42) -> tuple[float, float]:
    """IC bootstrap iid para a média. INVÁLIDO para séries autocorrelacionadas — use block_bootstrap."""
    rng = random.Random(seed)
    n = len(data)
    means = sorted(
        sum(rng.choices(data, k=n)) / n
        for _ in range(n_boot)
    )
    alpha = (1 - confidence) / 2
    return _quantile(means, alpha), _quantile(means, 1 - alpha)


def _quantile(sorted_xs: list, q: float) -> float:
    """Quantil por interpolação linear (tipo 7) sobre lista JÁ ORDENADA.

    Substitui a indexação truncada `xs[int(q*m)]`: o truncamento enviesa os
    extremos do IC (meio order-statistic por cauda) e degrada a cobertura
    empírica do bootstrap — medido no domínio stocks (teste de cobertura M5)."""
    m = len(sorted_xs)
    if m == 1:
        return sorted_xs[0]
    pos = q * (m - 1)
    i = int(pos)
    frac = pos - i
    if i + 1 < m:
        return sorted_xs[i] + frac * (sorted_xs[i + 1] - sorted_xs[i])
    return sorted_xs[-1]


def _ranks(values: list[float]) -> list[float]:
    """Ranks médios (1-based), empates pela média."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float | None:
    """Correlação de Spearman = Pearson sobre os ranks. None se n<3 ou variância nula.
    Primitiva de validação da plataforma (promovida do previsao-cripto)."""
    n = len(x)
    if n < 3:
        return None
    rx, ry = _ranks(x), _ranks(y)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx)
    vy = sum((b - my) ** 2 for b in ry)
    if vx == 0 or vy == 0:
        return None
    return cov / ((vx * vy) ** 0.5)


def _batch_se(units: list, statistic: Callable[[list], float],
              n_batches: int) -> float | None:
    """Erro-padrão da estatística por BATCH MEANS: estatística em n_batches segmentos
    contíguos, sd/sqrt(k). Segmentos longos (>> comprimento de correlação) tornam a
    estimativa robusta à dependência serial. None se < 2 segmentos válidos."""
    n = len(units)
    bl = n // n_batches
    if bl < 2:
        return None
    vals = []
    for i in range(n_batches):
        s = statistic(units[i * bl:(i + 1) * bl])
        if s is not None and math.isfinite(s):
            vals.append(s)
    k = len(vals)
    if k < 2:
        return None
    m = sum(vals) / k
    var = sum((v - m) ** 2 for v in vals) / (k - 1)
    return math.sqrt(var / k)


def block_bootstrap_ci(
    series: list,
    statistic: Callable[[list], float],
    block_length: int = 21,
    n_boot: int = 10_000,
    confidence: float = 0.95,
    seed: int = 42,
    method: str = "moving",
    interval: str = "percentile",
    n_batches: int = 10,
) -> tuple[float, float, list[float]]:
    """IC bootstrap em blocos para estatística arbitrária sobre série temporal.

    É a LENTE 2 do pedágio: não-paramétrica, assume o fardo da autocorrelação
    (blocos) e da dependência cross (reamostragem PAREADA) que o PSR ignora.

    `series` é uma lista ORDENADA NO TEMPO. Cada unidade pode ser um escalar
    (ex.: CLV por aposta) OU uma tupla pareada (ex.: (ret_estrategia, ret_benchmark)
    ou (score, retorno_fwd)) — `statistic` desempacota a unidade. Exemplos:
        block_bootstrap_ci(clv, mean)                                    # escalar
        block_bootstrap_ci(list(zip(a, b)),                              # pareado
            lambda u: sharpe([x[0] for x in u]) - sharpe([x[1] for x in u]))

    INVARIANTE DE CORREÇÃO: reamostra BLOCOS de UNIDADES (linhas no tempo), NUNCA
    colunas independentes. É isso que preserva a cross-correlação (dentro da
    unidade) E a autocorrelação (entre unidades do bloco). Reamostrar colunas
    separado infla o IC da diferença e fabrica "inconclusivo" falso.

    method='moving'    — Moving Block Bootstrap (blocos fixos de tamanho block_length)
    method='stationary' — Stationary Bootstrap (comprimentos ~ Geométrica(p=1/block_length),
                          índices circulares conforme Politis & Romano 1994)

    interval='percentile'  — quantis da distribuição bootstrap (histórico). MEDIDO no
        domínio stocks (2026-07-02, 500-1000 séries AR(1), n≈1755): cobre ~92% quando
        o nominal é 95% — anticonservador, infla falso-positivo. Mantido por
        retrocompatibilidade e para diagnóstico de geometria.
    interval='studentized' — bootstrap-t SIMÉTRICO: t* = (θ*-θ̂)/se*, com se por batch
        means (`n_batches` segmentos); IC = θ̂ ± q_conf(|t*|)·se_hat. Acurácia de
        segunda ordem; MEDIDO: ~93,5-93,8% de cobertura nas mesmas condições —
        o default recomendado para julgamento de hipótese (pedágio Lente 2).

    Retorna (lo, hi, distribuição bootstrap de θ*).
    """
    if interval not in ("percentile", "studentized"):
        raise ValueError(f"interval desconhecido: {interval!r}")
    rng = random.Random(seed)
    n = len(series)
    if n < block_length:
        raise ValueError(f"series length {n} < block_length {block_length}")

    theta_hat = se_hat = None
    if interval == "studentized":
        theta_hat = statistic(list(series))
        se_hat = _batch_se(list(series), statistic, n_batches)
        if theta_hat is None or not math.isfinite(theta_hat) \
                or se_hat is None or se_hat <= 0:
            raise ValueError(
                "interval='studentized': estatística ou SE por batch means degenerados "
                "na série original — não há como studentizar; use 'percentile' ou "
                "revise a estatística")

    p = 1.0 / block_length  # parâmetro geométrica para stationary bootstrap

    boot_stats: list[float] = []
    t_stats: list[float] = []
    for _ in range(n_boot):
        resampled: list = []
        while len(resampled) < n:
            start = rng.randrange(n)
            if method == "stationary":
                length = _geom_sample(rng, p)
            else:
                length = block_length
            for j in range(length):
                if len(resampled) >= n:
                    break
                resampled.append(series[(start + j) % n])
        resampled = resampled[:n]
        stat = statistic(resampled)
        if stat is None:            # reamostra degenerada (ex.: Spearman sem variância) cai fora
            continue
        boot_stats.append(stat)
        if interval == "studentized":
            se_star = _batch_se(resampled, statistic, n_batches)
            if se_star is not None and se_star > 0:
                t_stats.append((stat - theta_hat) / se_star)

    if not boot_stats:
        return None, None, []
    boot_stats.sort()

    if interval == "studentized":
        if not t_stats:
            raise ValueError("interval='studentized': nenhuma reamostra studentizável")
        abs_t = sorted(abs(t) for t in t_stats)
        half = _quantile(abs_t, confidence) * se_hat
        return theta_hat - half, theta_hat + half, boot_stats

    alpha = (1 - confidence) / 2
    lo = _quantile(boot_stats, alpha)
    hi = _quantile(boot_stats, 1 - alpha)
    return lo, hi, boot_stats


def spearman_block_ci(pairs, *, block_length: int = 5, n_boot: int = 10_000,
                      confidence: float = 0.95, seed: int = 42):
    """(rho_pontual, lo, hi) do Spearman entre pares (x, y) ORDENADOS NO TEMPO.

    Reamostra os pares em blocos (preserva a dependência serial de horizontes
    sobrepostos). (None, None, None) se n<4. Adapta block_length a amostras pequenas.
    Promovido do previsao-cripto: agora é primitiva canônica de significância."""
    n = len(pairs)
    if n < 4:
        return None, None, None
    bl = max(1, min(block_length, n // 3))
    rho = spearman([p[0] for p in pairs], [p[1] for p in pairs])
    lo, hi, _ = block_bootstrap_ci(
        pairs, lambda u: spearman([p[0] for p in u], [p[1] for p in u]),
        block_length=bl, n_boot=n_boot, confidence=confidence, seed=seed)
    return rho, lo, hi


def _geom_sample(rng: random.Random, p: float) -> int:
    """Amostra de distribuição Geométrica(p) — mínimo 1."""
    k = 1
    while rng.random() > p:
        k += 1
    return k


def sharpe(returns: list[float], periods_per_year: int = 252) -> float:
    """Sharpe anualizado (assume risk-free=0). Série constante ≠ 0 → sinal do retorno."""
    if len(returns) < 2:
        return float("nan")
    n = len(returns)
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if var == 0:
        # série constante: retorno positivo → +inf, negativo → -inf, zero → nan
        if mean > 0:
            return float("inf")
        if mean < 0:
            return float("-inf")
        return float("nan")
    std = math.sqrt(var)
    return (mean / std) * math.sqrt(periods_per_year)


def sortino(returns: list[float], periods_per_year: int = 252) -> float:
    """Sortino anualizado (assume MAR=0)."""
    if len(returns) < 2:
        return float("nan")
    n = len(returns)
    mean = sum(returns) / n
    downside_sq = sum(r ** 2 for r in returns if r < 0)
    downside_std = math.sqrt(downside_sq / n)
    if downside_std == 0:
        return float("nan")
    return (mean / downside_std) * math.sqrt(periods_per_year)


def max_drawdown(cum_returns: list[float]) -> float:
    """Max drawdown sobre série de retornos acumulados (equity curve)."""
    peak = float("-inf")
    mdd = 0.0
    for v in cum_returns:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0.0
        if dd > mdd:
            mdd = dd
    return mdd


# --- LENTE 1 do pedágio: Probabilistic Sharpe Ratio (closed-form, não-normalidade) ---

def _standardized_moments(data: list) -> tuple:
    """(n, média, desvio populacional, assimetria, curtose NÃO-excesso).

    Curtose normal -> 3 (convenção de Bailey & López de Prado, não a de excesso).
    """
    n = len(data)
    mean = sum(data) / n
    m2 = sum((x - mean) ** 2 for x in data) / n
    if m2 == 0:
        return n, mean, 0.0, 0.0, 3.0
    m3 = sum((x - mean) ** 3 for x in data) / n
    m4 = sum((x - mean) ** 4 for x in data) / n
    return n, mean, m2 ** 0.5, m3 / m2 ** 1.5, m4 / m2 ** 2


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def probabilistic_sharpe_ratio(returns: list, benchmark_sharpe: float = 0.0) -> float:
    """PSR — Probabilistic Sharpe Ratio (Bailey & López de Prado, 2012).

    Devolve P(Sharpe verdadeiro > benchmark_sharpe), corrigindo por assimetria,
    curtose e tamanho da amostra — pune estratégias que inflam o Sharpe com cauda
    gorda (risco de ruína). LENTE 1 do pedágio: fórmula fechada, custo ~zero,
    primeira barreira ANTES do block bootstrap pesado.

    `benchmark_sharpe` está em unidades POR-PERÍODO (o mesmo Sharpe não-anualizado
    que esta função observa internamente). Default 0.0 = nulo "sem skill".

    LIMITE: assume i.i.d. — NÃO corrige autocorrelação. Por isso existe a LENTE 2
    (block_bootstrap_ci pareado), que assume esse fardo. As duas são complementares.
    Verificado contra a implementação do QuantConnect/LEAN (Common/Statistics/Statistics.cs).
    """
    if len(returns) < 3:
        return float("nan")
    n, mean, std, skew, kurt = _standardized_moments(returns)
    if std == 0:
        return float("nan")
    sr = mean / std  # Sharpe observado por período (não anualizado)
    variance = (1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr * sr) / (n - 1)
    if variance <= 0:
        return float("nan")
    return _normal_cdf((sr - benchmark_sharpe) / variance ** 0.5)
