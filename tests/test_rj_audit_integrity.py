"""Guard unsupported statistical inputs without changing the frozen primary test."""
import pytest

import rj_judge
import rj_judge_robust


def test_episode_duplicates_cannot_be_permuted_as_independent_companies():
    units = [('A', 1.0, 1), ('A', 2.0, 1), ('B', 0.0, 0), ('B', 0.1, 0)]
    with pytest.raises(ValueError, match='one observation per company'):
        rj_judge.permutation_pvalue(units, n_perm=10)


def test_joint_max_t_cannot_fall_back_to_unrelated_samples():
    first = [(str(i), float(i), int(i < 3)) for i in range(6)]
    other = [('different-'+t, v, g) for t, v, g in first]
    with pytest.raises(ValueError, match='identical ordered companies and labels'):
        rj_judge_robust.romano_wolf_stepdown({'drawdown': first, 'liquidity': other}, n_perm=10)


def test_joint_max_t_rejects_conflicting_labels_for_same_companies():
    first = [(str(i), float(i), int(i < 3)) for i in range(6)]
    other = [(t, v, 1-g) for t, v, g in first]
    with pytest.raises(ValueError, match='identical ordered companies and labels'):
        rj_judge_robust.romano_wolf_stepdown({'drawdown': first, 'liquidity': other}, n_perm=10)
