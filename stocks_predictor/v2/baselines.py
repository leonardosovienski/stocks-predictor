"""Baselines no mesmo universo PIT, período, custos e protocolo das estratégias avaliadas.

Carteira (rodam no ``engine.run_backtest`` com a mesma ``ProtocolConfig``):
    EqualWeightUniverse   EW do universo PIT, rebalanceado na mesma frequência
    IndexBuyAndHold       compra o fundo de índice (``kind="index_fund"``) e mantém; caixa de proventos só é
                          reinvestido quando passa de ``sweep`` do NAV
    Momentum12_1          retorno de [D-252, D-21] pregões na série ajustada PIT; quintil superior, EW
    RandomPortfolio       n papéis sorteados do universo PIT a cada rebalanceamento (semente registrada)

Previsão (``evaluate_forecasters``): passeio aleatório (retorno previsto 0) e ingênuo (último retorno de h
pregões persiste), contra o retorno realizado de h pregões a partir do preço de execução — nunca do fechamento
que gerou a previsão.
"""

from __future__ import annotations

import hashlib
import math
from bisect import bisect_left, bisect_right

from .dataset import PITDataset, PITView, canonical
from .engine import DecisionContext, ProtocolConfig, Strategy, decision_universe, rebalance_signals


class EqualWeightUniverse(Strategy):
    name = "ew_universe"

    def targets(self, ctx: DecisionContext) -> dict[str, float]:
        n = len(ctx.universe)
        return {sid: 1.0 / n for sid in ctx.universe} if n else {}


class IndexBuyAndHold(Strategy):
    name = "index_buy_and_hold"
    universe_free = True

    def __init__(self, index_id: str, sweep: float = 0.02):
        if not 0 <= sweep < 1:
            raise ValueError("sweep em [0, 1)")
        self.index_id, self.sweep = index_id, sweep

    def describe(self) -> dict:
        return {"name": self.name, "index_id": self.index_id, "sweep": self.sweep}

    def targets(self, ctx: DecisionContext) -> dict[str, float] | None:
        if not ctx.view.listed(self.index_id):
            return None
        if ctx.weights.get(self.index_id, 0.0) >= 1 - self.sweep:
            return None
        return {self.index_id: 1.0}


def close_at(view: PITView, sid: str, sessions_back: int, max_stale: int) -> float | None:
    """Fechamento ajustado conhecido em ``calendar[-1 - sessions_back]`` (ou até ``max_stale`` pregões antes)."""
    cal = view.calendar
    target = len(cal) - 1 - sessions_back
    if target < 0:
        return None
    sessions, _opens, closes, _volumes = view.history(sid)
    j = bisect_right(sessions, cal[target]) - 1
    if j < 0 or target - bisect_left(cal, sessions[j]) > max_stale:
        return None
    return closes[j]


class Momentum12_1(Strategy):
    name = "momentum_12_1"

    def __init__(self, lookback: int = 252, skip: int = 21, quantile: float = 0.2, max_stale: int = 5):
        if not 0 < skip < lookback or not 0 < quantile <= 1 or max_stale < 0:
            raise ValueError("momentum: 0 < skip < lookback, 0 < quantile <= 1")
        self.lookback, self.skip, self.quantile, self.max_stale = lookback, skip, quantile, max_stale

    def describe(self) -> dict:
        return {"name": self.name, "lookback": self.lookback, "skip": self.skip, "quantile": self.quantile,
                "max_stale": self.max_stale}

    def scores(self, view: PITView, universe) -> dict[str, float]:
        out = {}
        for sid in universe:
            recent = close_at(view, sid, self.skip, self.max_stale)
            old = close_at(view, sid, self.lookback, self.max_stale)
            if recent is not None and old is not None:
                out[sid] = recent / old - 1
        return out

    def targets(self, ctx: DecisionContext) -> dict[str, float]:
        scores = self.scores(ctx.view, ctx.universe)
        if not scores:
            return {}
        ranked = sorted(scores, key=lambda sid: (-scores[sid], sid))
        top = ranked[: max(1, math.ceil(len(ranked) * self.quantile))]
        return {sid: 1.0 / len(top) for sid in top}


class RandomPortfolio(Strategy):
    def __init__(self, n_positions: int):
        if n_positions < 1:
            raise ValueError("n_positions >= 1")
        self.n_positions = n_positions
        self.name = f"random_{n_positions}"

    def describe(self) -> dict:
        return {"name": self.name, "n_positions": self.n_positions}

    def targets(self, ctx: DecisionContext) -> dict[str, float]:
        chosen = ctx.rng.sample(list(ctx.universe), min(self.n_positions, len(ctx.universe)))
        return {sid: 1.0 / len(chosen) for sid in sorted(chosen)} if chosen else {}


