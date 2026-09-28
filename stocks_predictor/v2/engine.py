"""Motor de avaliação v2: carteira por quantidades, caixa, custos explícitos, eventos societários e liquidez.

Ciclo de cada pregão ``s`` da janela ``[start, end]``:

1. Decisão (se ``s`` é execução de um sinal agendado): ``PITView`` do pregão seguinte ao sinal, universo PIT
   (listado + ADV mínimo), pesos atuais pelas marcas até o fechamento anterior; a estratégia devolve pesos-alvo
   (ou ``None`` = manter).
2. Eventos realizados com data ex ``s``: multiplicador de ações (desdobramento/grupamento/bonificação) e proventos
   em dinheiro por ação detida (vendido paga).
3. Deslistagem: posição em papel cujo último pregão já passou sai pelo ``delisting_value`` (ou último fechamento)
   com custos de negociação.
4. Execução no preço da convenção (sinal em ``D``, execução em ``D+lag``): vendas antes de compras, cada ordem
   limitada a ``max_participation × ADV`` da decisão, compras limitadas pelo caixa (sem alavancagem), custos
   debitados; sem barra no pregão = ordem não executada.
5. Aluguel sobre vendidos; marcação no fechamento; NAV.

A janela começa em caixa: o primeiro sinal é o fechamento anterior a ``start`` (carteira formada na execução
seguinte). Métricas são líquidas; ``evaluate`` também roda a mesma estratégia com custo zero (bruto) só para
decompor o custo.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field, replace
from datetime import date

from .costs import COMPONENTS, CostModel, LiquidityRule
from .dataset import PITDataset, PITView, canonical
from .execution import ExecutionConvention

ENGINE_VERSION = "stocks-pit-engine-v2/1"
FREQUENCIES = ("weekly", "monthly", "quarterly")
_TOL = 1e-9


class ProtocolError(ValueError):
    """Configuração ou estratégia fora do protocolo (falha fechada)."""


@dataclass(frozen=True)
class ProtocolConfig:
    start: str
    end: str
    rebalance: str
    execution: ExecutionConvention
    costs: CostModel
    liquidity: LiquidityRule
    initial_cash: float = 1_000_000.0
    seed: int = 0
    allow_short: bool = False

    def __post_init__(self):
        if self.rebalance not in FREQUENCIES:
            raise ProtocolError(f"rebalance: {FREQUENCIES}")
        if not (isinstance(self.initial_cash, (int, float)) and math.isfinite(self.initial_cash) and self.initial_cash > 0):
            raise ProtocolError("initial_cash > 0")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ProtocolError("seed inteiro")
        if self.start > self.end:
            raise ProtocolError("start > end")

    def with_costs(self, costs: CostModel) -> "ProtocolConfig":
        return replace(self, costs=costs)

    def with_window(self, start: str, end: str) -> "ProtocolConfig":
        return replace(self, start=start, end=end)

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "rebalance": self.rebalance,
                "execution": self.execution.to_dict(), "costs": self.costs.to_dict(),
                "liquidity": self.liquidity.to_dict(), "initial_cash": self.initial_cash, "seed": self.seed,
                "allow_short": self.allow_short, "engine": ENGINE_VERSION}


@dataclass(frozen=True)
class DecisionContext:
    view: PITView
    signal_session: str
    execution_session: str
    universe: tuple[str, ...]
    weights: dict[str, float]
    rng: random.Random


class Strategy:
    """Estratégia: pesos-alvo a partir só da ``DecisionContext``. ``universe_free`` libera o universo (índice)."""

    name = "strategy"
    universe_free = False

    def describe(self) -> dict:
        return {"name": self.name}

    def targets(self, ctx: DecisionContext) -> dict[str, float] | None:
        raise NotImplementedError


@dataclass
class BacktestResult:
    config: dict
    dataset_hash: str
    strategy: dict
    sessions: list[str]
    nav: list[float]
    returns: list[float]
    trades: list[dict]
    events: list[dict]
    decisions: list[dict]
    metrics: dict = field(default_factory=dict)

    def payload(self) -> dict:
        return {"config": self.config, "dataset_hash": self.dataset_hash, "strategy": self.strategy,
                "sessions": self.sessions, "nav": self.nav, "returns": self.returns, "trades": self.trades,
                "events": self.events, "decisions": self.decisions, "metrics": self.metrics}

    @property
    def digest(self) -> str:
        return hashlib.sha256(canonical(self.payload())).hexdigest()


def rebalance_signals(calendar: list[str], first: int, last: int, frequency: str) -> list[int]:
    """Índices de pregões de sinal em ``[first, last]``: o primeiro sempre, depois o último pregão de cada
    semana ISO, mês ou trimestre."""
    def period(session: str):
        d = date.fromisoformat(session)
        if frequency == "weekly":
            return d.isocalendar()[:2]
        if frequency == "monthly":
            return d.year, d.month
        return d.year, (d.month - 1) // 3
    out = [first] if first <= last else []
    for i in range(first + 1, last + 1):
        if i + 1 >= len(calendar) or period(calendar[i]) != period(calendar[i + 1]):
            out.append(i)
    return out


def decision_universe(view: PITView, rule: LiquidityRule) -> tuple[str, ...]:
    """Ações listadas conhecidas na decisão com ADV >= mínimo (pregões sem negócio contam zero)."""
    return tuple(sid for sid in view.listed_ids("equity")
                 if view.average_daily_value(sid, rule.adv_lookback, rule.statistic) >= max(rule.min_adv, _TOL))


def _check_targets(targets: dict, ctx: DecisionContext, strategy: Strategy, config: ProtocolConfig) -> dict[str, float]:
    if type(targets) is not dict:
        raise ProtocolError(f"{strategy.name}: alvo deve ser dict ou None")
    out = {}
    allowed = set(ctx.universe)
    for sid, weight in targets.items():
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not math.isfinite(weight):
            raise ProtocolError(f"{strategy.name}: peso inválido para {sid}")
        if not ctx.view.listed(sid):
            raise ProtocolError(f"{strategy.name}: {sid} não era listado/conhecido na decisão de {ctx.signal_session}")
        if not strategy.universe_free and sid not in allowed:
            raise ProtocolError(f"{strategy.name}: {sid} fora do universo PIT de {ctx.signal_session}")
        if weight < 0 and not config.allow_short:
            raise ProtocolError(f"{strategy.name}: venda a descoberto desabilitada")
        if weight:
            out[sid] = float(weight)
    if sum(abs(w) for w in out.values()) > 1 + 1e-9:
        raise ProtocolError(f"{strategy.name}: exposição bruta > 1 (sem alavancagem)")
    return out


def run_backtest(dataset: PITDataset, strategy: Strategy, config: ProtocolConfig) -> BacktestResult:
    cal = dataset.calendar
    first, last = dataset.position(config.start), dataset.position(config.end)
    if first < 1:
        raise ProtocolError("start precisa de ao menos um pregão anterior (o sinal inicial)")
    lag = config.execution.lag_sessions
    signal_indices = [i for i in rebalance_signals(cal, first - 1, last - lag, config.rebalance)]
    by_execution = {config.execution.execution_index(i): i for i in signal_indices}
    costs, rule, conv = config.costs, config.liquidity, config.execution
    cash = float(config.initial_cash)
    qty: dict[str, float] = {}
    mark: dict[str, float] = {}
    sessions, navs, returns, trades, events, decisions = [], [], [], [], [], []
    previous_nav = cash

    def pay(breakdown: dict[str, float]) -> float:
        return sum(breakdown[k] for k in COMPONENTS)

    for i in range(first, last + 1):
        s = cal[i]
        # 1. decisão (antes da abertura; estado até o fechamento anterior)
        order_book = None
        if i in by_execution:
            signal = by_execution[i]
            view = dataset.view(cal[signal + 1])
            nav_mark = cash + sum(q * mark[sid] for sid, q in qty.items())
            weights = {sid: q * mark[sid] / nav_mark for sid, q in qty.items() if q} if nav_mark > 0 else {}
            universe = decision_universe(view, rule)
            ctx = DecisionContext(view, cal[signal], s, universe, weights,
                                  random.Random(f"{config.seed}:{strategy.name}:{cal[signal]}"))
            raw = strategy.targets(ctx)
            decision = {"signal_session": cal[signal], "decision_at": view.decision_at, "execution_session": s,
                        "universe_size": len(universe), "hold": raw is None}
            if raw is not None:
                order_book = (ctx, _check_targets(raw, ctx, strategy, config))
                decision["targets"] = dict(sorted(order_book[1].items()))
            decisions.append(decision)
        # 2. eventos realizados com data ex em s
        for sid in sorted(qty):
            for multiplier in dataset.realized_actions(sid, s):
                qty[sid] *= multiplier
                mark[sid] /= multiplier
                events.append({"session": s, "security_id": sid, "event": "share_multiplier", "value": multiplier})
            amount = dataset.realized_cash(sid, s)
            if amount and qty[sid]:
                cash += qty[sid] * amount
                events.append({"session": s, "security_id": sid, "event": "cash", "value": qty[sid] * amount})
        # 3. deslistagem: sai pelo valor de saída com custo de negociação
        for sid in sorted(qty):
            info = dataset.securities[sid]
            if qty[sid] and info["delisted_on"] is not None and info["delisted_on"] < s:
                price = mark[sid] if info["delisting_value"] is None else info["delisting_value"]
                notional = abs(qty[sid]) * price
                breakdown = costs.order_cost(notional, math.inf)
                cash += (notional if qty[sid] > 0 else -notional) - pay(breakdown)
                events.append({"session": s, "security_id": sid, "event": "delisting", "quantity": qty[sid],
                               "price": price, "costs": breakdown})
                qty[sid] = 0.0
        # 4. execução
        if order_book is not None:
            ctx, targets = order_book
            cash = _execute(dataset, ctx, targets, conv, costs, rule, qty, mark, cash, trades, config.allow_short)
        # 5. marcação no fechamento, aluguel dos vendidos e NAV
        for sid in [sid for sid, q in qty.items() if not q]:
            del qty[sid]
        for sid in sorted(qty):
            bar = dataset.realized_bar(sid, s)
            if bar is not None:
                mark[sid] = bar.close
            if qty[sid] < 0:
                fee = costs.borrow_cost(qty[sid] * mark[sid])
                cash -= fee
                if fee:
                    events.append({"session": s, "security_id": sid, "event": "borrow", "value": fee})
        nav = cash + sum(q * mark[sid] for sid, q in qty.items())
        sessions.append(s)
        navs.append(nav)
        returns.append(nav / previous_nav - 1 if previous_nav > 0 else 0.0)
        previous_nav = nav
    result = BacktestResult(config.to_dict(), dataset.hash, strategy.describe(), sessions, navs, returns,
                            trades, events, decisions)
    result.metrics = performance(result, config)
    return result


def _execute(dataset, ctx, targets, conv, costs, rule, qty, mark, cash, trades, allow_short) -> float:
    s = ctx.execution_session
    bars = {sid: dataset.realized_bar(sid, s) for sid in sorted(set(qty) | set(targets))}
    reference = "close" if conv.price == "close" else "open"
    nav_exec = cash + sum(q * (getattr(bars[sid], reference) if bars[sid] else mark[sid]) for sid, q in qty.items())
    orders = []
    for sid in sorted(bars):
        bar = bars[sid]
        current = qty.get(sid, 0.0)
        record = {"signal_session": ctx.signal_session, "decision_at": ctx.view.decision_at, "session": s,
                  "security_id": sid, "price_field": conv.price}
        if bar is None:
            if abs(targets.get(sid, 0.0) * nav_exec) > _TOL or current:
                wanted = targets.get(sid, 0.0) * nav_exec / mark[sid] - current if sid in mark else None
                if wanted is None or abs(wanted) > _TOL:
                    trades.append(record | {"status": "unfilled", "reason": "no_bar", "requested_quantity": wanted})
            continue
        delta = targets.get(sid, 0.0) * nav_exec / getattr(bar, reference) - current
        if abs(delta) * getattr(bar, reference) <= _TOL * max(nav_exec, 1.0):
            continue
        side = 1 if delta > 0 else -1
        adv = ctx.view.average_daily_value(sid, rule.adv_lookback, rule.statistic)
        orders.append((side, sid, delta, conv.fill_price(bar, side), adv, record))
    # vendas antes das compras
    for side, sid, delta, price, adv, record in [o for o in orders if o[0] == -1]:
        requested = abs(delta) * price
        notional = min(requested, rule.max_participation * adv)
        if not allow_short:
            notional = min(notional, qty.get(sid, 0.0) * price)
        limited = "participation_cap" if notional < requested * (1 - 1e-12) else None
        cash = _fill(record, sid, -1, price, requested, notional, adv, limited, costs, qty, cash, trades)
    buys = [o for o in orders if o[0] == 1]
    capped = [min(abs(delta) * price, rule.max_participation * adv) for _s, _sid, delta, price, adv, _r in buys]
    scale = _affordable_scale(capped, [o[4] for o in buys], costs, cash)
    for (side, sid, delta, price, adv, record), cap in zip(buys, capped):
        requested = abs(delta) * price
        limited = "participation_cap" if cap < requested * (1 - 1e-12) else ("cash" if scale < 1 else None)
        cash = _fill(record, sid, 1, price, requested, cap * scale, adv, limited, costs, qty, cash, trades)
    return cash


def _affordable_scale(notionals: list[float], advs: list[float], costs: CostModel, cash: float) -> float:
    def need(k: float) -> float:
        return sum(n * k + sum(costs.order_cost(n * k, a).values()) for n, a in zip(notionals, advs) if n * k > 0)
    if not notionals or need(1.0) <= cash:
        return 1.0
    if cash <= 0:
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if need(mid) <= cash else (lo, mid)
    return lo


def _fill(record, sid, side, price, requested, notional, adv, limited, costs, qty, cash, trades) -> float:
    notional = max(notional, 0.0)
    if notional <= _TOL:
        trades.append(record | {"status": "unfilled", "reason": limited or "participation_cap", "side": side,
                                "requested_notional": requested})
        return cash
    breakdown = costs.order_cost(notional, adv)
    quantity = notional / price
    qty[sid] = qty.get(sid, 0.0) + side * quantity
    if abs(qty[sid]) * price <= _TOL:
        qty[sid] = 0.0
    cash += -side * notional - sum(breakdown.values())
    trades.append(record | {"status": "partial" if limited else "filled", "limited_by": limited, "side": side,
                            "quantity": quantity, "price": price, "notional": notional,
                            "requested_notional": requested, "participation": notional / adv if adv > 0 else None,
                            "costs": breakdown})
    return cash


def performance(result: BacktestResult, config: ProtocolConfig) -> dict:
    """Métricas líquidas. Sharpe aqui é com rf = 0 (o excesso sobre CDI/Selic é do Prompt 3b)."""
    per_year = config.costs.sessions_per_year
    rets, nav = result.returns, result.nav
    n = len(rets)
    total = nav[-1] / config.initial_cash - 1 if nav else 0.0
    mean = sum(rets) / n if n else 0.0
    var = sum((r - mean) ** 2 for r in rets) / (n - 1) if n > 1 else 0.0
    vol = math.sqrt(var)
    peak, drawdown = config.initial_cash, 0.0
    for value in nav:
        peak = max(peak, value)
        drawdown = min(drawdown, value / peak - 1)
    filled = [t for t in result.trades if t["status"] in ("filled", "partial")]
    component = {k: sum(t["costs"][k] for t in filled) for k in COMPONENTS}
    for event in result.events:
        if event["event"] == "delisting":
            for k in COMPONENTS:
                component[k] += event["costs"][k]
    borrow = sum(e["value"] for e in result.events if e["event"] == "borrow")
    traded = sum(t["notional"] for t in filled)
    mean_nav = sum(nav) / n if n else config.initial_cash
    years = n / per_year if n else 0.0
    return {
        "sessions": n,
        "final_nav": nav[-1] if nav else config.initial_cash,
        "total_return": total,
        "cagr": (1 + total) ** (1 / years) - 1 if years and total > -1 else None,
        "ann_vol": vol * math.sqrt(per_year),
        "sharpe_ann_rf0": mean / vol * math.sqrt(per_year) if vol > 0 else None,
        "max_drawdown": drawdown,
        "turnover_ann": traded / mean_nav / years if years and mean_nav > 0 else 0.0,
        "costs_total": sum(component.values()) + borrow,
        "costs_by_component": component | {"borrow": borrow},
        "trades_filled": len(filled),
        "trades_partial_participation": sum(1 for t in filled if t.get("limited_by") == "participation_cap"),
        "trades_partial_cash": sum(1 for t in filled if t.get("limited_by") == "cash"),
        "orders_unfilled": sum(1 for t in result.trades if t["status"] == "unfilled"),
        "rebalances": len(result.decisions),
        "metrics_are": "net of all modeled costs; sharpe with rf=0",
    }


def evaluate(dataset: PITDataset, strategy: Strategy, config: ProtocolConfig) -> dict:
    """Resultado líquido (principal) e bruto (mesma estratégia com custo zero), mais o digest reprodutível."""
    net = run_backtest(dataset, strategy, config)
    gross = run_backtest(dataset, strategy, config.with_costs(CostModel.zero()))
    return {"net": net.metrics, "gross": gross.metrics, "result_digest": net.digest,
            "cost_drag_total_return": gross.metrics["total_return"] - net.metrics["total_return"]}


__all__ = ["BacktestResult", "DecisionContext", "ENGINE_VERSION", "FREQUENCIES", "ProtocolConfig", "ProtocolError",
           "Strategy", "decision_universe", "evaluate", "performance", "rebalance_signals", "run_backtest"]
