import pytest

import economic_gate


def test_insufficient_matured_sample_holds_and_never_enables_capital():
    gate = economic_gate.EconomicRebalanceGate(minimum_observations=3)
    decision = gate.decide(0.002)
    assert decision.action == "HOLD"
    assert decision.observations == 0
    assert decision.capital_enabled is False


def test_conservative_edge_must_pay_turnover_and_hurdle():
    estimate = economic_gate.EdgeEstimate(0.01, 0.006, 24)
    hold = economic_gate.decide_rebalance(estimate, 0.005, minimum_net_edge=0.002)
    trade = economic_gate.decide_rebalance(estimate, 0.003, minimum_net_edge=0.002)
    assert hold.action == "HOLD"
    assert trade.action == "REBALANCE"
    assert trade.conservative_net_edge == pytest.approx(0.003)
    assert trade.capital_enabled is False


def test_decision_is_prequential_and_cannot_see_current_outcome():
    gate = economic_gate.EconomicRebalanceGate(minimum_observations=2, z_score=0.0)
    gate.observe(0.01)
    before = gate.decide(0.001)
    gate.observe(100.0)  # available only after the preceding decision
    after = gate.decide(0.001)
    assert before.action == "HOLD"
    assert before.observations == 0
    assert after.action == "REBALANCE"
    assert after.observations == 2


def test_invalid_cost_or_outcome_fails_high():
    gate = economic_gate.EconomicRebalanceGate()
    with pytest.raises(ValueError):
        gate.decide(-0.01)
    with pytest.raises(ValueError):
        gate.observe(float("nan"))
    with pytest.raises(ValueError):
        economic_gate.EconomicRebalanceGate(minimum_observations=1)
