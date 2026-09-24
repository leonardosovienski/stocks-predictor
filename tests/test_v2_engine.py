"""Protocolo v2 — execução, custos, liquidez, baselines, walk-forward e reprodutibilidade."""

import random

import pytest

from stocks_predictor.v2 import synthetic
from stocks_predictor.v2.baselines import (EqualWeightUniverse, IndexBuyAndHold, Momentum12_1, NaiveLastReturn,
                                           RandomPortfolio, RandomWalkForecaster, evaluate_forecasters,
                                           forward_return)
from stocks_predictor.v2.costs import CostModel, LiquidityRule
from stocks_predictor.v2.dataset import PITDataset
from stocks_predictor.v2.engine import (DecisionContext, ProtocolConfig, ProtocolError, Strategy,
                                        decision_universe, evaluate, rebalance_signals, run_backtest)
from stocks_predictor.v2.execution import ExecutionConvention, ExecutionError
from stocks_predictor.v2.walkforward import (LeakageError, Split, assert_separation, run_walk_forward,
                                             walk_forward_splits)

RAW = synthetic.build()
DS = PITDataset(RAW)
COSTS = CostModel(brokerage_bps=2.0, brokerage_fixed=5.0, exchange_fee_bps=3.0, spread_bps=7.5, slippage_bps=7.5,
                  impact_bps_at_full_adv=50.0, impact_exponent=0.5, borrow_bps_annual=300.0)
LIQ = LiquidityRule(min_adv=1e6, adv_lookback=63, max_participation=0.05)


def config(**overrides):
    base = dict(start="2020-01-02", end="2021-06-30", rebalance="monthly", execution=ExecutionConvention(),
                costs=COSTS, liquidity=LIQ, seed=11)
    return ProtocolConfig(**(base | overrides))


BASELINES = [EqualWeightUniverse(), IndexBuyAndHold("IDX11"), Momentum12_1(), RandomPortfolio(4)]


# -- obrigatório: execução nunca no fechamento que gerou o sinal -----------------------------------
@pytest.mark.parametrize("convention", [ExecutionConvention(1, "open"), ExecutionConvention(1, "close"),
                                        ExecutionConvention(2, "worst")])
def test_no_trade_uses_the_close_that_generated_the_signal(convention):
    for strategy in (EqualWeightUniverse(), Momentum12_1()):
        result = run_backtest(DS, strategy, config(execution=convention))
        filled = [t for t in result.trades if t["status"] != "unfilled"]
        assert filled
        for trade in filled:
            gap = DS.position(trade["session"]) - DS.position(trade["signal_session"])
            assert gap == convention.lag_sessions >= 1
            assert trade["decision_at"] < trade["session"] + "T13:00:00Z"  # decisão antes da abertura
            bar = DS.realized_bar(trade["security_id"], trade["session"])
            expected = {"open": bar.open, "close": bar.close,
                        "worst": max(bar.open, bar.close) if trade["side"] == 1 else min(bar.open, bar.close)}
            assert trade["price"] == expected[convention.price]
            assert trade["session"] > trade["signal_session"]


def test_same_close_execution_is_not_representable():
    with pytest.raises(ExecutionError, match="proibida"):
        ExecutionConvention(lag_sessions=0)
    with pytest.raises(ExecutionError):
        ExecutionConvention(lag_sessions=1, price="vwap")


class Spy(Strategy):
    name = "spy"

    def __init__(self):
        self.seen = []

    def targets(self, ctx):
        last = max((ctx.view.history(sid)[0][-1] for sid in ctx.universe if ctx.view.history(sid)[0]), default=None)
        self.seen.append((ctx.signal_session, ctx.execution_session, last, ctx.view.decision_at))
        return {sid: 1 / len(ctx.universe) for sid in ctx.universe}


