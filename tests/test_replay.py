"""Anti-lookahead estrutural ('feed, don't query') — contrato do Core compartilhado."""
import pytest

from predictor_core.replay import LookaheadError, PastView, replay


def test_replay_feeds_growing_past_once_per_step():
    seen = []
    replay([10, 20, 30], lambda p: seen.append((p.asof_index, len(p), p.latest)))
    assert seen == [(0, 1, 10), (1, 2, 20), (2, 3, 30)]


def test_replay_collects_nonnull_decisions_as_ledger():
    ledger = replay([1, 2, 3, 4], lambda p: p.latest if p.latest % 2 == 0 else None)
    assert ledger == [2, 4]


def test_pastview_allows_past_and_present():
    # Core 2.3 recebe somente o prefixo já observado; o futuro nem existe na view.
    pv = PastView((1, 2, 3))
    assert pv.latest == 3 and len(pv) == 3
    assert pv[0] == 1 and pv[2] == 3
    assert list(pv) == [1, 2, 3]


def test_pastview_blocks_future_index():
    pv = PastView((1, 2, 3))
    with pytest.raises(LookaheadError):
        _ = pv[3]
    with pytest.raises(LookaheadError):
        _ = pv[4]


def test_pastview_slice_clamps_no_leak():
    pv = PastView((1, 2, 3))
    assert pv[:] == (1, 2, 3)
    assert pv[:100] == (1, 2, 3)


def test_replay_handler_cannot_peek_future():
    """Killer test: um handler que tenta olhar o amanhã levanta LookaheadError."""
    with pytest.raises(LookaheadError):
        replay([1, 2, 3], lambda p: p[p.asof_index + 1])