# -- previsão ------------------------------------------------------------------------------------
class RandomWalkForecaster:
    name = "random_walk"

    def forecast(self, view: PITView, sid: str, horizon: int) -> float | None:
        return 0.0


class NaiveLastReturn:
    name = "naive_last_return"

    def __init__(self, max_stale: int = 5):
        self.max_stale = max_stale

    def forecast(self, view: PITView, sid: str, horizon: int) -> float | None:
        now = close_at(view, sid, 0, self.max_stale)
        before = close_at(view, sid, horizon, self.max_stale)
        return None if now is None or before is None else now / before - 1


def forward_return(dataset: PITDataset, sid: str, start_index: int, horizon: int, price: str) -> float | None:
    """Retorno total realizado de 1 ação comprada no pregão ``start_index`` e avaliada ``horizon`` pregões
    depois, no mesmo campo de preço; eventos societários e proventos realizados no caminho. ``None`` se faltar
    barra em uma das pontas (o par é excluído e contado)."""
    field = "close" if price == "close" else "open"
    cal = dataset.calendar
    end_index = start_index + horizon
    if end_index >= len(cal):
        return None
    first, last = dataset.realized_bar(sid, cal[start_index]), dataset.realized_bar(sid, cal[end_index])
    if first is None or last is None:
        return None
    shares, cash = 1.0, 0.0
    # eventos com data ex depois da compra e até o pregão final (a compra já é ex dos eventos do próprio dia)
    for i in range(start_index + 1, end_index + 1):
        for multiplier in dataset.realized_actions(sid, cal[i]):
            shares *= multiplier
        cash += shares * dataset.realized_cash(sid, cal[i])
    return (shares * getattr(last, field) + cash) / getattr(first, field) - 1


def evaluate_forecasters(dataset: PITDataset, config: ProtocolConfig, forecasters, horizon: int) -> dict:
    """Pares (previsão, realizado) no universo PIT de cada sinal agendado da janela; realizado começa no pregão
    de execução e termina dentro de ``config.end``."""
    if horizon < 1:
        raise ValueError("horizon >= 1")
    cal = dataset.calendar
    first, last = dataset.position(config.start), dataset.position(config.end)
    lag = config.execution.lag_sessions
    pairs = {f.name: [] for f in forecasters}
    excluded = 0
    for signal in rebalance_signals(cal, first - 1, last - lag - horizon, config.rebalance):
        view = dataset.view(cal[signal + 1])
        start = signal + lag
        for sid in decision_universe(view, config.liquidity):
            realized = forward_return(dataset, sid, start, horizon, config.execution.price)
            if realized is None:
                excluded += 1
                continue
            for f in forecasters:
                value = f.forecast(view, sid, horizon)
                if value is not None:
                    pairs[f.name].append((cal[signal], sid, value, realized))
    metrics = {}
    for name, rows in pairs.items():
        n = len(rows)
        errors = [p - r for _s, _sid, p, r in rows]
        directional = [(p > 0) == (r > 0) for _s, _sid, p, r in rows if p != 0 and r != 0]
        metrics[name] = {"n": n, "mse": sum(e * e for e in errors) / n if n else None,
                         "mae": sum(abs(e) for e in errors) / n if n else None,
                         "hit_rate": sum(directional) / len(directional) if directional else None}
    return {"horizon": horizon, "excluded_pairs": excluded, "metrics": metrics,
            "pairs": {name: rows for name, rows in pairs.items()}}


class ForecastBaselines(Strategy):
    """Previsores ingênuos como uma execução avaliativa do ledger (não é carteira: ``runner`` em vez do motor)."""

    def __init__(self, horizon: int, forecasters=None):
        self.horizon = horizon
        self.forecasters = forecasters or [RandomWalkForecaster(), NaiveLastReturn()]
        self.name = f"forecast_baselines_h{horizon}"

    def describe(self) -> dict:
        return {"name": self.name, "horizon": self.horizon, "forecasters": [f.name for f in self.forecasters]}

    def targets(self, ctx: DecisionContext):
        raise NotImplementedError("previsores não geram carteira")

    @staticmethod
    def runner(dataset: PITDataset, strategy: Strategy, config: ProtocolConfig) -> dict:
        if not isinstance(strategy, ForecastBaselines):
            raise TypeError("runner exclusivo de ForecastBaselines")
        out = evaluate_forecasters(dataset, config, strategy.forecasters, strategy.horizon)
        pairs = out.pop("pairs")
        return out | {"result_digest": hashlib.sha256(canonical(pairs)).hexdigest()}

    @staticmethod
    def primary(result: dict):
        return result["metrics"]["random_walk"]["mse"]


__all__ = ["EqualWeightUniverse", "ForecastBaselines", "IndexBuyAndHold", "Momentum12_1", "NaiveLastReturn",
           "RandomPortfolio", "RandomWalkForecaster", "close_at", "evaluate_forecasters", "forward_return"]
