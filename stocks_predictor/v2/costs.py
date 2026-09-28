"""Custos e liquidez explícitos. Nenhum componente tem valor padrão escondido: a configuração declara todos.

Custo de uma ordem de valor ``N`` (em R$, preço bruto × quantidade), com ``p = N / ADV`` na decisão:

    corretagem   N × brokerage_bps + brokerage_fixed por ordem
    emolumentos  N × exchange_fee_bps           (B3: negociação + liquidação)
    spread       N × spread_bps                  (meio spread pago por lado)
    slippage     N × slippage_bps
    impacto      N × impact_bps_at_full_adv × p ** impact_exponent      (0 desliga)

Aluguel (vendidos): ``|valor vendido| × borrow_bps_annual / sessions_per_year`` por pregão com posição vendida.
Todas as métricas de estratégia do motor v2 são líquidas desses custos.

``LiquidityRule``: na decisão, só entra no universo quem tem ADV >= ``min_adv`` nos últimos ``adv_lookback``
pregões (pregão sem negócio conta como zero); nenhuma ordem passa de ``max_participation × ADV``; o excedente
não é executado (fica registrado como não preenchido).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, fields

COMPONENTS = ("brokerage", "exchange_fee", "spread", "slippage", "impact")


def _finite_non_negative(name: str, value) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name}: número finito >= 0")


@dataclass(frozen=True)
class CostModel:
    brokerage_bps: float
    brokerage_fixed: float
    exchange_fee_bps: float
    spread_bps: float
    slippage_bps: float
    impact_bps_at_full_adv: float
    impact_exponent: float
    borrow_bps_annual: float
    sessions_per_year: int = 252

    def __post_init__(self):
        for f in fields(self):
            _finite_non_negative(f.name, getattr(self, f.name))
        if self.impact_exponent <= 0 or self.impact_exponent > 2:
            raise ValueError("impact_exponent em (0, 2]")
        if isinstance(self.sessions_per_year, bool) or not isinstance(self.sessions_per_year, int) \
                or self.sessions_per_year < 1:
            raise ValueError("sessions_per_year inteiro >= 1")

    @classmethod
    def zero(cls) -> "CostModel":
        return cls(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0)

    @classmethod
    def from_dict(cls, raw: dict) -> "CostModel":
        names = {f.name for f in fields(cls)}
        if set(raw) - names or {f.name for f in fields(cls) if f.name != "sessions_per_year"} - set(raw):
            raise ValueError(f"custos: campos exatos {sorted(names)}")
        return cls(**raw)

    def scaled(self, k: float) -> "CostModel":
        """Todos os componentes monetários multiplicados por ``k`` (o expoente do impacto não muda)."""
        _finite_non_negative("k", k)
        return CostModel(self.brokerage_bps * k, self.brokerage_fixed * k, self.exchange_fee_bps * k,
                         self.spread_bps * k, self.slippage_bps * k, self.impact_bps_at_full_adv * k,
                         self.impact_exponent, self.borrow_bps_annual * k, self.sessions_per_year)

    def order_cost(self, notional: float, adv: float) -> dict[str, float]:
        _finite_non_negative("notional", notional)
        if notional == 0:
            return dict.fromkeys(COMPONENTS, 0.0)
        impact = 0.0
        if self.impact_bps_at_full_adv:
            if not adv > 0:
                raise ValueError("impacto exige ADV > 0")
            impact = notional * self.impact_bps_at_full_adv / 1e4 * (notional / adv) ** self.impact_exponent
        return {
            "brokerage": notional * self.brokerage_bps / 1e4 + self.brokerage_fixed,
            "exchange_fee": notional * self.exchange_fee_bps / 1e4,
            "spread": notional * self.spread_bps / 1e4,
            "slippage": notional * self.slippage_bps / 1e4,
            "impact": impact,
        }

    def borrow_cost(self, short_value: float) -> float:
        """Aluguel de um pregão sobre o valor absoluto da posição vendida."""
        return abs(short_value) * self.borrow_bps_annual / 1e4 / self.sessions_per_year

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LiquidityRule:
    min_adv: float
    adv_lookback: int
    max_participation: float
    statistic: str = "mean"

    def __post_init__(self):
        _finite_non_negative("min_adv", self.min_adv)
        if isinstance(self.adv_lookback, bool) or not isinstance(self.adv_lookback, int) or self.adv_lookback < 1:
            raise ValueError("adv_lookback inteiro >= 1")
        if not (isinstance(self.max_participation, (int, float)) and 0 < self.max_participation <= 1):
            raise ValueError("max_participation em (0, 1]")
        if self.statistic not in ("mean", "median"):
            raise ValueError("statistic: mean | median")

    def to_dict(self) -> dict:
        return asdict(self)


__all__ = ["COMPONENTS", "CostModel", "LiquidityRule"]