def test_signal_only_sees_bars_up_to_the_signal_close():
    spy = Spy()
    run_backtest(DS, spy, config(execution=ExecutionConvention(2, "open")))
    assert spy.seen
    for signal, execution, last, decision_at in spy.seen:
        assert last == signal < execution
        assert decision_at[:10] <= execution


# -- obrigatório: custos --------------------------------------------------------------------------
@pytest.mark.parametrize("strategy", BASELINES, ids=lambda s: s.name)
def test_net_result_is_monotonically_non_increasing_in_costs(strategy):
    finals = [run_backtest(DS, strategy, config(costs=COSTS.scaled(k))).metrics["final_nav"]
              for k in (0.0, 0.5, 1.0, 2.0, 4.0, 8.0)]
    assert all(later <= earlier * (1 + 1e-12) for earlier, later in zip(finals, finals[1:])), finals
    assert finals[-1] < finals[0]


def test_every_cost_component_reduces_the_net_result():
    zero = run_backtest(DS, EqualWeightUniverse(), config(costs=CostModel.zero())).metrics["final_nav"]
    for name in ("brokerage_bps", "brokerage_fixed", "exchange_fee_bps", "spread_bps", "slippage_bps",
                 "impact_bps_at_full_adv"):
        only = CostModel.zero().to_dict() | {name: 10.0}
        result = run_backtest(DS, EqualWeightUniverse(), config(costs=CostModel.from_dict(only)))
        assert result.metrics["final_nav"] < zero, name
        assert result.metrics["costs_total"] > 0


def test_cost_model_is_explicit_and_monotone():
    with pytest.raises(ValueError):
        CostModel.from_dict({"spread_bps": 1.0})
    with pytest.raises(ValueError):
        CostModel.from_dict(COSTS.to_dict() | {"spread_bps": -1.0})
    small, large = COSTS.order_cost(1e5, 1e7), COSTS.order_cost(2e5, 1e7)
    assert all(large[k] >= small[k] for k in small)
    assert COSTS.scaled(2).order_cost(1e5, 1e7)["impact"] == pytest.approx(2 * small["impact"])
    with pytest.raises(ValueError, match="ADV"):
        COSTS.order_cost(1e5, 0.0)


def test_metrics_are_net_and_gross_is_only_a_decomposition():
    out = evaluate(DS, EqualWeightUniverse(), config())
    assert out["net"]["costs_total"] > 0 and out["gross"]["costs_total"] == 0
    assert out["net"]["total_return"] < out["gross"]["total_return"]
    assert out["cost_drag_total_return"] > 0


def test_equal_weight_baseline_pays_the_same_costs_as_any_strategy():
    ew = run_backtest(DS, EqualWeightUniverse(), config())
    fills = [t for t in ew.trades if t["status"] != "unfilled"]
    assert fills
    for t in fills:
        assert t["costs"] == pytest.approx(COSTS.order_cost(t["notional"], t["notional"] / t["participation"]))


# -- liquidez --------------------------------------------------------------------------------------
def test_liquidity_filter_and_participation_cap():
    result = run_backtest(DS, EqualWeightUniverse(), config(liquidity=LiquidityRule(1e6, 63, 0.001)))
    fills = [t for t in result.trades if t["status"] != "unfilled"]
    assert fills and all(t["participation"] <= 0.001 * (1 + 1e-9) for t in fills)
    assert any(t["limited_by"] == "participation_cap" for t in fills)
    for decision in result.decisions:
        assert "ILLQ" not in decision.get("targets", {})
    loose = decision_universe(DS.view("2021-03-01"), LiquidityRule(0.0, 63, 0.05))
    strict = decision_universe(DS.view("2021-03-01"), LiquidityRule(1e6, 63, 0.05))
    assert "ILLQ" in loose and "ILLQ" not in strict


