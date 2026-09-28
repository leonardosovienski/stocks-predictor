"""Convenção de execução explícita.

O sinal de ``D`` usa só barras até o fechamento de ``D`` (a ``PITView`` do pregão ``D+1`` antes da abertura) e é
executado em ``D + lag_sessions`` pregões, ``lag_sessions >= 1``. Executar no fechamento de ``D`` — o mesmo preço
que gerou o sinal — é proibido e não é representável: ``lag_sessions=0`` levanta ``ExecutionError``.

Preço de execução no pregão de execução: ``open`` (padrão, como o pré-registro da H1), ``close`` ou ``worst``
(cenário adverso: a pior das duas para o lado da ordem — compra paga o maior, venda recebe o menor).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .dataset import Bar

PRICES = ("open", "close", "worst")


class ExecutionError(ValueError):
    """Convenção de execução que permitiria usar o preço que gerou o sinal."""


@dataclass(frozen=True)
class ExecutionConvention:
    lag_sessions: int = 1
    price: str = "open"

    def __post_init__(self):
        if isinstance(self.lag_sessions, bool) or not isinstance(self.lag_sessions, int):
            raise ExecutionError("lag_sessions deve ser inteiro")
        if self.lag_sessions < 1:
            raise ExecutionError("execução no fechamento do pregão do sinal é proibida: lag_sessions >= 1")
        if self.price not in PRICES:
            raise ExecutionError(f"price deve ser um de {PRICES}")

    def execution_index(self, signal_index: int) -> int:
        return signal_index + self.lag_sessions

    def fill_price(self, bar: Bar, side: int) -> float:
        """Preço bruto negociado no pregão de execução; ``side`` +1 compra, -1 venda."""
        if side not in (1, -1):
            raise ValueError("side: +1 compra, -1 venda")
        if self.price == "open":
            return bar.open
        if self.price == "close":
            return bar.close
        return max(bar.open, bar.close) if side == 1 else min(bar.open, bar.close)

    def to_dict(self) -> dict:
        return asdict(self) | {"signal_data": "bars <= close(D)", "execution": f"D+{self.lag_sessions} {self.price}"}


__all__ = ["ExecutionConvention", "ExecutionError", "PRICES"]
