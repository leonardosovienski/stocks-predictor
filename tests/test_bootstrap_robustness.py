"""Robustez do block_bootstrap_ci canônico: descarte de reamostras degeneradas (None).

A LENTE 2 do pedágio precisa sobreviver a estatísticas que retornam None em reamostras
degeneradas (ex.: Spearman sobre um bloco de variância nula) — senão o sort() quebraria
silenciosamente. Teste DEDICADO da garantia (a primitiva mais importante da plataforma)."""
from predictor_core.stats import block_bootstrap_ci


def test_drops_none_resamples_keeps_the_rest():
    """None é descartado; o IC sai dos não-None restantes."""
    series = list(range(40))
    calls = {"n": 0}

    def stat(resampled):           # devolve None em metade das chamadas (determinístico)
        calls["n"] += 1
        return None if calls["n"] % 2 == 0 else sum(resampled) / len(resampled)

    lo, hi, dist = block_bootstrap_ci(series, stat, block_length=5, n_boot=100, seed=1)
    assert len(dist) == 50, f"esperava 50 não-None, veio {len(dist)}"
    assert lo is not None and hi is not None and lo <= hi


def test_all_none_returns_empty_not_crash():
    """Todas as reamostras degeneradas => (None, None, []) em vez de estourar no sort()."""
    series = list(range(40))
    assert block_bootstrap_ci(series, lambda r: None, block_length=5,
                              n_boot=50, seed=1) == (None, None, [])


def test_no_none_keeps_all_nboot():
    """Retrocompat: estatística que nunca dá None mantém n_boot inteiro."""
    series = list(range(40))
    _, _, dist = block_bootstrap_ci(series, lambda r: sum(r) / len(r),
                                    block_length=5, n_boot=100, seed=1)
    assert len(dist) == 100
