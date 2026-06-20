"""Portão de aceite da LENTE 2 (DESIGN §M5a) — cobertura empírica do IC.

O design exige que o IC95% cubra a verdade em ~95% sobre séries AR(1). A régua
PERCENTIL clássica foi medida como LIBERAL (sub-cobre); a `calibrated_ci` (IC-t por
blocos) corrige isso. Este teste é a barreira que faltava: roda um Monte Carlo CURTO
(rápido para a suíte) e exige que (a) a calibrada cubra perto de 95% e (b) seja
estritamente melhor que o percentil sob autocorrelação.

Curto de propósito (n_boot e sims reduzidos) — o estudo completo vive em
`lens2_calibration_study.py` na raiz do projeto. Aqui só garantimos a não-regressão.
"""
import random

from predictor_core.stats import calibrated_ci, block_bootstrap_ci


def _ar1(n, phi, rng, burn=200):
    x = 0.0
    for _ in range(burn):
        x = phi * x + rng.gauss(0, 1.0)
    out = []
    for _ in range(n):
        x = phi * x + rng.gauss(0, 1.0)
        out.append(x)
    return out


def _coverage(method_call, phi, n=160, n_sims=200, seed0=1234):
    rng = random.Random(seed0)
    hits = 0
    for i in range(n_sims):
        s = _ar1(n, phi, rng)
        lo, hi, _ = method_call(s, i)
        if lo is not None and lo <= 0.0 <= hi:
            hits += 1
    return hits / n_sims


_MEAN = lambda z: sum(z) / len(z)


def test_calibrated_ci_covers_near_95_under_autocorrelation():
    """A régua calibrada cobre ~95% (>=0.92) mesmo com autocorrelação moderada-alta."""
    cov = _coverage(lambda s, i: calibrated_ci(s, _MEAN, n_boot=400, seed=i), phi=0.6)
    assert cov >= 0.92, f"calibrated_ci sub-cobriu: {cov:.1%} (esperado ~95%)"


def test_calibrated_beats_percentile_under_autocorrelation():
    """A calibrada cobre MAIS que o percentil clássico sob autocorrelação (corrige a liberalidade)."""
    cal = _coverage(lambda s, i: calibrated_ci(s, _MEAN, n_boot=400, seed=i), phi=0.6)
    perc = _coverage(
        lambda s, i: block_bootstrap_ci(s, _MEAN, block_length=21, n_boot=400, seed=i),
        phi=0.6)
    assert cal > perc, f"calibrada ({cal:.1%}) deveria cobrir mais que percentil ({perc:.1%})"


def test_percentile_is_liberal_documented_baseline():
    """Documenta a régua ATUAL: o percentil sub-cobre sob autocorrelação (< 0.95)."""
    perc = _coverage(
        lambda s, i: block_bootstrap_ci(s, _MEAN, block_length=21, n_boot=400, seed=i),
        phi=0.6)
    assert perc < 0.95, f"esperava percentil liberal (<95%), veio {perc:.1%}"
