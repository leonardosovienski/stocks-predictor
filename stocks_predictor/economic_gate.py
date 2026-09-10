"""Opt-in arithmetic gate for future, pre-registered stock hypotheses.

The normal standard-error bound assumes suitable independent observations; it
does not correct serial dependence, adaptive search or selection bias. Callers
must attest maturity and chronology: this primitive has no date information.
It is not wired to a live strategy and never enables capital.
"""
from dataclasses import dataclass
import math
import statistics


@dataclass(frozen=True)
class EdgeEstimate:
    mean_gross_edge: float
    lower_gross_edge: float
    observations: int


@dataclass(frozen=True)
class RebalanceDecision:
    action: str
    expected_gross_edge: float | None
    lower_gross_edge: float | None
    turnover_cost: float
    conservative_net_edge: float | None
    observations: int
    reason: str
    capital_enabled: bool = False


def estimate_edge(observations, *, minimum_observations=12, z_score=1.96):
    """Estimate a conservative edge from already-matured period observations."""
    if type(minimum_observations) is not int or minimum_observations < 2 or not math.isfinite(z_score) or z_score < 0:
        raise ValueError("minimum_observations deve ser >= 2 e z_score >= 0")
    xs = [float(x) for x in observations]
    if any(not math.isfinite(x) for x in xs):
        raise ValueError("observations must be finite; missing outcomes cannot be silently dropped")
    if len(xs) < minimum_observations:
        return None
    mean = statistics.mean(xs)
    standard_error = statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0
    lower = mean - z_score * standard_error
    if not math.isfinite(mean) or not math.isfinite(lower):
        raise ValueError("nonfinite edge estimate")
    return EdgeEstimate(mean, lower, len(xs))


def decide_rebalance(estimate, turnover_cost, *, minimum_net_edge=0.0):
    """Rebalance only when the lower edge pays turnover cost plus the hurdle."""
    if any(not math.isfinite(x) or x < 0 for x in (turnover_cost, minimum_net_edge)):
        raise ValueError("turnover_cost e minimum_net_edge devem ser >= 0")
    if estimate is None:
        return RebalanceDecision(
            "HOLD", None, None, turnover_cost, None, 0,
            "amostra madura insuficiente")
    if (any(not math.isfinite(x) for x in (estimate.mean_gross_edge, estimate.lower_gross_edge))
            or estimate.lower_gross_edge > estimate.mean_gross_edge
            or type(estimate.observations) is not int or estimate.observations < 2):
        raise ValueError("invalid supplied edge estimate")
    conservative_net = estimate.lower_gross_edge - turnover_cost
    action = "REBALANCE" if conservative_net > minimum_net_edge else "HOLD"
    reason = ("edge conservador paga custo e hurdle" if action == "REBALANCE"
              else "edge conservador não paga custo e hurdle")
    return RebalanceDecision(
        action, estimate.mean_gross_edge, estimate.lower_gross_edge,
        turnover_cost, conservative_net, estimate.observations, reason)


class EconomicRebalanceGate:
    """Uses previously supplied outcomes; the caller must enforce their maturity."""

    def __init__(self, *, minimum_observations=12, z_score=1.96,
                 minimum_net_edge=0.0):
        if (type(minimum_observations) is not int or minimum_observations < 2
                or any(not math.isfinite(x) or x < 0 for x in (z_score, minimum_net_edge))):
            raise ValueError("política econômica inválida")
        self.minimum_observations = minimum_observations
        self.z_score = z_score
        self.minimum_net_edge = minimum_net_edge
        self._matured_gross_edges = []
        self.audit = []

    @property
    def matured_gross_edges(self):
        return tuple(self._matured_gross_edges)

    def decide(self, turnover_cost):
        estimate = estimate_edge(
            self._matured_gross_edges,
            minimum_observations=self.minimum_observations,
            z_score=self.z_score)
        decision = decide_rebalance(
            estimate, turnover_cost, minimum_net_edge=self.minimum_net_edge)
        self.audit.append(decision)
        return decision

    def observe(self, gross_switch_edge):
        """Append an outcome only after its decision period has matured."""
        value = float(gross_switch_edge)
        if not math.isfinite(value):
            raise ValueError("gross_switch_edge deve ser finito")
        self._matured_gross_edges.append(value)