# -- sobrevivência no motor ------------------------------------------------------------------------
def test_delisted_holdings_leave_at_delisting_value_and_bankruptcy_hurts():
    result = run_backtest(DS, EqualWeightUniverse(), config())
    exits = {e["security_id"]: e for e in result.events if e["event"] == "delisting"}
    assert exits["BUST"]["price"] == 0.0 and exits["BUST"]["session"] == "2020-07-01"
    assert exits["DEL1"]["session"] == "2020-10-01"
    held = [d for d in result.decisions if "BUST" in d.get("targets", {})]
    assert held and max(d["signal_session"] for d in held) <= "2020-06-30"


# -- baselines -------------------------------------------------------------------------------------
def test_index_buy_and_hold_buys_once_and_holds():
    result = run_backtest(DS, IndexBuyAndHold("IDX11"), config())
    fills = [t for t in result.trades if t["status"] != "unfilled"]
    assert {t["security_id"] for t in fills} == {"IDX11"}
    assert len(fills) <= 2 and sum(d["hold"] for d in result.decisions) >= len(result.decisions) - 2


def test_momentum_uses_the_top_quintile_of_12_1_scores():
    view = DS.view("2021-01-04")
    universe = decision_universe(view, LIQ)
    strategy = Momentum12_1()
    scores = strategy.scores(view, universe)
    assert scores and set(scores) <= set(universe)
    assert "IPO1" not in scores  # sem 252 pregões de histórico
    ctx = DecisionContext(view, view.signal_session, "2021-01-04", universe, {}, random.Random(0))
    targets = strategy.targets(ctx)
    best = sorted(scores, key=lambda s: -scores[s])[: len(targets)]
    assert set(targets) == set(best) and sum(targets.values()) == pytest.approx(1)


def test_random_portfolio_is_seeded_and_keeps_position_count():
    a = run_backtest(DS, RandomPortfolio(4), config())
    b = run_backtest(DS, RandomPortfolio(4), config())
    c = run_backtest(DS, RandomPortfolio(4), config(seed=12))
    assert a.digest == b.digest != c.digest
    assert all(len(d["targets"]) == 4 for d in a.decisions)


def test_naive_and_random_walk_forecasts_score_against_execution_prices():
    out = evaluate_forecasters(DS, config(), [RandomWalkForecaster(), NaiveLastReturn()], horizon=21)
    rw, naive = out["metrics"]["random_walk"], out["metrics"]["naive_last_return"]
    assert rw["n"] > 100 and naive["n"] > 100 and rw["hit_rate"] is None
    signal, sid, _forecast, realized = out["pairs"]["random_walk"][0]
    start = DS.position(signal) + 1
    assert realized == forward_return(DS, sid, start, 21, "open")
    assert all(s < "2021-06-30" for s, *_ in out["pairs"]["random_walk"])


def test_forward_return_accounts_for_split_and_dividends():
    start = DS.position("2020-03-25")
    total = forward_return(DS, "SPL1", start, 10, "open")
    a, b = DS.realized_bar("SPL1", DS.calendar[start]), DS.realized_bar("SPL1", DS.calendar[start + 10])
    assert total == pytest.approx(2 * b.open / a.open - 1)
    start = DS.position("2020-05-25")
    a, b = DS.realized_bar("DIV1", DS.calendar[start]), DS.realized_bar("DIV1", DS.calendar[start + 10])
    assert forward_return(DS, "DIV1", start, 10, "open") == pytest.approx((b.open + 0.45) / a.open - 1)


# -- contrato das estratégias ----------------------------------------------------------------------
class Fixed(Strategy):
    def __init__(self, targets, name="fixed", universe_free=False):
        self._targets, self.name, self.universe_free = targets, name, universe_free

    def targets(self, ctx):
        return self._targets


@pytest.mark.parametrize("targets, message", [
    ({"IPO1": 1.0}, "não era listado"),
    ({"ILLQ": 1.0}, "fora do universo"),
    ({"E01": 0.8, "E02": 0.8}, "exposição bruta"),
    ({"E01": -0.5}, "descoberto"),
    ({"E01": float("nan")}, "peso inválido"),
])
def test_strategy_targets_are_checked_against_the_pit_universe(targets, message):
    with pytest.raises(ProtocolError, match=message):
        run_backtest(DS, Fixed(targets), config(start="2020-01-02", end="2020-03-31"))


