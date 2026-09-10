"""Dated evidence for offline decisions; no capital authorization or retroactive PIT claim."""
from dataclasses import dataclass
from datetime import datetime
import math

from .economic_gate import EdgeEstimate, estimate_edge
from .source_catalog import utc_timestamp


@dataclass(frozen=True)
class DatedOutcome:
    observation_id: str
    decision_at: str
    matured_at: str
    observed_at: str
    gross_edge: float

    def validate(self) -> None:
        if not self.observation_id.strip() or not math.isfinite(self.gross_edge):
            raise ValueError('outcome identity and finite value required')
        decision, matured, observed = (
            datetime.fromisoformat(utc_timestamp(v))
            for v in (self.decision_at, self.matured_at, self.observed_at)
        )
        if not decision < matured <= observed:
            raise ValueError('outcome must mature after decision and before observation')


def estimate_asof(
    outcomes: list[DatedOutcome], asof: str, *, minimum_observations: int = 12,
    z_score: float = 1.96,
) -> EdgeEstimate | None:
    """Reject future/unmatured/duplicate evidence, rather than silently discarding it.

    This enforces supplied chronology. It cannot prove that a timestamp is truthful,
    that units are independent, or that an already viewed sample is a fresh holdout.
    """
    cutoff = datetime.fromisoformat(utc_timestamp(asof))
    seen: set[str] = set()
    values: list[float] = []
    for outcome in outcomes:
        outcome.validate()
        if outcome.observation_id in seen:
            raise ValueError('duplicate outcome identity')
        if datetime.fromisoformat(utc_timestamp(outcome.observed_at)) >= cutoff:
            raise ValueError('evidence must be observed strictly before the decision cutoff')
        seen.add(outcome.observation_id)
        values.append(outcome.gross_edge)
    return estimate_edge(values, minimum_observations=minimum_observations, z_score=z_score)
