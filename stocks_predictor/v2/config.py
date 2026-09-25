"""Leitura da configuração explícita do protocolo v2 (compartilhada pelas CLIs).

Formato (todos os campos obrigatórios; nenhum custo, liquidez ou convenção vem de padrão escondido):

    {"start", "end", "rebalance", "execution": {"lag_sessions", "price"},
     "costs": {todos os campos de CostModel}, "liquidity": {"min_adv", "adv_lookback", "max_participation",
     "statistic"}, "initial_cash", "seed", "allow_short",
     "baselines": {"index_id", "random_positions", "forecast_horizon",
                   "momentum": {"lookback", "skip", "quantile", "max_stale"}}}
"""

from __future__ import annotations

from .costs import CostModel, LiquidityRule
from .engine import ProtocolConfig
from .execution import ExecutionConvention

_TOP = {"start", "end", "rebalance", "execution", "costs", "liquidity", "initial_cash", "seed", "allow_short",
        "baselines"}
_BASELINES = {"index_id", "random_positions", "forecast_horizon", "momentum"}


def load_config(raw: dict) -> tuple[ProtocolConfig, dict]:
    """(ProtocolConfig, parâmetros dos baselines). Campo a mais ou a menos levanta ``ValueError``."""
    if set(raw) != _TOP or set(raw["baselines"]) != _BASELINES:
        raise ValueError(f"configuração: campos exatos {sorted(_TOP)} e baselines {sorted(_BASELINES)}")
    config = ProtocolConfig(start=raw["start"], end=raw["end"], rebalance=raw["rebalance"],
                            execution=ExecutionConvention(**raw["execution"]), costs=CostModel.from_dict(raw["costs"]),
                            liquidity=LiquidityRule(**raw["liquidity"]), initial_cash=raw["initial_cash"],
                            seed=raw["seed"], allow_short=raw["allow_short"])
    return config, raw["baselines"]


__all__ = ["load_config"]
