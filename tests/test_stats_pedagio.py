"""Pedágio de duas lentes — PSR (Lente 1) + block bootstrap pareado (Lente 2).

Aceite mecânico (propriedades, não leitura de código). A propriedade-chave nova é a
cobertura PAREADA: reamostrar unidades (linhas) preserva a cross-correlação — um
bootstrap que reamostra colunas separado FALHA o teste de invariante de forma
detectável.
"""
import random

from predictor_core.measurement.bootstrap import bootstrap_ci as block_bootstrap_ci
from predictor_core.measurement.stats import probabilistic_sharpe_ratio as psr


# --- LENTE 1: PSR -----------------------------------------------------------

def test_psr_bounded_0_1():
    rng = random.Random(1)
    r = [rng.gauss(0.001, 0.01) for _ in range(250)]
    assert 0.0 <= psr(r) <= 1.0


def test_psr_too_few_points_is_nan():
    assert psr([0.01, 0.02]) != psr([0.01, 0.02])  # NaN != NaN


def test_psr_strong_positive_beats_zero_null():
    """Sharpe por-período alto e n grande => alta confiança contra o nulo 0."""
    rng = random.Random(2)
    r = [rng.gauss(0.05, 0.05) for _ in range(500)]  # SR ~1.0 por período
    assert psr(r, 0.0) > 0.95


def test_psr_monotonic_in_benchmark():
    """Quanto mais alta a régua (benchmark), menor a P de batê-la."""
    rng = random.Random(3)
    r = [rng.gauss(0.02, 0.05) for _ in range(300)]
    assert psr(r, 0.0) > psr(r, 0.3)


def test_psr_more_data_raises_confidence():
    """Mesmo Sharpe, mais amostra => PSR maior (n-1 no denominador)."""
    rng = random.Random(11)
    short = [rng.gauss(0.02, 0.05) for _ in range(60)]
    rng = random.Random(11)
    long = [rng.gauss(0.02, 0.05) for _ in range(600)]
    assert psr(long, 0.0) > psr(short, 0.0)


def test_psr_penalizes_fat_left_tail():
    """Cauda esquerda gorda (assimetria negativa) abaixa o PSR — o ponto do PSR."""
    rng = random.Random(4)
    base = [rng.gauss(0.02, 0.04) for _ in range(400)]
    skewed = base[:]
    for i in range(0, len(skewed), 40):
        skewed[i] -= 0.20  # injeta saltos negativos
    assert psr(skewed, 0.0) < psr(base, 0.0)


# --- LENTE 2: block bootstrap pareado --------------------------------------

def _mean(u):
    return sum(u) / len(u)


def _mean_diff(u):
    return sum(x[0] for x in u) / len(u) - sum(x[1] for x in u) / len(u)


def test_paired_bootstrap_runs_with_tuples():
    rng = random.Random(5)
    a = [rng.gauss(0, 0.01) for _ in range(300)]
    b = [rng.gauss(0, 0.01) for _ in range(300)]
    lo, hi, dist = block_bootstrap_ci(list(zip(a, b)), _mean_diff, seed=7)
    assert lo <= hi and len(dist) == 10_000


def test_paired_bootstrap_reproducible():
    rng = random.Random(6)
    a = [rng.gauss(0, 0.01) for _ in range(200)]
    b = [rng.gauss(0, 0.01) for _ in range(200)]
    r1 = block_bootstrap_ci(list(zip(a, b)), _mean_diff, seed=13)
    r2 = block_bootstrap_ci(list(zip(a, b)), _mean_diff, seed=13)
    assert r1[:2] == r2[:2]


def test_paired_resampling_preserves_cross_correlation():
    """INVARIANTE: reamostrar UNIDADES (pares) junto preserva a cross-correlação.

    Duas séries que partilham um fator comum autocorrelacionado têm uma DIFERENÇA
    de variância ínfima — o fator cancela. O IC pareado da diferença deve então ser
    MAIS ESTREITO que o IC de uma série isolada. Isso só acontece com reamostragem
    conjunta (linhas): se as colunas fossem reamostradas separado, o fator NÃO
    cancelaria e o IC da diferença explodiria. É o teste que mata o bug clássico.
    """
    rng = random.Random(8)
    factor, s = [], 0.0
    for _ in range(400):
        s = 0.8 * s + rng.gauss(0, 0.01)        # fator comum autocorrelacionado
        factor.append(s)
    a = [f + rng.gauss(0, 0.0005) for f in factor]
    b = [f + rng.gauss(0, 0.0005) for f in factor]  # quase idêntica a `a`

    width_a = (lambda lo, hi, _: hi - lo)(*block_bootstrap_ci(a, _mean, block_length=21, seed=9))
    width_diff = (lambda lo, hi, _: hi - lo)(
        *block_bootstrap_ci(list(zip(a, b)), _mean_diff, block_length=21, seed=9))

    assert width_diff < width_a, (
        f"IC pareado da diferença ({width_diff:.6g}) deveria ser mais estreito que "
        f"o IC da série isolada ({width_a:.6g}) — o fator comum cancela só com "
        f"reamostragem conjunta de unidades")