def test_short_positions_pay_borrow():
    result = run_backtest(DS, Fixed({"E01": -0.3, "E02": 0.3}), config(allow_short=True))
    borrow = result.metrics["costs_by_component"]["borrow"]
    assert borrow > 0
    no_borrow = CostModel.from_dict(COSTS.to_dict() | {"borrow_bps_annual": 0.0})
    cheaper = run_backtest(DS, Fixed({"E01": -0.3, "E02": 0.3}), config(allow_short=True, costs=no_borrow))
    assert cheaper.metrics["final_nav"] > result.metrics["final_nav"]


def test_protocol_config_is_validated():
    with pytest.raises(ProtocolError):
        config(rebalance="daily")
    with pytest.raises(ProtocolError):
        config(start="2021-01-04", end="2020-01-02")
    with pytest.raises(ProtocolError):
        run_backtest(DS, EqualWeightUniverse(), config(start=DS.calendar[0]))


def test_rebalance_schedule_uses_period_ends():
    cal = DS.calendar
    monthly = [cal[i] for i in rebalance_signals(cal, cal.index("2020-01-02"), cal.index("2020-06-30"), "monthly")]
    assert monthly == ["2020-01-02", "2020-01-31", "2020-02-28", "2020-03-31", "2020-04-30", "2020-05-29",
                       "2020-06-30"]
    weekly = rebalance_signals(cal, 10, 40, "weekly")
    assert len(weekly) >= 6
    assert len(rebalance_signals(cal, 10, 300, "quarterly")) >= 4


# -- obrigatório: reprodutibilidade ---------------------------------------------------------------
@pytest.mark.parametrize("strategy", BASELINES, ids=lambda s: s.name)
def test_same_config_dataset_hash_and_seed_reproduce_the_same_result(strategy):
    again = PITDataset(synthetic.build())
    assert again.hash == DS.hash
    first, second = evaluate(DS, strategy, config()), evaluate(again, strategy, config())
    assert first == second


# -- walk-forward ----------------------------------------------------------------------------------
def test_walk_forward_splits_are_strictly_separated():
    splits = walk_forward_splits(len(DS.calendar), min_train=252, test_size=63, horizon=21, embargo=5)
    assert len(splits) >= 4
    for split in splits:
        assert split.train_end + 21 + 5 < split.test_start
    for a, b in zip(splits, splits[1:]):
        assert b.test_start == a.test_end + 1
    with pytest.raises(LeakageError):
        assert_separation([Split(0, 0, 100, 110, 150, 21, 5)])
    with pytest.raises(LeakageError, match="sobrepostos"):
        assert_separation([Split(0, 0, 100, 130, 150, 21, 5), Split(1, 0, 110, 140, 160, 21, 5)])


def test_walk_forward_fits_only_on_training_data():
    splits = walk_forward_splits(len(DS.calendar), min_train=252, test_size=63, horizon=21, embargo=5)
    seen = []

    def fit(view, split):
        seen.append((view.signal_session, DS.calendar[split.train_end]))
        return Momentum12_1()

    result, fitted = run_walk_forward(DS, fit, config(), splits)
    assert all(last == train_end for last, train_end in seen)
    assert result.sessions[0] == DS.calendar[splits[0].test_start]
    assert result.sessions[-1] == DS.calendar[splits[-1].test_end]
    assert len(fitted) == len(splits) and fitted[0]["model"]["name"] == "momentum_12_1"
    for decision in result.decisions:
        executed = DS.position(decision["execution_session"])
        split = next(s for s in splits if s.test_start <= executed <= s.test_end)
        assert DS.position(decision["signal_session"]) > split.train_end
