"""Walk-forward com separação temporal estrita.

Cada divisão tem treino ``[train_start, train_end]`` e teste ``[test_start, test_end]`` (índices de pregão) com
``train_end + horizon + embargo < test_start``: o horizonte do rótulo e o embargo nunca tocam o teste. O ajuste
recebe só a ``PITView`` de ``train_end`` (nada depois do fechamento de ``train_end`` existe para ele). Os testes
são contíguos, não se sobrepõem e são avaliados num único backtest contínuo, em que cada decisão usa o modelo
da divisão que contém o pregão de EXECUÇÃO — sempre ajustado antes do sinal.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass

from .dataset import PITDataset, PITView
from .engine import BacktestResult, DecisionContext, ProtocolConfig, Strategy, run_backtest


class LeakageError(ValueError):
    """Divisões sem separação estrita entre treino (+ horizonte + embargo) e teste."""


@dataclass(frozen=True)
class Split:
    index: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    horizon: int
    embargo: int

    def dates(self, calendar: list[str]) -> dict:
        return asdict(self) | {k: calendar[getattr(self, k)] for k in
                               ("train_start", "train_end", "test_start", "test_end")}


def assert_separation(splits: list[Split]) -> None:
    previous_end = None
    for split in splits:
        if not split.train_start <= split.train_end:
            raise LeakageError(f"divisão {split.index}: treino vazio")
        if split.horizon < 0 or split.embargo < 0:
            raise LeakageError(f"divisão {split.index}: horizonte/embargo negativos")
        if not split.train_end + split.horizon + split.embargo < split.test_start <= split.test_end:
            raise LeakageError(f"divisão {split.index}: treino + horizonte + embargo alcança o teste")
        if previous_end is not None and split.test_start <= previous_end:
            raise LeakageError(f"divisão {split.index}: testes sobrepostos")
        previous_end = split.test_end


def walk_forward_splits(n_sessions: int, *, min_train: int, test_size: int, horizon: int, embargo: int,
                        first_test_start: int | None = None, last: int | None = None,
                        train_window: int | None = None) -> list[Split]:
    """Treino expansivo (ou janela móvel de ``train_window`` pregões), testes contíguos de ``test_size``."""
    if min(min_train, test_size) < 1 or min(horizon, embargo) < 0:
        raise ValueError("min_train, test_size >= 1; horizon, embargo >= 0")
    last = n_sessions - 1 if last is None else last
    gap = horizon + embargo
    start = min_train + gap if first_test_start is None else first_test_start
    splits = []
    while start + test_size - 1 <= last:
        train_end = start - gap - 1
        train_start = 0 if train_window is None else max(0, train_end - train_window + 1)
        if train_end - train_start + 1 < min_train:
            raise ValueError("treino menor que min_train")
        splits.append(Split(len(splits), train_start, train_end, start, start + test_size - 1, horizon, embargo))
        start += test_size
    if not splits:
        raise ValueError("nenhuma divisão cabe no calendário")
    assert_separation(splits)
    return splits


class _Routed(Strategy):
    def __init__(self, dataset: PITDataset, fitted: list[tuple[Split, Strategy]]):
        self._dataset, self._fitted = dataset, fitted
        self.name = "walk_forward:" + fitted[0][1].name
        self.universe_free = any(model.universe_free for _split, model in fitted)

    def describe(self) -> dict:
        return {"name": self.name, "models": [model.describe() for _split, model in self._fitted]}

    def targets(self, ctx: DecisionContext):
        executed = self._dataset.position(ctx.execution_session)
        for split, model in self._fitted:
            if split.test_start <= executed <= split.test_end:
                if self._dataset.position(ctx.signal_session) <= split.train_end:
                    raise LeakageError("sinal dentro do treino do próprio modelo")
                return model.targets(ctx)
        raise LeakageError(f"execução {ctx.execution_session} fora das janelas de teste")


def run_walk_forward(dataset: PITDataset, fit: Callable[[PITView, Split], Strategy], config: ProtocolConfig,
                     splits: list[Split]) -> tuple[BacktestResult, list[dict]]:
    """Ajusta um modelo por divisão só com a visão do fim do treino e avalia os testes num backtest contínuo."""
    assert_separation(splits)
    cal = dataset.calendar
    fitted = []
    for split in splits:
        train_view = dataset.view(cal[split.train_end + 1])  # enxerga pregões <= train_end
        fitted.append((split, fit(train_view, split)))
    window = config.with_window(cal[splits[0].test_start], cal[splits[-1].test_end])
    result = run_backtest(dataset, _Routed(dataset, fitted), window)
    return result, [split.dates(cal) | {"model": model.describe()} for split, model in fitted]


__all__ = ["LeakageError", "Split", "assert_separation", "run_walk_forward", "walk_forward_splits"]
