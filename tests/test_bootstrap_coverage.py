"""Aceite do bootstrap (design §10/M5, propriedades a-e) — mecânica, não leitura de código.

CALIBRAÇÃO MEDIDA (2026-07-02, experimentos com 500-1000 séries por ponto):
o intervalo PERCENTILE cobre ~92% quando o nominal é 95% (n≈1755, AR(1) phi 0.15-0.30,
L 10-84, n_boot 200-1000, qualquer construção percentile/basic/simétrica) —
anticonservador; a limitação é do método, não da geometria. O intervalo STUDENTIZED
(bootstrap-t com batch means, vendor 0.7.2) cobre 93.5-93.8% nas mesmas condições e é
o que o pedágio deve usar. O aceite (a) roda com studentized; o percentile permanece
para diagnóstico de geometria (controle negativo).
"""
import math
import random

import pytest

from predictor_core.stats import _geom_sample, block_bootstrap_ci, ci_mean

SEED = 20260702
N_RAW = 1950          # -> 1755 pós burn-in: a escala do veredito real (2018-2024)
PHI = 0.3
BLOCK = 21            # o bloco da H1


def _ar1(rng, n, phi, sigma=1.0, mu=0.0):
    x = [mu]
    for _ in range(n - 1):
        x.append(mu + phi * (x[-1] - mu) + rng.gauss(0, sigma))
    return x[int(n * 0.1):]


def _mean(xs):
    return sum(xs) / len(xs)


@pytest.mark.slow
def test_a_coverage_ar1_studentized_within_2pp():
    """(a) ≥500 séries AR(1) com média conhecida: IC 95% studentizado cobre a verdade
    em 95%±2pp. O percentile FALHA este aceite (~92%, medido) — por isso o pedágio
    usa studentized."""
    rng = random.Random(SEED)
    n_series, hits = 500, 0
    for i in range(n_series):
        series = _ar1(rng, N_RAW, PHI)
        lo, hi, _ = block_bootstrap_ci(series, _mean, block_length=BLOCK,
                                       n_boot=400, seed=SEED + i,
                                       method="stationary", interval="studentized")
        if lo <= 0.0 <= hi:
            hits += 1
    cov = hits / n_series
    assert 0.93 <= cov <= 0.97, f"cobertura studentized fora de 95%±2pp: {cov:.3f}"


@pytest.mark.slow
def test_a_control_wrong_geometry_fails_detectably():
    """(a, controle negativo) geometria errada (bloco 1 = iid) sobre a MESMA série
    dependente sub-cobre de forma detectável no percentile (medido ~81-86%)."""
    rng = random.Random(SEED)
    n_series, hits = 150, 0
    for i in range(n_series):
        series = _ar1(rng, N_RAW, PHI)
        lo, hi, _ = block_bootstrap_ci(series, _mean, block_length=1,
                                       n_boot=200, seed=SEED + i,
                                       method="stationary", interval="percentile")
        if lo <= 0.0 <= hi:
            hits += 1
    cov = hits / n_series
    assert cov < 0.90, f"geometria iid deveria sub-cobrir detectavelmente: {cov:.3f}"


def test_b_mean_block_length_matches_L():
    """(b) comprimento médio empírico dos blocos ≈ L (Geométrica(1/L) => média L)."""
    rng = random.Random(SEED)
    L = 21
    draws = [_geom_sample(rng, 1.0 / L) for _ in range(50_000)]
    emp = sum(draws) / len(draws)
    assert abs(emp - L) / L < 0.03, f"comprimento médio {emp:.2f} != L={L}"


def test_c_resampled_indices_uniform():
    """(c) distribuição dos índices reamostrados ~uniforme (wrap circular: sem
    subamostragem nas bordas). A série É a lista de índices; a 'estatística' conta."""
    n, n_boot = 200, 300
    counts = [0] * n

    def counting_stat(resampled):
        for idx in resampled:
            counts[idx] += 1
        return 0.0

    block_bootstrap_ci(list(range(n)), counting_stat, block_length=10,
                       n_boot=n_boot, seed=SEED, method="stationary")
    expected = n_boot  # n_boot * n draws / n índices
    lo_c, hi_c = min(counts), max(counts)
    assert lo_c > 0.6 * expected and hi_c < 1.4 * expected, (
        f"índices não-uniformes: min={lo_c}, max={hi_c}, esperado≈{expected} "
        f"(bootstrap não-circular subamostra as bordas — pegaria aqui)")


def test_d_reproducible_with_seed():
    """(d) mesma seed => mesmo IC e mesma distribuição; seed diferente => distinta."""
    rng = random.Random(SEED)
    series = _ar1(rng, 400, PHI)
    a = block_bootstrap_ci(series, _mean, block_length=10, n_boot=200, seed=7,
                           method="stationary", interval="studentized")
    b = block_bootstrap_ci(series, _mean, block_length=10, n_boot=200, seed=7,
                           method="stationary", interval="studentized")
    c = block_bootstrap_ci(series, _mean, block_length=10, n_boot=200, seed=8,
                           method="stationary", interval="studentized")
    assert a == b, "mesma seed deveria reproduzir exatamente"
    assert a[2] != c[2], "seeds diferentes deveriam gerar distribuições diferentes"


def test_e_iid_underestimates_width_block_does_not():
    """(e) série autocorrelacionada onde o percentile iid subestima a largura do IC
    e o block a acerta (complementa test_m0_genesis, aqui com o studentized)."""
    rng = random.Random(SEED)
    series = _ar1(rng, 700, 0.6)
    lo_i, hi_i = ci_mean(series, n_boot=400, seed=SEED)
    lo_b, hi_b, _ = block_bootstrap_ci(series, _mean, block_length=21, n_boot=400,
                                       seed=SEED, method="stationary",
                                       interval="studentized")
    assert (hi_b - lo_b) > 1.3 * (hi_i - lo_i), (
        f"block studentized ({hi_b - lo_b:.4f}) deveria ser bem mais largo que "
        f"iid percentile ({hi_i - lo_i:.4f}) sob AR(1) phi=0.6")


def test_studentized_raises_on_degenerate_series():
    """Fail-loud: série constante não é studentizável — ValueError, não IC lixo."""
    with pytest.raises(ValueError):
        block_bootstrap_ci([1.0] * 100, _mean, block_length=5, n_boot=50,
                           interval="studentized")
