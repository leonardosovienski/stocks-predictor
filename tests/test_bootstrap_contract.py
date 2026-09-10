"""The typed adapter must preserve the frozen bootstrap's discarded samples."""
from predictor_core.measurement.bootstrap import bootstrap_ci
from stocks_predictor.rj_judge import family_verdict, _mean_diff


def test_typed_bootstrap_preserves_none_sample_semantics():
    units = [('A', 4.0, 1), ('B', 2.0, 0), ('C', 1.0, 0), ('D', 3.0, 0)]
    settings = {'bootstrap_scheme': 'cluster', 'n_boot': 256, 'confidence': 0.95, 'seed': 42}
    low, high, distribution = bootstrap_ci(
        units, _mean_diff, scheme='cluster', n_boot=256, confidence=0.95,
        seed=42, cluster_key=lambda unit: unit[0])
    assert 0 < len(distribution) < 256  # This sample really exercises invalid resamples.
    verdict = family_verdict(units, 'positive', {'judge': settings})
    assert verdict['ci'] == (low, high)
    assert verdict['effect'] == 2.0
